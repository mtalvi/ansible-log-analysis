from pydantic import BaseModel, Field
from typing import Optional
from typing import Literal


class ContextAgentState(BaseModel):
    log_summary: str = Field(description="The summary of Ansible error log")
    log: str = Field(description="The Ansible error log")
    cheat_sheet_context: Optional[str] = Field(
        description="The context from the cheat sheet that will help understand the log error.",
        default=None,
    )
    reasoning: Optional[str] = Field(
        description="The reasoning from the loki db that will help understand the log error.",
        default=None,
    )
    classification: Optional[
        Literal["need_more_context_from_loki_db", "no_need_more_context_from_loki_db"]
    ] = Field(
        description="determines if we need to fetch more context from loki db, 'need_more_context_from_loki_db' if we need to fetch more context, 'no_need_more_context_from_loki_db' if we don't need to fetch more context",
        default=None,
    )
    loki_context: Optional[str] = Field(
        description="The context from the loki db that will help understand the log error.",
        default=None,
    )
