"""FastAPI 应用入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, kb, stats
from app.core.config import get_settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表、初始化 admin。"""
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="电商知识库 RAG 问答系统",
        description="基于 LangChain 的企业级电商知识库问答 API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api")
    app.include_router(kb.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "LangChainRAG"}

    @app.get("/api/health")
    def api_health():
        return {"status": "ok"}

    return app


app = create_app()
