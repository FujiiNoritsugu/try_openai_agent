"""
OpenAIエージェントパイプライン用のデータモデル。
"""
from pydantic import BaseModel
from typing import Optional


class Emotion(BaseModel):
    """喜び、楽しさ、怒り、悲しみの値を持つ感情パラメータモデル。"""
    joy: int
    fun: int
    anger: int
    sad: int


class UserInput(BaseModel):
    """データと触れられた部位を持つユーザー入力モデル。"""
    data: str
    touched_area: str


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
