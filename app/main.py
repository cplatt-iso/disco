# app/main.py
import subprocess
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db import init_db, SessionLocal
from app.api import cstore
from app.models import RuleSet
from app.services.initialize import seed_default_ruleset

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Only seed default rule if no rulesets exist
    db = SessionLocal()
    has_rules = db.query(RuleSet).first() is not None
    db.close()
    if not has_rules:
        seed_default_ruleset()

    start_frontend()
    yield

app = FastAPI(lifespan=lifespan)

# Mount backend API routers
app.include_router(cstore.router, prefix="/api/cstore")

@app.get("/")
def root():
    return {"message": "DISCO backend is running"}

def start_frontend():
    if os.getenv("DISCO_DEV_FRONTEND", "1") == "1":
        subprocess.Popen(
            ["npm", "run", "dev", "--", "--host"],
            cwd=os.path.join(os.path.dirname(__file__), "frontend"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Frontend server started at http://<your-ip>:5173")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

