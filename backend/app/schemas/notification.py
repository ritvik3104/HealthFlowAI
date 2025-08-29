from pydantic import BaseModel
from datetime import datetime

# Properties to receive via API on creation
class NotificationCreate(BaseModel):
    message: str

# Properties shared by models stored in DB
class NotificationBase(NotificationCreate):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Properties to return to the client
class Notification(NotificationBase):
    pass
