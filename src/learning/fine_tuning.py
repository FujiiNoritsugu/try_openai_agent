"""
OpenAI fine-tuning integration for the emotion agent pipeline.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
import openai

from ..models.feedback_models import UserFeedback


class FineTuningManager:
    """Manages fine-tuning of OpenAI models for emotion responses."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the fine-tuning manager.

        Args:
            model_name: The base model to fine-tune.
        """
        self.model_name = model_name
        self.training_file_id = None
        self.fine_tuned_model = None

        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")

    def prepare_training_data(
        self, feedback_history: List[UserFeedback], output_path: str
    ) -> str:
        """
        Prepare training data for fine-tuning.

        Args:
            feedback_history: The feedback history to use for training.
            output_path: Path to save the training data.

        Returns:
            The path to the prepared training data.
        """
        high_quality_feedback = [f for f in feedback_history if f.accuracy_rating >= 4]

        if not high_quality_feedback:
            raise ValueError("No high-quality feedback available for training")

        training_examples = []

        for feedback in high_quality_feedback:
            system_message = {
                "role": "system",
                "content": "あなたは感情を持つチャットボットです。ユーザーからの刺激に対して適切な感情パラメータと応答を生成してください。",
            }

            user_message = {
                "role": "user",
                "content": f"刺激の強さ: {feedback.user_input.data}, 触れられた部位: {feedback.user_input.touched_area}",
            }

            emotion = feedback.generated_emotion
            assistant_content = json.dumps(
                {
                    "emotion": {
                        "joy": emotion.joy,
                        "fun": emotion.fun,
                        "anger": emotion.anger,
                        "sad": emotion.sad,
                    },
                    "message": feedback.comments or "適切な感情応答です。",
                },
                ensure_ascii=False,
            )

            assistant_message = {"role": "assistant", "content": assistant_content}

            training_example = {
                "messages": [system_message, user_message, assistant_message]
            }

            training_examples.append(training_example)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for example in training_examples:
                f.write(json.dumps(example, ensure_ascii=False) + "\n")

        return output_path

    def upload_training_file(self, file_path: str) -> str:
        """
        Upload a training file to OpenAI.

        Args:
            file_path: Path to the training file.

        Returns:
            The ID of the uploaded file.
        """
        try:
            with open(file_path, "rb") as f:
                response = openai.files.create(file=f, purpose="fine-tune")

            self.training_file_id = response.id
            return response.id
        except Exception as e:
            raise ValueError(f"Failed to upload training file: {e}")

    def create_fine_tuning_job(self, training_file_id: str) -> str:
        """
        Create a fine-tuning job.

        Args:
            training_file_id: The ID of the training file.

        Returns:
            The ID of the fine-tuning job.
        """
        try:
            response = openai.fine_tuning.jobs.create(
                training_file=training_file_id,
                model=self.model_name,
                suffix="emotion-agent",
            )

            return response.id
        except Exception as e:
            raise ValueError(f"Failed to create fine-tuning job: {e}")

    def check_fine_tuning_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a fine-tuning job.

        Args:
            job_id: The ID of the fine-tuning job.

        Returns:
            The status of the fine-tuning job.
        """
        try:
            response = openai.fine_tuning.jobs.retrieve(job_id)
            return {
                "status": response.status,
                "fine_tuned_model": response.fine_tuned_model,
                "created_at": response.created_at,
                "finished_at": response.finished_at,
                "error": response.error,
            }
        except Exception as e:
            raise ValueError(f"Failed to check fine-tuning status: {e}")

    def wait_for_fine_tuning(
        self, job_id: str, timeout_seconds: int = 3600
    ) -> Optional[str]:
        """
        Wait for a fine-tuning job to complete.

        Args:
            job_id: The ID of the fine-tuning job.
            timeout_seconds: Maximum time to wait in seconds.

        Returns:
            The fine-tuned model ID or None if the job failed or timed out.
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            status = self.check_fine_tuning_status(job_id)

            if status["status"] == "succeeded":
                self.fine_tuned_model = status["fine_tuned_model"]
                return status["fine_tuned_model"]

            if status["status"] in ["failed", "cancelled"]:
                print(f"Fine-tuning failed: {status['error']}")
                return None

            time.sleep(60)

        print("Fine-tuning timed out")
        return None

    def get_fine_tuned_model(self) -> Optional[str]:
        """
        Get the fine-tuned model ID.

        Returns:
            The fine-tuned model ID or None if no model has been fine-tuned.
        """
        return self.fine_tuned_model
