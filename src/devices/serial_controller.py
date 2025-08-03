"""
シリアル通信コントローラー

Arduino Uno R4とシリアル通信で接続し、振動パターンを送信するためのコントローラー。
WebSocketの代わりにUSBシリアル接続を使用します。
"""

import asyncio
import json
import logging
import serial
import serial.tools.list_ports
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..models.data_models import Emotion, PipelineContext, DeviceStatus


@dataclass
class VibrationStep:
    """振動ステップのデータクラス"""
    intensity: int  # 0-100%
    duration: int  # milliseconds


@dataclass
class VibrationPattern:
    """振動パターンのデータクラス"""
    steps: List[VibrationStep]
    interval: int = 0  # milliseconds between steps
    repeat_count: int = 1


class SerialController:
    """
    Arduinoデバイスとのシリアル通信を管理するコントローラー
    """

    def __init__(self, device_id: str, port: str = None, baudrate: int = 115200):
        """
        SerialControllerを初期化します。

        引数:
            device_id: デバイスの識別子
            port: シリアルポート（例: "COM3", "/dev/ttyUSB0"）
            baudrate: ボーレート（デフォルト: 115200）
        """
        self.device_id = device_id
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.logger = logging.getLogger(f"{__name__}.{device_id}")

    @staticmethod
    def find_arduino_ports() -> List[str]:
        """
        利用可能なArduinoポートを検出します。

        戻り値:
            Arduinoデバイスのポートのリスト
        """
        arduino_ports = []
        ports = serial.tools.list_ports.comports()
        
        logger = logging.getLogger(__name__)
        logger.info(f"検出されたシリアルポート数: {len(ports)}")
        
        for port in ports:
            logger.info(f"ポート: {port.device}, 説明: {port.description}, ハードウェアID: {port.hwid}")
            # Arduino Uno R4の一般的な識別子をチェック
            if "Arduino" in port.description or "USB" in port.description or "CH340" in port.description:
                arduino_ports.append(port.device)
        
        return arduino_ports

    async def connect(self) -> bool:
        """
        Arduinoデバイスに接続します。

        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        if self.is_connected:
            self.logger.warning(f"デバイス '{self.device_id}' は既に接続されています")
            return True

        try:
            # ポートが指定されていない場合は自動検出
            if not self.port:
                available_ports = self.find_arduino_ports()
                if available_ports:
                    self.port = available_ports[0]
                    self.logger.info(f"自動検出されたポート: {self.port}")
                else:
                    self.logger.error("Arduinoポートが見つかりません")
                    # 利用可能なすべてのポートを表示
                    all_ports = serial.tools.list_ports.comports()
                    if all_ports:
                        self.logger.info("利用可能なポート:")
                        for p in all_ports:
                            self.logger.info(f"  - {p.device}: {p.description}")
                    else:
                        self.logger.info("利用可能なポートがありません")
                    return False

            self.logger.info(f"ポート {self.port} への接続を試みています...")
            self.logger.info(f"ボーレート: {self.baudrate}")
            
            # シリアル接続を開く
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2.0,  # タイムアウトを延長
                write_timeout=2.0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # DTR/RTSをリセット（Arduino Uno R4のリセット回避）
            self.serial_connection.dtr = False
            self.serial_connection.rts = False
            await asyncio.sleep(0.1)
            self.serial_connection.dtr = True
            self.serial_connection.rts = True
            
            # 接続が安定するまで待機
            self.logger.info("接続の安定化を待っています...")
            await asyncio.sleep(3.0)  # 待機時間を延長
            
            # 接続確認
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # 接続テスト（簡単なメッセージを送信）
            test_pattern = '{"steps":[{"intensity":0,"duration":100}],"interval":0,"repeat_count":1}\n'
            self.serial_connection.write(test_pattern.encode())
            self.serial_connection.flush()
            
            self.is_connected = True
            self.logger.info(f"デバイス '{self.device_id}' がポート {self.port} に正常に接続されました")
            
            return True

        except serial.SerialException as e:
            self.logger.error(f"シリアル接続エラー (ポート: {self.port}): {str(e)}")
            self.logger.error(f"エラーの詳細: {type(e).__name__}")
            if "PermissionError" in str(e) or "Access is denied" in str(e):
                self.logger.error("アクセス拒否: ポートが他のプログラムで使用されている可能性があります")
            elif "could not open port" in str(e):
                self.logger.error("ポートを開けません: ポートが存在しないか、ドライバーの問題の可能性があります")
            return False
        except Exception as e:
            self.logger.error(f"接続中に予期しないエラーが発生しました: {str(e)}")
            self.logger.error(f"エラーの種類: {type(e).__name__}")
            import traceback
            self.logger.error(f"スタックトレース:\n{traceback.format_exc()}")
            return False

    async def disconnect(self) -> bool:
        """
        Arduinoデバイスから切断します。

        戻り値:
            切断が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.is_connected:
            self.logger.warning(f"デバイス '{self.device_id}' は接続されていません")
            return True

        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.is_connected = False
            self.logger.info(f"デバイス '{self.device_id}' から切断されました")
            return True

        except Exception as e:
            self.logger.error(f"切断中にエラーが発生しました: {str(e)}")
            return False

    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        振動パターンをデバイスに送信します。

        引数:
            pattern: 送信する振動パターン

        戻り値:
            送信が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.is_connected or not self.serial_connection:
            self.logger.error(f"デバイス '{self.device_id}' は接続されていません")
            return False

        try:
            # パターンをJSON形式に変換
            pattern_dict = {
                "steps": [
                    {"intensity": step.intensity, "duration": step.duration}
                    for step in pattern.steps
                ],
                "interval": pattern.interval,
                "repeat_count": pattern.repeat_count
            }
            
            json_data = json.dumps(pattern_dict)
            
            # データを送信（改行を追加してArduino側で区切りを認識できるように）
            self.serial_connection.write((json_data + "\n").encode())
            self.serial_connection.flush()
            
            self.logger.info(f"パターンをデバイス '{self.device_id}' に送信しました")
            return True

        except Exception as e:
            self.logger.error(f"パターン送信中にエラーが発生しました: {str(e)}")
            return False

    async def stop(self) -> bool:
        """
        デバイスの振動を停止します。

        戻り値:
            停止が成功した場合はTrue、それ以外の場合はFalse
        """
        # 空のパターンを送信して振動を停止
        stop_pattern = VibrationPattern(
            steps=[VibrationStep(intensity=0, duration=100)],
            interval=0,
            repeat_count=1
        )
        return await self.send_pattern(stop_pattern)

    async def get_status(self) -> Optional[DeviceStatus]:
        """
        デバイスの状態を取得します。

        戻り値:
            デバイスの状態、取得できない場合はNone
        """
        if not self.is_connected:
            return DeviceStatus(device_state="disconnected")
        
        return DeviceStatus(device_state="connected")

    def create_pattern_from_emotion(
        self, emotion: Emotion, emotion_category: str
    ) -> VibrationPattern:
        """
        感情データから振動パターンを生成します。

        引数:
            emotion: 感情データ
            emotion_category: 感情カテゴリ（joy, anger, sorrow, pleasure）

        戻り値:
            生成された振動パターン
        """
        # 感情カテゴリに応じた基本パターンを定義
        patterns = {
            "joy": {
                "base_intensity": 60,
                "variation": 20,
                "base_duration": 200,
                "interval": 100,
                "repeat_count": 3
            },
            "anger": {
                "base_intensity": 80,
                "variation": 10,
                "base_duration": 150,
                "interval": 50,
                "repeat_count": 5
            },
            "sorrow": {
                "base_intensity": 40,
                "variation": 10,
                "base_duration": 500,
                "interval": 200,
                "repeat_count": 2
            },
            "pleasure": {
                "base_intensity": 50,
                "variation": 30,
                "base_duration": 300,
                "interval": 150,
                "repeat_count": 4
            }
        }

        pattern_config = patterns.get(emotion_category, patterns["joy"])
        
        # 感情強度に基づいてパターンを調整
        emotion_intensity = max(emotion.joy, emotion.fun, emotion.anger, emotion.sad)
        
        steps = []
        for i in range(3):  # 3ステップのパターン
            intensity = int(
                pattern_config["base_intensity"] * emotion_intensity
                + pattern_config["variation"] * (i % 2)
            )
            intensity = min(100, max(0, intensity))
            
            duration = pattern_config["base_duration"] + (i * 50)
            
            steps.append(VibrationStep(intensity=intensity, duration=duration))
        
        return VibrationPattern(
            steps=steps,
            interval=pattern_config["interval"],
            repeat_count=pattern_config["repeat_count"]
        )


class SerialControllerManager:
    """
    複数のシリアルコントローラーを管理するマネージャー
    """

    def __init__(self):
        """SerialControllerManagerを初期化します。"""
        self.controllers: Dict[str, SerialController] = {}
        self.logger = logging.getLogger(__name__)

    def register_controller(
        self, device_id: str, port: str = None, baudrate: int = 115200
    ) -> None:
        """
        新しいコントローラーを登録します。

        引数:
            device_id: デバイスの識別子
            port: シリアルポート
            baudrate: ボーレート
        """
        if device_id in self.controllers:
            self.logger.warning(f"デバイス '{device_id}' は既に登録されています")
            return

        controller = SerialController(device_id, port, baudrate)
        self.controllers[device_id] = controller
        self.logger.info(f"デバイス '{device_id}' が登録されました")

    async def connect_all(self) -> Dict[str, bool]:
        """
        すべてのコントローラーを接続します。

        戻り値:
            デバイスIDと接続成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.connect()
        return results

    async def disconnect_all(self) -> Dict[str, bool]:
        """
        すべてのコントローラーを切断します。

        戻り値:
            デバイスIDと切断成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.disconnect()
        return results

    async def send_to_all(
        self, emotion: Emotion, emotion_category: str
    ) -> Dict[str, bool]:
        """
        すべてのデバイスに感情ベースの振動パターンを送信します。

        引数:
            emotion: 感情データ
            emotion_category: 感情カテゴリ

        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            pattern = controller.create_pattern_from_emotion(emotion, emotion_category)
            results[device_id] = await controller.send_pattern(pattern)
        return results

    async def stop_all(self) -> Dict[str, bool]:
        """
        すべてのデバイスの振動を停止します。

        戻り値:
            デバイスIDと停止成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.stop()
        return results

    async def get_all_status(self) -> Dict[str, Optional[DeviceStatus]]:
        """
        すべてのデバイスの状態を取得します。

        戻り値:
            デバイスIDと状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.get_status()
        return results

    async def process_pipeline_context(self, ctx: PipelineContext) -> Dict[str, bool]:
        """
        パイプラインコンテキストを処理し、振動パターンを送信します。

        引数:
            ctx: パイプラインコンテキスト

        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        if not ctx.emotion or not ctx.emotion_category:
            self.logger.warning("感情データまたはカテゴリがありません")
            return {}

        return await self.send_to_all(ctx.emotion, ctx.emotion_category)