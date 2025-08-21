from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Load the user message (prompt) from the markdown file
with open("src/alm/agents/analizer/prompts/create_log_summary.md", "r") as f:
    log_summary_user_message = f.read()

with open("src/alm/agents/analizer/prompts/categorize_log.md", "r") as f:
    log_category_user_message = f.read()

with open("src/alm/agents/analizer/prompts/suggest_step_by_step_solution.md", "r") as f:
    log_suggest_step_by_step_solution_user_message = f.read()


# create stractued output for summary log and categorize log
class SummarySchema(BaseModel):
    summary: str = Field(description="Summary of the log")


class CategorizeSchema(BaseModel):
    category: Literal[
        "GPU Autoscaling Issues",
        "Cert-Manager Webhook Issues",
        "KubeVirt VM Provisioning Issues",
        "Vault Secret Storage Issues",
        "Other",
    ] = Field(description="Category of the log")


class SuggestStepByStepSolutionSchema(BaseModel):
    step_by_step_solution: str = Field(
        description="Step by step solution to the problem"
    )


async def summarize_log(alert, llm: ChatOpenAI):
    llm_summary = llm.with_structured_output(SummarySchema)
    log = alert.logMessage
    log_summary = await llm_summary.ainvoke(
        [
            {"role": "system", "content": "You Ansible expert and helpful assistant"},
            {
                "role": "user",
                "content": log_summary_user_message.replace("{error_log}", log),
            },
        ]
    )
    return log_summary.summary


async def categorize_log(log_summary, llm: ChatOpenAI):
    llm_categorize = llm.with_structured_output(CategorizeSchema)
    log_category = await llm_categorize.ainvoke(
        [
            {"role": "system", "content": "You Ansible expert and helpful assistant"},
            {
                "role": "user",
                "content": log_category_user_message.replace(
                    "{log_summary}", log_summary
                ),
            },
        ]
    )
    return log_category.category


async def suggest_step_by_step_solution(log_summary: str, log: str, llm: ChatOpenAI):
    llm_suggest_step_by_step_solution = llm.with_structured_output(
        SuggestStepByStepSolutionSchema
    )
    log_suggest_step_by_step_solution = await llm_suggest_step_by_step_solution.ainvoke(
        [
            {"role": "system", "content": "You Ansible expert and helpful assistant"},
            {
                "role": "user",
                "content": log_suggest_step_by_step_solution_user_message.replace(
                    "{log_summary}", log_summary
                ).replace("{error_log}", log),
            },
        ]
    )
    return log_suggest_step_by_step_solution.step_by_step_solution
