"""
OpenAI agent pipeline for emotion-based responses.
This is a refactored version of the original implementation.
"""
from dotenv import load_dotenv
import asyncio

from src.main import interact


load_dotenv()

if __name__ == "__main__":
    asyncio.run(interact())
