import json
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, Request

app = FastAPI()

# Initialize Firebase
firebase_json = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_json:
    raise ValueError("Missing FIREBASE_CREDENTIALS in environment variables")

cred = credentials.Certificate(json.loads(firebase_json))  # Load from Vercel env
firebase_admin.initialize_app(cred, {"databaseURL": "https://game-lobby-75ba5-default-rtdb.firebaseio.com/"})

# Firebase Database Reference
DATA_REF = db.reference("entries")  # Path where we'll store data


def clean_old_entries():
    """Remove entries older than 5 minutes."""
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=5)
    
    all_entries = DATA_REF.get() or {}  # Fetch all data
    updated_entries = {key: value for key, value in all_entries.items() if datetime.fromisoformat(value["timestamp"]) > cutoff}

    DATA_REF.set(updated_entries)  # Save back to Firebase


@app.post("/register")
async def register(request: Request):
    """Register new data with a timestamp and clean old entries."""
    new_entry = await request.json()
    
    if not isinstance(new_entry, dict):
        return {"status": "error", "message": "Invalid JSON format"}

    new_entry["timestamp"] = datetime.utcnow().isoformat()
    entry_id = DATA_REF.push(new_entry)  # Push new entry with unique key

    clean_old_entries()  # Remove expired entries

    return {"status": "success", "id": entry_id.key}


@app.get("/list")
async def list_data(sort: str = None, order: str = "asc", filter: str = None):
    """Returns stored data with optional sorting and filtering."""
    entries = DATA_REF.get() or {}

    data = list(entries.values())  # Convert dict to list

    # Apply filtering
    if filter:
        data = [entry for entry in data if filter in entry]

    # Apply sorting
    if sort:
        try:
            data.sort(key=lambda x: x.get(sort, ""), reverse=(order == "desc"))
        except Exception as e:
            return {"error": f"Sorting failed: {str(e)}"}

    return data
