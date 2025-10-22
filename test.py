from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = FastAPI()

@app.get("/env")
def read_env():
    return {
        "model": os.getenv("EMBEDDINGS_LLM_MODEL_NAME"),
        "url": os.getenv("EMBEDDINGS_LLM_URL"),
        "api_key": os.getenv("EMBEDDINGS_LLM_API_KEY"),
    }
