"""缓存与限流工具。"""

import pytest
from fastapi import HTTPException

from app.utils.cache import cache_clear, cache_get, cache_set, make_cache_key, normalize_question
from app.utils.rate_limit import RateLimiter


def test_normalize_question_collapses_spaces():
    assert normalize_question("  你好   世界  ") == "你好 世界"


def test_make_cache_key_stable():
    """相同语义问题应得到相同缓存键。"""
    k1 = make_cache_key("Hello World")
    k2 = make_cache_key("  hello   world  ")
    assert k1 == k2
    assert len(k1) == 64  # sha256 hex


def test_cache_set_get_clear():
    cache_clear()
    key = make_cache_key("unit-test-cache")
    assert cache_get(key) is None
    cache_set(key, [{"filename": "a.md"}])
    assert cache_get(key) == [{"filename": "a.md"}]
    cache_clear()
    assert cache_get(key) is None


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter()
    limiter.check("test-key", limit=2, window_seconds=60)
    limiter.check("test-key", limit=2, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        limiter.check("test-key", limit=2, window_seconds=60)
    assert exc.value.status_code == 429
