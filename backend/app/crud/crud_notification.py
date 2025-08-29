from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

def create_notification(db: Session, notification_in: NotificationCreate, user_id: int) -> Notification:
    """
    Create a new notification for a user.
    """
    db_notification = Notification(
        message=notification_in.message,
        user_id=user_id
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notifications_by_user(db: Session, user_id: int) -> List[Notification]:
    """
    Retrieve all unread notifications for a specific user, ordered by most recent first.
    """
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).order_by(Notification.created_at.desc()).all()

def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
    """
    Mark a specific notification as read.
    Ensures that a user can only mark their own notifications as read.
    """
    db_notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if db_notification:
        db_notification.is_read = True
        db.commit()
        db.refresh(db_notification)
    return db_notification
