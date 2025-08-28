import asyncio
import time

from src.alm.database import get_session
from src.alm.grafana_alert_mocker import ingest_alerts
from src.alm.llm import get_llm

from src.alm.agents.analizer.node import (
    cluster_logs,
    summarize_log,
    categorize_log,
    suggest_step_by_step_solution,
)
from src.alm.models import GrafanaAlert
from sqlmodel import select

from src.alm.database import init_tables


async def whole_pipeline():
    await _pipeline(
        load_alerts_from_db=False,
        generate_log_summaries=True,
        generate_log_categories=True,
        generate_step_by_step_solutions=True,
        restart_db=True,
    )


async def only_generate_log_summaries():
    await _pipeline(
        load_alerts_from_db=True,
        generate_log_summaries=True,
        generate_log_categories=False,
        generate_step_by_step_solutions=False,
        restart_db=False,
    )


async def only_generate_log_categories():
    await _pipeline(
        load_alerts_from_db=True,
        generate_log_summaries=False,
        generate_log_categories=True,
        generate_step_by_step_solutions=False,
        restart_db=False,
    )


async def only_generate_step_by_step_solutions():
    await _pipeline(
        load_alerts_from_db=True,
        generate_log_summaries=False,
        generate_log_categories=False,
        generate_step_by_step_solutions=True,
        restart_db=False,
    )


async def _pipeline(
    load_alerts_from_db=False,
    generate_log_summaries=True,
    generate_log_categories=True,
    generate_step_by_step_solutions=True,
    restart_db=False,
):
    llm = get_llm()

    if restart_db:
        await init_tables(delete_tables=True)

    # Load the alerts
    if not load_alerts_from_db:
        alerts = [
            alert for alert in ingest_alerts("data/logs/failed") if alert is not None
        ]
        print(f"alerts ingested {len(alerts)}")
    else:
        async with get_session() as db:
            alerts = await db.exec(select(GrafanaAlert))
            alerts = alerts.all()
            print(f"alerts loaded from db {len(alerts)}")
    alerts = alerts[:5]

    # Cluster logs
    cluster_labels = cluster_logs(
        [alert.logMessage for alert in alerts], algorithm="meanshift"
    )

    # Create log summaries
    if generate_log_summaries:
        print("generating log summaries")
        start_time = time.time()
        log_summaries = await asyncio.gather(
            *[summarize_log(alert.logMessage, llm) for alert in alerts]
        )
        elapsed_time = time.time() - start_time
        print(
            f"log_summaries finished {len(log_summaries)} - Time: {elapsed_time:.2f}s"
        )
    else:
        log_summaries = [alert.logSummary for alert in alerts]

    # Create log Category
    if generate_log_categories:
        print("generating log categories")
        start_time = time.time()
        log_categories = await asyncio.gather(
            *[categorize_log(log_summary, llm) for log_summary in log_summaries]
        )
        elapsed_time = time.time() - start_time
        print(
            f"log categories finished {len(log_categories)} - Time: {elapsed_time:.2f}s"
        )
    else:
        log_categories = [alert.expertClassification for alert in alerts]

    # # Create step by step solution
    if generate_step_by_step_solutions:
        print("generating step by step solutions")
        start_time = time.time()
        step_by_step_solutions = await asyncio.gather(
            *[
                suggest_step_by_step_solution(log_summary, alert.logMessage, llm)
                for log_summary, alert in zip(log_summaries, alerts)
            ]
        )
        elapsed_time = time.time() - start_time
        print(
            f"step by step solutions finished {len(step_by_step_solutions)} - Time: {elapsed_time:.2f}s"
        )
    else:
        step_by_step_solutions = [alert.stepByStepSolution for alert in alerts]

    async def add_or_update_alert(
        alert, log_summary, log_category, step_by_step_solution, cluster_label
    ):
        async with get_session() as db:
            alert.logSummary = log_summary
            alert.expertClassification = log_category
            alert.stepByStepSolution = step_by_step_solution
            alert.logCluster = cluster_label
            db.add(alert)
            await db.commit()
            await db.refresh(alert)

    start_time = time.time()
    await asyncio.gather(
        *[
            add_or_update_alert(
                alert, log_summary, log_category, step_by_step_solution, cluster_label
            )
            for alert, log_summary, log_category, step_by_step_solution, cluster_label in zip(
                alerts,
                log_summaries,
                log_categories,
                step_by_step_solutions,
                cluster_labels,
            )
        ]
    )
    elapsed_time = time.time() - start_time
    print(f"database alerts added - Time: {elapsed_time:.2f}s")
