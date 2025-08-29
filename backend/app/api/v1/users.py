from fastapi import APIRouter, Depends
from app.schemas.user import User
from app.models.user import User as UserModel
from app.services import auth_service

router = APIRouter()

@router.get("/me", response_model=User)
def read_users_me(current_user: UserModel = Depends(auth_service.get_current_user)):
    """
    Get the details of the currently logged-in user.
    """
    return current_user
