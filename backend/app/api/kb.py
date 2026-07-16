"""知识库管理：仅管理员。"""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.deps import AdminUser, DbSession
from app.models.document import Document
from app.rag.loaders import SUPPORTED_EXTENSIONS
from app.rag.vectorstore import delete_by_document_id
from app.schemas.chat import PageMeta
from app.schemas.kb import DocumentList, DocumentOut
from app.services.ingest_service import process_document
from app.utils.cache import cache_clear

router = APIRouter(prefix="/kb", tags=["知识库"])


@router.get("/documents", response_model=DocumentList)
def list_documents(
    admin: AdminUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
) -> DocumentList:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    q = db.query(Document)
    total = q.count()
    items = (
        q.order_by(Document.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return DocumentList(
        items=[DocumentOut.model_validate(i) for i in items],
        meta=PageMeta(total=total, page=page, page_size=page_size),
    )


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> DocumentOut:
    settings = get_settings()
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名无效")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {suffix}，允许: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"文件超过大小限制 {settings.max_upload_mb}MB",
        )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    # 磁盘用 UUID 名，避免中文/重名问题；原始名记在数据库
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = settings.upload_dir / stored_name
    stored_path.write_bytes(raw)

    doc = Document(
        filename=file.filename,
        stored_path=str(stored_path),
        file_type=suffix.lstrip("."),
        file_size=len(raw),
        status="pending",
        uploaded_by=admin.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 异步入库，接口立刻返回
    background_tasks.add_task(process_document, doc.id)
    return DocumentOut.model_validate(doc)


@router.post("/documents/{document_id}/retry", response_model=DocumentOut)
def retry_document(
    document_id: int,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> DocumentOut:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.status == "processing":
        raise HTTPException(status_code=400, detail="文档正在处理中")
    doc.status = "pending"
    doc.error_message = None
    db.commit()
    db.refresh(doc)
    background_tasks.add_task(process_document, doc.id)
    return DocumentOut.model_validate(doc)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, admin: AdminUser, db: DbSession) -> None:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删向量
    try:
        delete_by_document_id(doc.id)
    except Exception:  # noqa: BLE001
        pass

    # 删文件
    try:
        p = Path(doc.stored_path)
        if p.exists():
            p.unlink()
    except Exception:  # noqa: BLE001
        pass

    db.delete(doc)
    db.commit()
    cache_clear()
