# app/api/database.py

import json
import os
import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

# Assume db logic is updated as shown in step 3
from app import db # Or wherever your updated DB logic resides

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - API-DB - %(message)s')

router = APIRouter()

DATABASE_CONFIG_FILE = os.getenv('DATABASE_CONFIG_PATH', 'app/config/database.json')
# WARNING: Storing passwords in config files is insecure for production.
# Consider using environment variables (e.g., os.getenv('DATABASE_PASSWORD'))
# and adjusting the Pydantic model and saving logic accordingly.

DEFAULT_DB_CONFIG = {
  "db_type": "sqlite", "db_path": "disco.db", "db_host": None,
  "db_port": None, "db_name": None, "db_user": None, "db_password": None
}

# --- Pydantic Model for Validation ---
class DatabaseConfig(BaseModel):
    db_type: Literal['sqlite', 'postgresql', 'mysql']
    db_path: Optional[str] = None # Required for sqlite
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None # Insecure storage - see warning above

    @validator('db_path', always=True)
    def check_sqlite_path(cls, v, values):
        if values.get('db_type') == 'sqlite' and not v:
            raise ValueError('db_path is required for sqlite')
        return v

    @validator('db_host', always=True)
    def check_remote_host(cls, v, values):
        db_type = values.get('db_type')
        if db_type in ['postgresql', 'mysql'] and not v:
            raise ValueError(f'db_host is required for {db_type}')
        return v

    # Add similar validators for port, db_name, db_user if needed for pg/mysql

def load_db_config() -> dict:
    """Loads DB config, merging with defaults."""
    try:
        if os.path.exists(DATABASE_CONFIG_FILE):
            with open(DATABASE_CONFIG_FILE, "r") as f:
                loaded_config = json.load(f)
            config = DEFAULT_DB_CONFIG.copy()
            config.update(loaded_config)
            logging.info(f"Loaded DB config from {DATABASE_CONFIG_FILE}")
            # Validate loaded config before returning (optional but good)
            # DatabaseConfig(**config)
            return config
        else:
            logging.warning(f"DB Config file {DATABASE_CONFIG_FILE} not found. Using defaults.")
            return DEFAULT_DB_CONFIG.copy()
    except Exception as e:
        logging.error(f"Error loading DB config: {e}. Using defaults.")
        return DEFAULT_DB_CONFIG.copy()

def save_db_config(data: dict):
    """Saves the DB configuration."""
    try:
        with open(DATABASE_CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved DB config to {DATABASE_CONFIG_FILE}")
    except Exception as e:
        logging.error(f"Failed to save DB config: {e}")
        raise # Re-raise

# --- API Endpoints ---

@router.get("/config", response_model=DatabaseConfig)
async def get_database_config():
    """Retrieves the current database configuration."""
    try:
        raw_config = load_db_config()
        # Validate before returning
        return DatabaseConfig(**raw_config)
    except Exception as e:
        logging.error(f"Error reading/validating DB config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load/validate DB configuration: {e}")

@router.put("/config")
async def update_database_config(config: DatabaseConfig):
    """
    Updates the database configuration.
    Requires application restart to take effect.
    """
    logging.info(f"Received request to update DB config: {config.dict(exclude={'db_password'})}") # Exclude password from logs
    try:
        # Note: This saves the password to the file if provided. Consider security implications.
        save_db_config(config.dict())
        return {
            "status": "Configuration saved successfully.",
            "message": "IMPORTANT: A restart of the application is required for these changes to take effect."
        }
    except Exception as e:
        logging.error(f"Failed to save DB configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save DB configuration: {e}")

@router.post("/initialize")
async def initialize_database():
    """
    Attempts to connect to the database using current settings
    and initialize the schema (create tables).
    """
    logging.info("Received request to initialize database schema.")
    try:
        # The db.init_db function should now use the dynamically loaded config
        connection_successful, message = db.test_db_connection()
        if not connection_successful:
             logging.error(f"Database connection test failed: {message}")
             raise HTTPException(status_code=500, detail=f"Database connection test failed: {message}")

        logging.info("Database connection successful. Attempting schema initialization...")
        init_success, init_message = db.initialize_schema() # New function in db.py

        if init_success:
            logging.info(f"Database initialization successful: {init_message}")
            return {"status": "Database connection successful and schema initialized/verified.", "message": init_message}
        else:
            logging.error(f"Database schema initialization failed: {init_message}")
            raise HTTPException(status_code=500, detail=f"Schema initialization failed: {init_message}")

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        raise http_exc
    except Exception as e:
        logging.error(f"Unexpected error during database initialization: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
