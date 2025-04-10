"""
Learning module for the OpenAI agent pipeline.
"""
import json
import os
import numpy as np
from typing import Dict, List, Optional, Tuple

from ..models.feedback_models import UserFeedback, EmotionPattern, LearningData
from ..models.data_models import UserInput, Emotion


class EmotionLearner:
    """Learns emotion patterns from user feedback."""
    
    def __init__(self, feedback_collector):
        """
        Initialize the emotion learner.
        
        Args:
            feedback_collector: The feedback collector to use.
        """
        self.feedback_collector = feedback_collector
        self.learning_data = feedback_collector.learning_data
    
    def update_patterns(self):
        """Update emotion patterns based on feedback history."""
        area_feedback = {}
        
        for feedback in self.learning_data.feedback_history:
            area = feedback.user_input.touched_area
            if area not in area_feedback:
                area_feedback[area] = []
            area_feedback[area].append(feedback)
        
        new_patterns = []
        for area, feedbacks in area_feedback.items():
            intensity_groups = self._group_by_intensity(feedbacks)
            
            for intensity_range, group_feedbacks in intensity_groups.items():
                pattern = self._create_pattern(area, intensity_range, group_feedbacks)
                new_patterns.append(pattern)
        
        self.learning_data.emotion_patterns = new_patterns
        self.feedback_collector.save_learning_data()
    
    def _group_by_intensity(self, feedbacks: List[UserFeedback]) -> Dict[Tuple[float, float], List[UserFeedback]]:
        """
        Group feedback by stimulus intensity ranges.
        
        Args:
            feedbacks: List of feedback items.
            
        Returns:
            Dictionary mapping intensity ranges to feedback lists.
        """
        groups = {}
        ranges = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
        
        for feedback in feedbacks:
            intensity = float(feedback.user_input.data)
            
            for r in ranges:
                if r[0] <= intensity < r[1] or (r[1] == 1.0 and intensity == 1.0):
                    if r not in groups:
                        groups[r] = []
                    groups[r].append(feedback)
                    break
        
        return groups
    
    def _create_pattern(self, area: str, intensity_range: Tuple[float, float], feedbacks: List[UserFeedback]) -> EmotionPattern:
        """
        Create an emotion pattern from feedback.
        
        Args:
            area: The touched area.
            intensity_range: The stimulus intensity range.
            feedbacks: List of feedback items.
            
        Returns:
            The created emotion pattern.
        """
        avg_intensity = sum(float(f.user_input.data) for f in feedbacks) / len(feedbacks)
        
        emotion_sums = {"joy": 0, "fun": 0, "anger": 0, "sad": 0}
        for feedback in feedbacks:
            emotion = feedback.generated_emotion
            emotion_sums["joy"] += emotion.joy
            emotion_sums["fun"] += emotion.fun
            emotion_sums["anger"] += emotion.anger
            emotion_sums["sad"] += emotion.sad
        
        emotion_avgs = {k: v / len(feedbacks) for k, v in emotion_sums.items()}
        
        sample_count = len(feedbacks)
        rating_variance = np.var([f.accuracy_rating for f in feedbacks]) if sample_count > 1 else 0
        confidence = min(0.5 + (sample_count / 20), 0.9)  # Max confidence of 0.9
        
        if rating_variance > 0:
            confidence = max(confidence - (rating_variance / 10), 0.1)  # Min confidence of 0.1
        
        return EmotionPattern(
            touched_area=area,
            stimulus_intensity=avg_intensity,
            emotion_values=emotion_avgs,
            confidence=confidence,
            sample_count=sample_count
        )
    
    def predict_emotion(self, user_input: UserInput) -> Optional[Emotion]:
        """
        Predict emotion based on learned patterns.
        
        Args:
            user_input: The user input.
            
        Returns:
            The predicted emotion or None if no suitable pattern is found.
        """
        if not self.learning_data.emotion_patterns:
            return None
        
        area = user_input.touched_area
        intensity = float(user_input.data)
        
        area_patterns = [p for p in self.learning_data.emotion_patterns if p.touched_area == area]
        if not area_patterns:
            return None
        
        closest_pattern = min(area_patterns, key=lambda p: abs(p.stimulus_intensity - intensity))
        
        if abs(closest_pattern.stimulus_intensity - intensity) > 0.2:
            return None
        
        emotion_values = closest_pattern.emotion_values
        return Emotion(
            joy=round(emotion_values["joy"]),
            fun=round(emotion_values["fun"]),
            anger=round(emotion_values["anger"]),
            sad=round(emotion_values["sad"])
        )
