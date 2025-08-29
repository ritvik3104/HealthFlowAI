import logging
from app.db.session import engine, Base
from app.models import user, appointment # Import all models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Creating all database tables...")
    try:
        # The Base.metadata object has collected all the table definitions
        # from our models. This command creates all of them in the database
        # connected by the engine.
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    init_db()
