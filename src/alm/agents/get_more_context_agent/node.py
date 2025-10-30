from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal


class LokiRouterSchema(BaseModel):
    reasoning: str = Field(description="the reasoning for the decision")
    classification: Literal[
        "need_more_context_from_loki_db", "no_need_more_context_from_loki_db"
    ] = Field(
        description="determines if we need to fetch more context from loki db, 'need_more_context_from_loki_db' if we need to fetch more context, 'no_need_more_context_from_loki_db' if we don't need to fetch more context"
    )


with open("src/alm/agents/get_more_context_agent/prompts/loki_router.md", "r") as f:
    loki_router_user_message = f.read()


async def get_cheat_sheet_context(log_summary: str):
    # retrive context that is relevent to solve the problem
    # context = TODO
    # return context
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
