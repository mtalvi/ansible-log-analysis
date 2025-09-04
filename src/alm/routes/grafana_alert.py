from typing import List
from datetime import datetime
from langchain_openai import ChatOpenAI
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.alm.database import get_session_gen
from src.alm.models import GrafanaAlert
from src.alm.agents.graph import get_graph
from src.alm.llm import get_llm

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
    alerts = await session.exec(select(GrafanaAlert))
    return alerts.all()


@router.get(
    "/by-expert-class/",
    summary="Get grafana alerts by expert class",
    response_model=List[GrafanaAlert],
)
async def get_grafana_alerts_by_expert_class(
    expert_class: str = Query(..., description="The expert class to filter alerts by"),
    session: AsyncSession = Depends(get_session_gen),
) -> List[GrafanaAlert]:
    query = select(GrafanaAlert).where(
        GrafanaAlert.expertClassification == expert_class
    )
    alerts = await session.exec(query)
    return alerts


@router.get(
    "/unique-clusters/",
    summary="Get unique log clusters for an expert class with representative alerts",
    response_model=List[GrafanaAlert],
)
async def get_unique_clusters_by_expert_class(
    expert_class: str = Query(..., description="The expert class to filter alerts by"),
    session: AsyncSession = Depends(get_session_gen),
) -> List[GrafanaAlert]:
    """Get one representative alert for each unique log cluster within an expert class."""
    from sqlalchemy import func

    # Get one alert per unique cluster within the expert class
    subquery = (
        select(GrafanaAlert.logCluster, func.min(GrafanaAlert.id).label("min_id"))
        .where(GrafanaAlert.expertClassification == expert_class)
        .where(GrafanaAlert.logCluster.is_not(None))
        .group_by(GrafanaAlert.logCluster)
    ).alias("clusters")

    query = (
        select(GrafanaAlert)
        .join(subquery, GrafanaAlert.id == subquery.c.min_id)
        .order_by(GrafanaAlert.logCluster)
    )

    alerts = await session.exec(query)
    return alerts


@router.get(
    "/by-expert-class-and-log-cluster/",
    summary="Get grafana alerts by expert class and log cluster",
    response_model=List[GrafanaAlert],
)
async def get_grafana_alerts_by_expert_class_and_log_cluster(
    expert_class: str = Query(..., description="The expert class to filter alerts by"),
    log_cluster: str = Query(..., description="The log cluster to filter alerts by"),
    session: AsyncSession = Depends(get_session_gen),
) -> List[GrafanaAlert]:
    query = select(GrafanaAlert).where(
        GrafanaAlert.logCluster == log_cluster,
        GrafanaAlert.expertClassification == expert_class,
    )
    alerts = await session.exec(query)
    return alerts


@router.post("/", status_code=status.HTTP_202_ACCEPTED, summary="Post log alert")
async def post_log_alert(
    log_alert: str, session: AsyncSession = Depends(get_session_gen)
) -> GrafanaAlert:
    graph_result = await get_graph().ainvoke({"logMessage": log_alert})

    # Convert string timestamp to datetime object if provided
    # Parse ISO format timestamp (e.g., '2025-09-04T09:07:06.596Z')
    # If no timestamp is provided, the model will default to current time
    # if 'logTimestamp' in graph_result and graph_result['logTimestamp']:
    #     timestamp_str = graph_result['logTimestamp']
    #     if timestamp_str.endswith('Z'):
    #         # Remove 'Z' and parse as UTC
    #         timestamp_str = timestamp_str[:-1]
    #     graph_result['logTimestamp'] = datetime.fromisoformat(timestamp_str)
    # else:
    #     # Remove the key so the model can use its default (current time)
    #     graph_result.pop('logTimestamp', None)

    grafana_alert = GrafanaAlert(**graph_result)

    session.add(grafana_alert)
    await session.commit()
    await session.refresh(grafana_alert)
    return grafana_alert
