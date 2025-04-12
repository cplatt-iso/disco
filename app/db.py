# app/db.py
"""
Handles database configuration, connection, session management,
and schema initialization based on settings in app/config/database.json.
"""
import os
import json
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# --- Constants and Configuration ---
DATABASE_CONFIG_FILE = os.getenv('DATABASE_CONFIG_PATH', 'app/config/database.json')
DEFAULT_DB_CONFIG = {
  "db_type": "sqlite",
  "db_path": "disco.db", # Default relative path for SQLite
  "db_host": None,
  "db_port": None,
  "db_name": None,
  "db_user": None,
  "db_password": None # Password should ideally come from ENV
}
DATABASE_PASSWORD_ENV_VAR = 'DATABASE_PASSWORD' # ENV variable for password

# --- Logging Setup ---
# Use a named logger for better context in logs
logger = logging.getLogger(__name__)
# Ensure logging is configured (basicConfig is often called in main.py,
# but having a basic setup here can be a fallback)
if not logging.getLogger().hasHandlers():
     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# --- Internal Configuration Loading ---
def load_db_config_internal() -> dict:
    """
    Internal function to load DB config, prioritizing environment variables
    for sensitive data like passwords. Should only be called internally
    by this module during setup.
    """
    config = DEFAULT_DB_CONFIG.copy()
    if os.path.exists(DATABASE_CONFIG_FILE):
        try:
            with open(DATABASE_CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                # Only update if loaded is a dictionary
                if isinstance(loaded, dict):
                    config.update(loaded)
                else:
                    logger.warning(f"Content of {DATABASE_CONFIG_FILE} is not a valid JSON object. Using defaults.")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {DATABASE_CONFIG_FILE}. Using defaults.", exc_info=True)
        except Exception as e:
            logger.error(f"Error loading {DATABASE_CONFIG_FILE}: {e}. Using defaults.", exc_info=True)
    else:
        logger.info(f"Configuration file {DATABASE_CONFIG_FILE} not found. Using default database settings.")


    # --- IMPORTANT: Password Handling ---
    env_password = os.getenv(DATABASE_PASSWORD_ENV_VAR)
    if env_password:
        if config.get('db_password') and config['db_password'] != env_password:
             logger.warning(f"Password found in both config file and ${DATABASE_PASSWORD_ENV_VAR} environment variable. Using environment variable.")
        config['db_password'] = env_password
        logger.info(f"Using database password from ${DATABASE_PASSWORD_ENV_VAR} environment variable.")
    elif config.get('db_password'):
         # Only log if password came from file and not ENV
         logger.warning(f"Using database password from config file ({DATABASE_CONFIG_FILE}). Use ${DATABASE_PASSWORD_ENV_VAR} environment variable for better security in production.")
    # --- End Password Handling ---

    return config

# --- Database URL Construction ---
def get_database_url() -> str:
    """
    Constructs the SQLAlchemy database URL based on the loaded configuration.
    Handles SQLite, PostgreSQL, and MySQL types.
    """
    config = load_db_config_internal()
    db_type = config.get('db_type', DEFAULT_DB_CONFIG['db_type'])

    logger.info(f"Attempting to configure database connection for type: {db_type}")

    if db_type == "sqlite":
        db_path = config.get('db_path', DEFAULT_DB_CONFIG['db_path'])
        # Ensure the directory exists for the SQLite file if a path is specified
        abs_db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(abs_db_path)
        try:
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Using SQLite database at: {abs_db_path}")
            # Use 4 slashes for absolute paths on Unix/Mac, 3 for relative or Windows absolute
            # SQLAlchemy typically handles this correctly with 3 slashes for absolute paths too.
            return f"sqlite:///{abs_db_path}"
        except OSError as e:
             logger.error(f"Failed to create directory for SQLite DB at {db_dir}: {e}. Using in-memory DB as fallback.", exc_info=True)
             return "sqlite:///:memory:" # Fallback to in-memory

    elif db_type in ["postgresql", "mysql"]:
        user = config.get('db_user')
        password = config.get('db_password') # Already prioritized ENV var
        host = config.get('db_host')
        port = config.get('db_port')
        dbname = config.get('db_name')

        # Validate required fields for remote databases
        missing_fields = [field for field in ['db_user', 'db_host', 'db_port', 'db_name'] if not config.get(field)]
        if missing_fields:
            logger.error(f"Missing required configuration field(s) for database type '{db_type}': {', '.join(missing_fields)}. Falling back to default SQLite.")
            # Fallback safely to default SQLite configuration
            return f"sqlite:///{os.path.abspath(DEFAULT_DB_CONFIG['db_path'])}"

        # Choose driver and default port based on type
        driver = ""
        default_port = None
        if db_type == "postgresql":
            driver = "postgresql+psycopg2" # Requires psycopg2-binary
            default_port = 5432
        elif db_type == "mysql":
            driver = "mysql+mysqlconnector" # Requires mysql-connector-python
            default_port = 3306

        # Use default port if not specified or invalid
        try:
            port = int(port) if port else default_port
        except ValueError:
             logger.warning(f"Invalid port '{port}' configured for {db_type}. Using default port {default_port}.")
             port = default_port

        # Encode password if present (SQLAlchemy handles URL encoding)
        encoded_password = f":{password}" if password else ""

        url = f"{driver}://{user}{encoded_password}@{host}:{port}/{dbname}"
        logger.info(f"Configured {db_type} database connection: {driver}://{user}:***@{host}:{port}/{dbname}")
        return url
    else:
        logger.error(f"Unsupported db_type '{db_type}' specified in configuration. Falling back to default SQLite.")
        # Fallback safely to default SQLite configuration
        return f"sqlite:///{os.path.abspath(DEFAULT_DB_CONFIG['db_path'])}"


# --- SQLAlchemy Core Setup ---
SQLALCHEMY_DATABASE_URL = get_database_url()
logger.info(f"SQLAlchemy Engine will use URL derived from configuration.")

# Create engine
# Consider connection pooling options for production (pool_size, max_overflow)
# `connect_args` might be needed for specific drivers or settings (e.g., SSL)
engine_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
     # connect_args={"check_same_thread": False} is only needed if using SQLite
     # with multiple threads, which might be the case with FastAPI's async nature.
     engine_args["connect_args"] = {"check_same_thread": False}

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_args)
except ImportError as e:
     logger.critical(f"Failed to create SQLAlchemy engine: Driver missing? {e}", exc_info=True)
     # Propagate the error to prevent the app from starting incorrectly
     raise ImportError(f"Database driver potentially missing for URL {SQLALCHEMY_DATABASE_URL}: {e}") from e


# Session Factory - Use this to create sessions in your application logic (e.g., via FastAPI dependency)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for your declarative models
# IMPORTANT: Ensure all your SQLAlchemy models in `app/models.py` (or elsewhere)
# inherit from this `Base` object.
# Example:
# from app.db import Base
# class MyModel(Base):
#    __tablename__ = 'my_table'
#    # ... columns ...
Base = declarative_base()

from app import models # Assuming your models are in app/models.py
logger.info("SQLAlchemy Base created and models implicitly imported.")

# --- Database Utility Functions ---

def test_db_connection() -> tuple[bool, str]:
    """
    Tests the database connection using the configured engine.

    Returns:
        tuple[bool, str]: (True, "Connection successful.") on success,
                          (False, error_message) on failure.
    """
    if not engine:
         return False, "SQLAlchemy engine is not initialized."
    try:
        # Use a short timeout for the connection test if possible (driver-dependent)
        # Example for PostgreSQL: connection = engine.connect().execution_options(connection_timeout=5)
        with engine.connect() as connection:
            # Optional: Perform a simple query
            # connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful.")
            return True, "Connection successful."
    except OperationalError as e:
        # Specific error for connection issues (wrong host, port, credentials, db name)
        msg = f"Connection failed (OperationalError): Check host, port, credentials, database name. Error: {e}"
        logger.error(msg)
        return False, msg
    except SQLAlchemyError as e:
        # Broader SQLAlchemy errors
        msg = f"Connection failed (SQLAlchemyError): {e}"
        logger.error(msg)
        return False, msg
    except Exception as e:
        # Catch-all for unexpected errors during connection
        msg = f"An unexpected error occurred during connection test: {e}"
        logger.error(msg, exc_info=True)
        return False, msg

def initialize_schema() -> tuple[bool, str]:
    """
    Initializes the database schema by creating tables defined in models
    that inherit from the `Base` object.

    This function does NOT handle database migrations (schema changes).

    Returns:
        tuple[bool, str]: (True, success_message) on success,
                          (False, error_message) on failure.
    """
    global Base # Ensure Base from this module is used
    if Base is None or not hasattr(Base, 'metadata'):
         msg = "Declarative base (Base) or its metadata is not defined. Cannot initialize schema."
         logger.error(msg)
         return False, msg
    if not engine:
         return False, "SQLAlchemy engine is not initialized. Cannot initialize schema."

    try:
        logger.info("Attempting to create database tables based on Base.metadata...")
        # Create tables that don't exist. Does not alter existing tables.
        Base.metadata.create_all(bind=engine)
        logger.info("SQLAlchemy Base.metadata.create_all() executed successfully.")

        # Verify table creation by inspecting the database
        try:
             inspector = inspect(engine)
             tables = inspector.get_table_names()
             # Check against expected tables defined in Base.metadata
             expected_tables = set(Base.metadata.tables.keys())
             missing_tables = expected_tables - set(tables)

             if not expected_tables:
                 msg = "Schema initialization ran, but no tables are defined in Base.metadata."
                 logger.warning(msg)
                 # Return True because create_all succeeded, but message indicates empty schema
                 return True, msg
             elif missing_tables:
                 msg = f"Schema initialization ran, but expected tables are missing: {', '.join(missing_tables)}. Detected: {', '.join(tables)}"
                 logger.warning(msg)
                 # Return True as create_all didn't error, but warn about missing tables
                 return True, msg
             else:
                 msg = f"Schema initialized/verified successfully. Detected tables: {', '.join(tables)}"
                 logger.info(msg)
                 return True, msg
        except Exception as inspect_e:
             # If inspection fails, still report create_all success but note inspection issue
             msg = f"Schema initialization (create_all) appeared successful, but failed to verify tables via inspection: {inspect_e}"
             logger.warning(msg)
             return True, msg # create_all didn't raise error

    except OperationalError as e:
        # Errors during CREATE TABLE often indicate permission issues or DB connection problems
        msg = f"Schema initialization failed (OperationalError during create_all): {e}"
        logger.error(msg)
        return False, msg
    except Exception as e:
        # Catch-all for unexpected errors during schema creation
        msg = f"An unexpected error occurred during schema initialization (create_all): {e}"
        logger.error(msg, exc_info=True)
        return False, msg


# --- FastAPI Dependency (Optional Convenience) ---
# You can place this here or in a dedicated `dependencies.py` file.
# Use this in your FastAPI path operations to get a DB session.
# Example: def my_api_route(db: Session = Depends(get_db)): ...
# from sqlalchemy.orm import Session
# from fastapi import Depends
# def get_db():
#     """FastAPI dependency to provide a database session per request."""
#     database = SessionLocal()
#     try:
#         yield database
#     finally:
#         database.close()
