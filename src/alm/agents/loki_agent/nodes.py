"""
LangGraph node functions for Loki MCP integration.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI

from alm.agents.loki_agent.schemas import IdentifyMissingDataSchema, LogStream


async def identify_missing_data(
    log_summary: str, log_stream: LogStream | Dict[str, Any], llm: ChatOpenAI
):
    """
    Identify what critical data is missing to fully understand and resolve the issue.

    Args:
        log_summary: Summary of the log to analyze
        log_stream: Log stream of the log (can be LogStream object or dict)
        llm: ChatOpenAI instance to use for generation

    Returns:
        str: Natural language description of missing data needed for investigation
    """
    with open("src/alm/agents/loki_agent/prompts/identify_missing_data.md", "r") as f:
        generate_loki_query_request_user_message = f.read()

    # Convert log_stream to LogStream object if it's a dict
    if isinstance(log_stream, dict):
        log_stream_obj = LogStream.model_validate(log_stream)
    else:
        log_stream_obj = log_stream

    llm_identify_missing_data = llm.with_structured_output(IdentifyMissingDataSchema)
    missing_data_result = await llm_identify_missing_data.ainvoke(
        [
            {
                "role": "system",
                "content": "You are an Ansible expert and helpful assistant specializing in log analysis",
            },
            {
                "role": "user",
                "content": generate_loki_query_request_user_message.replace(
                    "{log_summary}", log_summary
                ).replace(
                    "{log_stream}",
                    log_stream_obj.model_dump_json(indent=2, exclude_none=True),
                ),
            },
        ]
    )
    return missing_data_result.missing_data_request
