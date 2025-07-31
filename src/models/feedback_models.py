"""
Feedback and learning data models for the OpenAI agent pipeline.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4, UUID

from .data_models import UserInput, Emotion


class UserFeedback(BaseModel):
    """User feedback on emotion responses."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_input: UserInput
    generated_emotion: Emotion
    accuracy_rating: int = Field(ge=1, le=5)  # 1-5 scale
    expected_emotion: Optional[Dict[str, int]] = None
    comments: Optional[str] = None


class EmotionPattern(BaseModel):
    """Learned pattern connecting stimulus to emotion."""

    touched_area: str
    stimulus_intensity: float
    emotion_values: Dict[str, float]
    confidence: float = 0.5  # How confident we are in this pattern
    sample_count: int = 1  # Number of samples this pattern is based on


class LearningData(BaseModel):
    """Collection of feedback and learned patterns."""

    feedback_history: List[UserFeedback] = []
    emotion_patterns: List[EmotionPattern] = []
    last_updated: datetime = Field(default_factory=datetime.now)
