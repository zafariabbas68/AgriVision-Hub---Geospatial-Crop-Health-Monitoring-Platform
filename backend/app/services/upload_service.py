import os
import shutil
from pathlib import Path

class UploadService:
    UPLOAD_DIR = Path("/tmp/agrivision_uploads")
    
    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, file, task_id: str) -> str:
        """Save uploaded file to temporary storage"""
        file_extension = Path(file.filename).suffix
        file_path = self.UPLOAD_DIR / f"{task_id}{file_extension}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return str(file_path)
