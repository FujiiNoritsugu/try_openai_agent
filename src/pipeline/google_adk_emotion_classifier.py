"""
Google ADKを使用した感情分類ロジック。
"""

import json
import uuid
from typing import Tuple
from google.adk import Runner
from google.genai import types

from ..models.data_models import PipelineContext, HandoffOutput, Emotion
from ..agents.google_adk_factory import agent_factory
from .google_adk_session_manager import session_manager


class EmotionClassifier:
    """Google ADKを使用した感情分類を担当するクラス"""

    def __init__(self):
        self.agent_factory = agent_factory
        self.session_service = session_manager.session_service
        self.session_counter = 0

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
            session_service=self.session_service,
            app_name="emotion_pipeline"
        )
        
        # 感情データと性別を含む入力を準備
        input_data = {
            "emotion": emotion.model_dump(),
            "gender": gender
        }
        
        # Google ADKの正しい形式でメッセージを作成
        message = types.Content(parts=[types.Part(text=json.dumps(input_data))])
        
        # Runnerを実行
        self.session_counter += 1
        session_id = f"classifier_session_{self.session_counter}"
        user_id = f"classifier_user_{gender}_{self.session_counter}"
        
        # セッションを事前に作成
        try:
            await self.session_service.create_session(
                session_id=session_id,
                user_id=user_id,
                app_name="emotion_pipeline"
            )
        except Exception as e:
            print(f"Session creation error: {e}")
            # 既存のセッションがある場合は続行
        
        events = list(runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ))
        
        # 最後のイベントから結果を取得
        result = None
        for event in events:
            if hasattr(event, 'output'):
                result = event
        
        # 結果を解析
        try:
            if result and hasattr(result, 'output'):
                result_data = json.loads(result.output)
            else:
                print("No output found in runner events")
                return "", "感情の分類に失敗しました。"
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