"""
OpenAIエージェントパイプラインの実行ロジック。
"""

from typing import Dict, Any, Optional, Tuple

from ..models.data_models import UserInput, PipelineContext
from ..learning.emotion_learner import EmotionLearner
from .emotion_processor import EmotionProcessor
from .emotion_classifier import EmotionClassifier
from .error_handler import handle_pipeline_error, log_error


class EmotionPipeline:
    """感情分析パイプライン"""

    def __init__(self):
        self.emotion_processor = EmotionProcessor()
        self.emotion_classifier = EmotionClassifier()

    @handle_pipeline_error
    async def run(
        self, user_input: UserInput, emotion_learner: Optional[EmotionLearner] = None
    ) -> PipelineContext:
        """
        感情分析パイプラインを実行する。

        Args:
            user_input: ユーザー入力
            emotion_learner: オプションの感情学習器

        Returns:
            パイプラインコンテキスト
        """
        ctx = PipelineContext(user_input=user_input)

        # 学習済み感情の取得を試みる
        if emotion_learner:
            learned_emotion = emotion_learner.predict_emotion(user_input)
            if learned_emotion:
                emotion, message, is_learned = (
                    self.emotion_processor.use_learned_emotion(learned_emotion)
                )
                ctx.emotion = emotion
                ctx.original_message = message
                ctx.is_learned_response = is_learned
            else:
                # 学習データがない場合は通常の処理
                await self._process_emotion(user_input, ctx)
        else:
            # 学習器がない場合は通常の処理
            await self._process_emotion(user_input, ctx)

        # 感情を分類する
        emotion_category, final_message = (
            await self.emotion_classifier.classify_emotion(
                ctx.emotion, user_input.gender, ctx
            )
        )

        ctx.emotion_category = emotion_category
        ctx.modified_message = final_message

        return ctx

    async def _process_emotion(
        self, user_input: UserInput, ctx: PipelineContext
    ) -> None:
        """感情を処理する内部メソッド"""
        emotion, message, is_learned = await self.emotion_processor.extract_emotion(
            user_input, ctx
        )
        ctx.emotion = emotion
        ctx.original_message = message
        ctx.is_learned_response = is_learned


# グローバルパイプラインインスタンス
_pipeline = EmotionPipeline()


async def run_pipeline(
    user_input: UserInput, emotion_learner: Optional[EmotionLearner] = None
) -> Tuple[Optional[PipelineContext], Optional[Exception]]:
    """
    感情分析パイプラインを実行する（後方互換性のため）。

    Args:
        user_input: ユーザー入力
        emotion_learner: オプションの感情学習器

    Returns:
        (コンテキスト, エラー)のタプル
    """
    try:
        ctx = await _pipeline.run(user_input, emotion_learner)
        return ctx, None
    except Exception as e:
        log_error(e, "run_pipeline")
        return None, e


def format_pipeline_results(ctx: Optional[PipelineContext]) -> Dict[str, Any]:
    """
    パイプラインの結果を表示用にフォーマットする。

    Args:
        ctx: 結果を含むパイプラインコンテキスト。

    Returns:
        フォーマットされた結果の辞書。
    """
    if not ctx:
        return {}

    return {
        "extracted_emotion": ctx.emotion.model_dump() if ctx.emotion else None,
        "original_message": ctx.original_message,
        "emotion_category": ctx.emotion_category,
        "final_message": ctx.modified_message,
        "is_learned_response": getattr(ctx, "is_learned_response", False),
    }
