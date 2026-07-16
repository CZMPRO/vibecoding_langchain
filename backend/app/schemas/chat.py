"""会话与问答相关模型。"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default="新会话", max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceItem(BaseModel):
    doc_id: Optional[int] = None
    filename: str = ""
    chunk_id: str = ""
    content: str = ""
    score: Optional[float] = None


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: List[SourceItem] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    conversation_id: Optional[int] = Field(default=None, description="为空则自动新建会话")
    question: str = Field(..., min_length=1, max_length=4000)
    stream: bool = True


class ChatResponse(BaseModel):
    conversation_id: int
    user_message_id: int
    assistant_message_id: int
    answer: str
    sources: List[SourceItem] = []


class FeedbackRequest(BaseModel):
    rating: int = Field(..., description="1 赞 / -1 踩")
    comment: Optional[str] = Field(default=None, max_length=500)


class FeedbackOut(BaseModel):
    id: int
    message_id: int
    rating: int
    comment: Optional[str] = None

    model_config = {"from_attributes": True}


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int


class ConversationList(BaseModel):
    items: List[ConversationOut]
    meta: PageMeta


class MessageList(BaseModel):
    items: List[MessageOut]
    meta: PageMeta
