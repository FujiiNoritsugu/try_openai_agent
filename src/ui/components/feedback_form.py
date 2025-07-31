"""
フィードバックフォームコンポーネント。
"""

import json
import streamlit as st
from typing import Dict, Any

from ...models.data_models import UserInput, Emotion
from ...models.feedback_models import UserFeedback
from ...learning.feedback_collector import FeedbackCollector
from ...learning.emotion_learner import EmotionLearner


def collect_feedback(
    user_input: UserInput, emotion: Emotion, results: Dict[str, Any]
) -> None:
    """ユーザーからのフィードバックを収集する"""
    st.subheader("フィードバック")
    st.write("この感情応答の正確さを評価してください:")

    col1, col2 = st.columns([3, 2])

    with col1:
        accuracy_rating = st.slider(
            "正確さ評価",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
            help="1: 全く正確でない, 5: 非常に正確",
        )

        comments = st.text_area(
            "コメント (任意)",
            placeholder="この感情応答についてのコメントを入力してください...",
        )

    with col2:
        st.write("期待する感情値 (任意):")
        expected_joy = st.slider(
            "喜び", min_value=0, max_value=5, value=emotion.joy, step=1
        )
        expected_fun = st.slider(
            "楽しさ", min_value=0, max_value=5, value=emotion.fun, step=1
        )
        expected_anger = st.slider(
            "怒り", min_value=0, max_value=5, value=emotion.anger, step=1
        )
        expected_sad = st.slider(
            "悲しみ", min_value=0, max_value=5, value=emotion.sad, step=1
        )

    if st.button("フィードバックを送信"):
        feedback = UserFeedback(
            user_input=user_input,
            generated_emotion=emotion,
            accuracy_rating=accuracy_rating,
            expected_emotion={
                "joy": expected_joy,
                "fun": expected_fun,
                "anger": expected_anger,
                "sad": expected_sad,
            },
            comments=comments if comments else None,
        )

        feedback_collector = FeedbackCollector()
        feedback_collector.add_feedback(feedback)

        emotion_learner = EmotionLearner(feedback_collector)
        emotion_learner.update_patterns()

        st.success("フィードバックが送信されました。ありがとうございます！")

        if st.checkbox("学習パターンを表示"):
            st.json(
                json.loads(
                    json.dumps(
                        emotion_learner.learning_data.emotion_patterns,
                        default=lambda o: (
                            o.model_dump() if hasattr(o, "model_dump") else str(o)
                        ),
                    )
                )
            )
