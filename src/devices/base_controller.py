"""
ベースコントローラーモジュール

このモジュールは、ArduinoControllerとWebSocketControllerの共通機能を提供する
抽象基底クラスを定義します。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import aiohttp
from pydantic import BaseModel, Field, validator

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator


class BaseControllerConfig(BaseModel):
    """
    コントローラーの基本設定クラス
    """
    host: str = Field(..., description="デバイスのホストアドレス")
    port: int = Field(..., ge=1, le=65535, description="デバイスのポート番号")
    timeout: float = Field(5.0, gt=0, description="通信タイムアウト（秒）")
    retry_count: int = Field(3, ge=0, description="再試行回数")
    retry_delay: float = Field(1.0, gt=0, description="再試行間の遅延（秒）")
    
    @validator("host")
    def validate_host(cls, v):
        if not v or not v.strip():
            raise ValueError("ホストアドレスは空にできません")
        return v.strip()


class BaseController(ABC):
    """
    デバイスコントローラーの抽象基底クラス
    
    このクラスは、様々なデバイスコントローラーの共通機能を提供します。
    """
    
    def __init__(self, config: BaseControllerConfig):
        """
        コントローラーを初期化します。
        
        引数:
            config: コントローラーの設定
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_owner = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        デバイスへの接続を確立します。
        
        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        デバイスから切断します。
        
        戻り値:
            切断が成功した場合はTrue、それ以外の場合はFalse
        """
        pass
    
    @abstractmethod
    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        振動パターンをデバイスに送信します。
        
        引数:
            pattern: 送信する振動パターン
            
        戻り値:
            送信が成功した場合はTrue、それ以外の場合はFalse
        """
        pass
    
    async def send_emotion(
        self, emotion: Emotion, emotion_category: Optional[str] = None
    ) -> bool:
        """
        感情データに基づいて振動パターンを生成し、デバイスに送信します。
        
        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            emotion_category: オプションの感情カテゴリ指定
            
        戻り値:
            パターンが生成され正常に送信された場合はTrue、それ以外の場合はFalse
        """
        # 入力値の検証
        if not self._validate_emotion(emotion):
            self.logger.error("無効な感情データが提供されました")
            return False
            
        pattern = VibrationPatternGenerator.generate_pattern(emotion, emotion_category)
        return await self.send_pattern(pattern)
    
    async def process_pipeline_context(self, ctx: PipelineContext) -> bool:
        """
        パイプラインコンテキストを処理し、適切な振動パターンをデバイスに送信します。
        
        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト
            
        戻り値:
            パターンが正常に送信された場合はTrue、それ以外の場合はFalse
        """
        if not ctx.emotion:
            self.logger.warning("コンテキストを処理できません: 感情データがありません")
            return False
            
        return await self.send_emotion(ctx.emotion, ctx.emotion_category)
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリ"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーのエグジット"""
        await self.disconnect()
        return False
    
    async def _cleanup_session(self) -> None:
        """セッションをクリーンアップします。"""
        if self.session and self._session_owner:
            await self.session.close()
            self.session = None
            self._session_owner = False
    
    async def _ensure_session(self) -> None:
        """セッションが存在することを確認します。"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            self._session_owner = True
    
    def _convert_pattern_to_arduino_format(
        self, pattern: VibrationPattern
    ) -> Dict[str, Any]:
        """
        振動パターンをArduino用のフォーマットに変換します。
        
        引数:
            pattern: 変換する振動パターン
            
        戻り値:
            Arduino用のフォーマットに変換されたパターン
        """
        steps: List[Dict[str, int]] = []
        
        for step in pattern.steps:
            # 強度を0-100の範囲に変換（検証済み）
            intensity = max(0, min(100, int(step.intensity * 100)))
            
            steps.append({
                "intensity": intensity,
                "duration": step.duration_ms
            })
        
        return {
            "steps": steps,
            "interval": pattern.interval_ms,
            "repeat_count": pattern.repeat_count
        }
    
    def _validate_emotion(self, emotion: Emotion) -> bool:
        """
        感情データが有効かどうかを検証します。
        
        引数:
            emotion: 検証する感情データ
            
        戻り値:
            有効な場合はTrue、それ以外の場合はFalse
        """
        if not emotion:
            return False
            
        # すべての感情値が0-10の範囲内であることを確認（整数値）
        values = [emotion.joy, emotion.fun, emotion.anger, emotion.sad]
        return all(0 <= v <= 10 for v in values)
    
    async def _retry_with_backoff(
        self, 
        operation, 
        operation_name: str,
        *args, 
        **kwargs
    ) -> Optional[Any]:
        """
        指数バックオフで操作を再試行します。
        
        引数:
            operation: 実行する非同期関数
            operation_name: ログ用の操作名
            *args: 操作に渡す位置引数
            **kwargs: 操作に渡すキーワード引数
            
        戻り値:
            操作の結果、または失敗した場合はNone
        """
        for attempt in range(self.config.retry_count):
            try:
                result = await operation(*args, **kwargs)
                if attempt > 0:
                    self.logger.info(f"{operation_name}が成功しました（試行{attempt + 1}回目）")
                return result
            except aiohttp.ClientError as e:
                self.logger.error(f"{operation_name}中にネットワークエラーが発生しました: {str(e)}")
            except asyncio.TimeoutError:
                self.logger.error(f"{operation_name}がタイムアウトしました")
            except Exception as e:
                self.logger.error(f"{operation_name}中に予期しないエラーが発生しました: {str(e)}")
            
            if attempt < self.config.retry_count - 1:
                delay = self.config.retry_delay * (2 ** attempt)  # 指数バックオフ
                self.logger.info(
                    f"再試行中... ({attempt + 1}/{self.config.retry_count}) - {delay}秒待機"
                )
                await asyncio.sleep(delay)
        
        self.logger.error(f"{operation_name}が{self.config.retry_count}回の試行後に失敗しました")
        return None


class BaseControllerManager(ABC):
    """
    コントローラーマネージャーの抽象基底クラス
    
    このクラスは、複数のデバイスコントローラーを管理するための共通機能を提供します。
    """
    
    def __init__(self):
        """コントローラーマネージャーを初期化します。"""
        self.controllers: Dict[str, BaseController] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def register_controller(self, device_id: str, **kwargs) -> BaseController:
        """
        新しいコントローラーを登録します。
        
        引数:
            device_id: デバイスの識別子
            **kwargs: コントローラー固有のパラメータ
            
        戻り値:
            登録されたコントローラー
        """
        pass
    
    def get_controller(self, device_id: str) -> Optional[BaseController]:
        """
        IDで登録済みのコントローラーを取得します。
        
        引数:
            device_id: デバイスの識別子
            
        戻り値:
            見つかった場合はコントローラー、それ以外の場合はNone
        """
        return self.controllers.get(device_id)
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのデバイスに接続します。
        
        戻り値:
            デバイスIDと接続成功状態をマッピングした辞書
        """
        results = {}
        tasks = []
        
        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(controller.connect())
            tasks.append((device_id, task))
        
        for device_id, task in tasks:
            results[device_id] = await task
            
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのデバイスから切断します。
        
        戻り値:
            デバイスIDと切断成功状態をマッピングした辞書
        """
        results = {}
        tasks = []
        
        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(controller.disconnect())
            tasks.append((device_id, task))
        
        for device_id, task in tasks:
            results[device_id] = await task
            
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
        tasks = []
        
        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(
                controller.send_emotion(emotion, emotion_category)
            )
            tasks.append((device_id, task))
        
        for device_id, task in tasks:
            results[device_id] = await task
            
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
        tasks = []
        
        for device_id, controller in self.controllers.items():
            task = asyncio.create_task(controller.process_pipeline_context(ctx))
            tasks.append((device_id, task))
        
        for device_id, task in tasks:
            results[device_id] = await task
            
        return results
    
    def remove_controller(self, device_id: str) -> bool:
        """
        コントローラーを削除します。
        
        引数:
            device_id: 削除するデバイスの識別子
            
        戻り値:
            削除が成功した場合はTrue、それ以外の場合はFalse
        """
        if device_id in self.controllers:
            del self.controllers[device_id]
            self.logger.info(f"コントローラーを削除しました: {device_id}")
            return True
        return False
    
    def list_controllers(self) -> List[str]:
        """
        登録されているすべてのコントローラーのIDを返します。
        
        戻り値:
            デバイスIDのリスト
        """
        return list(self.controllers.keys())