import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base

class UserRole(str, enum.Enum):
    """
    Enumeration for user roles.
    """
    PATIENT = "patient"
    DOCTOR = "doctor"

class User(Base):
    """
    Database model for a user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean(), default=True)

    # Relationships
    # A user can have many appointments as a patient
    appointments_as_patient = relationship(
        "Appointment",
        foreign_keys="[Appointment.patient_id]",
        back_populates="patient"
    )
    # A user can have many appointments as a doctor
    appointments_as_doctor = relationship(
        "Appointment",
        foreign_keys="[Appointment.doctor_id]",
        back_populates="doctor"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
