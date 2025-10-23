from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.graph import MessagesState


async def loki_node(state: MessagesState):
    return Command(goto=END, update={"messages": state["messages"]})  # TODO change me


def build_graph():
    builder = StateGraph(MessagesState)
    builder.add_edge(START, "loki_node")
    builder.add_node("loki_node", loki_node)
    return builder.compile()


loki_agent = build_graph()
