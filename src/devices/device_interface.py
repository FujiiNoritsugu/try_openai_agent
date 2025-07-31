"""
触覚フィードバックデバイスのインターフェース。

このモジュールは、触覚フィードバックデバイスと通信し、
感情分析結果に基づいて振動パターンを送信するためのインターフェースを提供します。

注意: このファイルはモックの実装であり、実際のデバイス通信は含まれていません。
実際のデバイス実装については、arduino_controller.pyおよびwebsocket_controller.pyを参照してください。
"""

from typing import Dict, Any, Optional, List
import json
import asyncio
import logging

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator


class HapticDeviceInterface:
    """
    触覚フィードバックデバイスと通信するためのインターフェース。

    このクラスは、感情分析結果に基づいて接続された触覚デバイスに
    振動パターンを送信するためのメソッドを提供します。
    """

    def __init__(
        self, device_id: str = "default", host: str = "localhost", port: int = 8765
    ):
        """
        触覚デバイスインターフェースを初期化します。

        引数:
            device_id: デバイスの識別子
            host: デバイス通信のホストアドレス
            port: デバイス通信のポート
        """
        self.device_id = device_id
        self.host = host
        self.port = port
        self.connected = False
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> bool:
        """
        触覚デバイスとの接続を確立します。

        実際の実装では、物理デバイスとの接続を確立します。
        現時点ではプレースホルダーです。

        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        self.logger.info(
            f"Connecting to haptic device {self.device_id} at {self.host}:{self.port}"
        )

        await asyncio.sleep(0.5)

        self.connected = True
        self.logger.info(f"Connected to haptic device {self.device_id}")
        return True

    async def disconnect(self) -> bool:
        """
        触覚デバイスとの接続を切断します。

        戻り値:
            切断が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            return True

        self.logger.info(f"Disconnecting from haptic device {self.device_id}")

        await asyncio.sleep(0.2)

        self.connected = False
        self.logger.info(f"Disconnected from haptic device {self.device_id}")
        return True

    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        振動パターンをデバイスに送信します。

        引数:
            pattern: 送信する振動パターン

        戻り値:
            パターンが正常に送信された場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            self.logger.warning("Cannot send pattern: device not connected")
            return False

        pattern_json = pattern.to_json()

        self.logger.info(f"Sending pattern to device {self.device_id}: {pattern_json}")

        await asyncio.sleep(0.3)

        self.logger.info(f"Pattern sent successfully to device {self.device_id}")
        return True

    async def send_emotion(
        self, emotion: Emotion, emotion_category: Optional[str] = None
    ) -> bool:
        """
        感情データに基づいて振動パターンを生成し送信します。

        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            emotion_category: オプションの感情カテゴリ指定

        戻り値:
            パターンが生成され正常に送信された場合はTrue、それ以外の場合はFalse
        """
        pattern = VibrationPatternGenerator.generate_pattern(emotion, emotion_category)

        return await self.send_pattern(pattern)

    async def process_pipeline_context(self, ctx: PipelineContext) -> bool:
        """
        パイプラインコンテキストを処理し、適切な振動パターンを送信します。

        このメソッドは、パイプラインコンテキストから感情データとカテゴリを抽出し、
        適切な振動パターンをデバイスに送信します。

        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト

        戻り値:
            パターンが正常に送信された場合はTrue、それ以外の場合はFalse
        """
        if not ctx.emotion:
            self.logger.warning("Cannot process context: no emotion data")
            return False

        return await self.send_emotion(ctx.emotion, ctx.emotion_category)


class HapticFeedbackManager:
    """
    触覚フィードバックデバイスのマネージャー。

    このクラスは、触覚デバイスを管理し、感情ベースのフィードバックを
    送信するための高レベルインターフェースを提供します。
    """

    def __init__(self):
        """触覚フィードバックマネージャーを初期化します。"""
        self.devices = {}
        self.logger = logging.getLogger(__name__)

    def register_device(
        self, device_id: str, host: str = "localhost", port: int = 8765
    ) -> HapticDeviceInterface:
        """
        新しい触覚デバイスを登録します。

        引数:
            device_id: デバイスの識別子
            host: デバイスのホストアドレス
            port: デバイスのポート

        戻り値:
            登録されたデバイスインターフェース
        """
        device = HapticDeviceInterface(device_id, host, port)
        self.devices[device_id] = device
        self.logger.info(f"Registered haptic device: {device_id}")
        return device

    def get_device(self, device_id: str) -> Optional[HapticDeviceInterface]:
        """
        IDで登録済みのデバイスを取得します。

        引数:
            device_id: デバイスの識別子

        戻り値:
            見つかった場合はデバイスインターフェース、それ以外の場合はNone
        """
        return self.devices.get(device_id)

    async def connect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのデバイスに接続します。

        戻り値:
            デバイスIDと接続成功状態をマッピングした辞書
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.connect()
        return results

    async def disconnect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのデバイスから切断します。

        戻り値:
            デバイスIDと切断成功状態をマッピングした辞書
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.disconnect()
        return results

    async def send_to_all(
        self, emotion: Emotion, emotion_category: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        感情データをすべての接続されたデバイスに送信します。

        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            emotion_category: オプションの感情カテゴリ指定

        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.send_emotion(emotion, emotion_category)
        return results

    async def process_pipeline_context(self, ctx: PipelineContext) -> Dict[str, bool]:
        """
        パイプラインコンテキストを処理し、すべての接続されたデバイスに送信します。

        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト

        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.process_pipeline_context(ctx)
        return results


haptic_manager = HapticFeedbackManager()
