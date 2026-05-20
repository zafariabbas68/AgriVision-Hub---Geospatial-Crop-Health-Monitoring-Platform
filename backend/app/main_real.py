from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import threading
import time
from app.real_ndvi import calculate_real_ndvi, calculate_ndvi_from_rgb

app = FastAPI(title="AgriVision Hub - Real NDVI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

tasks = {}

def process_real_ndvi(task_id: str, file_path: str):
    """Process REAL NDVI calculation"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 30
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        file_ext = Path(file_path).suffix.lower()
        
        # Choose calculation method based on file type
        if file_ext in ['.tif', '.tiff']:
            result = calculate_real_ndvi(file_path)
            tasks[task_id]["calculation_method"] = "True NDVI (Multispectral)"
        else:
            result = calculate_ndvi_from_rgb(file_path)
            tasks[task_id]["calculation_method"] = "GRVI (RGB Proxy)"
        
        tasks[task_id]["progress"] = 80
        
        if 'error' not in result:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 100
            tasks[task_id]["ndvi_stats"] = result
            tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
            # Create GeoJSON for visualization
            tasks[task_id]["geojson"] = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [13.4050, 52.5200], [13.4150, 52.5200],
                            [13.4150, 52.5300], [13.4050, 52.5300],
                            [13.4050, 52.5200]
                        ]]
                    },
                    "properties": {
                        "ndvi_value": result.get('mean_ndvi', 0.5),
                        "healthy_percentage": result.get('healthy_percentage', 50),
                        "area_hectares": 2.5
                    }
                }]
            }
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = result.get('error')
        
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.post("/api/v2/upload")
async def upload_real(file: UploadFile = File(...), field_name: Optional[str] = None):
    task_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    tasks[task_id] = {
        "task_id": task_id,
        "filename": file.filename,
        "field_name": field_name or "Unknown Field",
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "file_path": str(file_path),
        "ndvi_stats": None,
        "geojson": None
    }
    
    thread = threading.Thread(target=process_real_ndvi, args=(task_id, str(file_path)))
    thread.start()
    
    return {"task_id": task_id, "status": "pending", "message": "Real NDVI processing started"}

@app.get("/api/v2/task/{task_id}")
async def get_real_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "tasks": len(tasks), "version": "2.0 - Real NDVI"}

@app.get("/api/v1/tasks")
async def list_tasks():
    return list(tasks.values())
