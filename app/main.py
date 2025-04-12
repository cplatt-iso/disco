# app/main.py
import subprocess
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

# Import necessary components from your modules
from app import db # Imports SessionLocal, test_db_connection, initialize_schema
from app.models import RuleSet # Ensure models are imported so Base.metadata is populated
from app.api import cstore as cstore_api
from app.api import database as database_api
from app.api import ruleset as ruleset_api
from app.services.initialize import seed_default_ruleset

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    - Tests database connection.
    - Initializes database schema (creates tables if they don't exist). <--- ADDED
    - Seeds default ruleset if needed.
    - Starts frontend dev server (if enabled).
    """
    logger.info("Application startup sequence initiated...")
    db_ready = False
    schema_initialized = False

    # 1. Test Database Connection
    logger.info("Testing database connection...")
    try:
        connected, message = db.test_db_connection()
        if not connected:
            logger.critical(f"CRITICAL: Initial database connection failed: {message}. Database features may be unavailable.")
            # App might still start, but DB operations will likely fail
        else:
            logger.info(f"Initial database connection successful: {message}")
            db_ready = True
    except Exception as e:
        logger.critical(f"CRITICAL: Error during initial database connection test: {e}", exc_info=True)

    # 2. Initialize Database Schema (if connection was successful) <-- *** NEW STEP ***
    if db_ready:
        logger.info("Initializing database schema (creating tables if necessary)...")
        try:
            init_success, init_message = db.initialize_schema() # Call schema creation
            if init_success:
                logger.info(f"Database schema initialization successful: {init_message}")
                schema_initialized = True
            else:
                logger.error(f"Database schema initialization failed: {init_message}")
                # Decide if app should stop here? For now, log and continue.
        except Exception as e:
             logger.error(f"Unexpected error during schema initialization: {e}", exc_info=True)


    # 3. Seed Default Ruleset (only if DB connected, schema initialized, and no rules exist)
    #    We check schema_initialized flag now.
    if db_ready and schema_initialized:
        logger.info("Checking for existing rulesets...")
        try:
            with db.SessionLocal() as session:
                has_rules = session.query(RuleSet).first() is not None

            if not has_rules:
                logger.info("No rulesets found. Attempting to seed default ruleset...")
                seed_default_ruleset() # Call the seeding function
                logger.info("Default ruleset seeding process initiated.")
            else:
                logger.info("Existing rulesets found. Skipping default seeding.")
        # Catch specific exception if possible, or general Exception
        except Exception as e:
             # This error (no such table) should not happen anymore if schema_initialized is true,
             # but keep general error handling.
            logger.error(f"Error during ruleset check/seeding: {e}", exc_info=True)
    elif db_ready and not schema_initialized:
         logger.warning("Skipping ruleset seeding because schema initialization failed.")
    else:
         logger.warning("Skipping ruleset seeding because database connection failed.")


    # 4. Start Frontend Development Server (if enabled)
    start_frontend()

    logger.info("Application startup sequence finished.")
    yield
    # --- Shutdown logic ---
    logger.info("Application shutdown sequence initiated...")
    logger.info("Application shutdown sequence finished.")


# --- FastAPI Application Instance ---
app = FastAPI(
    title="DISCO Backend",
    description="Backend services for the DICOM Orchestration system.",
    version="0.1.0",
    lifespan=lifespan
)

# --- Mount API Routers ---
logger.info("Registering API routers...")
app.include_router(
    cstore_api.router,
    prefix="/api/cstore",
    tags=["C-STORE SCP"]
)
app.include_router(
    database_api.router,
    prefix="/api/database",
    tags=["Database Configuration"]
)
app.include_router( 
    ruleset_api.router,
    prefix="/api/rulesets", 
    tags=["Rulesets & Rules"]
)
logger.info("API routers registered.")

# --- Root Endpoint ---
@app.get("/", tags=["General"])
def root():
    """Provides a simple status message indicating the backend is running."""
    return {"message": "DISCO backend is running"}

# --- Frontend Server Function ---
def start_frontend():
    """Starts the frontend development server if DISCO_DEV_FRONTEND=1."""
    if os.getenv("DISCO_DEV_FRONTEND", "1") == "1":
        logger.info("DISCO_DEV_FRONTEND=1 detected. Starting frontend dev server...")
        try:
            frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
            process = subprocess.Popen(
                ["npm", "run", "dev", "--", "--host"],
                cwd=frontend_dir,
            )
            logger.info(f"Frontend dev server process started (likely on port 5173). Check npm output.")
        except FileNotFoundError:
            logger.error(f"Failed to start frontend: 'npm' command not found. Is Node.js/npm installed and in PATH?")
        except Exception as e:
            logger.error(f"Failed to start frontend subprocess: {e}", exc_info=True)
    else:
        logger.info("DISCO_DEV_FRONTEND is not '1'. Skipping frontend dev server start.")

# --- Main Execution Block ---
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info(f"Starting Uvicorn server on {host}:{port} (Reload: {reload})")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )
