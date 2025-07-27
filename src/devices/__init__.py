"""
Device modules for the OpenAI agent pipeline.

このモジュールは、感情分析パイプラインと触覚フィードバックデバイスとの統合を提供します。
主要なコンポーネント:
- Arduino/ESP32ベースのデバイス用のHTTPコントローラー
- WebSocketベースのリアルタイム通信コントローラー
- 振動パターンの定義と生成
- パイプライン統合機能
"""

# 基底クラス
from .base_controller import (
    BaseController,
    BaseControllerConfig,
    BaseControllerManager,
)

# Arduino HTTP コントローラー
from .arduino_controller import (
    ArduinoController,
    ArduinoControllerConfig,
    ArduinoControllerManager,
)

# WebSocket コントローラー
from .websocket_controller import (
    WebSocketController,
    WebSocketControllerConfig,
    WebSocketControllerManager,
    DeviceStatus,
)

# 振動パターン
from .vibration_patterns import (
    VibrationStep,
    VibrationPattern,
    EmotionVibrationPatterns,
    VibrationPatternGenerator,
)

# パイプライン統合
from .pipeline_integration import (
    HapticFeedbackIntegration,
)

# デバイスインターフェース（モック）
from .device_interface import (
    HapticDeviceInterface,
)

__all__ = [
    # 基底クラス
    "BaseController",
    "BaseControllerConfig",
    "BaseControllerManager",
    # Arduino コントローラー
    "ArduinoController",
    "ArduinoControllerConfig",
    "ArduinoControllerManager",
    # WebSocket コントローラー
    "WebSocketController",
    "WebSocketControllerConfig",
    "WebSocketControllerManager",
    "DeviceStatus",
    # 振動パターン
    "VibrationStep",
    "VibrationPattern",
    "EmotionVibrationPatterns",
    "VibrationPatternGenerator",
    # パイプライン統合
    "HapticFeedbackIntegration",
    # デバイスインターフェース
    "HapticDeviceInterface",
]
