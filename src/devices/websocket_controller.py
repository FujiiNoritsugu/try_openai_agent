"""
WebSocketコントローラーモジュール

このモジュールは、WebSocketを使用してArduino Uno R4 WiFiと通信し、
リアルタイムの振動パターン送信と状態監視を行うためのインターフェースを提供します。
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List, Callable
import aiohttp
from pydantic import BaseModel, Field

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator
from .base_controller import BaseController, BaseControllerConfig, BaseControllerManager


class WebSocketControllerConfig(BaseControllerConfig):
    """
    WebSocketコントローラーの設定クラス
    """

    ws_path: str = Field("/ws", description="WebSocketのパス")
    heartbeat_interval: float = Field(10.0, gt=0, description="ハートビート間隔（秒）")

    def __init__(self, **data):
        # 環境変数からデフォルト値を設定
        data.setdefault("host", os.getenv("WEBSOCKET_HOST", "192.168.1.100"))
        data.setdefault("port", int(os.getenv("WEBSOCKET_PORT", "80")))
        data.setdefault("ws_path", os.getenv("WEBSOCKET_PATH", "/ws"))
        data.setdefault("timeout", float(os.getenv("WEBSOCKET_TIMEOUT", "5.0")))
        data.setdefault("retry_count", int(os.getenv("WEBSOCKET_RETRY_COUNT", "3")))
        data.setdefault("retry_delay", float(os.getenv("WEBSOCKET_RETRY_DELAY", "1.0")))
        data.setdefault(
            "heartbeat_interval", float(os.getenv("WEBSOCKET_HEARTBEAT", "10.0"))
        )
        super().__init__(**data)


class DeviceStatus(BaseModel):
    """
    デバイスの状態を表すモデル
    """

    device_state: str  # idle, playing, error
    is_playing: bool
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    current_repeat: Optional[int] = None
    total_repeats: Optional[int] = None
    error_message: Optional[str] = None


class WebSocketController(BaseController):
    """
    WebSocketを使用したArduino Uno R4 WiFiコントローラークラス

    このクラスは、WebSocket経由でArduino Uno R4と通信し、
    振動パターンを送信し、リアルタイムの状態更新を受信するためのメソッドを提供します。
    """

    def __init__(self, config: Optional[WebSocketControllerConfig] = None):
        """
        WebSocketコントローラーを初期化します。

        引数:
            config: コントローラーの設定。指定しない場合はデフォルト設定が使用されます。
        """
        super().__init__(config or WebSocketControllerConfig())
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.status_listeners: List[Callable[[DeviceStatus], None]] = []
        self.last_status: Optional[DeviceStatus] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._status_monitor_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """
        WebSocketを使用してArduinoデバイスへの接続を確立します。

        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        if self.connected:
            return True

        self.logger.info(
            f"WebSocket経由でArduinoデバイスに接続中: ws://{self.config.host}:{self.config.port}{self.config.ws_path}"
        )

        try:
            await self._ensure_session()

            async with self.session.get(
                f"http://{self.config.host}:{self.config.port}/status"
            ) as response:
                if response.status != 200:
                    self.logger.error(
                        f"デバイスの状態確認に失敗しました: {response.status}"
                    )
                    await self._cleanup_session()
                    return False

                self.logger.info(
                    "デバイスがオンラインです。WebSocket接続を確立します。"
                )

            self.ws = await self.session.ws_connect(
                f"ws://{self.config.host}:{self.config.port}{self.config.ws_path}",
                timeout=self.config.timeout,
            )

            self.connected = True
            self.logger.info("WebSocket接続が確立されました")

            self._start_background_tasks()

            return True

        except aiohttp.ClientError as e:
            self.logger.error(
                f"WebSocket接続中にネットワークエラーが発生しました: {str(e)}"
            )
            await self._cleanup_session()
            return False
        except asyncio.TimeoutError:
            self.logger.error("WebSocket接続がタイムアウトしました")
            await self._cleanup_session()
            return False
        except Exception as e:
            self.logger.error(
                f"WebSocket接続中に予期しないエラーが発生しました: {str(e)}"
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

        self.logger.info("WebSocket接続を切断中")

        await self._stop_background_tasks()

        if self.ws:
            await self.ws.close()
            self.ws = None

        await self._cleanup_session()

        self.connected = False
        self.logger.info("WebSocket接続が切断されました")
        return True

    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        振動パターンをWebSocket経由でArduinoデバイスに送信します。

        引数:
            pattern: 送信する振動パターン

        戻り値:
            送信が成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.connected or not self.ws:
            self.logger.warning("パターンを送信できません: WebSocket接続がありません")
            return False

        arduino_pattern = self._convert_pattern_to_specific_format(pattern)

        self.logger.info(
            f"パターンをWebSocket経由で送信中: {json.dumps(arduino_pattern)}"
        )

        for attempt in range(self.config.retry_count):
            try:
                await self.ws.send_json(arduino_pattern)

                response = await asyncio.wait_for(
                    self.ws.receive_json(), timeout=self.config.timeout
                )

                if response.get("status") == "ok":
                    self.logger.info("パターンが正常に送信されました")
                    return True
                else:
                    self.logger.warning(
                        f"パターン送信に失敗しました: {response.get('message', 'Unknown error')}"
                    )

            except asyncio.TimeoutError:
                self.logger.error("パターン送信がタイムアウトしました")
            except aiohttp.ClientError as e:
                self.logger.error(
                    f"パターン送信中にネットワークエラーが発生しました: {str(e)}"
                )

                if not self.connected or not self.ws or self.ws.closed:
                    self.logger.info(
                        "WebSocket接続が切断されました。再接続を試みます。"
                    )
                    await self.disconnect()
                    if await self.connect():
                        self.logger.info("WebSocket接続が再確立されました")
                    else:
                        self.logger.error("WebSocket再接続に失敗しました")
                        return False
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

    async def stop_vibration(self) -> bool:
        """
        現在再生中の振動パターンを停止します。

        戻り値:
            停止コマンドが正常に送信された場合はTrue、それ以外の場合はFalse
        """
        if not self.connected:
            self.logger.warning(
                "停止コマンドを送信できません: WebSocket接続がありません"
            )
            return False

        self.logger.info("停止コマンドを送信中")

        try:
            await self.ws.send_str("stop")

            response = await self.ws.receive_json(timeout=self.config.timeout)

            if response.get("status") == "ok":
                self.logger.info("振動が正常に停止されました")
                return True
            else:
                self.logger.warning(
                    f"振動停止に失敗しました: {response.get('message', 'Unknown error')}"
                )
                return False

        except Exception as e:
            self.logger.error(f"停止コマンド送信中にエラーが発生しました: {str(e)}")
            return False

    async def get_status(self) -> Optional[DeviceStatus]:
        """
        デバイスの現在の状態を取得します。

        戻り値:
            デバイスの状態を表すDeviceStatusオブジェクト、または取得に失敗した場合はNone
        """
        if not self.connected:
            self.logger.warning("状態を取得できません: WebSocket接続がありません")
            return None

        self.logger.debug("デバイスの状態を要求中")

        try:
            await self.ws.send_str("status")

            response = await self.ws.receive_json(timeout=self.config.timeout)

            if response.get("type") == "status":
                status = DeviceStatus(
                    device_state=response.get("device_state", "unknown"),
                    is_playing=response.get("is_playing", False),
                    current_step=response.get("current_step"),
                    total_steps=response.get("total_steps"),
                    current_repeat=response.get("current_repeat"),
                    total_repeats=response.get("total_repeats"),
                    error_message=response.get("error_message"),
                )
                self.last_status = status
                return status
            else:
                self.logger.warning(f"状態取得に失敗しました: {response}")
                return None

        except Exception as e:
            self.logger.error(f"状態取得中にエラーが発生しました: {str(e)}")
            return None

    def add_status_listener(self, listener: Callable[[DeviceStatus], None]) -> None:
        """
        デバイスの状態変更を監視するリスナーを追加します。

        引数:
            listener: 状態が変更されたときに呼び出されるコールバック関数
        """
        self.status_listeners.append(listener)
        self.logger.debug(
            f"状態リスナーが追加されました（合計: {len(self.status_listeners)}）"
        )

    def remove_status_listener(self, listener: Callable[[DeviceStatus], None]) -> None:
        """
        状態リスナーを削除します。

        引数:
            listener: 削除するリスナー
        """
        if listener in self.status_listeners:
            self.status_listeners.remove(listener)
            self.logger.debug(
                f"状態リスナーが削除されました（残り: {len(self.status_listeners)}）"
            )

    def _convert_pattern_to_specific_format(
        self, pattern: VibrationPattern
    ) -> Dict[str, Any]:
        """
        WebSocket用にパターンを変換します。

        引数:
            pattern: 変換する振動パターン

        戻り値:
            WebSocket用のフォーマットに変換されたパターン
        """
        # 基本的な変換を使用
        base_format = self._convert_pattern_to_arduino_format(pattern)

        # WebSocket固有のフィールドを追加
        base_format["type"] = "pattern"
        base_format["timestamp"] = asyncio.get_event_loop().time()

        return base_format

    def _start_background_tasks(self) -> None:
        """バックグラウンドタスクを開始します。"""
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        if not self._status_monitor_task:
            self._status_monitor_task = asyncio.create_task(self._status_monitor_loop())

    async def _stop_background_tasks(self) -> None:
        """バックグラウンドタスクを停止します。"""
        tasks_to_cancel = []

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            tasks_to_cancel.append(self._heartbeat_task)
            self._heartbeat_task = None

        if self._status_monitor_task:
            self._status_monitor_task.cancel()
            tasks_to_cancel.append(self._status_monitor_task)
            self._status_monitor_task = None

        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    async def _heartbeat_loop(self) -> None:
        """
        定期的にハートビートを送信するループ。
        接続が切断された場合は再接続を試みます。
        """
        while self.connected:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                if not self.connected or not self.ws or self.ws.closed:
                    self.logger.warning(
                        "WebSocket接続が切断されました。再接続を試みます。"
                    )
                    await self.disconnect()
                    if await self.connect():
                        self.logger.info("WebSocket接続が再確立されました")
                    else:
                        self.logger.error("WebSocket再接続に失敗しました")
                        break
                else:
                    await self.ws.send_str("heartbeat")
                    await asyncio.wait_for(
                        self.ws.receive_json(), timeout=self.config.timeout
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"ハートビート中にエラーが発生しました: {str(e)}")
                await asyncio.sleep(1)  # エラー発生時は短い間隔で再試行

    async def _status_monitor_loop(self) -> None:
        """
        WebSocketからの状態更新を監視するループ。
        受信した状態更新をリスナーに通知します。
        """
        while self.connected:
            try:
                if not self.ws or self.ws.closed:
                    await asyncio.sleep(1)
                    continue

                msg = await self.ws.receive(timeout=None)

                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)

                        if data.get("type") == "status":
                            status = DeviceStatus(
                                device_state=data.get("device_state", "unknown"),
                                is_playing=data.get("is_playing", False),
                                current_step=data.get("current_step"),
                                total_steps=data.get("total_steps"),
                                current_repeat=data.get("current_repeat"),
                                total_repeats=data.get("total_repeats"),
                                error_message=data.get("error_message"),
                            )

                            self.last_status = status

                            for listener in self.status_listeners:
                                try:
                                    listener(status)
                                except Exception as e:
                                    self.logger.error(
                                        f"状態リスナーの実行中にエラーが発生しました: {str(e)}"
                                    )
                    except json.JSONDecodeError:
                        self.logger.warning(
                            f"無効なJSONメッセージを受信しました: {msg.data}"
                        )

                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    self.logger.warning("WebSocket接続がサーバーによって閉じられました")
                    break

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(
                        f"WebSocketエラーが発生しました: {self.ws.exception()}"
                    )
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"状態監視中にエラーが発生しました: {str(e)}")
                await asyncio.sleep(1)  # エラー発生時は短い間隔で再試行


class WebSocketControllerManager(BaseControllerManager):
    """
    WebSocketコントローラーのマネージャークラス

    このクラスは、複数のWebSocketコントローラーを管理し、
    感情ベースのフィードバックを送信するための高レベルインターフェースを提供します。
    """

    def register_controller(
        self, device_id: str, host: str, port: int = 80, ws_path: str = "/ws"
    ) -> WebSocketController:
        """
        新しいWebSocketコントローラーを登録します。

        引数:
            device_id: デバイスの識別子
            host: デバイスのホストアドレス
            port: デバイスのポート
            ws_path: WebSocketのパス

        戻り値:
            登録されたWebSocketコントローラー
        """
        config = WebSocketControllerConfig(host=host, port=port, ws_path=ws_path)
        controller = WebSocketController(config)
        self.controllers[device_id] = controller
        self.logger.info(f"WebSocketコントローラーを登録しました: {device_id}")
        return controller

    async def stop_all(self) -> Dict[str, bool]:
        """
        すべての接続されたWebSocketコントローラーの振動を停止します。

        戻り値:
            デバイスIDと停止成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.stop_vibration()
        return results

    async def get_all_status(self) -> Dict[str, Optional[DeviceStatus]]:
        """
        すべての接続されたWebSocketコントローラーの状態を取得します。

        戻り値:
            デバイスIDと状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.get_status()
        return results
