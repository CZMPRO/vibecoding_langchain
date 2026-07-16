"""文档入库服务：解析 → 切块 → 向量化 → 更新状态。"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.rag.loaders import load_file_to_documents
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_documents, delete_by_document_id
from app.utils.cache import cache_clear


def process_document(document_id: int) -> None:
    """后台任务入口：处理单个文档入库。"""
    db: Session = SessionLocal()
    try:
        doc: Optional[Document] = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = "processing"
        doc.error_message = None
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()

        path = Path(doc.stored_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {doc.stored_path}")

        # 先清掉旧向量（重试入库时）
        delete_by_document_id(doc.id)

        raw_docs = load_file_to_documents(path, doc.filename)
        chunks = split_documents(raw_docs)
        if not chunks:
            raise ValueError("切块结果为空")

        ids = []
        for i, chunk in enumerate(chunks):
            chunk.metadata = {
                **(chunk.metadata or {}),
                "doc_id": doc.id,
                "filename": doc.filename,
                "chunk_index": i,
                "file_type": doc.file_type,
            }
            ids.append(f"{doc.id}_{i}")

        # 批量写入 Chroma（内部会批处理 embedding）
        add_documents(chunks, ids=ids)

        doc.status = "ready"
        doc.chunk_count = len(chunks)
        doc.error_message = None
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()
        # 知识库变更后清空检索缓存
        cache_clear()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "failed"
            doc.error_message = str(exc)[:1000]
            doc.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
