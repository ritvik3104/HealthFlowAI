from sqlalchemy.orm import Session
from typing import List

from app.models.prompt_history import PromptHistory
from app.schemas.prompt_history import PromptHistoryCreate

def create_prompt_history(db: Session, history_in: PromptHistoryCreate, user_id: int) -> PromptHistory:
    """
    Create a new prompt history record in the database.
    """
    db_history = PromptHistory(
        **history_in.dict(),
        user_id=user_id
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def get_prompt_history_by_user(db: Session, user_id: int) -> List[PromptHistory]:
    """
    Retrieve all prompt history records for a specific user, ordered by most recent first.
    """
    return db.query(PromptHistory).filter(PromptHistory.user_id == user_id).order_by(PromptHistory.created_at.desc()).all()
