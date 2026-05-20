from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import threading
import time
import os
import random

app = FastAPI(title="AgriVision Hub API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("/tmp/agrivision_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

tasks = {}

def process_task(task_id: str, file_path: str):
    """Simulate NDVI processing with realistic values"""
    time.sleep(3)
    
    # Generate realistic NDVI based on filename or random
    # In production, you'd actually analyze the image here
    ndvi_value = round(random.uniform(0.2, 0.8), 3)
    
    if "healthy" in str(file_path).lower():
        ndvi_value = 0.72
    elif "stressed" in str(file_path).lower():
        ndvi_value = 0.35
    
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["progress"] = 100
    tasks[task_id]["ndvi_value"] = ndvi_value
    tasks[task_id]["health_status"] = "Excellent" if ndvi_value > 0.6 else "Good" if ndvi_value > 0.4 else "Moderate" if ndvi_value > 0.2 else "Poor"
    tasks[task_id]["completed_at"] = datetime.now().isoformat()

@app.get("/")
async def root():
    return {
        "message": "AgriVision Hub API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": ["/api/v1/health", "/api/v1/upload", "/api/v1/tasks", "/api/v1/task/{task_id}"]
    }

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "tasks": len(tasks), "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/upload")
async def upload(file: UploadFile = File(...), field_name: Optional[str] = None):
    task_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{task_id}{file_ext}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "field_name": field_name or "Unknown Field",
        "status": "processing",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "ndvi_value": None,
        "health_status": None
    }
    
    thread = threading.Thread(target=process_task, args=(task_id, str(file_path)))
    thread.start()
    
    return {"task_id": task_id, "status": "processing", "message": "Upload successful", "progress": 0}

@app.get("/api/v1/tasks")
async def list_tasks():
    return list(tasks.values())

@app.get("/api/v1/task/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
