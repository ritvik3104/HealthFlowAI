from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.appointment import AppointmentStatus
from app.schemas.user import User # To nest user info in appointment response

# Shared properties
class AppointmentBase(BaseModel):
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

# Properties to receive via API on creation
class AppointmentCreate(AppointmentBase):
    patient_id: int
    doctor_id: int

# Properties to receive via API on update
class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

# Properties shared by models stored in DB
class AppointmentInDBBase(AppointmentBase):
    id: int
    patient_id: int
    doctor_id: int
    status: AppointmentStatus

    class Config:
        orm_mode = True

# Properties to return to the client
class Appointment(AppointmentInDBBase):
    patient: User
    doctor: User

# Properties stored in DB
class AppointmentInDB(AppointmentInDBBase):
    pass
