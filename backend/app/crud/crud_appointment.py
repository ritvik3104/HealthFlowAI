from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import and_

from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.models.user import User
from app.services.google_calendar_service import create_calendar_event 

def create_appointment(db: Session, appointment: AppointmentCreate) -> Appointment:
    """Create a new appointment in the database and push to Google Calendar."""
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # Add appointment to Google Calendar
    event_link = create_event(
        summary=f"Appointment with Doctor ID {db_appointment.doctor_id}",
        description=db_appointment.notes or "Medical Appointment",
        start_time=db_appointment.start_time,
        end_time=db_appointment.end_time,
    )

    # Attach calendar link to appointment object (not persisted in DB, just returned)
    db_appointment.google_calendar_link = event_link

    return db_appointment

def get_appointment(db: Session, appointment_id: int) -> Optional[Appointment]:
    """Retrieve a single appointment by its ID."""
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()

def get_appointments_by_user(db: Session, user_id: int) -> List[Appointment]:
    """Retrieve all appointments for a specific user (either as a patient or doctor)."""
    return db.query(Appointment).filter(
        (Appointment.patient_id == user_id) | (Appointment.doctor_id == user_id)
    ).all()

def get_appointments_by_doctor_for_day(db: Session, doctor_id: int, target_date: date) -> List[Appointment]:
    """Retrieve all appointments for a specific doctor on a given day."""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    return db.query(Appointment).options(
        joinedload(Appointment.patient)
    ).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.start_time >= start_of_day,
        Appointment.start_time <= end_of_day
    ).order_by(Appointment.start_time).all()

def count_appointments_for_doctor(db: Session, doctor_id: int, start_date: datetime, end_date: datetime) -> int:
    """Counts the number of appointments for a specific doctor within a given date range."""
    return db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date
        )
    ).count()

def search_appointments_by_notes(db: Session, doctor_id: int, start_date: datetime, end_date: datetime, keyword: str) -> int:
    """Counts appointments for a doctor in a date range where the notes contain a specific keyword."""
    return db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date,
            Appointment.notes.ilike(f"%{keyword}%")
        )
    ).count()

def update_appointment(db: Session, appointment_id: int, appointment_update: AppointmentUpdate) -> Optional[Appointment]:
    """Update an existing appointment."""
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    
    update_data = appointment_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
        
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

def get_appointment_details_for_doctor(db: Session, doctor_id: int, start_date: datetime, end_date: datetime) -> List[Appointment]:
    """Gets a list of full appointment objects for a doctor within a date range, including patient info."""
    return db.query(Appointment).options(
        joinedload(Appointment.patient)
    ).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.start_time >= start_date,
        Appointment.start_time <= end_date
    ).order_by(Appointment.start_time).all()

# ✅ FIX: Get only registered doctors (to avoid fake names from LLM)
def get_registered_doctors(db: Session) -> List[User]:
    """Fetch only registered doctors from User table."""
    return db.query(User).filter(User.role == "doctor").all()
