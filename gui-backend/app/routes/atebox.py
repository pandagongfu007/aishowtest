# app/routes/atebox.py
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Path

from app.models import TestResult

router = APIRouter()


@router.get("/{atebox_id}/results", response_model=List[TestResult])
async def get_atebox_results(
    atebox_id: int = Path(..., ge=1, le=5),
) -> List[TestResult]:
    """
    Fake recent test results for one Atebox.
    TODO: replace with real data from vendor middleware.
    """
    now = datetime.utcnow()

    return [
        TestResult(
            case_name=f"CASE_{atebox_id}_001",
            start_time=now - timedelta(seconds=30),
            end_time=now - timedelta(seconds=10),
            result="PASS",
            message="示例用例通过",
        ),
        TestResult(
            case_name=f"CASE_{atebox_id}_002",
            start_time=now - timedelta(minutes=2),
            end_time=now - timedelta(minutes=1, seconds=30),
            result="FAIL",
            message="示例用例失败",
        ),
    ]
