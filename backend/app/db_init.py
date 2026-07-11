import time
import logging
from sqlalchemy import text
from app.core.database import engine, Base
from app.models.database import User, Upload, Analysis, Scores, WordScore, Feedback, ConsentLog, AuditLog, DeletionRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_initializer")


def init_db():
    logger.info("Initializing database...")
    retries = 10
    connected = False
    
    while retries > 0 and not connected:
        try:
            # Check connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            connected = True
            logger.info("Database connection verified.")
        except Exception as e:
            retries -= 1
            logger.warning(f"Database connection failed. Retrying in 3 seconds... ({retries} retries left)")
            time.sleep(3)

    if not connected:
        logger.error("Could not connect to database. Exiting.")
        raise Exception("Database connection timeout.")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise e


if __name__ == "__main__":
    init_db()
