from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

# Shared properties
class UserBase(BaseModel):
    """
    Base schema for user properties.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Requires email, password, full_name, and role.
    """
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

# Properties to receive via API on update
class UserUpdate(UserBase):
    """
    Schema for updating an existing user.
    All fields are optional.
    """
    password: Optional[str] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    """
    Base schema for user properties as stored in the database.
    Includes the user's ID.
    """
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    class Config:
        # This tells Pydantic to read the data even if it is not a dict,
        # but an ORM model (or any other arbitrary object with attributes).
        orm_mode = True

# Properties to return to the client
class User(UserInDBBase):
    """
    Schema for returning user data from the API.
    This is the public-facing model.
    """
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    """
    Schema for the user as stored in the database.
    Includes the hashed password.
    """
    hashed_password: str
