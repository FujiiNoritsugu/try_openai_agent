"""
アプリケーション設定モジュール。
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EmotionSettings:
    """感情パラメータの設定"""

    min_value: int = 0
    max_value: int = 5
    default_intensity: float = 0.5


@dataclass
class UISettings:
    """UI関連の設定"""

    body_parts: Dict[str, str] = field(
        default_factory=lambda: {
            "頭": "頭部（頭頂部、後頭部など）",
            "顔": "顔（額、頬、顎など）",
            "首": "首（前面、後面、側面）",
            "肩": "肩（左右の肩、肩甲骨など）",
            "腕": "腕（上腕、前腕など）",
            "手": "手（手のひら、指、手首など）",
            "胸": "胸部（胸骨、乳房など）",
            "腹": "腹部（上腹部、下腹部など）",
            "腰": "腰部（腰椎周辺）",
            "臀部": "臀部（お尻）",
            "脚": "脚（太もも、ふくらはぎなど）",
            "足": "足（足首、足の裏、指など）",
        }
    )
    default_body_part: str = "胸"
    genders: list = field(default_factory=lambda: ["男性", "女性", "その他"])
    default_gender: str = "男性"


@dataclass
class DeviceSettings:
    """デバイス関連の設定"""

    default_host: str = "192.168.1.100"
    default_port: int = 80
    default_ws_path: str = "/ws"
    connection_timeout: int = 10
    reconnect_interval: int = 5


@dataclass
class LearningSettings:
    """学習関連の設定"""

    feedback_file: str = "data/feedback/feedback_history.json"
    learning_patterns_file: str = "data/learning/emotion_patterns.json"
    min_samples_for_pattern: int = 3
    confidence_threshold: float = 0.7


@dataclass
class LoggingSettings:
    """ロギング関連の設定"""

    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class AppSettings:
    """アプリケーション全体の設定"""

    app_title: str = "感情エージェントパイプライン"
    emotion: EmotionSettings = field(default_factory=EmotionSettings)
    ui: UISettings = field(default_factory=UISettings)
    device: DeviceSettings = field(default_factory=DeviceSettings)
    learning: LearningSettings = field(default_factory=LearningSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    @classmethod
    def from_env(cls) -> "AppSettings":
        """環境変数から設定を読み込む"""
        settings = cls()

        # 環境変数からの上書き
        if log_level := os.getenv("LOG_LEVEL"):
            settings.logging.log_level = log_level

        if log_file := os.getenv("LOG_FILE"):
            settings.logging.log_file = log_file

        if default_host := os.getenv("DEVICE_DEFAULT_HOST"):
            settings.device.default_host = default_host

        if default_port := os.getenv("DEVICE_DEFAULT_PORT"):
            settings.device.default_port = int(default_port)

        return settings


# グローバル設定インスタンス
settings = AppSettings.from_env()


def get_settings() -> AppSettings:
    """現在の設定を取得する"""
    return settings


def update_settings(**kwargs) -> None:
    """設定を更新する"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
