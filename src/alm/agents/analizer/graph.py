from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, Command
from pydantic import BaseModel, Field
from src.alm.agents.analizer import prompts
from src.alm.agents.analizer.state import AnalizerState
from src.alm.utils import checks


class RouterOutputSchema(BaseModel):
    """Analyze the log and decide if it the error is can be solve by modifing the Ansible playbook or can be ignored."""

    reasoning: str = Field(
        description="Step by step reasoning for the classification decision."
    )
    classification: Literal["need_to_solve", "can_be_ignored"] = Field(
        description="The classification of the log:\n'need_to_solve' if the error is can be solved by modifying the Ansible playbook\n'can_be_ignored' if the error is can not be solved by modifying the Ansible playbook."
    )


# Nodes
def error_analysis(
    state: AnalizerState, llm: ChatOpenAI
) -> Command[Literal["solver_agent", "__end__"]]:
    """Analyze the log and decide if it the error is can be solve by modifing the Ansible playbook or can be ignored."""

    # Run string checks
    if checks.check_if_ansible_log_should_be_ignored(state.log_input):
        goto = END
        update = {"classification": "can_be_ignored"}
    else:
        system_prompt = prompts.SYSTEM_PROMPT
        user_prompt = prompts.USER_PROMPT.format(log=state.log_input)

        llm_router = llm.with_structured_output(RouterOutputSchema)
        llm_router_response = llm_router.invoke(system_prompt, user_prompt)

        classification = llm_router_response.classification
        reasoning = llm_router_response.reasoning

        goto = "solver_agent" if classification == "need_to_solve" else END
        update = {"classification": classification, "reasoning": reasoning}

    return Command(goto=goto, update=update)


# def summarize_error(state: AnalizerState, llm: ChatOpenAI):
#     """Summarize the error."""

#     system_prompt = prompts.SYSTEM_PROMPT
#     user_prompt = prompts.USER_PROMPT.format(log=state.log_input)

#     llm_summarizer = llm.with_structured_output(SummarizerOutputSchema)
#     llm_summarizer_response = llm_summarizer.invoke(
#         system_prompt,
#         user_prompt
#     )
