# app/main.py
from .db import init_db

def setup_database():
    init_db()

if __name__ == "__main__":
    setup_database()

