"""
Feedback collection module for the OpenAI agent pipeline.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models.feedback_models import UserFeedback, LearningData
from ..models.data_models import UserInput, Emotion, PipelineContext


class FeedbackCollector:
    """Collects and stores user feedback on emotion responses."""
    
    def __init__(self, data_path: str = "data/feedback"):
        """
        Initialize the feedback collector.
        
        Args:
            data_path: Path to store feedback data.
        """
        self.data_path = data_path
        self.ensure_data_directory()
        self.learning_data = self.load_learning_data()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs(self.data_path, exist_ok=True)
    
    def load_learning_data(self) -> LearningData:
        """
        Load learning data from disk.
        
        Returns:
            The loaded learning data or a new instance if none exists.
        """
        learning_data_path = os.path.join(self.data_path, "learning_data.json")
        
        if os.path.exists(learning_data_path):
            try:
                with open(learning_data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return LearningData.model_validate(data)
            except Exception as e:
                print(f"Error loading learning data: {e}")
                return LearningData()
        else:
            return LearningData()
    
    def save_learning_data(self):
        """Save learning data to disk."""
        learning_data_path = os.path.join(self.data_path, "learning_data.json")
        
        self.learning_data.last_updated = datetime.now()
        
        with open(learning_data_path, "w", encoding="utf-8") as f:
            data_dict = self.learning_data.model_dump()
            json.dump(data_dict, f, default=self._json_serializer, indent=2)
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def add_feedback(self, feedback: UserFeedback):
        """
        Add user feedback to the learning data.
        
        Args:
            feedback: The user feedback to add.
        """
        self.learning_data.feedback_history.append(feedback)
        self.save_learning_data()
    
    def get_feedback_history(self) -> List[UserFeedback]:
        """
        Get the feedback history.
        
        Returns:
            The feedback history.
        """
        return self.learning_data.feedback_history
    
    def get_recent_feedback(self, limit: int = 10) -> List[UserFeedback]:
        """
        Get the most recent feedback.
        
        Args:
            limit: Maximum number of feedback items to return.
            
        Returns:
            The most recent feedback items.
        """
        sorted_feedback = sorted(
            self.learning_data.feedback_history,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_feedback[:limit]
