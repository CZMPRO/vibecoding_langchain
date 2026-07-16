"""Embedding 工厂：支持远程 OpenAI 兼容 或 本地哈希向量（免下载）。"""

from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import List

from langchain_core.embeddings import Embeddings

from app.core.config import get_settings


class LocalHashEmbeddings(Embeddings):
    """
    本地中文友好哈希向量。

    不需要联网下载模型，适合第三方网关没有 embedding 接口的情况。
    原理：对字符 n-gram 做稳定哈希映射到固定维度，并做 L2 归一化。
    对商品名、参数、政策等关键词匹配效果够用，适合毕设演示。
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").strip().lower()
        text = re.sub(r"\s+", " ", text)
        tokens: List[str] = []
        # 英文/数字词
        tokens.extend(re.findall(r"[a-z0-9_]+", text))
        # 中文等连续非空格字符：1-gram + 2-gram
        pure = re.sub(r"\s+", "", text)
        for i, ch in enumerate(pure):
            if "一" <= ch <= "鿿" or not ch.isascii():
                tokens.append(ch)
                if i + 1 < len(pure):
                    tokens.append(pure[i : i + 2])
        if not tokens and text:
            tokens = [text]
        return tokens

    def _embed_one(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in self._tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % self.dim
            sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
            vec[idx] += sign
        # L2 归一化，便于相似度比较
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)


@lru_cache
def get_embeddings() -> Embeddings:
    """获取向量模型客户端（单例）。"""
    settings = get_settings()
    provider = (settings.embedding_provider or "local").strip().lower()

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

    # 默认本地哈希向量：零依赖下载，开箱即用
    return LocalHashEmbeddings(dim=settings.local_embedding_dim)
