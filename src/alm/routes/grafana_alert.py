from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.alm.database import get_session_gen
from src.alm.models import GrafanaAlert

router = APIRouter(prefix="/grafana-alert", tags=["grafana-alert"])


@router.get(
    "/{alert_id}", summary="Get grafana alert by id", response_model=GrafanaAlert
)
async def get_grafana_alert(
    alert_id: int, session: AsyncSession = Depends(get_session_gen)
) -> GrafanaAlert:
    alert = await session.get(GrafanaAlert, alert_id)
    return alert


@router.get("/", summary="Get all grafana alerts", response_model=List[GrafanaAlert])
async def get_grafana_alerts(
    session: AsyncSession = Depends(get_session_gen),
) -> List[GrafanaAlert]:
    alerts = await session.exec(select(GrafanaAlert)).all()
    return alerts


@router.get(
    "/by-category/",
    summary="Get grafana alerts by category",
    response_model=List[GrafanaAlert],
)
async def get_grafana_alerts_by_category(
    category: str = Query(..., description="The category to filter alerts by"),
    session: AsyncSession = Depends(get_session_gen),
) -> List[GrafanaAlert]:
    query = select(GrafanaAlert).where(GrafanaAlert.logClassification == category)
    alerts = await session.exec(query)
    return alerts


# @router.post("", status_code=status.HTTP_202_ACCEPTED, summary="Submit grafana alert")
# async def submit_grafana_alert(grafana_alert: GrafanaAlert, session: AsyncSession = Depends(get_session_gen)) -> dict[str, str]:
#     session.add(grafana_alert)
#     await session.commit()
#     await session.refresh(grafana_alert)
#     return grafana_alert
