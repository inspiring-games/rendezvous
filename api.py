from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import json
import os

app = FastAPI()
DATA_FILE = "/tmp/data.json"  # Must use /tmp/ in Vercel
EXPIRATION_MINUTES = 5

def load_data():
    """Loads JSON data from file, or returns an empty list if the file doesn't exist."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []  # Reset if file is corrupted
    return []

def save_data(data):
    """Saves JSON data to file with error handling."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Error writing data file:", e)  # Debug log

@app.post("/register")
async def register(request: Request):
    """Handles a POST request to register data, adding a timestamp and removing expired entries."""
    try:
        data = load_data()
        new_entry = await request.json()
        
        # Add timestamp safely
        new_entry["timestamp"] = datetime.utcnow().isoformat()

        # Append new entry
        data.append(new_entry)

        # Remove expired entries
        cutoff = datetime.utcnow() - timedelta(minutes=EXPIRATION_MINUTES)
        filtered_data = []
        
        for entry in data:
            try:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time > cutoff:
                    filtered_data.append(entry)
            except Exception as e:
                print("Skipping invalid entry:", e)  # Debugging
        
        save_data(filtered_data)
        return {"status": "success", "message": "Data registered", "entries": len(filtered_data)}

    except Exception as e:
        print("Register API Error:", e)  # Debug log
        return {"status": "error", "message": "Server error"}

@app.get("/list")
@app.post("/list")
async def list_data(request: Request, sort: str = None, order: str = "asc", filter_key: str = None):
    """Lists the stored data with optional sorting and filtering."""
    try:
        data = load_data()

        # Apply filtering
        if filter_key:
            data = [entry for entry in data if filter_key in entry]

        # Apply sorting
        if sort:
            try:
                data.sort(key=lambda x: x.get(sort, ""), reverse=(order == "desc"))
            except TypeError:
                pass  # Ignore sorting errors

        return data
    except Exception as e:
        print("List API Error:", e)  # Debugging
        return {"status": "error", "message": "Server error"}
