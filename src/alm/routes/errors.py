from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/errors", tags=["errors"])


class ErrorLog(BaseModel):
    """Incoming error log payload."""

    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "ERROR"
    labels: Dict[str, str] = {}
    context: Optional[Dict[str, str]] = None


@router.post("", status_code=status.HTTP_202_ACCEPTED, summary="Submit error log")
async def submit_error_log(log: ErrorLog) -> dict[str, str]:
    # Mock acceptance for now
    return {"status": "accepted"}


@router.get("/by-category/{category}", summary="Get error logs by category")
async def get_error_logs_by_category(
    category: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """Fetch error logs from Loki filtered by a `category` label.

    If no time range is provided, defaults to the last hour.
    """
    loki_url = os.environ.get("LOKI_URL", "http://localhost:3100")

    # Default time range: last hour
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(hours=1)

    # Loki expects nanosecond timestamps
    start_ns = int(start.timestamp() * 1_000_000_000)
    end_ns = int(end.timestamp() * 1_000_000_000)

    query = f'{{level="ERROR",category="{category}"}}'
    params = {
        "query": query,
        "start": str(start_ns),
        "end": str(end_ns),
        "limit": str(limit),
        "direction": "backward",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{loki_url}/loki/api/v1/query_range", params=params
        )
        response.raise_for_status()
        payload = response.json()

    entries: list[Dict[str, Any]] = []
    for stream in payload.get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for ts, line in stream.get("values", []):
            entries.append(
                {
                    "timestamp": ts,
                    "message": line,
                    "labels": labels,
                }
            )

    return {"count": len(entries), "entries": entries}
