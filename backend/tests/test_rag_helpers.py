"""RAG 辅助函数（不调用外部模型）。"""

from types import SimpleNamespace

from app.rag.prompts import EMPTY_KNOWLEDGE_REPLY, GENERAL_SYSTEM_PROMPT, SYSTEM_PROMPT
from app.schemas.chat import SourceItem
from app.services.rag_service import (
    _hybrid_score,
    _keyword_score,
    _rerank_and_filter,
    _score_to_similarity,
    _tokenize_terms,
    build_general_messages,
    build_messages,
    is_confident_kb_hit,
    looks_like_general_question,
    should_use_general_mode,
    format_context as rag_format_context,
    format_history,
    sources_to_json,
)


def test_score_to_similarity_monotone():
    """距离越小，相关度越高。"""
    assert _score_to_similarity(0) > _score_to_similarity(1)
    assert 0 < _score_to_similarity(2) <= 1


def test_format_context_and_history():
    sources = [
        SourceItem(doc_id=1, filename="a.md", chunk_id="1_0", content="支持游泳", score=0.8),
    ]
    ctx = rag_format_context(sources)
    assert "a.md" in ctx
    assert "支持游泳" in ctx

    empty_ctx = rag_format_context([])
    assert "无相关" in empty_ctx

    hist = format_history([{"role": "user", "content": "你好"}, {"role": "assistant", "content": "您好"}])
    assert "用户" in hist and "助手" in hist


def test_sources_to_json_roundtrip():
    sources = [SourceItem(filename="x.md", content="hi", score=0.5, chunk_id="1_1")]
    raw = sources_to_json(sources)
    assert "x.md" in raw
    assert "hi" in raw


def test_empty_knowledge_reply_not_blank():
    assert len(EMPTY_KNOWLEDGE_REPLY) > 10


def test_hybrid_prompts_exist():
    """混合模式：知识库提示与通用提示都应存在且角色不同。"""
    assert "知识库" in SYSTEM_PROMPT
    assert "通用" in GENERAL_SYSTEM_PROMPT or "常识" in GENERAL_SYSTEM_PROMPT


def test_build_general_messages_no_context_required():
    msgs = build_general_messages("1+1等于多少", [])
    assert len(msgs) >= 2
    joined = " ".join(str(m.content) for m in msgs)
    assert "1+1" in joined


def test_build_messages_includes_sources():
    sources = [
        SourceItem(doc_id=1, filename="尺码.txt", chunk_id="1_0", content="推荐M码", score=0.9),
    ]
    msgs = build_messages("推荐尺码", sources, [])
    joined = " ".join(str(m.content) for m in msgs)
    assert "尺码.txt" in joined or "推荐M码" in joined


def test_looks_like_general_math_question():
    assert looks_like_general_question("1+1等于多少")
    assert looks_like_general_question("那我只想知道1+1等于多少")
    assert looks_like_general_question("2*3是多少")
    assert looks_like_general_question("你好")
    # 商品问题不应判成纯通用
    assert not looks_like_general_question("身高163推荐尺码")
    assert not looks_like_general_question("云朵耳机续航多久")


def test_weak_source_triggers_general_mode():
    weak = [SourceItem(filename="sample_products.md", content="耳机", score=0.204, chunk_id="1_0")]
    assert not is_confident_kb_hit(weak)
    assert should_use_general_mode("随便问点什么无关的", weak)

    strong = [SourceItem(filename="尺码推荐.txt", content="M码", score=0.72, chunk_id="1_0")]
    assert is_confident_kb_hit(strong)
    assert not should_use_general_mode("推荐尺码", strong)


def test_rerank_drops_ultra_weak_without_fallback():
    """弱相关且关键词不足时，应返回空列表（交给通用模式），不再硬保底一条。"""
    query = "1+1等于多少"
    noise = SimpleNamespace(
        page_content="云朵降噪耳机 Air 续航 30 小时 价格 399",
        metadata={"doc_id": 9, "filename": "sample_products.md", "chunk_index": 0},
    )
    # 距离较大 → 向量分不高；关键词与算术题几乎不重叠
    sources = _rerank_and_filter(query, [(noise, 2.5)])
    assert sources == []


def test_tokenize_and_keyword_prefers_size_file():
    """问尺码时，尺码文档关键词分应明显高于洗涤文档。"""
    query = "给推荐一些尺码，我身高163，体重60公斤"
    size_score = _keyword_score(
        query,
        content="身高160-170 体重建议M码 L码 尺码对照表",
        filename="尺码推荐.txt",
    )
    wash_score = _keyword_score(
        query,
        content="水温不超过30度 轻柔洗涤 禁止暴晒 养护要点",
        filename="洗涤养护.txt",
    )
    assert size_score > wash_score
    assert size_score >= 0.3
    assert wash_score < size_score * 0.75


def test_rerank_filters_irrelevant_chunks():
    """混合重排后应丢掉明显不相关的洗涤片段，保留尺码。"""
    query = "推荐尺码 身高163 体重60"

    size_doc = SimpleNamespace(
        page_content="根据身高体重选择尺码：160-170cm 建议 M/L 码",
        metadata={"doc_id": 1, "filename": "尺码推荐.txt", "chunk_index": 0},
    )
    wash_doc = SimpleNamespace(
        page_content="洗涤方法：冷水手洗，使用中性洗涤剂，平铺阴干",
        metadata={"doc_id": 2, "filename": "洗涤养护.txt", "chunk_index": 0},
    )
    wash_doc2 = SimpleNamespace(
        page_content="禁止烘干暴晒，避免纤维老化",
        metadata={"doc_id": 2, "filename": "洗涤养护.txt", "chunk_index": 1},
    )
    # 距离故意给洗涤更近一点，模拟哈希向量误召回
    pairs = [
        (wash_doc, 0.8),
        (wash_doc2, 0.85),
        (size_doc, 1.2),
    ]
    sources = _rerank_and_filter(query, pairs)
    names = [s.filename for s in sources]
    assert "尺码推荐.txt" in names
    # 洗涤不应主导结果
    assert names.count("洗涤养护.txt") <= 1
    # 最高分应是尺码
    assert sources[0].filename == "尺码推荐.txt"


def test_hybrid_score_weights():
    settings = SimpleNamespace(hybrid_vector_weight=0.45, hybrid_keyword_weight=0.55)
    h = _hybrid_score(0.4, 0.8, settings)
    assert 0.4 < h < 0.8
    assert abs(h - (0.45 * 0.4 + 0.55 * 0.8)) < 1e-6


def test_tokenize_terms_contains_domain_words():
    terms = _tokenize_terms("请问这件衣服的尺码和洗涤方式")
    assert "尺码" in terms
    assert "洗涤" in terms
