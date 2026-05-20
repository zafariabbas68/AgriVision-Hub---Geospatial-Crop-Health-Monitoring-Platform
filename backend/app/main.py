from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import numpy as np
from PIL import Image

# Import satellite service
from app.services.satellite_service import satellite_service

app = FastAPI(title="AgriVision Hub", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store tasks
tasks = {}

def calculate_ndvi_from_rgb(image_path):
    """Calculate NDVI proxy from RGB image"""
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        if len(img_array.shape) == 3:
            r = img_array[:,:,0].astype(np.float32) / 255.0
            g = img_array[:,:,1].astype(np.float32) / 255.0
            
            grvi = (g - r) / (g + r + 1e-10)
            grvi = np.clip(grvi, -0.5, 0.8)
            
            healthy_mask = grvi > 0.3
            moderate_mask = (grvi >= 0.1) & (grvi <= 0.3)
            poor_mask = grvi < 0.1
            
            healthy_pct = np.sum(healthy_mask) / grvi.size * 100
            moderate_pct = np.sum(moderate_mask) / grvi.size * 100
            poor_pct = np.sum(poor_mask) / grvi.size * 100
            
            if healthy_pct > 60:
                interpretation = "Excellent"
                recommendation = "Maintain current practices"
            elif healthy_pct > 40:
                interpretation = "Good"
                recommendation = "Monitor regularly"
            elif healthy_pct > 20:
                interpretation = "Moderate"
                recommendation = "Consider irrigation"
            else:
                interpretation = "Poor"
                recommendation = "Immediate intervention needed"
            
            return {
                'mean_ndvi': float(np.mean(grvi)),
                'min_ndvi': float(np.min(grvi)),
                'max_ndvi': float(np.max(grvi)),
                'healthy_percentage': float(healthy_pct),
                'moderate_percentage': float(moderate_pct),
                'poor_percentage': float(poor_pct),
                'interpretation': interpretation,
                'recommendation': recommendation
            }
        return {'error': 'Invalid image format'}
    except Exception as e:
        return {'error': str(e)}

def process_ndvi(task_id, file_path):
    """Process NDVI calculation"""
    try:
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 30
        
        result = calculate_ndvi_from_rgb(file_path)
        
        tasks[task_id]["progress"] = 80
        
        if 'error' not in result:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 100
            tasks[task_id]["ndvi_stats"] = result
            tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
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
                        "ndvi_value": round(result.get('mean_ndvi', 0.5), 3),
                        "healthy_percentage": round(result.get('healthy_percentage', 0), 1),
                        "interpretation": result.get('interpretation', 'Unknown')
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

@app.get("/")
async def root():
    return {"message": "AgriVision Hub API", "version": "2.0"}

@app.get("/api/v1/health")
async def health():
    completed = len([t for t in tasks.values() if t.get("status") == "completed"])
    return {"status": "healthy", "total_tasks": len(tasks), "completed": completed}

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
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "ndvi_stats": None,
        "geojson": None
    }
    
    thread = threading.Thread(target=process_ndvi, args=(task_id, str(file_path)))
    thread.start()
    
    return {"task_id": task_id, "status": "pending", "message": "NDVI analysis started"}

@app.get("/api/v1/task/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]

@app.get("/api/v1/tasks")
async def list_tasks():
    return list(tasks.values())

# ============= SATELLITE ENDPOINTS =============

@app.post("/api/v2/satellite/point")
async def satellite_point_analysis(lat: float, lon: float):
    """Analyze a point using satellite data"""
    result = satellite_service.get_ndvi_for_point(lat, lon)
    return {"success": True, "data": result}

@app.post("/api/v2/satellite/field")
async def satellite_field_analysis(coordinates: List[List[float]], field_name: str):
    """Analyze a field using satellite data"""
    if len(coordinates) < 3:
        return {"success": False, "error": "Need at least 3 coordinates"}
    
    result = satellite_service.get_ndvi_for_field(coordinates)
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "field_name": field_name,
        "filename": "satellite_analysis",
        "source": "Satellite",
        "status": "completed",
        "ndvi_stats": result,
        "created_at": datetime.now().isoformat(),
        "type": "satellite"
    }
    
    return {"success": True, "task_id": task_id, "results": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# Also support GET for easier testing
@app.get("/api/v2/satellite/point")
async def satellite_point_analysis_get(lat: float, lon: float):
    """Analyze a point using satellite data (GET method)"""
    result = satellite_service.get_ndvi_for_point(lat, lon)
    return {"success": True, "data": result}
