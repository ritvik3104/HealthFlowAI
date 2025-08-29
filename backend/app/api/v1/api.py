from fastapi import APIRouter
from app.api.v1 import auth, patients, doctors, agent, users

# This is the main router for the v1 API.
# It creates the api_router object and includes all the other specific routers.
api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
