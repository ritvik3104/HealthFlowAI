import logging
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from app.models.user import User, UserRole
from app.schemas.user import UserCreate

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a single user from the database by their email address."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieves a single user from the database by their ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_users_by_role(db: Session, role: UserRole) -> List[User]:
    """Retrieves all users from the database with a specific role."""
    return db.query(User).filter(User.role == role).all()

def get_doctor_by_name(db: Session, name: str) -> Optional[User]:
    """
    Retrieves a single doctor from the database by their full name.
    Performs a case-insensitive search.
    """
    return db.query(User).filter(User.role == UserRole.DOCTOR, User.full_name.ilike(f"%{name}%")).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
