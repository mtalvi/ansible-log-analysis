"""Used to mock the Grafana alerting system."""

import os
import re
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field
from src.alm.patterns.aap import AAP_LOG_ERROR, AAP_LOG_FATAL

# import pathlib


class GrafanaAlert(BaseModel):
    """Grafana alert payload for Loki log alerts."""

    # # Optional ID field
    # id: Optional[int] = Field(default=None)

    # Grouping information
    logTimestamp: datetime
    logMessage: str = Field(description="Original log message that triggered the alert")
    logSummary: Optional[str] = Field(
        default=None, description="Summary of the log message"
    )
    logClassification: Optional[str] = Field(
        default=None, description="Classification of the log message"
    )
    labels: Dict[str, str] = Field(
        default={}, description="Labels used for grouping alerts"
    )

    # # Loki-specific fields that might be extracted from log content
    # logLevel: Optional[str] = None  # Log level from Loki logs (info, warn, error, etc.)
    # # logStream: Optional[str] = None  # Loki log stream identifier
    # logSource: Optional[str] = None  # Source of the log (e.g., service name, pod name)

    # log_type: Optional[str] = None
    # task_name: Optional[str] = None


def _filter_matches_end_with_ignoring(matches: list[re.Match]) -> list[re.Match]:
    """Filter matches that end with 'ignoring'."""
    return [
        m
        for m in matches
        if not m.groupdict().get("logmessage", "").endswith("ignoring")
    ]


def grafana_alert_mock(path: str) -> Optional[GrafanaAlert]:
    """Mock the Grafana alerting system."""
    with open(path, "r") as file:
        content = file.read()
    matches = _filter_matches_end_with_ignoring(
        list(re.finditer(AAP_LOG_ERROR, content, re.MULTILINE))
    )

    if not matches:
        matches = _filter_matches_end_with_ignoring(
            re.finditer(AAP_LOG_FATAL, content, re.MULTILINE)
        )
        if not matches:
            return None

    # Get the last match
    last_match = matches[-1]
    groups = last_match.groupdict()

    # Create GrafanaAlert instance with extracted data
    alert = GrafanaAlert(
        logTimestamp=(
            datetime.strptime(groups.get("timestamp"), "%A %d %B %Y  %H:%M:%S %z")
            if groups.get("timestamp")
            else None
        ),
        logMessage=groups.get("logmessage", ""),  # Full matched text as the log message
        # logSummary=groups.get('logsummary', ''),
        # logClassification=groups.get('logclassification', ''),
        labels={
            # 'log_source': groups.get('host', '').strip(),
            "task_name": groups.get("task_name", "").strip(),
            "host": groups.get("host", "").strip(),
        },
        # logLevel=groups.get('status', ''),  # Use status as log level (fatal/error)
        # logSource=pathlib.Path(path).name
    )

    return alert


def ingest_alerts(directory: str) -> list[GrafanaAlert]:
    """Ingest alerts from a directory."""
    alerts = []
    error_count = 0
    success_count = 0
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            try:
                alerts.append(grafana_alert_mock(os.path.join(directory, file)))
                success_count += 1
            except Exception:
                error_count += 1
    print(f"{error_count} errors and {success_count} successes")
    return alerts, error_count
