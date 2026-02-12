from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    user_id: str = "user_1"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    context_used: Optional[str] = None
    step_logs: Optional[Dict[str, Any]] = None
    grounding_metadata: Optional[Dict[str, Any]] = None
