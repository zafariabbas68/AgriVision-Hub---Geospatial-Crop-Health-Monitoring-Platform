from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import threading
import time

app = FastAPI(title="AgriVision Hub", version="1.0.0")

# Configure CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agrivision-frontend.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Allow all for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/agrivision_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

tasks = {}

def process_task(task_id: str, file_path: str):
    """Simulate NDVI processing"""
    time.sleep(2)
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["progress"] = 100
    tasks[task_id]["result"] = {"ndvi": 0.65, "health": "good"}

@app.get("/")
async def root():
    return {"message": "AgriVision Hub API", "status": "running"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "tasks": len(tasks), "server": "running"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...), field_name: Optional[str] = None):
    task_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "field_name": field_name or "Unknown Field",
        "status": "processing",
        "progress": 50,
        "created_at": datetime.now().isoformat()
    }
    
    thread = threading.Thread(target=process_task, args=(task_id, str(file_path)))
    thread.start()
    
    return {"task_id": task_id, "status": "processing", "message": "Upload successful"}

@app.get("/api/v1/task/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]

@app.get("/api/v1/tasks")
async def list_tasks():
    return list(tasks.values())
