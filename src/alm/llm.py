"""
LLM configuration module for the Ansible Log Monitor.
This module provides a factory for creating LLM (Language Learning Model) instances using OpenAI's API.
"""

import os

from langchain_openai import ChatOpenAI

# Constants for API configuration
API_KEY: str = os.getenv("OPENAI_API_TOKEN", "")
BASE_URL: str = os.getenv("OPENAI_API_ENDPOINT", "")

if not API_KEY or not BASE_URL:
    raise ValueError(
        "OpenAI API configuration not found. Please set both OPENAI_API_TOKEN and OPENAI_API_ENDPOINT environment variables."
    )


def get_llm(model: str = "llama-4-scout-17b-16e-w4a16", temperature: float = 0.7):
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_TOKEN"),
        base_url=os.getenv("OPENAI_API_ENDPOINT"),
        model=model,
        temperature=temperature,
    )
    return llm
