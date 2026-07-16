"""知识库文档模型。"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.chat import PageMeta


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    items: List[DocumentOut]
    meta: PageMeta


class StatsOut(BaseModel):
    user_count: int
    document_count: int
    ready_document_count: int
    conversation_count: int
    message_count: int
    today_qa_count: int
