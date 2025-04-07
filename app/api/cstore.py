# app/api/cstore.py

from fastapi import APIRouter, Request
from pydantic import BaseModel
import subprocess
import signal
import logging
import json
import os
from fastapi.responses import JSONResponse

router = APIRouter()
cstore_process = None

CONFIG_FILE = "app/config/cstore.json"

# ---------- CONFIGURATION MODEL ----------

class CStoreConfig(BaseModel):
    ae_title: str
    port: int

# ---------- CONFIGURATION MANAGEMENT ----------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"ae_title": "DISCO_STORESCP", "port": 11112}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/config")
def get_config():
    try:
        return load_config()
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to load config"})

@router.post("/config")
def update_config(cfg: CStoreConfig):
    try:
        logging.info(f"Updating C-STORE config: {cfg}")
        save_config(cfg.dict())
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Failed to update config: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})

# ---------- LISTENER CONTROL ----------

@router.get("/status")
def cstore_status():
    global cstore_process
    running = cstore_process is not None and cstore_process.poll() is None
    logging.info(f"C-STORE status: {'running' if running else 'stopped'}")
    return {"running": running}

@router.post("/start")
def start_cstore():
    global cstore_process
    if cstore_process is None or cstore_process.poll() is not None:
        cstore_process = subprocess.Popen([
            "python", "-m", "app.services.cstore_scp"
        ])
        logging.info("Started C-STORE listener")
        return {"status": "started"}
    return {"status": "already_running"}

@router.post("/stop")
def stop_cstore():
    global cstore_process
    if cstore_process is not None:
        logging.info("Stopping C-STORE listener")
        cstore_process.terminate()
        try:
            cstore_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cstore_process.kill()
        cstore_process = None
        logging.info("Stopped C-STORE listener")
        return {"status": "stopped"}
    return {"status": "not_running"}

