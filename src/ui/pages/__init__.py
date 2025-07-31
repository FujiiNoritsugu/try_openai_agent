"""
UIページモジュール。
"""

from .emotion_analysis import display_analysis_page
from .learning_data import display_learning_page
from .device_settings import display_device_settings_page

__all__ = [
    "display_analysis_page",
    "display_learning_page",
    "display_device_settings_page",
]
