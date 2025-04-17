"""
パイプライン統合モジュール

このモジュールは、感情分析パイプラインと触覚フィードバックデバイスを統合し、
感情分析の結果に基づいて適切な振動パターンをデバイスに送信するための
インターフェースを提供します。
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..models.data_models import PipelineContext, Emotion
from ..pipeline.pipeline import run_pipeline, format_pipeline_results
from .websocket_controller import websocket_manager, WebSocketController


class HapticFeedbackIntegration:
    """
    感情分析パイプラインと触覚フィードバックデバイスを統合するクラス
    
    このクラスは、感情分析パイプラインの結果を処理し、
    WebSocketコントローラーを通じて適切な振動パターンを
    触覚フィードバックデバイスに送信します。
    """
    
    def __init__(self):
        """HapticFeedbackIntegrationを初期化します。"""
        self.logger = logging.getLogger(__name__)
        self.websocket_manager = websocket_manager
        self.connected_devices = set()
        self.is_initialized = False
    
    async def initialize(self, device_configs: List[Dict[str, Any]]) -> bool:
        """
        触覚フィードバックシステムを初期化します。
        
        引数:
            device_configs: デバイス設定のリスト。各設定は以下のキーを含む辞書:
                - device_id: デバイスの識別子
                - host: デバイスのホストアドレス
                - port: デバイスのポート（オプション、デフォルト: 80）
                - ws_path: WebSocketのパス（オプション、デフォルト: "/ws"）
                
        戻り値:
            初期化が成功した場合はTrue、それ以外の場合はFalse
        """
        if self.is_initialized:
            self.logger.warning("触覚フィードバックシステムは既に初期化されています")
            return True
            
        self.logger.info(f"{len(device_configs)}台のデバイスで触覚フィードバックシステムを初期化中")
        
        try:
            for config in device_configs:
                device_id = config.get("device_id")
                host = config.get("host")
                port = config.get("port", 80)
                ws_path = config.get("ws_path", "/ws")
                
                if not device_id or not host:
                    self.logger.error(f"無効なデバイス設定: {config}")
                    continue
                    
                self.websocket_manager.register_controller(device_id, host, port, ws_path)
                self.connected_devices.add(device_id)
                
            if self.connected_devices:
                connection_results = await self.websocket_manager.connect_all()
                
                for device_id, success in connection_results.items():
                    if success:
                        self.logger.info(f"デバイス '{device_id}' に正常に接続しました")
                    else:
                        self.logger.warning(f"デバイス '{device_id}' への接続に失敗しました")
                        self.connected_devices.remove(device_id)
                
                self.is_initialized = True
                self.logger.info(f"触覚フィードバックシステムが初期化されました（接続済みデバイス: {len(self.connected_devices)}）")
                return len(self.connected_devices) > 0
            else:
                self.logger.warning("初期化するデバイスがありません")
                return False
                
        except Exception as e:
            self.logger.error(f"触覚フィードバックシステムの初期化中にエラーが発生しました: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """
        触覚フィードバックシステムをシャットダウンします。
        
        戻り値:
            シャットダウンが成功した場合はTrue、それ以外の場合はFalse
        """
        if not self.is_initialized:
            self.logger.warning("触覚フィードバックシステムは初期化されていません")
            return True
            
        self.logger.info("触覚フィードバックシステムをシャットダウン中")
        
        try:
            await self.websocket_manager.stop_all()
            
            disconnect_results = await self.websocket_manager.disconnect_all()
            
            for device_id, success in disconnect_results.items():
                if success:
                    self.logger.info(f"デバイス '{device_id}' から正常に切断しました")
                else:
                    self.logger.warning(f"デバイス '{device_id}' からの切断に失敗しました")
            
            self.connected_devices.clear()
            self.is_initialized = False
            self.logger.info("触覚フィードバックシステムがシャットダウンされました")
            return True
            
        except Exception as e:
            self.logger.error(f"触覚フィードバックシステムのシャットダウン中にエラーが発生しました: {str(e)}")
            return False
    
    async def process_pipeline_result(self, ctx: PipelineContext) -> Dict[str, bool]:
        """
        パイプラインの結果を処理し、接続されたすべてのデバイスに振動パターンを送信します。
        
        引数:
            ctx: 感情データとカテゴリを含むパイプラインコンテキスト
            
        戻り値:
            デバイスIDと送信成功状態をマッピングした辞書
        """
        if not self.is_initialized:
            self.logger.warning("触覚フィードバックシステムが初期化されていません")
            return {}
            
        if not self.connected_devices:
            self.logger.warning("接続されたデバイスがありません")
            return {}
            
        if not ctx.emotion:
            self.logger.warning("感情データがありません")
            return {}
            
        self.logger.info(f"パイプライン結果を処理中: カテゴリ={ctx.emotion_category}, 感情={ctx.emotion}")
        
        try:
            results = await self.websocket_manager.process_pipeline_context(ctx)
            
            for device_id, success in results.items():
                if success:
                    self.logger.info(f"デバイス '{device_id}' にパターンを正常に送信しました")
                else:
                    self.logger.warning(f"デバイス '{device_id}' へのパターン送信に失敗しました")
            
            return results
            
        except Exception as e:
            self.logger.error(f"パイプライン結果の処理中にエラーが発生しました: {str(e)}")
            return {}
    
    async def run_pipeline_and_send(self, user_input, emotion_learner=None) -> Tuple[Dict[str, Any], Dict[str, bool]]:
        """
        パイプラインを実行し、結果を触覚フィードバックデバイスに送信します。
        
        引数:
            user_input: パイプラインに渡すユーザー入力
            emotion_learner: オプションの感情学習モジュール
            
        戻り値:
            (フォーマットされたパイプライン結果, デバイス送信結果)のタプル
        """
        if not self.is_initialized:
            self.logger.warning("触覚フィードバックシステムが初期化されていません")
            return {}, {}
            
        self.logger.info("パイプラインを実行し、結果を触覚フィードバックデバイスに送信します")
        
        try:
            ctx, error = await run_pipeline(user_input, emotion_learner)
            
            if error:
                self.logger.error(f"パイプライン実行中にエラーが発生しました: {str(error)}")
                return {}, {}
                
            formatted_results = format_pipeline_results(ctx)
            
            device_results = await self.process_pipeline_result(ctx)
            
            return formatted_results, device_results
            
        except Exception as e:
            self.logger.error(f"パイプライン実行と送信中にエラーが発生しました: {str(e)}")
            return {}, {}
    
    async def stop_all_devices(self) -> Dict[str, bool]:
        """
        すべてのデバイスの振動を停止します。
        
        戻り値:
            デバイスIDと停止成功状態をマッピングした辞書
        """
        if not self.is_initialized:
            self.logger.warning("触覚フィードバックシステムが初期化されていません")
            return {}
            
        self.logger.info("すべてのデバイスの振動を停止中")
        
        try:
            results = await self.websocket_manager.stop_all()
            
            for device_id, success in results.items():
                if success:
                    self.logger.info(f"デバイス '{device_id}' の振動を正常に停止しました")
                else:
                    self.logger.warning(f"デバイス '{device_id}' の振動停止に失敗しました")
            
            return results
            
        except Exception as e:
            self.logger.error(f"デバイス停止中にエラーが発生しました: {str(e)}")
            return {}
    
    async def get_all_device_status(self) -> Dict[str, Any]:
        """
        すべてのデバイスの状態を取得します。
        
        戻り値:
            デバイスIDと状態をマッピングした辞書
        """
        if not self.is_initialized:
            self.logger.warning("触覚フィードバックシステムが初期化されていません")
            return {}
            
        self.logger.info("すべてのデバイスの状態を取得中")
        
        try:
            return await self.websocket_manager.get_all_status()
            
        except Exception as e:
            self.logger.error(f"デバイス状態取得中にエラーが発生しました: {str(e)}")
            return {}


haptic_feedback = HapticFeedbackIntegration()
