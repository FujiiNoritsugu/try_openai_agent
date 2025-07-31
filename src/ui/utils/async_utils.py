"""
非同期処理のユーティリティ関数。
"""

import asyncio
from typing import Any, Coroutine


def run_async(coroutine: Coroutine[Any, Any, Any]) -> Any:
    """同期的なコンテキストから非同期関数を実行する。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)
