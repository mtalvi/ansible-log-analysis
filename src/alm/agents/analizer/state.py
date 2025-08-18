from typing import Literal

from langgraph.graph import MessagesState


class AnalizerState(MessagesState):
    """
    State for the analizer agent.
    """

    log_input: str
    classification_decision: Literal["need_to_solve", "can_be_ignored"]
