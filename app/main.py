# app/main.py

import logging
import os
import subprocess
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import database setup (engine/SessionLocal created based on config in db.py)
# Base is implicitly available via models when they inherit from db.Base
from .db import SessionLocal, init_db, check_if_rulesets_exist, get_configured_database_url
# Import models and schemas
from . import models, schemas

# Import API route modules
from .api import ruleset, cstore
# --- Correct path for Database API router ---
from .api import database as database_router
# --- Import Auth Router ---
from .api import auth as auth_router

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Application Startup/Shutdown Logic ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    log.info("Application startup sequence initiated...")

    # Log configured DB URL (read at startup by db.py)
    configured_db_url = get_configured_database_url()
    log.info(f"Using database configured at startup: {configured_db_url[:15]}..." if configured_db_url else "Database URL not configured!")

    # Initialize DB (create tables if they don't exist)
    log.info("Initializing database schema (creating tables if necessary)...")
    try:
        db_init_result = init_db() # This now uses the engine created in db.py
        log.info(f"Database schema initialization result: {db_init_result}")
        if "failed" in db_init_result.lower():
             log.warning("Database initialization reported issues. Application might not function correctly.")
             # Consider stopping startup if init fails critically
             # raise RuntimeError("Database initialization failed.")

    except Exception as e:
        log.error(f"CRITICAL: Unhandled exception during database initialization: {e}")
        # raise e # Stop startup
        yield # Allow shutdown logic to run
        return # Exit lifespan

    # --- SEEDING LOGIC ---
    log.info("Checking for existing data (users/roles)...")
    db = None # Define db outside try block
    try:
        db = SessionLocal() # Get a session for seeding
        # Check/Create Admin Role
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        if not admin_role:
            log.info("Admin role not found. Creating default admin role...")
            admin_role = models.Role(name="admin", description="Administrator role with full access")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            log.info("Default 'admin' role created.")
        else:
            log.info("Admin role already exists.")

        # Check/Create Admin User
        ADMIN_EMAIL = os.getenv("DISCO_ADMIN_EMAIL", "admin@example.com")
        ADMIN_PASSWORD = os.getenv("DISCO_ADMIN_PASSWORD", "changeme") # CHANGE THIS DEFAULT!

        admin_user = db.query(models.User).filter(models.User.email == ADMIN_EMAIL).first()
        if not admin_user:
            log.info(f"Admin user '{ADMIN_EMAIL}' not found. Creating default admin user...")
            try:
                from .core.security import get_password_hash
                if not ADMIN_PASSWORD:
                     log.error("Cannot create admin user: DISCO_ADMIN_PASSWORD is not set or is empty.")
                else:
                    hashed_password = get_password_hash(ADMIN_PASSWORD)
                    admin_user = models.User(email=ADMIN_EMAIL, hashed_password=hashed_password, is_active=True, is_superuser=True, auth_provider='local')
                    if admin_role: # Ensure admin_role exists before appending
                        admin_user.roles.append(admin_role)
                    db.add(admin_user)
                    db.commit()
                    log.info(f"Default admin user '{ADMIN_EMAIL}' created. PASSWORD IS '{ADMIN_PASSWORD}' - CHANGE THIS!")
            except ImportError:
                log.error("Could not import get_password_hash from app.core.security. Cannot create admin user.")
                db.rollback()
            except Exception as e:
                log.error(f"Error creating default admin user: {e}")
                db.rollback()
        else:
            log.info(f"Admin user '{ADMIN_EMAIL}' already exists.")

        # Check rulesets
        log.info("Checking for existing rulesets...")
        if not check_if_rulesets_exist(db):
             log.info("No existing rulesets found.")
        else:
            log.info("Existing rulesets found.")

    except Exception as e:
         log.error(f"An error occurred during data seeding: {e}")
         if db: db.rollback() # Rollback any partial seeding changes
    finally:
        if db: db.close() # Ensure session is closed
    # --- END SEEDING LOGIC ---


    # --- Start Frontend Dev Server (Optional) ---
    frontend_process = None
    run_frontend_dev = os.getenv("DISCO_DEV_FRONTEND", "0") == "1"
    if run_frontend_dev:
        log.info("DISCO_DEV_FRONTEND=1 detected. Starting frontend dev server...")
        # ... (frontend startup logic remains the same) ...
        try:
            frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))
            if not os.path.exists(os.path.join(frontend_dir, 'package.json')):
                 log.error(f"package.json not found in {frontend_dir}. Cannot start frontend.")
            else:
                frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=(sys.platform == 'win32'))
                log.info(f"Frontend dev server process started (PID: {frontend_process.pid}). Check npm output.")
                time.sleep(3)
        except Exception as e:
            log.error(f"Failed to start frontend dev server: {e}")
            frontend_process = None
    else:
         log.info("Frontend dev server not started (DISCO_DEV_FRONTEND!=1).")


    log.info("Application startup sequence finished.")
    yield # Application runs here
    # Shutdown logic
    log.info("Application shutdown sequence initiated...")
    # ... (frontend shutdown logic remains the same) ...
    if frontend_process and frontend_process.poll() is None:
        log.info(f"Terminating frontend dev server process (PID: {frontend_process.pid})...")
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
            log.info("Frontend dev server terminated.")
        except subprocess.TimeoutExpired:
            log.warning("Frontend dev server did not terminate gracefully, killing.")
            frontend_process.kill()
    log.info("Application shutdown sequence finished.")

# --- Create FastAPI App Instance with Lifespan Manager ---
app = FastAPI(
    title="DISCO API",
    version="0.1.0",
    description="DICOM Identification Service and Configuration Orchestrator",
    lifespan=lifespan
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Add production frontend URL here if needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register API Routers ---
log.info("Registering API routers...")
# Include Authentication router
try:
    # Use the imported auth_router variable
    app.include_router(auth_router.router, tags=["Authentication"], prefix="/api/auth")
    log.info("Authentication router registered successfully.")
except NameError:
     log.error("auth_router variable not defined (Import failed?). Authentication router not registered.")
except Exception as e:
    log.error(f"An unexpected error occurred while registering Authentication router: {e}")

# Include RuleSets router
try:
    # Ensure variable 'ruleset' exists from import
    app.include_router(ruleset.router, prefix="/api", tags=["RuleSets"])
    log.info("RuleSets router registered successfully.")
except NameError:
     log.error("ruleset router variable not defined (Import failed?). RuleSets router not registered.")
except Exception as e:
     log.error(f"An unexpected error occurred while registering RuleSets router: {e}")

# Include CStore router
try:
    # Ensure variable 'cstore' exists from import
    app.include_router(cstore.router, prefix="/api", tags=["CStore"])
    log.info("CStore router registered successfully.")
except NameError:
     log.error("cstore router variable not defined (Import failed?). CStore router not registered.")
except Exception as e:
    log.error(f"An unexpected error occurred while registering CStore router: {e}")

# --- Include Database Config router ---
try:
    # Use the imported database_router variable
    app.include_router(database_router.router, prefix="/api", tags=["DatabaseConfig"])
    log.info("DatabaseConfig router registered successfully.")
except NameError:
     log.error("database_router variable not defined (Import failed?). DatabaseConfig router not registered.")
except Exception as e:
     log.error(f"An unexpected error occurred while registering DatabaseConfig router: {e}")


# --- Root Endpoint ---
@app.get("/", tags=["Root"], include_in_schema=False)
async def read_root():
    return {"message": "Welcome to the DISCO API. See /docs for details."}


# --- Static Files Mount ---
static_files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend/dist"))
if os.path.exists(static_files_dir) and os.path.isdir(static_files_dir):
     log.info(f"Serving static files from: {static_files_dir}")
     # Serve index.html for any path not matching API routes or other static files
     app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")
else:
     log.warning(f"Static files directory not found or not a directory: {static_files_dir}. Frontend build may be missing.")
     if not any(route.path == "/" for route in app.routes if isinstance(route, Route)): # Check if root GET exists
          @app.get("/", tags=["Root"], include_in_schema=False)
          async def missing_frontend_message():
              return {"message": "Welcome to DISCO API. Frontend not found.", "docs": "/docs"}


# --- Main Execution Block ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    reload = os.getenv("UVICORN_RELOAD", "true").lower() == "true"

    log.info(f"Attempting to start Uvicorn server directly via __main__ on {host}:{port} (Reload: {reload})...")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[os.path.dirname(__file__)] if reload else None,
        log_level="info"
    )
