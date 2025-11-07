# app/routes/video.py
from typing import List

import os

import yaml
from fastapi import APIRouter

from app.config import settings
from app.models import VideoStream

router = APIRouter()


@router.get("/streams", response_model=List[VideoStream])
async def list_streams() -> List[VideoStream]:
    """
    Read video stream metadata from YAML file and return to GUI.
    If file does not exist or is invalid, return an empty list.
    """
    path = settings.video_streams_file

    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []

    streams_cfg = data.get("streams", []) or []
    result: List[VideoStream] = []

    for item in streams_cfg:
        try:
            result.append(
                VideoStream(
                    id=str(item.get("id", "")),
                    label=str(item.get("label", "")),
                    url=str(item.get("url", "")),
                    source=item.get("source"),
                )
            )
        except Exception:
            # skip bad entries
            continue

    return result
