"""
OpenAIエージェントパイプライン用のデータモデル。
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class Emotion(BaseModel):
    """喜び、楽しさ、怒り、悲しみの値を持つ感情パラメータモデル。"""

    joy: float
    fun: float
    anger: float
    sad: float


class UserInput(BaseModel):
    """データと触れられた部位を持つユーザー入力モデル。"""

    data: str
    touched_area: str
    gender: str = "男性"  # デフォルト値は「男性」


class OriginalOutput(BaseModel):
    """感情抽出エージェント用の出力モデル。"""

    emotion: Emotion
    message: str


class HandoffOutput(BaseModel):
    """感情カテゴリエージェント用の出力モデル。"""

    emotion_category: str
    message: str


class PipelineContext(BaseModel):
    """パイプラインエージェント間で状態を共有するためのコンテキストモデル。"""

    user_input: UserInput  # ユーザーからの刺激入力
    emotion: Optional[Emotion] = None  # エージェント1が導出した感情
    original_message: str = ""  # エージェント1が導出した元のメッセージ
    emotion_category: str = ""  # エージェント2が分類した喜怒哀楽カテゴリ
    modified_message: str = ""  # エージェント3が生成した最終メッセージ
    is_learned_response: bool = False  # 学習データに基づいた応答かどうか
    metadata: Dict[str, Any] = {}  # 追加のメタデータ


class DeviceStatus(BaseModel):
    """デバイスの状態を表すモデル。"""
    
    device_state: str  # "connected", "disconnected", "connecting" など
