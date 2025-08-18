from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Log(SQLModel, table=True):
    __tablename__ = "logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    level: Optional[str] = Field(default=None, max_length=50)
    message: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None, max_length=255)
