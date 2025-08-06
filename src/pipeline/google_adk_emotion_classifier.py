"""
Google ADKを使用した感情分類ロジック。
"""

import json
from typing import Tuple
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from ..models.data_models import PipelineContext, HandoffOutput, Emotion
from ..agents.google_adk_factory import agent_factory


class EmotionClassifier:
    """Google ADKを使用した感情分類を担当するクラス"""

    def __init__(self):
        self.agent_factory = agent_factory
        self.session_service = InMemorySessionService()

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
        # 分類エージェントを作成（サブエージェントを含む）
        classification_agent = self.agent_factory.create_classifier_agent()

        # Google ADKのRunnerを使用してエージェントを実行
        runner = Runner(
            agent=classification_agent,
            session_service=self.session_service
        )
        
        # 感情データと性別を含む入力を準備
        input_data = {
            "emotion": emotion.model_dump(),
            "gender": gender
        }
        
        # エージェントを実行
        result = await runner.run(json.dumps(input_data))
        
        # 結果を解析
        try:
            result_data = json.loads(result.output)
            emotion_category = result_data.get("emotion_category", "")
            
            # 感情カテゴリに基づいて適切なエージェントに処理を委譲
            # Google ADKのsub_agentsが自動的にルーティングを処理
            if emotion_category:
                # サブエージェントの応答を取得
                final_message = result_data.get("message", "")
            else:
                final_message = "感情の分類に失敗しました。"
                
            return emotion_category, final_message
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing classification result: {e}")
            return "", "感情の分類中にエラーが発生しました。"