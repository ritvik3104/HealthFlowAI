import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.initial_data import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI(
    title="Doc Demo API",
    description="API for the Smart Doctor Appointment and Reporting Assistant",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    logger.info("Application startup...")
    try:
        init_db()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        # In a real app, you might want to exit if the DB fails to init
        # For now, we log the error and continue.

# Set up CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def read_root():
    """
    A simple root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Doc Demo API!"}

# Include the API router
app.include_router(api_router, prefix=settings.API_V1_STR)
