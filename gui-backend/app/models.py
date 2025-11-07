# E:\2025fanmai\code\aishowtest\gui-backend\app\models.py

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class AteboxStatus(BaseModel):
    """Status summary for one Atebox box."""
    id: int
    name: str
    online: bool = False
    last_result: Optional[str] = None
    last_updated: Optional[datetime] = None


class TestResult(BaseModel):
    """Single test case result."""
    case_name: str
    start_time: datetime
    end_time: datetime
    result: str
    message: Optional[str] = None


class VideoStream(BaseModel):
    """Video stream metadata for GUI playback."""
    id: str
    label: str
    url: str
    source: Optional[str] = None
