import os
import logging
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal

# Configure logging
logger = logging.getLogger(__name__)


class LokiRouterSchema(BaseModel):
    reasoning: str = Field(description="the reasoning for the decision")
    classification: Literal[
        "need_more_context_from_loki_db", "no_need_more_context_from_loki_db"
    ] = Field(
        description="determines if we need to fetch more context from loki db, 'need_more_context_from_loki_db' if we need to fetch more context, 'no_need_more_context_from_loki_db' if we don't need to fetch more context"
    )


with open("src/alm/agents/get_more_context_agent/prompts/loki_router.md", "r") as f:
    loki_router_user_message = f.read()


# Lazy-loading singleton for RAG pipeline
_rag_pipeline = None
_rag_enabled = None


def _initialize_rag_pipeline():
    """
    Initialize RAG pipeline with lazy loading (singleton pattern).
    This ensures the FAISS index is loaded only once and reused across requests.

    Returns:
        AnsibleErrorQueryPipeline instance or None if RAG is disabled/failed
    """
    global _rag_pipeline, _rag_enabled

    # Check if already initialized
    if _rag_enabled is not None:
        return _rag_pipeline

    # Check if RAG is enabled via environment variable
    rag_enabled_env = os.getenv("RAG_ENABLED", "true").lower()
    if rag_enabled_env not in ["true", "1", "yes"]:
        logger.info("RAG is disabled (RAG_ENABLED=%s)", rag_enabled_env)
        _rag_enabled = False
        _rag_pipeline = None
        return None

    try:
        logger.info("Initializing RAG pipeline (lazy loading)...")

        from alm.rag.query_pipeline import AnsibleErrorQueryPipeline

        # Get configuration from environment variables
        top_k = int(os.getenv("RAG_TOP_K", "10"))
        top_n = int(os.getenv("RAG_TOP_N", "3"))
        similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.6"))

        # Initialize pipeline (this loads the FAISS index)
        _rag_pipeline = AnsibleErrorQueryPipeline(
            top_k=top_k,
            top_n=top_n,
            similarity_threshold=similarity_threshold,
        )

        _rag_enabled = True
        logger.info(
            "✓ RAG pipeline initialized successfully with %d errors in index",
            len(_rag_pipeline.embedder.error_store),
        )

        return _rag_pipeline

    except FileNotFoundError as e:
        logger.warning("RAG index not found: %s", e)
        logger.warning(
            "RAG functionality disabled - proceeding without cheat sheet context"
        )
        _rag_enabled = False
        _rag_pipeline = None
        return None

    except Exception as e:
        logger.error("Failed to initialize RAG pipeline: %s", e, exc_info=True)
        logger.warning(
            "RAG functionality disabled - proceeding without cheat sheet context"
        )
        _rag_enabled = False
        _rag_pipeline = None
        return None


def _format_rag_results(response) -> str:
    """
    Format RAG query results into a structured string for LLM context.

    Args:
        response: QueryResponse from RAG pipeline

    Returns:
        Formatted string with error solutions
    """
    if not response.results:
        return "No matching solutions found in knowledge base."

    output = ["## Relevant Error Solutions from Knowledge Base\n"]

    for i, result in enumerate(response.results, 1):
        output.append(f"### Error {i}: {result.error_title}")
        output.append(f"**Confidence Score:** {result.similarity_score:.2f}\n")

        if result.sections.description:
            output.append("**Description:**")
            output.append(result.sections.description)
            output.append("")

        if result.sections.symptoms:
            output.append("**Symptoms:**")
            output.append(result.sections.symptoms)
            output.append("")

        if result.sections.resolution:
            output.append("**Resolution:**")
            output.append(result.sections.resolution)
            output.append("")

        if result.sections.code:
            output.append("**Code Example:**")
            output.append(f"```\n{result.sections.code}\n```")
            output.append("")

        output.append("---\n")

    return "\n".join(output)


async def get_cheat_sheet_context(log_summary: str) -> str:
    """
    Retrieve relevant context from the RAG knowledge base for solving the error.

    This function:
    1. Lazily initializes the RAG pipeline (loads FAISS index on first call)
    2. Queries the knowledge base with the log summary
    3. Formats the results for LLM consumption
    4. Returns empty string if RAG is disabled or fails

    Args:
        log_summary: Summary of the Ansible error log

    Returns:
        Formatted string with relevant error solutions, or empty string if unavailable
    """
    logger.info("Retrieving cheat sheet context for log summary")

    # Initialize RAG pipeline (lazy loading)
    pipeline = _initialize_rag_pipeline()

    if pipeline is None:
        logger.debug("RAG pipeline not available, returning empty context")
        return ""

    try:
        # Query the RAG system
        logger.debug("Querying RAG system with log summary: %s...", log_summary[:100])
        response = pipeline.query(log_summary)

        # Format results
        formatted_context = _format_rag_results(response)

        logger.info(
            "✓ Retrieved %d relevant errors from knowledge base (search time: %.2fms)",
            response.metadata["num_results"],
            response.metadata["search_time_ms"],
        )

        return formatted_context

    except Exception as e:
        logger.error("Error querying RAG system: %s", e, exc_info=True)
        logger.warning("Proceeding without cheat sheet context")
        return ""


async def loki_router(
    log_summary: str, cheat_sheet_context: str, llm: ChatOpenAI
) -> LokiRouterSchema:
    llm_structured = llm.with_structured_output(LokiRouterSchema)
    output = await llm_structured.ainvoke(
        [
            {
                "role": "system",
                "content": "You are an Ansible expert and helpful assistant",
            },
            {
                "role": "user",
                "content": loki_router_user_message.format(
                    log_summary=log_summary, cheat_sheet_context=cheat_sheet_context
                ),
            },
        ]
    )
    return LokiRouterSchema.model_validate(output)
