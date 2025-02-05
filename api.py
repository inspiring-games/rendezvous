from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import json
import os

app = FastAPI()
DATA_FILE = "/tmp/data.json"  # Use /tmp/ for write permissions in Vercel
EXPIRATION_MINUTES = 5

def load_data():
    """Loads JSON data from file, or returns an empty list if the file doesn't exist."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    """Saves JSON data to file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

@app.post("/register")
async def register(request: Request):
    """Handles a POST request to register data, adding a timestamp and removing expired entries."""
    data = load_data()
    new_entry = await request.json()
    
    # Add timestamp
    new_entry["timestamp"] = datetime.utcnow().isoformat()

    # Append new entry
    data.append(new_entry)

    # Remove expired entries
    cutoff = datetime.utcnow() - timedelta(minutes=EXPIRATION_MINUTES)
    data = [entry for entry in data if datetime.fromisoformat(entry["timestamp"]) > cutoff]

    save_data(data)
    return {"status": "success", "message": "Data registered", "entries": len(data)}

@app.get("/list")
@app.post("/list")
async def list_data(request: Request, sort: str = None, order: str = "asc", filter_key: str = None):
    """Lists the stored data with optional sorting and filtering."""
    data =
