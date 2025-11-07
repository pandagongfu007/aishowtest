# E:\2025fanmai\code\aishowtest\gui-backend\app\routes\overview.py

from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.models import AteboxStatus

router = APIRouter()


@router.get("/", response_model=List[AteboxStatus])
async def get_overview() -> List[AteboxStatus]:
    """
    Return a fake overview of 5 Atebox boxes for now.
    TODO: replace with real data from vendor middleware.
    """
    now = datetime.utcnow()

    items: List[AteboxStatus] = []
    for i in range(1, 6):
        items.append(
            AteboxStatus(
                id=i,
                name=f"Atebox-{i}",
                online=True,
                last_result="PASS",
                last_updated=now,
            )
        )

    return items
