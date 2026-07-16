"""RAG 核心：检索 + 拼提示词 + 生成（支持流式）。

检索采用「向量召回 + 关键词重排 + 阈值过滤 + 同文档去重」，
减轻本地哈希向量把不相关文档（如洗涤 vs 尺码）塞进引用的问题。
"""

from __future__ import annotations

import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple

from langchain_core.messages import AIMessageChunk

from app.core.config import get_settings
from app.rag.llm import get_chat_llm
from app.rag.prompts import EMPTY_KNOWLEDGE_REPLY, general_prompt, rag_prompt
from app.rag.vectorstore import similarity_search_with_score
from app.schemas.chat import SourceItem
from app.utils.cache import cache_get, cache_set, make_cache_key

# 缓存版本：改算法后自动避开旧结果
_CACHE_VERSION = "retrieve-v3"

# 电商/知识库相关主题词：出现则更倾向走知识库模式
_PRODUCT_HINT_WORDS = (
    "尺码",
    "尺寸",
    "号型",
    "洗涤",
    "养护",
    "洗护",
    "退货",
    "保修",
    "参数",
    "规格",
    "价格",
    "多少钱",
    "运费",
    "发票",
    "材质",
    "面料",
    "商品",
    "产品",
    "耳机",
    "手表",
    "咖啡",
    "库存",
    "发货",
    "物流",
    "售后",
    "优惠",
    "活动",
    "sku",
    "型号",
    "续航",
    "防水",
    "身高",
    "体重",
    "推荐码",
)


def _score_to_similarity(score: float) -> float:
    """
    Chroma/默认距离多为 L2，数值越小越相似。
    转成 0~1 大致相关度，方便前端展示。
    """
    sim = 1.0 / (1.0 + float(score))
    return round(sim, 4)


def _tokenize_terms(text: str) -> Set[str]:
    """中英混合分词：英文词、数字、中文 2/3 字词，用于关键词重叠打分。"""
    text = (text or "").strip().lower()
    if not text:
        return set()

    terms: Set[str] = set()
    terms.update(re.findall(r"[a-z][a-z0-9_\-]{1,}", text))
    terms.update(re.findall(r"\d+(?:\.\d+)?", text))

    # 去掉空白后抽中文 n-gram
    pure = re.sub(r"\s+", "", text)
    # 保留中文与常见连接符
    cjk = "".join(ch for ch in pure if "一" <= ch <= "鿿" or ch.isalnum())
    for n in (2, 3):
        if len(cjk) < n:
            continue
        for i in range(len(cjk) - n + 1):
            gram = cjk[i : i + n]
            # 至少含一个汉字，避免纯数字 n-gram 过碎
            if any("一" <= ch <= "鿿" for ch in gram):
                terms.add(gram)

    # 文件名里常见主题词单独加强（整词命中）
    for kw in (
        "尺码",
        "尺寸",
        "号型",
        "洗涤",
        "养护",
        "洗护",
        "退货",
        "保修",
        "参数",
        "规格",
        "价格",
        "运费",
        "发票",
        "材质",
        "面料",
        "推荐",
        "身高",
        "体重",
    ):
        if kw in text:
            terms.add(kw)

    return terms


def _keyword_score(query: str, content: str, filename: str) -> float:
    """
    查询与片段/文件名的关键词重叠分（0~1）。
    文件名命中给更高权重：问「尺码」时优先「尺码推荐.txt」，压低「洗涤养护.txt」。
    """
    q_terms = _tokenize_terms(query)
    if not q_terms:
        return 0.0

    f_terms = _tokenize_terms(filename)
    c_terms = _tokenize_terms(content)

    hit_file = q_terms & f_terms
    hit_content = q_terms & c_terms
    covered = hit_file | hit_content
    if not covered:
        return 0.0

    coverage = len(covered) / max(len(q_terms), 1)
    # 文件名命中：每个命中词加分，上限 0.35
    file_bonus = min(0.35, 0.12 * len(hit_file))
    # 正文命中密度
    content_bonus = min(0.25, 0.04 * len(hit_content))

    # 查询核心主题词（较长的 2~3 字）若只在别的文档文件名里出现、本片段完全没有，则 coverage 已低
    score = min(1.0, coverage * 0.7 + file_bonus + content_bonus)
    return round(score, 4)


def _hybrid_score(vector_sim: float, keyword: float, settings) -> float:
    vw = float(settings.hybrid_vector_weight)
    kw = float(settings.hybrid_keyword_weight)
    total = vw + kw
    if total <= 0:
        return vector_sim
    return round((vw * vector_sim + kw * keyword) / total, 4)


def _rerank_and_filter(
    question: str,
    pairs: List[Tuple[Any, float]],
) -> List[SourceItem]:
    """
    对向量召回结果做：混合打分 → 阈值过滤 → 同文档限流 → 截断 Top-K。
    """
    settings = get_settings()
    if not pairs:
        return []

    scored: List[Tuple[float, float, float, Any, float]] = []
    # (hybrid, keyword, vector_sim, doc, raw_distance)
    for doc, distance in pairs:
        meta = doc.metadata or {}
        filename = str(meta.get("filename") or "未知文档")
        content = doc.page_content or ""
        vector_sim = _score_to_similarity(distance)
        keyword = _keyword_score(question, content, filename)
        hybrid = _hybrid_score(vector_sim, keyword, settings)
        scored.append((hybrid, keyword, vector_sim, doc, float(distance)))

    min_kw = float(settings.retrieve_min_keyword_score)
    # 必须有一定关键词重叠，或向量非常高，否则视为噪声
    scored = [row for row in scored if row[1] >= min_kw or row[2] >= 0.62]
    if not scored:
        return []

    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    best = scored[0][0]
    min_abs = float(settings.retrieve_min_score)
    min_rel = best * float(settings.retrieve_relative_ratio)

    # 同时满足：混合分足够 + 关键词足够（向量极高时可略放宽关键词）
    filtered = []
    for row in scored:
        hybrid, keyword, vector_sim, _doc, _dist = row
        if hybrid < min_abs or hybrid < min_rel:
            continue
        if keyword < min_kw and vector_sim < 0.62:
            continue
        filtered.append(row)

    # 不再「硬保底一条」：弱相关宁可走通用问答，也不要误绑商品文档
    if not filtered:
        return []

    max_per_doc = max(1, int(settings.retrieve_max_per_doc))
    top_k = max(1, int(settings.retrieve_top_k))
    per_doc: Dict[str, int] = {}
    sources: List[SourceItem] = []

    for hybrid, keyword, vector_sim, doc, _dist in filtered:
        meta = doc.metadata or {}
        doc_id = meta.get("doc_id")
        try:
            doc_id_int = int(doc_id) if doc_id is not None else None
        except (TypeError, ValueError):
            doc_id_int = None
        filename = str(meta.get("filename") or "未知文档")
        # 按文件名限流（比 doc_id 更直观，避免同主题刷屏）
        key = filename or str(doc_id_int)
        if per_doc.get(key, 0) >= max_per_doc:
            continue
        per_doc[key] = per_doc.get(key, 0) + 1

        chunk_index = meta.get("chunk_index", 0)
        sources.append(
            SourceItem(
                doc_id=doc_id_int,
                filename=filename,
                chunk_id=f"{doc_id}_{chunk_index}",
                content=(doc.page_content or "")[:1200],
                # 前端展示用混合分，更接近真实「相关程度」
                score=hybrid,
            )
        )
        if len(sources) >= top_k:
            break

    return sources


def looks_like_general_question(question: str) -> bool:
    """
    判断是否更像通用/闲聊/算术题，而不是商品知识库问题。
    命中时优先走通用模式，避免弱检索把 sample_products 误绑上来。
    """
    q = (question or "").strip()
    if not q:
        return False

    q_compact = re.sub(r"\s+", "", q.lower())

    # 含明显商品/业务词 → 不当作纯通用题
    if any(w in q_compact for w in _PRODUCT_HINT_WORDS):
        return False

    # 纯算术 / 加减乘除
    if re.fullmatch(r"[\d\.\+\-\*/×÷（）()\s等于是多少？?啊呀呢啦哦~！!。,.]+", q):
        return True
    if re.search(r"\d+\s*[\+\-\*/×÷]\s*\d+", q) and ("等于" in q or "多少" in q or "=" in q):
        return True
    if re.search(r"(一\s*\+\s*一|1\s*\+\s*1).*(等于|多少)", q_compact):
        return True

    # 短问候 / 自我介绍类
    greetings = (
        "你好",
        "您好",
        "在吗",
        "嗨",
        "hello",
        "hi",
        "你是谁",
        "你叫什么",
        "谢谢",
        "再见",
    )
    if q_compact in greetings or any(q_compact == g or q_compact.startswith(g) for g in greetings):
        if len(q_compact) <= 12:
            return True

    # 极短且无业务词的闲聊
    if len(q_compact) <= 4 and not re.search(r"[一-鿿]{2,}", q_compact):
        return True

    return False


def is_confident_kb_hit(sources: List[SourceItem]) -> bool:
    """引用是否足够「像真命中」，不够则改走通用模式。"""
    if not sources:
        return False
    settings = get_settings()
    best = max((s.score or 0.0) for s in sources)
    return best >= float(settings.retrieve_min_score)


def should_use_general_mode(question: str, sources: List[SourceItem]) -> bool:
    """混合路由：通用题 或 无可靠知识库命中 → 通用简答。"""
    if looks_like_general_question(question):
        return True
    return not is_confident_kb_hit(sources)


def retrieve_sources(question: str) -> List[SourceItem]:
    """检索知识库片段：多召回 + 关键词重排过滤，带短时缓存。"""
    # 明显通用题：直接不检索，省一次向量查询，也避免噪声引用
    if looks_like_general_question(question):
        return []

    settings = get_settings()
    key = make_cache_key(f"{_CACHE_VERSION}|{question}")
    cached = cache_get(key)
    if cached is not None:
        return cached

    candidate_k = max(int(settings.retrieve_candidate_k), int(settings.retrieve_top_k))
    pairs = similarity_search_with_score(question, k=candidate_k)
    sources = _rerank_and_filter(question, pairs)

    cache_set(key, sources)
    return sources


def format_context(sources: List[SourceItem]) -> str:
    if not sources:
        return "（无相关片段）"
    parts = []
    for i, s in enumerate(sources, start=1):
        score_txt = f"{s.score:.2f}" if s.score is not None else "N/A"
        parts.append(f"[{i}] 来源：{s.filename} | 相关度：{score_txt}\n{s.content}")
    return "\n\n".join(parts)


def format_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return "（无）"
    lines = []
    for h in history:
        role = "用户" if h.get("role") == "user" else "助手"
        lines.append(f"{role}: {h.get('content', '')}")
    return "\n".join(lines)


def build_messages(question: str, sources: List[SourceItem], history: List[Dict[str, str]]):
    """知识库命中：严格 RAG 提示词。"""
    return rag_prompt.format_messages(
        context=format_context(sources),
        history=format_history(history),
        question=question,
    )


def build_general_messages(question: str, history: List[Dict[str, str]]):
    """知识库未命中：允许常识简答的通用提示词。"""
    return general_prompt.format_messages(
        history=format_history(history),
        question=question,
    )


async def _astream_tokens(messages) -> AsyncIterator[str]:
    """统一流式取 token，减少重复代码。"""
    llm = get_chat_llm(streaming=True)
    async for chunk in llm.astream(messages):
        text = ""
        if isinstance(chunk, AIMessageChunk):
            text = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        else:
            content = getattr(chunk, "content", None)
            if isinstance(content, str):
                text = content
        if text:
            yield text


async def generate_answer(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Tuple[str, List[SourceItem]]:
    """
    非流式完整生成（混合模式）：
    - 可靠知识库命中 → 严格按文档回答，返回引用
    - 通用题 / 弱命中 → 常识简答，引用为空
    """
    history = history or []
    sources = retrieve_sources(question)
    use_general = should_use_general_mode(question, sources)
    # 弱命中不展示误导性引用
    out_sources: List[SourceItem] = [] if use_general else sources
    llm = get_chat_llm(streaming=False)

    try:
        if use_general:
            messages = build_general_messages(question, history)
        else:
            messages = build_messages(question, sources, history)
        result = await llm.ainvoke(messages)
        content = result.content if isinstance(result.content, str) else str(result.content)
        return content, out_sources
    except Exception:
        if not use_general:
            raise
        return EMPTY_KNOWLEDGE_REPLY, []


async def stream_answer(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """
    流式生成（混合模式）。产出字典事件：
    - {"type": "sources", "sources": [...]}  # 通用/弱命中时为空
    - {"type": "token", "content": "..."}
    - {"type": "done", "answer": "..."}
    """
    history = history or []
    sources = retrieve_sources(question)
    use_general = should_use_general_mode(question, sources)
    out_sources: List[SourceItem] = [] if use_general else sources

    yield {
        "type": "sources",
        "sources": [s.model_dump() for s in out_sources],
    }

    if use_general:
        messages = build_general_messages(question, history)
    else:
        messages = build_messages(question, sources, history)

    full: List[str] = []
    try:
        async for text in _astream_tokens(messages):
            full.append(text)
            yield {"type": "token", "content": text}
    except Exception as exc:
        if use_general and not full:
            yield {"type": "token", "content": EMPTY_KNOWLEDGE_REPLY}
            yield {"type": "done", "answer": EMPTY_KNOWLEDGE_REPLY}
            return
        yield {"type": "error", "message": f"生成失败：{exc}"}
        return

    answer = "".join(full)
    if not answer and use_general:
        answer = EMPTY_KNOWLEDGE_REPLY
        yield {"type": "token", "content": answer}
    yield {"type": "done", "answer": answer}


def sources_to_json(sources: List[SourceItem]) -> str:
    return json.dumps([s.model_dump() for s in sources], ensure_ascii=False)
