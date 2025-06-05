from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class HistoryChatbotModel(BaseModel):
    _id: Optional[str] = None
    user_id: str
    date_chat: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())
    content: List[Dict[str, Any]]

class ChatRequest(BaseModel):
    user_id: str
    content: str

class UpdateChatRequest(BaseModel):
    hischat_id: str
    user_message: str