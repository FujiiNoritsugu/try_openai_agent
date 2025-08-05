"""
非同期処理のユーティリティ関数。
"""

import asyncio
from typing import Any, Coroutine


def run_async(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """同期的なコンテキストから非同期関数を実行する。"""
    # Streamlitは内部でasyncioを使用しているため、
    # asyncio.run()を使用して新しいイベントループを作成
    return asyncio.run(coroutine)
