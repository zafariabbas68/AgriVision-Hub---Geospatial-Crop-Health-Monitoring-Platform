from datetime import datetime
from typing import Optional

class TaskModel:
    def __init__(self, task_id: str, filename: str, status: str, 
                 created_at: datetime, file_path: str, field_name: Optional[str] = None):
        self.task_id = task_id
        self.filename = filename
        self.status = status  # pending, processing, completed, failed
        self.progress = 0
        self.created_at = created_at
        self.completed_at = None
        self.file_path = file_path
        self.field_name = field_name
        self.result_url = None
        self.error = None
        self.ndvi_data = None
