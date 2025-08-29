from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the SQLAlchemy engine
# The engine is the starting point for any SQLAlchemy application.
# It's the low-level object that connects to the database.
engine = create_engine(
    settings.DATABASE_URL,
    # connect_args are needed for SQLite, but good to have for other dbs
    # For PostgreSQL, you might not need this, but it doesn't hurt.
    # connect_args={"check_same_thread": False} # This is for SQLite only
)

# Create a configured "Session" class
# A session manages the connection to the database and handles transactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
# All of our database models (tables) will be created from this class.
Base = declarative_base()
