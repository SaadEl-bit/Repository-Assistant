import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

GROQ_MODEL = "llama-3.3-70b-versatile"
DEEPSEEK_MODEL = "deepseek-chat"


def get_llm():
    if NVIDIA_API_KEY and MODEL_NAME:
        print(f"Using NVIDIA LLM (primary): {MODEL_NAME}")
        return ChatOpenAI(
            model=MODEL_NAME,
            api_key=NVIDIA_API_KEY,
            base_url=NVIDIA_BASE_URL,
            temperature=0,
        )

    if GROQ_API_KEY:
        print("Using Groq LLM (fallback)")
        return ChatOpenAI(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
            temperature=0,
        )

    if DEEPSEEK_API_KEY:
        print("Using DeepSeek LLM (fallback)")
        return ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=0,
        )

    raise ValueError("No LLM configured. Set NVIDIA_API_KEY + MODEL_NAME, GROQ_API_KEY, or DEEPSEEK_API_KEY in .env")
