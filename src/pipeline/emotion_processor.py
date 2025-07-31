"""
感情処理ロジック。
"""

import json
from typing import Optional, Tuple
from agents import Runner, Agent

from ..models.data_models import UserInput, PipelineContext, OriginalOutput, Emotion
from ..agents.factory import agent_factory


class EmotionProcessor:
    """感情処理を担当するクラス"""

    def __init__(self):
        self.agent_factory = agent_factory

    async def extract_emotion(
        self, user_input: UserInput, context: PipelineContext
    ) -> Tuple[Optional[Emotion], Optional[str], bool]:
        """
        ユーザー入力から感情を抽出する。

        Args:
            user_input: ユーザー入力
            context: パイプラインコンテキスト

        Returns:
            (感情データ, メッセージ, 学習応答フラグ)のタプル
        """
        gender = user_input.gender

        # 感情抽出エージェントを性別対応で作成
        emotion_agent = self.agent_factory.create_emotion_agent_with_gender(
            "emotion_extractor", gender
        )

        # エージェントを実行
        result = await Runner.run(
            emotion_agent, json.dumps(user_input.model_dump()), context=context
        )

        final_output: OriginalOutput = result.final_output
        return final_output.emotion, final_output.message, False

    def use_learned_emotion(
        self, learned_emotion: Emotion
    ) -> Tuple[Emotion, str, bool]:
        """
        学習済み感情を使用する。

        Args:
            learned_emotion: 学習済み感情データ

        Returns:
            (感情データ, メッセージ, 学習応答フラグ)のタプル
        """
        message = "学習データに基づいた感情応答です。"
        return learned_emotion, message, True
