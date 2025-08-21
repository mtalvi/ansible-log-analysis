import asyncio
import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

from langchain_openai import ChatOpenAI
from src.alm.database import get_session, init_tables
from src.alm.grafana_alert_mocker import ingest_alerts
from src.alm.llm import get_llm

from src.alm.agents.analizer.node import summarize_log, categorize_log


async def init_df():
    llm = get_llm()

    # Load the alerts
    alerts = [alert for alert in ingest_alerts("data/logs/failed") if alert is not None]
    print(f'alerts finished {len(alerts)}')
    # Create log summaries
    log_summaries = await asyncio.gather(
        *[summarize_log(alert, llm) for alert in alerts]
    )
    print(f'log_summaries finished {len(log_summaries)}')
    # Create log Category
    log_categories = await asyncio.gather(
        *[
            categorize_log(log_summary, llm)
            for log_summary in log_summaries
        ]
    )
    print(f'log categories finished {len(log_categories)}')
    async def add_alert(alert, log_summary, log_category):
        async with get_session() as db:
            alert.logSummary = log_summary
            alert.logClassification = log_category
            db.add(alert)
            await db.commit()
            await db.refresh(alert)

    await asyncio.gather(
        *[
            add_alert(alert, log_summary, log_category)
            for alert, log_summary, log_category in zip(
                alerts, log_summaries, log_categories
            )
        ]
    )

async def main():
    print(os.getenv("DATABASE_URL"))
    await init_tables()
    print('tables initialized')
    await init_df()

if __name__ == "__main__":
    asyncio.run(main())