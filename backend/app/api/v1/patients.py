from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.crud import crud_appointment
from app.models.user import User
from app.schemas.appointment import Appointment, AppointmentCreate
from app.api.v1.auth import get_db
from app.services import auth_service

router = APIRouter()

@router.post("/appointments", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_new_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Create a new appointment with enhanced error handling.
    - A logged-in user can only create an appointment for themselves.
    - Checks for invalid patient or doctor IDs.
    """
    if appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only book appointments for yourself."
        )
    
    try:
        return crud_appointment.create_appointment(db=db, appointment=appointment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor or Patient with the provided ID not found. Please check the IDs and try again."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


@router.get("/appointments", response_model=List[Appointment])
def read_user_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieve all appointments for the currently logged-in user.
    """
    appointments = crud_appointment.get_appointments_by_user(db, user_id=current_user.id)
    return appointments
