from src.alm.llm import get_llm
from src.alm.models import GrafanaAlert
from src.alm.agents.node import (
    summarize_log,
    classify_log,
    suggest_step_by_step_solution,
    router_step_by_step_solution,
    infer_cluster_log,
)
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from typing import Literal

llm = get_llm()


# Nodes
async def cluster_logs_node(
    state: GrafanaAlert,
) -> Command[Literal["summarize_log_node"]]:
    logs = state.logMessage
    log_cluster = infer_cluster_log(logs)
    return Command(goto="summarize_log_node", update={"logCluster": log_cluster})


async def summarize_log_node(
    state: GrafanaAlert,
) -> Command[Literal["classify_log_node"]]:
    log_summary = await summarize_log(state.logMessage, llm)
    return Command(goto="classify_log_node", update={"logSummary": log_summary})


async def classify_log_node(
    state: GrafanaAlert,
) -> Command[Literal["router_step_by_step_solution_node"]]:
    log_summary = state.logSummary
    log_category = await classify_log(log_summary, llm)
    return Command(
        goto="router_step_by_step_solution_node",
        update={"expertClassification": log_category},
    )


async def suggest_step_by_step_solution_node(
    state: GrafanaAlert,
) -> Command[Literal[END]]:
    log_summary = state.logSummary
    log = state.logMessage
    step_by_step_solution = await suggest_step_by_step_solution(log_summary, log, llm)
    return Command(goto=END, update={"stepByStepSolution": step_by_step_solution})


async def router_step_by_step_solution_node(
    state: GrafanaAlert,
) -> Command[
    Literal["suggest_step_by_step_solution_node", "step_by_step_solution_agent_node"]
]:
    log_summary = state.logSummary
    log = state.logMessage
    step_by_step_solution = await router_step_by_step_solution(log_summary, log, llm)
    return Command(
        goto="suggest_step_by_step_solution_node"
        if step_by_step_solution == "straightforward"
        else "step_by_step_solution_agent_node",
        update={"shouldBeStraightforward": step_by_step_solution == "straightforward"},
    )


async def step_by_step_solution_agent_node(
    state: GrafanaAlert,
) -> Command[Literal[END]]:
    log_summary = state.logSummary
    log = state.logMessage
    step_by_step_solution = await suggest_step_by_step_solution(
        log_summary, log, llm
    )  # TODO replace it with agent
    return Command(goto=END, update={"stepByStepSolution": step_by_step_solution})


def build_graph():
    """call ainvoke to the graph to invoke it asynchronously"""
    builder = StateGraph(GrafanaAlert)
    builder.add_edge(START, "cluster_logs_node")
    builder.add_node("cluster_logs_node", cluster_logs_node)
    builder.add_node(summarize_log_node)
    builder.add_node(classify_log_node)
    builder.add_node(suggest_step_by_step_solution_node)
    builder.add_node(router_step_by_step_solution_node)
    builder.add_node(step_by_step_solution_agent_node)

    return builder.compile()


_compiled_graph = build_graph()


def get_graph():
    return _compiled_graph
