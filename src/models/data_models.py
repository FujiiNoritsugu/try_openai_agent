"""
Data models for the OpenAI agent pipeline.
"""
from pydantic import BaseModel
from typing import Optional


class Emotion(BaseModel):
    """Emotion parameters model with joy, fun, anger, and sad values."""
    joy: int
    fun: int
    anger: int
    sad: int


class UserInput(BaseModel):
    """User input model with data and touched area."""
    data: str
    touched_area: str


class OriginalOutput(BaseModel):
    """Output model for the emotion extraction agent."""
    emotion: Emotion
    message: str


class HandoffOutput(BaseModel):
    """Output model for emotion category agents."""
    emotion_category: str
    message: str


class PipelineContext(BaseModel):
    """Context model for sharing state between pipeline agents."""
    user_input: UserInput  # ユーザーからの刺激入力
    emotion: Optional[Emotion] = None  # エージェント1が導出した感情
    original_message: str = ""  # エージェント1が導出した元のメッセージ
    emotion_category: str = ""  # エージェント2が分類した喜怒哀楽カテゴリ
    modified_message: str = ""  # エージェント3が生成した最終メッセージ
