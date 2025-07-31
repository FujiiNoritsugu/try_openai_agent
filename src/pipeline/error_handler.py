"""
エラーハンドリングユーティリティ。
"""

import traceback
from typing import Optional, TypeVar, Callable, Any
from functools import wraps

from ..utils import get_logger

# ロガーの設定
logger = get_logger(__name__)

T = TypeVar("T")


class PipelineError(Exception):
    """パイプライン実行エラー"""

    pass


def handle_pipeline_error(func: Callable[..., T]) -> Callable[..., T]:
    """
    パイプラインエラーをハンドリングするデコレータ。

    Args:
        func: ラップする関数

    Returns:
        ラップされた関数
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Pipeline error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise PipelineError(f"Pipeline execution failed: {str(e)}") from e

    return wrapper


def log_error(error: Exception, context: str) -> None:
    """
    エラーをログに記録する。

    Args:
        error: エラーオブジェクト
        context: エラーが発生したコンテキスト
    """
    logger.error(f"Error in {context}: {str(error)}")
    logger.error(traceback.format_exc())
