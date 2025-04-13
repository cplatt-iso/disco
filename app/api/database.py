# app/api/database.py

import json
import logging
import os
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator, ValidationError # Import ValidationError
from sqlalchemy.orm import Session # Keep if needed for future DB interactions here

# Use standard logging
log = logging.getLogger(__name__)

# --- Configuration Model ---
# Use Literal for specific choices for db_type
DatabaseType = Literal["sqlite", "postgresql", "mysql"] # Add other supported types

# Define default config path relative to this file or project root
# Using project root might be more robust if file location changes
DEFAULT_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config'))
DEFAULT_DATABASE_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, 'database.json')


class DatabaseConfig(BaseModel):
    db_type: DatabaseType = Field(..., description="Type of database (e.g., 'sqlite')")
    db_path: Optional[str] = Field(None, description="Path for SQLite file")
    db_conn_str: Optional[str] = Field(None, description="Full connection string for non-SQLite DBs")

    # Private attribute to store the config path, not part of the model validation itself
    _config_path: str = DEFAULT_DATABASE_CONFIG_PATH

    # Pydantic V2 custom initialization/root validator approach
    # Use model_validator to load data after initial field checks (if any)
    # This is a cleaner way than overriding __init__ in Pydantic v2
    @classmethod
    def load_from_file(cls, path: str = DEFAULT_DATABASE_CONFIG_PATH) -> 'DatabaseConfig':
        """Class method to load configuration from a JSON file."""
        log.info(f"Attempting to load database config from: {path}")
        config_data = {}
        if not os.path.exists(path):
            log.warning(f"Config file not found at {path}. Cannot load DatabaseConfig.")
            # Raise an error or return a default config - raising is clearer
            raise FileNotFoundError(f"Database configuration file not found: {path}")

        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
            log.info(f"Successfully loaded data from {path}")
            # Validate the loaded data using Pydantic's own validation
            instance = cls(**config_data) # This will trigger validation
            instance._config_path = path # Store the path used
            return instance
        except json.JSONDecodeError as e:
            log.error(f"Error decoding JSON from {path}: {e}")
            raise ValueError(f"Invalid JSON in config file: {path}") from e
        except ValidationError as e:
            log.error(f"Validation error loading config from {path}: {e}")
            raise ValueError(f"Invalid configuration data in {path}") from e
        except Exception as e:
            log.error(f"Unexpected error loading config from {path}: {e}")
            raise RuntimeError(f"Failed to load database config") from e


    def save_to_file(self, path: Optional[str] = None):
        """Saves the current configuration back to the JSON file."""
        save_path = path or self._config_path
        log.info(f"Attempting to save database config to: {save_path}")
        try:
             # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # Use model_dump (Pydantic V2) to get serializable data
            config_data = self.model_dump(include={'db_type', 'db_path', 'db_conn_str'})
            with open(save_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            log.info(f"Database configuration successfully saved to {save_path}")
            # IMPORTANT: Remind user that restart is needed
            log.warning("Database configuration saved. Application restart is required for changes to take effect.")
        except Exception as e:
            log.error(f"Error saving database config to {save_path}: {e}")
            raise RuntimeError("Failed to save database configuration.") from e


    @validator('db_path', always=True)
    def check_path_if_sqlite(cls, v, values):
        """Validate that db_path is set if db_type is sqlite."""
        db_type = values.get('db_type')
        if db_type == 'sqlite' and not v:
            raise ValueError('db_path is required when db_type is sqlite')
        return v

    @validator('db_conn_str', always=True)
    def check_conn_str_if_not_sqlite(cls, v, values):
        """Validate that db_conn_str is set if db_type is not sqlite."""
        db_type = values.get('db_type')
        if db_type != 'sqlite' and not v:
            raise ValueError(f'db_conn_str is required when db_type is {db_type}')
        return v

    def get_sqlalchemy_url(self) -> Optional[str]:
        """Generates the SQLAlchemy URL based on the configuration."""
        if self.db_type == "sqlite":
            if self.db_path:
                # Ensure the path is absolute or handle relative paths carefully
                abs_path = os.path.abspath(self.db_path)
                # Ensure directory exists before engine tries to create the file
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                return f"sqlite:///{abs_path}"
            else:
                 # Should be caught by validator, but belts and braces
                 log.error("Cannot generate SQLAlchemy URL: db_type is sqlite but db_path is missing.")
                 return None
        elif self.db_conn_str:
            # For other types, use the provided connection string directly
            # Ensure it includes the driver (e.g., postgresql+psycopg2://...)
            return self.db_conn_str
        else:
            log.error(f"Cannot generate SQLAlchemy URL: db_type is {self.db_type} but db_conn_str is missing.")
            return None


# --- API Router ---
# Keep the router for managing the config via API
router = APIRouter()

# Dependency to get the current config instance (loaded at startup)
# This doesn't work well if db.py loads it first. We need a single source of truth.
# It's better for db.py to load it, and the API uses that instance or reloads as needed.
# Let's remove this dependency for now and handle config in endpoints directly or via app state if needed later.

@router.get("/database/config", response_model=DatabaseConfig)
async def get_database_config():
    """Gets the current database configuration from the file."""
    try:
        # Reload from file for API requests to ensure freshness
        config = DatabaseConfig.load_from_file()
        # Exclude private attribute when returning
        return config
    except FileNotFoundError:
         raise HTTPException(status_code=404, detail="Database configuration file not found.")
    except Exception as e:
         log.error(f"Error reading database config via API: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to read database configuration: {e}")

@router.put("/database/config", response_model=DatabaseConfig)
async def update_database_config(config_update: DatabaseConfig):
    """
    Updates the database configuration file.
    Requires application restart to take effect.
    """
    try:
        # The input 'config_update' is already validated by Pydantic
        config_update.save_to_file() # Save the validated data
         # Return the saved config (which should match input)
        return config_update
    except ValueError as e: # Catch validation errors during save if any added later
         raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e: # Catch file save errors
         raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log.error(f"Unexpected error saving database config via API: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while saving the configuration.")
