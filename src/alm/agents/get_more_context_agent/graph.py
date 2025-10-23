from src.alm.llm import get_llm

from src.alm.agents.get_more_context_agent.node import (
    get_cheat_sheet_context,
    loki_router,
)
from src.alm.agents.get_more_context_agent.state import ContextAgentState
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

llm = get_llm()


async def cheat_sheet_context_node(state: ContextAgentState):
    cheat_sheet_context = await get_cheat_sheet_context(state.log_summary)
    return Command(
        goto="loki_router_node", update={"cheat_sheet_context": cheat_sheet_context}
    )


async def loki_router_node(state: ContextAgentState):
    reasoning, classification = await loki_router(
        state.log_summary, state.cheat_sheet_context, llm
    )
    return Command(
        goto="loki_sub_agent"
        if classification == "need_more_context_from_loki_db"
        else END,
        update={"reasoning": reasoning, "classification": classification},
    )


async def loki_sub_agent(state: ContextAgentState):
    # context = await loki_agent.ainvoke({}) # TODO choose the input for the agent NOTE you have reasoning why we need loki, can be used or removed.
    context = None  # TODO change me
    return Command(goto=END, update={"loki_context": context})


def build_graph():
    builder = StateGraph(ContextAgentState)
    builder.add_edge(START, "cheat_sheet_context_node")
    builder.add_node("cheat_sheet_context_node", cheat_sheet_context_node)
    builder.add_node("loki_router_node", loki_router_node)
    builder.add_node("loki_sub_agent", loki_sub_agent)
    return builder.compile()


more_context_agent_graph = build_graph()
