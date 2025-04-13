# app/db.py

import logging
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session # <--- IMPORT Session HERE
from sqlalchemy.ext.declarative import declarative_base
from fastapi import HTTPException

log = logging.getLogger(__name__)

# --- Corrected import path for DatabaseConfig ---
try:
    from .api.database import DatabaseConfig, DEFAULT_DATABASE_CONFIG_PATH
except ImportError:
    log.error("Could not import DatabaseConfig from app.api.database. Please check the file and class definition.")
    DatabaseConfig = None

# --- Global variables ---
DATABASE_URL = None
engine = None
SessionLocal = None
# Define Base here for models to import
Base = declarative_base()
log.info("SQLAlchemy Base created. Models should inherit from this.")


# --- Load Configuration and Initialize SQLAlchemy ---
try:
    if DatabaseConfig:
        log.info(f"Loading database configuration using DatabaseConfig class...")
        # Let DatabaseConfig handle finding the path or using default
        db_config = DatabaseConfig.load_from_file()
        DATABASE_URL = db_config.get_sqlalchemy_url()
        log.info(f"Database URL configured: {DATABASE_URL[:15]}...")

        if DATABASE_URL:
            connect_args = {}
            if DATABASE_URL.startswith("sqlite"):
                connect_args = {"check_same_thread": False}
            engine = create_engine(DATABASE_URL, connect_args=connect_args)
            log.info("SQLAlchemy Engine created.")
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            log.info("SQLAlchemy SessionLocal factory created.")
        else:
            log.error("Database URL could not be determined from configuration.")
            raise ValueError("Database URL is not configured.")
    else:
        raise ImportError("DatabaseConfig class could not be imported. Cannot initialize database.")

except Exception as e:
    log.error(f"CRITICAL: Failed to initialize database engine/session from config: {e}")
    engine = None
    SessionLocal = None
    DATABASE_URL = None
    raise RuntimeError(f"Database initialization failed: {e}") from e


# --- Dependency to Get DB Session ---
def get_db():
    """ FastAPI dependency that provides a SQLAlchemy database session. """
    if SessionLocal is None:
        log.error("Attempted to get DB session, but SessionLocal is None (initialization failed).")
        raise HTTPException(status_code=503, detail="Database connection not available.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Initialization Function ---
def init_db():
    """ Initializes the database by creating tables. """
    if Base is None or engine is None:
        msg = "Database Base or Engine not initialized (check config/startup logs). Cannot create tables."
        log.error(msg)
        return msg
    try:
        log.info(f"Attempting to create database tables on engine: {str(engine.url)}")
        Base.metadata.create_all(bind=engine)
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            detected_tables = ', '.join(tables) if tables else 'None'
            log.info(f"SQLAlchemy Base.metadata.create_all() executed.")
            return f"Schema initialized/verified successfully. Detected tables: {detected_tables}"
        except Exception as inspect_err:
            log.warning(f"Could not inspect tables after creation: {inspect_err}")
            return "Schema creation attempted, but table verification failed."
    except Exception as e:
        log.error(f"Error during Base.metadata.create_all(): {e}")
        try:
            with engine.connect() as connection:
                 log.info("Simple connection test successful after create_all failure.")
                 return f"Schema creation failed ({e}), but basic connection OK."
        except Exception as conn_err:
             log.error(f"Simple connection test also failed: {conn_err}")
             return f"Schema creation AND basic connection failed: {e}"

# --- Data Check Function ---
# Type hint uses the imported Session
def check_if_rulesets_exist(db: Session = None) -> bool:
    """ Checks if any rulesets exist in the database. """
    from . import models # Import models locally
    close_session = False
    if db is None:
        if SessionLocal is None:
            log.error("Cannot check for rulesets: SessionLocal not initialized.")
            return False
        db = SessionLocal()
        close_session = True

    try:
        if engine: # Check if engine was initialized
            inspector = inspect(engine)
            if models.Ruleset.__tablename__ not in inspector.get_table_names():
                 log.warning(f"Table '{models.Ruleset.__tablename__}' does not exist. Cannot check for rulesets.")
                 return False
            # Check if session is valid before querying
            if not db.is_active:
                 log.warning("Cannot check for rulesets: Database session is not active.")
                 return False
            count = db.query(models.Ruleset).count()
            return count > 0
        else:
            log.error("Cannot check for rulesets: Database engine not initialized.")
            return False
    except Exception as e:
         log.error(f"Error checking for existing rulesets: {e}")
         # Optionally re-raise or handle specific DB connection errors
         return False # Default to false on error
    finally:
        if close_session and db:
            db.close()

# --- Helper to get current config URL ---
def get_configured_database_url() -> str | None:
    """ Returns the database URL loaded at startup. """
    return DATABASE_URL

# --- Simple Connection Test ---
def test_connection() -> str:
    """ Attempts a simple connection using the initialized database engine. """
    if engine is None:
        return "Database engine not initialized (check config/startup logs)."
    try:
        # Use a short timeout
        with engine.connect().execution_options(connection_timeout=5) as connection:
            log.info("Database connection test successful via test_connection().")
            return "Connection successful."
    except Exception as e:
        log.error(f"Database connection test failed: {e}")
        return f"Connection failed: {e}"
