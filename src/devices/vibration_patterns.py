"""
Vibration patterns for haptic feedback device.

This module defines the vibration patterns for different emotion categories
and provides a generator to create appropriate patterns based on emotion data.
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json

from ..models.data_models import Emotion


@dataclass
class VibrationStep:
    """A single step in a vibration pattern."""
    intensity: float  # 0.0-1.0 vibration intensity
    duration: int     # Duration in milliseconds


@dataclass
class VibrationPattern:
    """
    Represents a vibration pattern with sequence of intensity and duration.
    
    Attributes:
        steps: List of vibration steps (intensity and duration pairs)
        interval: Time between vibrations in milliseconds
        repetitions: Number of times to repeat the pattern
    """
    steps: List[VibrationStep]
    interval: int  # Interval between vibrations in milliseconds
    repetitions: int  # Number of times to repeat the pattern
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the pattern to a dictionary for serialization."""
        return {
            "steps": [{"intensity": step.intensity, "duration": step.duration} 
                     for step in self.steps],
            "interval": self.interval,
            "repetitions": self.repetitions
        }
    
    def to_json(self) -> str:
        """Convert the pattern to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VibrationPattern':
        """Create a VibrationPattern from a dictionary."""
        steps = [VibrationStep(step["intensity"], step["duration"]) 
                for step in data["steps"]]
        return cls(
            steps=steps,
            interval=data["interval"],
            repetitions=data["repetitions"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VibrationPattern':
        """Create a VibrationPattern from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class EmotionVibrationPatterns:
    """
    Defines vibration patterns for different emotion categories.
    
    Each emotion category (joy, anger, sorrow, pleasure) has base patterns
    that are adjusted based on the intensity of the emotion.
    """
    
    @staticmethod
    def joy_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        Generate a joy vibration pattern.
        
        Joy is represented by rhythmic, light vibrations that are upbeat and positive.
        
        Args:
            intensity_level: Emotion intensity from 0-5
            
        Returns:
            A VibrationPattern for joy emotion
        """
        base_intensity = 0.6
        base_duration = 200  # ms
        base_interval = 100  # ms
        base_repetitions = 3
        
        if intensity_level >= 4:  # High intensity
            intensity = base_intensity + 0.2
            repetitions = 5
        elif intensity_level <= 1:  # Low intensity
            intensity = base_intensity - 0.2
            repetitions = 2
        else:  # Medium intensity
            intensity = base_intensity
            repetitions = base_repetitions
            
        steps = [
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1, base_duration),
            VibrationStep(intensity, base_duration)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=repetitions
        )
    
    @staticmethod
    def anger_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        Generate an anger vibration pattern.
        
        Anger is represented by strong, short, rapid vibrations that convey tension and intensity.
        
        Args:
            intensity_level: Emotion intensity from 0-5
            
        Returns:
            A VibrationPattern for anger emotion
        """
        base_intensity = 0.9
        base_duration = 100  # ms
        base_interval = 50   # ms
        base_repetitions = 4
        
        if intensity_level >= 4:  # High intensity
            intensity = 1.0
            interval = 30  # ms
        elif intensity_level <= 1:  # Low intensity
            intensity = 0.7
            interval = 80  # ms
        else:  # Medium intensity
            intensity = base_intensity
            interval = base_interval
            
        steps = [
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1 if intensity < 1.0 else 1.0, base_duration - 20),
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1 if intensity < 1.0 else 1.0, base_duration - 20)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=interval,
            repetitions=base_repetitions
        )
    
    @staticmethod
    def sorrow_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        Generate a sorrow vibration pattern.
        
        Sorrow is represented by weak, slow, prolonged vibrations that convey quietness and introspection.
        
        Args:
            intensity_level: Emotion intensity from 0-5
            
        Returns:
            A VibrationPattern for sorrow emotion
        """
        base_intensity = 0.4
        base_duration = 500  # ms
        base_interval = 300  # ms
        base_repetitions = 2
        
        if intensity_level >= 4:  # High intensity
            duration = 700  # ms
            interval = 200  # ms
        elif intensity_level <= 1:  # Low intensity
            intensity = 0.2
            duration = 300  # ms
        else:  # Medium intensity
            intensity = base_intensity
            duration = base_duration
            interval = base_interval
            
        steps = [
            VibrationStep(base_intensity, duration),
            VibrationStep(base_intensity - 0.1, duration + 100)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=base_repetitions
        )
    
    @staticmethod
    def pleasure_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        Generate a pleasure vibration pattern.
        
        Pleasure is represented by medium-strength, melodic vibration patterns that convey relaxation and enjoyment.
        
        Args:
            intensity_level: Emotion intensity from 0-5
            
        Returns:
            A VibrationPattern for pleasure emotion
        """
        base_intensity = 0.5
        base_repetitions = 3
        base_interval = 150  # ms
        
        if intensity_level >= 4:  # High intensity
            max_intensity = 0.7
        elif intensity_level <= 1:  # Low intensity
            max_intensity = 0.5
        else:  # Medium intensity
            max_intensity = 0.6
            
        steps = [
            VibrationStep(base_intensity - 0.1, 250),
            VibrationStep(base_intensity, 300),
            VibrationStep(max_intensity, 350),
            VibrationStep(base_intensity, 300),
            VibrationStep(base_intensity - 0.1, 250)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=base_repetitions
        )


class VibrationPatternGenerator:
    """
    Generates appropriate vibration patterns based on emotion data.
    
    This class analyzes emotion data and creates vibration patterns
    that best represent the emotional state, including handling
    mixed emotions.
    """
    
    @staticmethod
    def get_dominant_emotions(emotion: Emotion, threshold: int = 2) -> List[Tuple[str, int]]:
        """
        Identify dominant emotions from the emotion data.
        
        Args:
            emotion: Emotion object with joy, fun, anger, and sad values
            threshold: Minimum value to consider an emotion as significant
            
        Returns:
            List of (emotion_name, intensity) tuples, sorted by intensity
        """
        emotion_values = [
            ("joy", emotion.joy),
            ("fun", emotion.fun),
            ("anger", emotion.anger),
            ("sad", emotion.sad)
        ]
        
        dominant = [(name, value) for name, value in emotion_values if value >= threshold]
        return sorted(dominant, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def map_emotion_to_category(emotion_name: str) -> str:
        """
        Map emotion parameter names to emotion categories.
        
        Args:
            emotion_name: Name of the emotion parameter
            
        Returns:
            Emotion category name
        """
        mapping = {
            "joy": "joy",      # 喜
            "fun": "pleasure", # 楽
            "anger": "anger",  # 怒
            "sad": "sorrow"    # 哀
        }
        return mapping.get(emotion_name, "joy")  # Default to joy if unknown
    
    @staticmethod
    def generate_pattern(emotion: Emotion, emotion_category: Optional[str] = None) -> VibrationPattern:
        """
        Generate a vibration pattern based on emotion data and category.
        
        Args:
            emotion: Emotion object with joy, fun, anger, and sad values
            emotion_category: Optional category override (joy, anger, sorrow, pleasure)
            
        Returns:
            A VibrationPattern representing the emotional state
        """
        if emotion_category:
            category = emotion_category.lower()
            
            category_mapping = {
                "喜": "joy",
                "怒": "anger",
                "哀": "sorrow",
                "楽": "pleasure"
            }
            
            if category in category_mapping:
                category = category_mapping[category]
                
            if category == "joy":
                intensity_level = emotion.joy
            elif category == "anger":
                intensity_level = emotion.anger
            elif category == "sorrow":
                intensity_level = emotion.sad
            elif category == "pleasure":
                intensity_level = emotion.fun
            else:
                intensity_level = (emotion.joy + emotion.fun + emotion.anger + emotion.sad) // 4
                
            if category == "joy":
                return EmotionVibrationPatterns.joy_pattern(intensity_level)
            elif category == "anger":
                return EmotionVibrationPatterns.anger_pattern(intensity_level)
            elif category == "sorrow":
                return EmotionVibrationPatterns.sorrow_pattern(intensity_level)
            elif category == "pleasure":
                return EmotionVibrationPatterns.pleasure_pattern(intensity_level)
            else:
                return EmotionVibrationPatterns.joy_pattern(intensity_level)
        
        dominant_emotions = VibrationPatternGenerator.get_dominant_emotions(emotion)
        
        if not dominant_emotions:
            return VibrationPattern(
                steps=[VibrationStep(0.3, 300)],
                interval=200,
                repetitions=1
            )
            
        primary_emotion, primary_intensity = dominant_emotions[0]
        primary_category = VibrationPatternGenerator.map_emotion_to_category(primary_emotion)
        
        if primary_category == "joy":
            return EmotionVibrationPatterns.joy_pattern(primary_intensity)
        elif primary_category == "anger":
            return EmotionVibrationPatterns.anger_pattern(primary_intensity)
        elif primary_category == "sorrow":
            return EmotionVibrationPatterns.sorrow_pattern(primary_intensity)
        elif primary_category == "pleasure":
            return EmotionVibrationPatterns.pleasure_pattern(primary_intensity)
        else:
            return EmotionVibrationPatterns.joy_pattern(primary_intensity)
