"""
APIサーバー

このモジュールは、FastAPIアプリケーションをUvicornサーバーで実行するためのエントリーポイントを提供します。
"""
import os
import logging
import uvicorn
from dotenv import load_dotenv

from .app import app


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """APIサーバーのメイン関数"""
    load_dotenv()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    logger.info(f"APIサーバーを起動します: {host}:{port}")
    
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    main()
