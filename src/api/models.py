"""
APIモデル

このモジュールは、APIリクエストとレスポンスのためのPydanticモデルを定義します。
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ..models.data_models import Emotion, UserInput


class DeviceConfig(BaseModel):
    """デバイス設定モデル"""
    device_id: str = Field(..., description="デバイスの識別子")
    host: str = Field(..., description="デバイスのホストアドレス")
    port: int = Field(80, description="デバイスのポート")
    ws_path: str = Field("/ws", description="WebSocketのパス")


class DeviceStatus(BaseModel):
    """デバイス状態モデル"""
    device_id: str = Field(..., description="デバイスの識別子")
    device_state: str = Field(..., description="デバイスの状態")
    connected: bool = Field(..., description="接続状態")
    last_updated: Optional[str] = Field(None, description="最終更新時刻")


class EmotionAnalysisRequest(BaseModel):
    """感情分析リクエストモデル"""
    user_input: UserInput = Field(..., description="ユーザー入力データ")
    send_to_devices: bool = Field(False, description="結果をデバイスに送信するかどうか")


class EmotionAnalysisResponse(BaseModel):
    """感情分析レスポンスモデル"""
    extracted_emotion: Optional[Dict[str, float]] = Field(None, description="抽出された感情パラメータ")
    original_message: str = Field("", description="元のメッセージ")
    emotion_category: str = Field("", description="感情カテゴリ")
    final_message: str = Field("", description="最終メッセージ")
    is_learned_response: bool = Field(False, description="学習データに基づいた応答かどうか")
    device_results: Optional[Dict[str, bool]] = Field(None, description="デバイス送信結果")


class DeviceListResponse(BaseModel):
    """デバイスリストレスポンスモデル"""
    devices: List[DeviceConfig] = Field([], description="登録済みデバイスのリスト")


class DeviceStatusResponse(BaseModel):
    """デバイス状態レスポンスモデル"""
    devices: List[DeviceStatus] = Field([], description="デバイスの状態リスト")


class VibrationRequest(BaseModel):
    """振動リクエストモデル"""
    emotion: Emotion = Field(..., description="感情パラメータ")
    emotion_category: str = Field(..., description="感情カテゴリ")
    device_ids: Optional[List[str]] = Field(None, description="送信先デバイスIDのリスト（指定しない場合はすべてのデバイス）")


class VibrationResponse(BaseModel):
    """振動レスポンスモデル"""
    results: Dict[str, bool] = Field({}, description="デバイスIDと送信成功状態のマッピング")


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル"""
    error: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(None, description="エラーの詳細情報")
