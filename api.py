import requests
import json
from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import os

app = FastAPI()

# Gist details
GIST_ID = "dffa549bb0ddd4e06d38c87319349994"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Store this in Vercel's environment variables
GIST_URL = f"https://api.github.com/gists/{GIST_ID}"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def fetch_data():
    """Fetches current JSON data from the Gist."""
    response = requests.get(GIST_URL)
    if response.status_code == 200:
        gist_content = response.json()
        return json.loads(gist_content["files"]["data.json"]["content"])
    return []

def save_data(data):
    """Updates the Gist with new JSON data."""
    payload = {
        "files": {
            "data.json": {
                "content": json.dumps(data, indent=4)
            }
        }
    }
    response = requests.patch(GIST_URL, headers=HEADERS, json=payload)
    return response.status_code == 200

@app.post("/register")
async def register(request: Request):
    """Handles a POST request to register data, adding a timestamp and removing expired entries."""
    data = fetch_data()
    new_entry = await request.json()
    new_entry["timestamp"] = datetime.utcnow().isoformat()
    data.append(new_entry)

    # Remove expired entries (older than 5 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    data = [entry for entry in data if datetime.fromisoformat(entry["timestamp"]) > cutoff]

    if save_data(data):
        return {"status": "success", "entries": len(data)}
    return {"status": "error", "message": "Failed to update data"}

@app.get("/list")
async def list_data(sort: str = None, order: str = "asc", filter: str = None):
    """Returns the stored data, with optional sorting and filtering."""
    data = fetch_data()

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
