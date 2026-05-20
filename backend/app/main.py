from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import threading
import time

app = FastAPI(title="AgriVision Hub API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("/tmp/agrivision_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Store tasks in memory
tasks = {}

def process_ndvi_task(task_id: str, file_path: str):
    """Simulate NDVI processing in background"""
    time.sleep(2)
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["progress"] = 100
    tasks[task_id]["ndvi_value"] = 0.65
    tasks[task_id]["health"] = "Healthy"

@app.get("/")
async def root():
    return {"message": "AgriVision Hub API", "status": "running", "version": "1.0.0"}

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy", 
        "tasks": len(tasks), 
        "server": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...), 
    field_name: Optional[str] = None
):
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Save file
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create task
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "field_name": field_name or "Unknown Field",
        "status": "processing",
        "progress": 50,
        "created_at": datetime.now().isoformat(),
        "file_path": str(file_path)
    }
    
    # Start background processing
    thread = threading.Thread(target=process_ndvi_task, args=(task_id, str(file_path)))
    thread.start()
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "File uploaded successfully. Processing started.",
        "progress": 50
    }

@app.get("/api/v1/task/{task_id}")
async def get_task(task_id: str):
    """Get task status and results"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/api/v1/tasks")
async def list_tasks():
    """List all tasks"""
    return list(tasks.values())

@app.delete("/api/v1/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id in tasks:
        del tasks[task_id]
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")
