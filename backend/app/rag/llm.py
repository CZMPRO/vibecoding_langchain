"""聊天大模型工厂：OpenAI 兼容接口，单例复用。"""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache
def get_chat_llm(streaming: bool = True) -> ChatOpenAI:
    """获取聊天模型。streaming=True 用于打字机效果。"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.2,
        streaming=streaming,
    )
