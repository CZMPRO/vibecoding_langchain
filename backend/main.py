"""Vercel / 生产入口：对外暴露 app，便于平台自动识别 FastAPI。

本地开发仍可使用：
  python run.py
或：
  uvicorn app.main:app --reload
"""

from app.main import app

__all__ = ["app"]
