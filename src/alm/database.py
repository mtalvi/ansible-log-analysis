from __future__ import annotations

import os
from typing import Generator

from sqlmodel import Session, create_engine

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/logsdb"
)

# Create SQLModel engine
engine = create_engine(DATABASE_URL)


# Dependency to get database session
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
