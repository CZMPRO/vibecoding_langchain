"""应用配置：从环境变量 / .env 读取，换模型不用改代码。"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# backend 目录（本文件位于 backend/app/core/）
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """全局配置。"""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI 兼容
    openai_api_key: str = "sk-placeholder"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # embedding 来源：openai（远程）/ local（本地哈希向量，免下载）
    embedding_provider: str = "local"
    local_embedding_model: str = "hash-zh-v1"
    local_embedding_dim: int = 384

    # 安全
    jwt_secret: str = "please-change-this-secret-key-in-production"
    jwt_expire_minutes: int = 1440
    jwt_algorithm: str = "HS256"
    admin_username: str = "admin"
    admin_password: str = "123456"

    # 路径：Vercel Functions 仅允许写入 /tmp，本地仍使用 backend/data
    data_dir: str = "/tmp/langchain-rag" if os.getenv("VERCEL") else "./data"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # RAG
    chunk_size: int = 600
    chunk_overlap: int = 100
    retrieve_top_k: int = 4  # 最终返回给前端/模型的条数
    retrieve_candidate_k: int = 16  # 先多取候选，再重排过滤
    retrieve_min_score: float = 0.32  # 混合分低于此视为不相关（勿过低，否则 1+1 会误命中商品文）
    retrieve_min_keyword_score: float = 0.12  # 关键词分过低则不算有效命中
    retrieve_relative_ratio: float = 0.72  # 相对最优分的保留比例
    retrieve_max_per_doc: int = 2  # 同一文档最多保留几条，避免刷屏
    hybrid_vector_weight: float = 0.45  # 向量分权重
    hybrid_keyword_weight: float = 0.55  # 关键词分权重（本地哈希向量时更重要）
    history_turns: int = 5
    max_upload_mb: int = 20

    # 缓存
    retrieve_cache_ttl: int = 300
    retrieve_cache_size: int = 256

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        return path

    @property
    def sqlite_url(self) -> str:
        db_file = self.data_path / "app.db"
        # SQLAlchemy 需要正斜杠路径
        return f"sqlite:///{db_file.as_posix()}"

    @property
    def chroma_dir(self) -> Path:
        return self.data_path / "chroma"

    @property
    def upload_dir(self) -> Path:
        return self.data_path / "uploads"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """单例配置，避免重复读盘。"""
    return Settings()
