"""
Arduinoコントローラーモジュール

このモジュールは、Arduino Uno R4 WiFiと通信し、
振動パターンを送信するためのインターフェースを提供します。
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List
import aiohttp

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator
from .base_controller import BaseController, BaseControllerConfig, BaseControllerManager


class ArduinoControllerConfig(BaseControllerConfig):
    """
    Arduinoコントローラーの設定クラス
    """

    def __init__(self, **data):
        # 環境変数からデフォルト値を設定
        data.setdefault("host", os.getenv("ARDUINO_HOST", "192.168.43.166"))
        data.setdefault("port", int(os.getenv("ARDUINO_PORT", "80")))
        data.setdefault("timeout", float(os.getenv("ARDUINO_TIMEOUT", "5.0")))
        data.setdefault("retry_count", int(os.getenv("ARDUINO_RETRY_COUNT", "3")))
        data.setdefault("retry_delay", float(os.getenv("ARDUINO_RETRY_DELAY", "1.0")))
        super().__init__(**data)


class ArduinoController(BaseController):
    """
    Arduino Uno R4 WiFiコントローラークラス

    このクラスは、WiFi経由でArduino Uno R4と通信し、
    振動パターンを送信するためのメソッドを提供します。
    """

    def __init__(self, config: Optional[ArduinoControllerConfig] = None):
        """
        Arduinoコントローラーを初期化します。

        引数:
            config: コントローラーの設定。指定しない場合はデフォルト設定が使用されます。
        """
        super().__init__(config or ArduinoControllerConfig())

    async def connect(self) -> bool:
        """
        Arduinoデバイスへの接続を確立します。

        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        if self.connected:
            return True

        self.logger.info(
            f"Arduinoデバイスに接続中: {self.config.host}:{self.config.port}"
        )

        try:
            await self._ensure_session()

            # タイムアウトを使わずに接続テスト
            async with self.session.get(
                f"http://{self.config.host}:{self.config.port}/status"
            ) as response:
                if response.status == 200:
                    self.connected = True
                    self.logger.info("Arduinoデバイスに接続しました")
                    return True
                else:
                    self.logger.error(
                        f"Arduinoデバイスへの接続に失敗しました: {response.status}"
                    )
                    await self._cleanup_session()
                    return False

        except aiohttp.ClientError as e:
            self.logger.error(
                f"Arduinoデバイスへの接続中にネットワークエラーが発生しました: {str(e)}"
            )
            await self._cleanup_session()
            return False
        except asyncio.TimeoutError:
            self.logger.error("Arduinoデバイスへの接続がタイムアウトしました")
            await self._cleanup_session()
            return False
        except Exception as e:
            self.logger.error(
                f"Arduinoデバイスへの接続中に予期しないエラーが発生しました: {str(e)}"
            )
            await self._cleanup_session()
            return False

    async def disconnect(self) -> bool:
        """
        Arduinoデバイスから切断します。

        戻り値:
            切断が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            return True

        self.logger.info("Arduinoデバイスから切断中")

        await self._cleanup_session()

        self.connected = False
        self.logger.info("Arduinoデバイスから切断しました")
        return True

    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        振動パターンをArduinoデバイスに送信します。

        引数:
            pattern: 送信する振動パターン

        戻り値:
            送信が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            self.logger.warning(
                "パターンを送信できません: デバイスに接続されていません"
            )
            return False
        
        # セッションを確保
        await self._ensure_session()

        arduino_pattern = self._convert_pattern_to_arduino_format(pattern)

        self.logger.info(
            f"パターンをArduinoデバイスに送信中: {json.dumps(arduino_pattern)}"
        )

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.post(
                    f"http://{self.config.host}:{self.config.port}/",
                    json=arduino_pattern
                ) as response:
                    if response.status == 200:
                        self.logger.info("パターンが正常に送信されました")
                        return True
                    else:
                        self.logger.warning(
                            f"パターン送信に失敗しました: {response.status}"
                        )

            except aiohttp.ClientError as e:
                self.logger.error(
                    f"パターン送信中にネットワークエラーが発生しました: {str(e)}"
                )
            except asyncio.TimeoutError:
                self.logger.error("パターン送信がタイムアウトしました")
            except Exception as e:
                self.logger.error(
                    f"パターン送信中に予期しないエラーが発生しました: {str(e)}"
                )

            if attempt < self.config.retry_count - 1:
                self.logger.info(
                    f"再試行中... ({attempt + 1}/{self.config.retry_count})"
                )
                await asyncio.sleep(self.config.retry_delay)

        return False

    async def stop(self) -> bool:
        """
        現在再生中の振動パターンを停止します。

        戻り値:
            停止が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            self.logger.warning(
                "停止コマンドを送信できません: デバイスに接続されていません"
            )
            return False

        self.logger.info("振動を停止中")

        try:
            # セッションを確保
            await self._ensure_session()
            
            async with self.session.post(
                f"http://{self.config.host}:{self.config.port}/stop"
            ) as response:
                if response.status == 200:
                    self.logger.info("振動が正常に停止されました")
                    return True
                else:
                    self.logger.warning(
                        f"振動停止に失敗しました: {response.status}"
                    )
                    return False

        except aiohttp.ClientError as e:
            self.logger.error(
                f"振動停止中にネットワークエラーが発生しました: {str(e)}"
            )
            return False
        except asyncio.TimeoutError:
            self.logger.error("振動停止がタイムアウトしました")
            return False
        except Exception as e:
            self.logger.error(
                f"振動停止中に予期しないエラーが発生しました: {str(e)}"
            )
            return False

    async def get_status(self) -> Optional[Dict[str, Any]]:
        """
        デバイスの現在の状態を取得します。

        戻り値:
            状態情報を含む辞書、取得失敗時はNone
        """
        if not self.connected:
            self.logger.warning(
                "ステータスを取得できません: デバイスに接続されていません"
            )
            return None

        self.logger.info("デバイスステータスを取得中")

        try:
            # セッションを確保
            await self._ensure_session()
            
            # タイムアウトを使わずに接続テスト
            async with self.session.get(
                f"http://{self.config.host}:{self.config.port}/status"
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    self.logger.info(f"ステータス取得成功: {status}")
                    return status
                else:
                    self.logger.warning(
                        f"ステータス取得に失敗しました: {response.status}"
                    )
                    return None

        except aiohttp.ClientError as e:
            self.logger.error(
                f"ステータス取得中にネットワークエラーが発生しました: {str(e)}"
            )
            return None
        except asyncio.TimeoutError:
            self.logger.error("ステータス取得がタイムアウトしました")
            return None
        except Exception as e:
            self.logger.error(
                f"ステータス取得中に予期しないエラーが発生しました: {str(e)}"
            )
            return None


class ArduinoControllerManager(BaseControllerManager):
    """
    Arduinoコントローラーのマネージャークラス

    このクラスは、複数のArduinoデバイスを管理し、
    感情ベースのフィードバックを送信するための高レベルインターフェースを提供します。
    """

    def register_controller(
        self, device_id: str, host: str, port: int = 80
    ) -> ArduinoController:
        """
        新しいArduinoコントローラーを登録します。

        引数:
            device_id: デバイスの識別子
            host: デバイスのホストアドレス
            port: デバイスのポート

        戻り値:
            登録されたArduinoコントローラー
        """
        config = ArduinoControllerConfig(host=host, port=port)
        controller = ArduinoController(config)
        self.controllers[device_id] = controller
        self.logger.info(f"Arduinoコントローラーを登録しました: {device_id}")
        return controller

    async def get_all_status(self) -> Dict[str, Any]:
        """
        すべてのデバイスのステータスを取得します。

        戻り値:
            デバイスIDとステータスをマッピングした辞書
        """
        results = {}
        tasks = []

        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(controller.get_status())
            tasks.append((device_id, task))

        for device_id, task in tasks:
            status = await task
            if status:
                results[device_id] = status
            else:
                results[device_id] = {"connected": False, "playing": False}

        return results

    async def send_to_all(self, emotion: Emotion, emotion_category: str) -> Dict[str, bool]:
        """
        すべてのデバイスに感情ベースの振動パターンを送信します。

        引数:
            emotion: 感情データ
            emotion_category: 感情カテゴリ

        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        from ..models.data_models import PipelineContext, UserInput
        
        # PipelineContextを作成
        ctx = PipelineContext(
            user_input=UserInput(data="test", touched_area="test", gender="その他"),
            emotion=emotion,
            emotion_category=emotion_category
        )
        
        results = {}
        tasks = []

        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(controller.process_pipeline_context(ctx))
            tasks.append((device_id, task))

        for device_id, task in tasks:
            results[device_id] = await task

        return results
