"""
感情ベースの応答のためのOpenAIエージェントパイプライン。
これは元の実装のリファクタリングバージョンです。
"""
from dotenv import load_dotenv
import asyncio

from src.main import interact


load_dotenv()

if __name__ == "__main__":
    asyncio.run(interact())
