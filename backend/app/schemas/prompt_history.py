from pydantic import BaseModel
from datetime import datetime

# Properties to receive via API on creation
class PromptHistoryCreate(BaseModel):
    prompt_text: str
    response_text: str

# Properties shared by models stored in DB
class PromptHistoryBase(PromptHistoryCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Properties to return to the client
class PromptHistory(PromptHistoryBase):
    pass
