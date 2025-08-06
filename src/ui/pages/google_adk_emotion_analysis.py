"""
Google ADKを使用した感情分析ページ。
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple

from ...models.data_models import UserInput, Emotion
from ...pipeline.google_adk_pipeline import run_pipeline, format_pipeline_results
from ...learning.feedback_collector import FeedbackCollector
from ...learning.emotion_learner import EmotionLearner
from ...devices.pipeline_integration import haptic_feedback
from ..components import (
    clickable_body_part_selector,
    display_emotion_visualization,
    collect_feedback,
)
from ..utils.async_utils import run_async


def display_analysis_page() -> None:
    """感情分析ページを表示する"""
    st.markdown(
        """
    このアプリケーションは、ユーザー入力（刺激の強さと触れられた部位）から感情を抽出・分類し、
    適切な感情応答を生成します。フィードバックを提供することで、システムの学習を支援できます。
    触覚フィードバックデバイスが接続されている場合は、感情に応じた振動パターンが送信されます。
    """
    )

    st.header("入力")

    data_value = st.slider(
        "刺激の強さ",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="0.0: 何も感じない, 0.5: 最も気持ちいい, 1.0: 痛みを感じる",
    )

    gender = st.radio(
        "性別",
        options=["男性", "女性", "その他"],
        index=0,
        horizontal=True,
        help="システムが回答する際の性別を選択します",
    )

    touched_area = clickable_body_part_selector()

    use_learning = st.checkbox(
        "学習データを使用",
        value=True,
        help="チェックすると、過去のフィードバックに基づいた学習データを使用します",
    )

    use_haptic_feedback = st.checkbox(
        "触覚フィードバックを使用",
        value=True,
        help="チェックすると、感情分析結果を触覚フィードバックデバイスに送信します",
    )

    if st.button("感情を分析"):
        analyze_emotion(
            data_value, gender, touched_area, use_learning, use_haptic_feedback
        )


def analyze_emotion(
    data_value: float,
    gender: str,
    touched_area: str,
    use_learning: bool,
    use_haptic_feedback: bool,
) -> None:
    """感情分析を実行する"""
    with st.spinner("感情を分析中..."):
        user_input = UserInput(
            data=str(data_value), touched_area=touched_area, gender=gender
        )

        emotion_learner = None
        if use_learning:
            feedback_collector = FeedbackCollector()
            emotion_learner = EmotionLearner(feedback_collector)

        results, error = process_with_haptic_feedback(
            user_input, emotion_learner, use_haptic_feedback
        )

        if error:
            st.error(f"エラーが発生しました: {error}")
        elif results:
            display_results(results, user_input)


def process_with_haptic_feedback(
    user_input: UserInput,
    emotion_learner: Optional[EmotionLearner],
    use_haptic_feedback: bool,
) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
    """触覚フィードバックを含む処理を実行する"""
    if (
        use_haptic_feedback
        and "haptic_devices" in st.session_state
        and st.session_state.haptic_devices
    ):
        try:
            if (
                not hasattr(st.session_state, "haptic_initialized")
                or not st.session_state.haptic_initialized
            ):
                st.session_state.haptic_initialized = run_async(
                    haptic_feedback.initialize(st.session_state.haptic_devices)
                )

            if st.session_state.haptic_initialized:
                results, device_results = run_async(
                    haptic_feedback.run_pipeline_and_send(user_input, emotion_learner)
                )

                if device_results:
                    st.success("触覚フィードバックデバイスに振動パターンを送信しました")
                    for device_id, success in device_results.items():
                        if success:
                            st.info(f"デバイス '{device_id}' に正常に送信されました")
                        else:
                            st.warning(f"デバイス '{device_id}' への送信に失敗しました")

                return results, None
            else:
                st.warning(
                    "触覚フィードバックシステムの初期化に失敗しました。通常のパイプラインを使用します。"
                )
                ctx, error = run_async(run_pipeline(user_input, emotion_learner))
                results = format_pipeline_results(ctx) if not error else None
                return results, error
        except Exception as e:
            st.error(f"触覚フィードバック処理中にエラーが発生しました: {str(e)}")
            ctx, error = run_async(run_pipeline(user_input, emotion_learner))
            results = format_pipeline_results(ctx) if not error else None
            return results, error
    else:
        ctx, error = run_async(run_pipeline(user_input, emotion_learner))
        results = format_pipeline_results(ctx) if not error else None
        return results, error


def display_results(results: Dict[str, Any], user_input: UserInput) -> None:
    """分析結果を表示する"""
    st.header("結果")

    if results.get("is_learned_response", False):
        st.info("この応答は学習データに基づいています")

    st.subheader("抽出された感情")
    emotion_data = results["extracted_emotion"]
    st.json(emotion_data)

    display_emotion_visualization(emotion_data)

    st.subheader("元のメッセージ")
    st.write(results["original_message"])

    st.subheader("感情カテゴリ")
    st.write(results["emotion_category"])

    st.subheader("最終メッセージ")
    st.write(results["final_message"])

    if emotion_data:
        emotion = Emotion(**emotion_data)
        collect_feedback(user_input, emotion, results)