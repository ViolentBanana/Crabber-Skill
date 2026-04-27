import os
import json
import time
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

# Configuration paths
CRABBER_HOME = Path(os.path.expanduser("~/.crabber"))
DB_PATH = CRABBER_HOME / "db.json"
TEMPLATES_DIR = CRABBER_HOME / "core" / "templates"

app = FastAPI(title="Crabber Skill Server")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Background task for cleanup
async def cleanup_task():
    while True:
        try:
            if DB_PATH.exists():
                with open(DB_PATH, "r") as f:
                    db = json.load(f)
                
                now = time.time()
                active_files = []
                files_changed = False
                
                for file_info in db.get("files", []):
                    created_at = file_info.get("created_at", 0)
                    ttl = file_info.get("ttl", 3600)  # Default 1 hour
                    
                    if ttl > 0 and (now - created_at) > ttl:
                        # File expired, remove symlink
                        symlink_path = Path(file_info["path"])
                        try:
                            if symlink_path.is_symlink():
                                symlink_path.unlink()
                            files_changed = True
                        except Exception as e:
                            print(f"Error removing symlink {symlink_path}: {e}")
                    else:
                        active_files.append(file_info)
                
                if files_changed:
                    db["files"] = active_files
                    with open(DB_PATH, "w") as f:
                        json.dump(db, f, indent=4)
        except Exception as e:
            print(f"Cleanup task error: {e}")
            
        await asyncio.sleep(60) # Run cleanup every minute

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_task())

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/files")
async def get_files():
    if not DB_PATH.exists():
        return {"files": []}
    
    with open(DB_PATH, "r") as f:
        try:
            db = json.load(f)
            # Filter out files where symlink is mysteriously gone
            valid_files = []
            for file_info in db.get("files", []):
                if Path(file_info["path"]).exists():
                    valid_files.append(file_info)
            return {"files": valid_files}
        except json.JSONDecodeError:
            return {"files": []}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(DB_PATH, "r") as f:
        db = json.load(f)
        
    for file_info in db.get("files", []):
        if file_info.get("id") == file_id:
            file_path = Path(file_info["path"])
            if file_path.exists():
                return FileResponse(
                    path=file_path,
                    filename=file_info.get("name", "download"),
                    media_type="application/octet-stream"
                )
            else:
                raise HTTPException(status_code=404, detail="Underlying file not found")
                
    raise HTTPException(status_code=404, detail="File metadata not found")

if __name__ == "__main__":
    import uvicorn
    # Typically run via `crabber-cli`, but can be tested directly
    uvicorn.run(app, host="0.0.0.0", port=8888)
