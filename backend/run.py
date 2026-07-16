"""启动后端：在 backend 目录执行 python run.py"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,  # 单 worker，避免 Chroma 多进程写锁
    )
