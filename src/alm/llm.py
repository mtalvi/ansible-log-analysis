import os

from langchain_openai import ChatOpenAI

# Constants for API configuration
API_KEY: str = os.getenv("OPENAI_API_TOKEN", "")
BASE_URL: str = os.getenv("OPENAI_API_ENDPOINT", "")

# Constants for model configuration
MODEL: str = os.getenv("OPENAI_MODEL", "llama-4-scout-17b-16e-w4a16")
TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

if not API_KEY or not BASE_URL:
    raise ValueError(
        "OpenAI API configuration not found. Please set both OPENAI_API_TOKEN and OPENAI_API_ENDPOINT environment variables."
    )


def get_llm(model: str = MODEL, temperature: float = TEMPERATURE):
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=model,
        temperature=temperature,
    )
    return llm
