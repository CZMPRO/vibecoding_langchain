"""进程内 TTL 缓存：替代 Redis，适合本机单进程演示。"""

import hashlib
import re
from typing import Any, Optional

from cachetools import TTLCache

from app.core.config import get_settings

_settings = get_settings()
_retrieve_cache: TTLCache = TTLCache(
    maxsize=_settings.retrieve_cache_size,
    ttl=_settings.retrieve_cache_ttl,
)


def normalize_question(text: str) -> str:
    """问题归一化，便于缓存命中。"""
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def make_cache_key(text: str) -> str:
    return hashlib.sha256(normalize_question(text).encode("utf-8")).hexdigest()


def cache_get(key: str) -> Optional[Any]:
    return _retrieve_cache.get(key)


def cache_set(key: str, value: Any) -> None:
    _retrieve_cache[key] = value


def cache_clear() -> None:
    _retrieve_cache.clear()
