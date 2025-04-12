# app/api/cstore.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field # Added Field for potential validation later
import subprocess
# import signal # Not strictly needed for terminate/kill
import logging
import json
import os
import time # Added for potential delay

# --- Logging Setup ---
# Consider moving logging config to a central place if needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - API - %(message)s')

router = APIRouter()

# Global variable to hold the subprocess reference
cstore_process = None

# --- Configuration Handling ---
# Define path relative to project root or use environment variable
CONFIG_FILE = os.getenv('CSTORE_CONFIG_PATH', 'app/config/cstore.json')

DEFAULT_CONFIG = {
    "ae_title": "DISCO_STORESCP",
    "port": 11112,
    "bind_address": "0.0.0.0",
    "max_pdu_size": 116794,
    "storage_dir": "dicom_inbound" # Match the key used in cstore_scp.py
}

# Updated Pydantic Model to include all fields
class CStoreConfig(BaseModel):
    ae_title: str
    port: int = Field(..., gt=0, le=65535) # Example validation: port range
    bind_address: str
    max_pdu_size: int = Field(..., gt=0)   # Example validation: positive integer
    storage_dir: str # Renamed from storage_directory to match cstore_scp.py's expected key

def load_config() -> dict:
    """Loads C-STORE configuration, merging with defaults."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                loaded_config = json.load(f)
            # Ensure all default keys are present
            config = DEFAULT_CONFIG.copy()
            config.update(loaded_config) # Overwrite defaults with loaded values
            logging.info(f"Loaded config from {CONFIG_FILE}")
            return config
        else:
            logging.warning(f"Config file {CONFIG_FILE} not found. Using defaults.")
            return DEFAULT_CONFIG.copy()
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {CONFIG_FILE}. Using defaults.")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logging.error(f"Unexpected error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(data: dict):
    """Saves the C-STORE configuration."""
    try:
        # Optional: Add validation before saving if not relying solely on Pydantic
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved config to {CONFIG_FILE}")
    except Exception as e:
        logging.error(f"Failed to save config to {CONFIG_FILE}: {e}")
        # Re-raise to signal failure to the endpoint handler
        raise

# --- Listener Control Functions ---

def _start_listener_process():
    """Internal function to start the listener subprocess."""
    global cstore_process
    if cstore_process is None or cstore_process.poll() is not None:
        try:
            logging.info("Attempting to start C-STORE listener subprocess...")
            # Ensure the command uses the correct path/module structure
            # Using '-m' assumes 'app' is in PYTHONPATH or run from root
            cstore_process = subprocess.Popen(
                ["python", "-m", "app.services.cstore_scp"],
                # Add error/output redirection if desired for debugging
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
            )
            # Optional: Brief pause to let the process start
            time.sleep(1)
            if cstore_process.poll() is None:
                logging.info(f"C-STORE listener started successfully (PID: {cstore_process.pid}).")
                return True
            else:
                # Process terminated immediately, likely an error in cstore_scp.py startup
                stderr = cstore_process.stderr.read().decode() if cstore_process.stderr else "N/A"
                logging.error(f"C-STORE listener failed to start. Exit code: {cstore_process.returncode}. Stderr: {stderr}")
                cstore_process = None
                return False
        except Exception as e:
            logging.error(f"Exception occurred while starting C-STORE listener: {e}")
            cstore_process = None
            return False
    else:
        logging.warning("C-STORE listener start requested but process seems to be running.")
        return False # Indicate it wasn't newly started

def _stop_listener_process():
    """Internal function to stop the listener subprocess."""
    global cstore_process
    if cstore_process is not None and cstore_process.poll() is None:
        pid = cstore_process.pid
        logging.info(f"Attempting to stop C-STORE listener (PID: {pid})...")
        try:
            cstore_process.terminate() # Send SIGTERM first
            cstore_process.wait(timeout=5) # Wait for graceful shutdown
            logging.info(f"C-STORE listener (PID: {pid}) terminated gracefully.")
            cstore_process = None
            return True
        except subprocess.TimeoutExpired:
            logging.warning(f"C-STORE listener (PID: {pid}) did not terminate gracefully. Sending SIGKILL.")
            cstore_process.kill() # Force kill
            try:
                cstore_process.wait(timeout=2) # Wait briefly after kill
            except Exception:
                pass # Ignore wait errors after kill
            logging.info(f"C-STORE listener (PID: {pid}) killed.")
            cstore_process = None
            return True
        except Exception as e:
            logging.error(f"Exception occurred while stopping C-STORE listener (PID: {pid}): {e}")
            # Attempt to ensure process is cleared even if wait fails
            cstore_process = None
            return False # Indicate stop might not have been clean
    else:
        logging.warning("C-STORE listener stop requested but process is not running or already stopped.")
        if cstore_process is not None and cstore_process.poll() is not None:
            cstore_process = None # Clean up handle if process terminated externally
        return False # Indicate it wasn't running or wasn't stopped by this call


# ---------- API Endpoints ----------

@router.get("/config", response_model=CStoreConfig) # Use response_model for validation/docs
async def get_config():
    """Retrieves the current C-STORE SCP configuration."""
    try:
        # Load raw config dict
        raw_config = load_config()
        # Validate against Pydantic model before returning
        # This ensures consistency and catches missing keys from manual edits
        validated_config = CStoreConfig(**raw_config)
        return validated_config
    except Exception as e:
        logging.error(f"Error loading/validating config: {e}")
        raise HTTPException(status_code=500, detail="Failed to load or validate configuration")

# --- CHANGED TO PUT ---
@router.put("/config") # Accept PUT requests for updates
async def update_config_and_restart(cfg: CStoreConfig): # Use updated model
    """Updates the C-STORE SCP configuration and restarts the listener."""
    logging.info(f"Received request to update C-STORE config: {cfg.dict()}")

    try:
        # 1. Save the new configuration
        save_config(cfg.dict()) # Save the validated data

        # 2. Stop the current listener (if running)
        was_running = cstore_process is not None and cstore_process.poll() is None
        if was_running:
            if not _stop_listener_process():
                 # Stop failed, maybe log but proceed cautiously?
                 logging.warning("Failed to stop the running listener, attempting restart anyway.")
                 # Or raise error: raise HTTPException(status_code=500, detail="Failed to stop existing listener")

        # 3. Start the listener with the new config
        if _start_listener_process():
             return {"status": "Configuration updated and listener (re)started successfully."}
        else:
            # Start failed after saving config
             raise HTTPException(status_code=500, detail="Configuration saved, but failed to start listener process.")

    except Exception as e:
        logging.error(f"Failed during config update/restart process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration or restart listener: {e}")


@router.get("/status")
async def cstore_status():
    """Checks the running status of the C-STORE listener subprocess."""
    global cstore_process
    if cstore_process is not None and cstore_process.poll() is None:
        running = True
        pid = cstore_process.pid
    else:
        if cstore_process is not None and cstore_process.poll() is not None:
            # Process finished/crashed, clear the handle
            logging.info(f"Listener process (PID: {cstore_process.pid}) found terminated with exit code {cstore_process.returncode}. Clearing handle.")
            cstore_process = None
        running = False
        pid = None
    # logging.info(f"C-STORE status check: {'running' if running else 'stopped'}")
    return {"running": running, "pid": pid}

@router.post("/start")
async def start_cstore():
    """Starts the C-STORE listener subprocess if not already running."""
    if _start_listener_process():
        return {"status": "started"}
    else:
        # Check if it's already running vs failed to start
        if cstore_process is not None and cstore_process.poll() is None:
             return {"status": "already_running"}
        else:
             # Start failed
             # Use 500 Internal Server Error for failure to start
             raise HTTPException(status_code=500, detail="Listener process failed to start. Check logs.")

@router.post("/stop")
async def stop_cstore():
    """Stops the C-STORE listener subprocess if running."""
    if _stop_listener_process():
         return {"status": "stopped"}
    else:
         # Check if it wasn't running vs failed to stop
         # This path is hit if process was already stopped or stop failed
         # Let's assume "not_running" is the most common case here
         return {"status": "not_running"}
