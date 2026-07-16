"""Chroma 向量库单例。"""

from functools import lru_cache
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "ecommerce_kb"


@lru_cache
def get_vectorstore() -> Chroma:
    """本地持久化 Chroma，数据落在 data/chroma。"""
    settings = get_settings()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def add_documents(docs: List[LCDocument], ids: Optional[List[str]] = None) -> List[str]:
    """批量写入向量。"""
    store = get_vectorstore()
    return store.add_documents(docs, ids=ids)


def delete_by_document_id(document_id: int) -> None:
    """按业务文档 id 删除所有相关 chunk。"""
    store = get_vectorstore()
    # Chroma 通过 where 过滤 metadata
    try:
        store._collection.delete(where={"doc_id": document_id})  # noqa: SLF001
    except Exception:
        # 兼容不同版本 API
        results = store.get(where={"doc_id": document_id})
        ids = results.get("ids") or []
        if ids:
            store.delete(ids=ids)


def similarity_search_with_score(query: str, k: int = 5):
    """相似度检索，返回 (Document, score) 列表。"""
    store = get_vectorstore()
    return store.similarity_search_with_score(query, k=k)
