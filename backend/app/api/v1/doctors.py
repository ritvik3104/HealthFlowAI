from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.models.user import User, UserRole
from app.schemas.appointment import Appointment, AppointmentUpdate
from app.api.v1.auth import get_db
from app.services import auth_service

router = APIRouter()

def require_doctor(current_user: User = Depends(auth_service.get_current_user)):
    """
    Dependency to ensure the current user is a doctor.
    Raises a 403 Forbidden error if the user is not a doctor.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires doctor privileges."
        )
    return current_user

@router.get("/appointments", response_model=List[Appointment])
def read_doctor_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Retrieve all appointments for the currently logged-in doctor.
    """
    appointments = crud.crud_appointment.get_appointments_by_user(db, user_id=current_user.id)
    return appointments

@router.patch("/appointments/{appointment_id}", response_model=Appointment)
def update_appointment_status(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Update the status or notes of an appointment.
    - Only the doctor assigned to the appointment can update it.
    """
    db_appointment = crud.crud_appointment.get_appointment(db, appointment_id=appointment_id)
    
    if not db_appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
        
    if db_appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this appointment")

    return crud.crud_appointment.update_appointment(db, appointment_id=appointment_id, appointment_update=appointment_update)
