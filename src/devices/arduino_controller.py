"""
Arduinoコントローラーモジュール

このモジュールは、Arduino Uno R4 WiFiと通信し、
振動パターンを送信するためのインターフェースを提供します。
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from pydantic import BaseModel

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator


class ArduinoControllerConfig(BaseModel):
    """
    Arduinoコントローラーの設定クラス
    """
    host: str = "192.168.1.100"  # Arduinoのデフォルトホスト
    port: int = 80               # Arduinoのデフォルトポート
    timeout: float = 5.0         # 通信タイムアウト（秒）
    retry_count: int = 3         # 再試行回数
    retry_delay: float = 1.0     # 再試行間の遅延（秒）


class ArduinoController:
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
        self.config = config or ArduinoControllerConfig()
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.session = None
    
    async def connect(self) -> bool:
        """
        Arduinoデバイスへの接続を確立します。
        
        戻り値:
            接続が成功した場合はTrue、それ以外の場合はFalse
        """
        if self.connected:
            return True
            
        self.logger.info(f"Arduinoデバイスに接続中: {self.config.host}:{self.config.port}")
        
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            async with self.session.get(f"http://{self.config.host}:{self.config.port}/status") as response:
                if response.status == 200:
                    self.connected = True
                    self.logger.info("Arduinoデバイスに接続しました")
                    return True
                else:
                    self.logger.error(f"Arduinoデバイスへの接続に失敗しました: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Arduinoデバイスへの接続中にエラーが発生しました: {str(e)}")
            if self.session:
                await self.session.close()
                self.session = None
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
        
        if self.session:
            await self.session.close()
            self.session = None
            
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
            self.logger.warning("パターンを送信できません: デバイスに接続されていません")
            return False
            
        arduino_pattern = self._convert_pattern_to_arduino_format(pattern)
        
        self.logger.info(f"パターンをArduinoデバイスに送信中: {json.dumps(arduino_pattern)}")
        
        for attempt in range(self.config.retry_count):
            try:
                async with self.session.post(
                    f"http://{self.config.host}:{self.config.port}/pattern",
                    json=arduino_pattern
                ) as response:
                    if response.status == 200:
                        self.logger.info("パターンが正常に送信されました")
                        return True
                    else:
                        self.logger.warning(f"パターン送信に失敗しました: {response.status}")
                        
            except Exception as e:
                self.logger.error(f"パターン送信中にエラーが発生しました: {str(e)}")
                
            if attempt < self.config.retry_count - 1:
                self.logger.info(f"再試行中... ({attempt + 1}/{self.config.retry_count})")
                await asyncio.sleep(self.config.retry_delay)
                
        return False
    
    async def send_emotion(self, emotion: Emotion, emotion_category: Optional[str] = None) -> bool:
        """
        感情データに基づいて振動パターンを生成し、Arduinoデバイスに送信します。
        
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
        パイプラインコンテキストを処理し、適切な振動パターンをArduinoデバイスに送信します。
        
        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト
            
        戻り値:
            パターンが正常に送信された場合はTrue、それ以外の場合はFalse
        """
        if not ctx.emotion:
            self.logger.warning("コンテキストを処理できません: 感情データがありません")
            return False
            
        return await self.send_emotion(ctx.emotion, ctx.emotion_category)
    
    def _convert_pattern_to_arduino_format(self, pattern: VibrationPattern) -> Dict[str, Any]:
        """
        振動パターンをArduino用のフォーマットに変換します。
        
        引数:
            pattern: 変換する振動パターン
            
        戻り値:
            Arduino用のフォーマットに変換されたパターン
        """
        steps = []
        
        for step in pattern.steps:
            intensity = int(step.intensity * 100)
            
            steps.append({
                "intensity": intensity,
                "duration": step.duration_ms
            })
        
        return {
            "steps": steps,
            "interval": pattern.interval_ms,
            "repeat_count": pattern.repeat_count
        }


class ArduinoControllerManager:
    """
    Arduinoコントローラーのマネージャークラス
    
    このクラスは、複数のArduinoデバイスを管理し、
    感情ベースのフィードバックを送信するための高レベルインターフェースを提供します。
    """
    
    def __init__(self):
        """Arduinoコントローラーマネージャーを初期化します。"""
        self.controllers = {}
        self.logger = logging.getLogger(__name__)
    
    def register_controller(self, device_id: str, host: str, port: int = 80) -> ArduinoController:
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
    
    def get_controller(self, device_id: str) -> Optional[ArduinoController]:
        """
        IDで登録済みのコントローラーを取得します。
        
        引数:
            device_id: デバイスの識別子
            
        戻り値:
            見つかった場合はArduinoコントローラー、それ以外の場合はNone
        """
        return self.controllers.get(device_id)
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのArduinoデバイスに接続します。
        
        戻り値:
            デバイスIDと接続成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.connect()
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """
        登録されたすべてのArduinoデバイスから切断します。
        
        戻り値:
            デバイスIDと切断成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.disconnect()
        return results
    
    async def send_to_all(self, emotion: Emotion, emotion_category: Optional[str] = None) -> Dict[str, bool]:
        """
        感情データをすべての接続されたArduinoデバイスに送信します。
        
        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            emotion_category: オプションの感情カテゴリ指定
            
        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.send_emotion(emotion, emotion_category)
        return results
    
    async def process_pipeline_context(self, ctx: PipelineContext) -> Dict[str, bool]:
        """
        パイプラインコンテキストを処理し、すべての接続されたArduinoデバイスに送信します。
        
        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト
            
        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        results = {}
        for device_id, controller in self.controllers.items():
            results[device_id] = await controller.process_pipeline_context(ctx)
        return results


arduino_manager = ArduinoControllerManager()
