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
    time.sleep(2)
    
    # Generate realistic NDVI based on filename
    filename = str(file_path).lower()
    if "healthy" in filename:
        ndvi = round(random.uniform(0.55, 0.75), 3)
        health = "Excellent"
    elif "stressed" in filename:
        ndvi = round(random.uniform(0.25, 0.45), 3)
        health = "Moderate"
    else:
        ndvi = round(random.uniform(0.35, 0.65), 3)
        health = "Good" if ndvi > 0.45 else "Moderate"
    
    tasks[task_id]["status"] = "completed"
    tasks[task_id]["progress"] = 100
    tasks[task_id]["ndvi_value"] = ndvi
    tasks[task_id]["health_status"] = health
    tasks[task_id]["completed_at"] = datetime.now().isoformat()

@app.get("/")
async def root():
    return {"message": "AgriVision Hub API", "status": "running", "version": "2.0.0"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "tasks": len(tasks)}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...), field_name: Optional[str] = None):
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
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat()
    }
    
    thread = threading.Thread(target=process_task, args=(task_id, str(file_path)))
    thread.start()
    
    return {"task_id": task_id, "status": "pending", "message": "Upload successful"}

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

@app.get("/api/v1/report/{task_id}")
async def generate_report(task_id: str):
    """Generate PDF report for a task"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    
    task = tasks[task_id]
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Crop Health Report</title></head>
    <body>
        <h1>🌾 AgriVision Hub - Crop Health Report</h1>
        <h2>Field: {task.get('field_name', 'Unknown')}</h2>
        <p>NDVI Value: {task.get('ndvi_value', 'N/A')}</p>
        <p>Health Status: {task.get('health_status', 'Unknown')}</p>
        <p>Analyzed: {task.get('created_at', 'N/A')}</p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

# ============= NEW FEATURES =============

from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import json

@app.get("/api/v1/report/{task_id}")
async def generate_report(task_id: str):
    """Generate HTML report for a task"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    
    task = tasks[task_id]
    
    # Determine health color
    ndvi = task.get('ndvi_value', 0)
    if ndvi > 0.6:
        health_color = "#27ae60"
        health_text = "Excellent 🌟"
    elif ndvi > 0.4:
        health_color = "#3498db"
        health_text = "Good ✅"
    elif ndvi > 0.2:
        health_color = "#f39c12"
        health_text = "Moderate ⚠️"
    else:
        health_color = "#e74c3c"
        health_text = "Poor 🚨"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgriVision Hub - Crop Health Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 2px solid #eee;
            }}
            .header h1 {{
                color: #667eea;
                margin: 0;
            }}
            .ndvi-value {{
                font-size: 48px;
                font-weight: bold;
                color: {health_color};
                text-align: center;
                margin: 20px 0;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 20px 0;
            }}
            .info-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
            }}
            .info-card label {{
                font-weight: bold;
                color: #666;
                display: block;
                margin-bottom: 5px;
            }}
            .footer {{
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #eee;
                font-size: 12px;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌾 AgriVision Hub</h1>
                <p>Crop Health Report</p>
            </div>
            
            <div class="ndvi-value">
                NDVI: {task.get('ndvi_value', 'N/A')}
            </div>
            
            <div class="info-grid">
                <div class="info-card">
                    <label>Field Name</label>
                    <strong>{task.get('field_name', 'Unknown')}</strong>
                </div>
                <div class="info-card">
                    <label>Health Status</label>
                    <strong style="color: {health_color};">{health_text}</strong>
                </div>
                <div class="info-card">
                    <label>Filename</label>
                    <strong>{task.get('filename', 'Unknown')}</strong>
                </div>
                <div class="info-card">
                    <label>Analysis Date</label>
                    <strong>{task.get('created_at', 'Unknown')[:19]}</strong>
                </div>
            </div>
            
            <div class="info-card">
                <label>Recommendation</label>
                <p>{task.get('recommendation', 'Monitor crop health regularly.')}</p>
            </div>
            
            <div class="footer">
                Generated by AgriVision Hub • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/api/v1/weather/{lat}/{lon}")
async def get_weather(lat: float, lon: float):
    """Get current weather data for location"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True,
                    "hourly": "temperature_2m,relative_humidity_2m",
                    "timezone": "auto"
                }
            )
            weather_data = response.json()
            
            return {
                "success": True,
                "location": {"lat": lat, "lon": lon},
                "current": weather_data.get("current_weather", {}),
                "forecast": weather_data.get("hourly", {}).get("temperature_2m", [])[:24],
                "message": "Weather data retrieved successfully"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/v1/export/{task_id}")
async def export_task_data(task_id: str):
    """Export task data as JSON for download"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    
    task = tasks[task_id]
    
    # Create export data
    export_data = {
        "export_date": datetime.now().isoformat(),
        "task": task,
        "analysis": {
            "ndvi_value": task.get('ndvi_value', 'N/A'),
            "health_status": task.get('health_status', 'Unknown'),
            "classification": "Excellent" if task.get('ndvi_value', 0) > 0.6 else "Good" if task.get('ndvi_value', 0) > 0.4 else "Moderate" if task.get('ndvi_value', 0) > 0.2 else "Poor",
            "recommendation": task.get('recommendation', 'Monitor regularly')
        }
    }
    
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f"attachment; filename=agrivision_report_{task_id}.json"}
    )


@app.get("/api/v1/stats/advanced")
async def get_advanced_stats():
    """Get advanced statistics about all analyses"""
    completed_tasks = [t for t in tasks.values() if t.get("status") == "completed" and t.get("ndvi_value")]
    
    if not completed_tasks:
        return {"message": "No completed analyses yet"}
    
    ndvi_values = [t.get("ndvi_value", 0) for t in completed_tasks]
    
    # Count by health category
    excellent = sum(1 for v in ndvi_values if v > 0.6)
    good = sum(1 for v in ndvi_values if 0.4 < v <= 0.6)
    moderate = sum(1 for v in ndvi_values if 0.2 < v <= 0.4)
    poor = sum(1 for v in ndvi_values if v <= 0.2)
    
    return {
        "total_analyses": len(completed_tasks),
        "average_ndvi": round(sum(ndvi_values) / len(ndvi_values), 3),
        "max_ndvi": max(ndvi_values),
        "min_ndvi": min(ndvi_values),
        "health_distribution": {
            "excellent": excellent,
            "good": good,
            "moderate": moderate,
            "poor": poor
        },
        "most_recent": completed_tasks[-1] if completed_tasks else None
    }
