"""文本切块：把长文切成适合检索的小片段。"""

from typing import List

from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


def split_documents(docs: List[LCDocument]) -> List[LCDocument]:
    """中文友好分隔符切块。"""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    return splitter.split_documents(docs)
