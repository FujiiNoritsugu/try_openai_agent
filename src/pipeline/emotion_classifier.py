"""
感情分類ロジック。
"""

import json
from typing import Tuple
from agents import Runner

from ..models.data_models import PipelineContext, HandoffOutput, Emotion
from ..agents.factory import agent_factory


class EmotionClassifier:
    """感情分類を担当するクラス"""

    def __init__(self):
        self.agent_factory = agent_factory

    async def classify_emotion(
        self, emotion: Emotion, gender: str, context: PipelineContext
    ) -> Tuple[str, str]:
        """
        感情を分類し、適切なエージェントにハンドオフする。

        Args:
            emotion: 感情データ
            gender: 性別
            context: パイプラインコンテキスト

        Returns:
            (感情カテゴリ, 最終メッセージ)のタプル
        """
        # 性別対応のハンドオフエージェントを作成
        emotion_handoffs = []
        for agent_type in ["joy", "anger", "sorrow", "pleasure"]:
            agent = self.agent_factory.create_emotion_agent_with_gender(
                agent_type, gender
            )
            emotion_handoffs.append(agent)

        # 分類エージェントを作成
        classification_agent = self.agent_factory.create_classifier_agent(
            emotion_handoffs
        )

        # エージェントを実行
        result = await Runner.run(
            classification_agent,
            input=json.dumps(emotion.model_dump()),
            context=context,
        )

        handoff_output: HandoffOutput = result.final_output
        return handoff_output.emotion_category, handoff_output.message
