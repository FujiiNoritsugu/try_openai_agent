"""
学習データページ。
"""

import streamlit as st

from ...learning.feedback_collector import FeedbackCollector
from ...learning.emotion_learner import EmotionLearner


def display_learning_page() -> None:
    """学習データページを表示する"""
    st.header("学習データ")

    st.markdown(
        """
    このページでは、システムが収集したフィードバックと学習したパターンを確認できます。
    ユーザーからのフィードバックに基づいて、システムは刺激と感情の関係を学習します。
    """
    )

    display_learning_stats()
    display_recent_feedback()
    display_learning_patterns()


def display_learning_stats() -> None:
    """学習データの統計を表示する"""
    feedback_collector = FeedbackCollector()
    emotion_learner = EmotionLearner(feedback_collector)

    st.subheader("学習データの統計")

    feedback_count = len(feedback_collector.learning_data.feedback_history)
    st.write(f"収集されたフィードバック: **{feedback_count}**")

    pattern_count = len(emotion_learner.learning_data.emotion_patterns)
    st.write(f"学習されたパターン: **{pattern_count}**")

    if pattern_count > 0:
        area_patterns = {}
        for pattern in emotion_learner.learning_data.emotion_patterns:
            area = pattern.touched_area
            if area not in area_patterns:
                area_patterns[area] = 0
            area_patterns[area] += 1

        st.write("部位ごとのパターン数:")
        for area, count in area_patterns.items():
            st.write(f"- {area}: {count}")

        if emotion_learner.learning_data.emotion_patterns:
            most_confident = max(
                emotion_learner.learning_data.emotion_patterns,
                key=lambda p: p.confidence,
            )
            st.write(
                f"最も信頼度の高いパターン: **{most_confident.touched_area}** (信頼度: {most_confident.confidence:.2f})"
            )


def display_recent_feedback() -> None:
    """最近のフィードバックを表示する"""
    st.subheader("最近のフィードバック")
    feedback_collector = FeedbackCollector()
    recent_feedback = feedback_collector.get_recent_feedback(5)

    if recent_feedback:
        for i, feedback in enumerate(recent_feedback):
            with st.expander(
                f"フィードバック {i+1} ({feedback.timestamp.strftime('%Y-%m-%d %H:%M')})"
            ):
                st.write(f"部位: {feedback.user_input.touched_area}")
                st.write(f"刺激の強さ: {feedback.user_input.data}")
                st.write(f"正確さ評価: {feedback.accuracy_rating}/5")

                st.write("生成された感情:")
                st.json(feedback.generated_emotion.model_dump())

                if feedback.expected_emotion:
                    st.write("期待された感情:")
                    st.json(feedback.expected_emotion)

                if feedback.comments:
                    st.write(f"コメント: {feedback.comments}")
    else:
        st.info(
            "まだフィードバックがありません。感情分析ページでフィードバックを提供してください。"
        )


def display_learning_patterns() -> None:
    """学習されたパターンを表示する"""
    st.subheader("学習されたパターン")
    feedback_collector = FeedbackCollector()
    emotion_learner = EmotionLearner(feedback_collector)

    if emotion_learner.learning_data.emotion_patterns:
        for i, pattern in enumerate(emotion_learner.learning_data.emotion_patterns):
            with st.expander(
                f"パターン {i+1} ({pattern.touched_area}, 強さ: {pattern.stimulus_intensity:.1f})"
            ):
                st.write(f"部位: {pattern.touched_area}")
                st.write(f"刺激の強さ: {pattern.stimulus_intensity:.2f}")
                st.write(f"信頼度: {pattern.confidence:.2f}")
                st.write(f"サンプル数: {pattern.sample_count}")

                st.write("感情値:")
                st.json(pattern.emotion_values)
    else:
        st.info(
            "まだ学習パターンがありません。感情分析ページでフィードバックを提供してください。"
        )
