"""
Google ADKを使用した感情処理ロジック。
"""

import json
import uuid
from typing import Optional, Tuple
from google.adk import Runner
from google.genai import types

from ..models.data_models import UserInput, PipelineContext, OriginalOutput, Emotion
from ..agents.google_adk_factory import agent_factory
from .google_adk_session_manager import session_manager


class EmotionProcessor:
    """Google ADKを使用した感情処理を担当するクラス"""

    def __init__(self):
        self.agent_factory = agent_factory
        self.session_service = session_manager.session_service
        self.session_counter = 0

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

        # Google ADKのRunnerを使用してエージェントを実行
        runner = Runner(
            agent=emotion_agent, 
            session_service=self.session_service,
            app_name="emotion_pipeline"
        )
        
        # ユーザー入力をJSON形式で送信
        input_json = json.dumps(user_input.model_dump())
        
        # Google ADKの正しい形式でメッセージを作成
        message = types.Content(parts=[types.Part(text=input_json)])
        
        # Runnerを実行
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        user_id = f"user_{user_input.gender}_{self.session_counter}"
        
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
        
        try:
            events = list(runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ))
        except Exception as e:
            print(f"Runner execution error: {e}")
            return None, None, False
        
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
                return None, None, False
            emotion_data = result_data.get("emotion", {})
            emotion = Emotion(
                joy=emotion_data.get("joy", 0),
                fun=emotion_data.get("fun", 0),
                anger=emotion_data.get("anger", 0),
                sad=emotion_data.get("sad", 0)
            )
            message = result_data.get("message", "")
            return emotion, message, False
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing emotion result: {e}")
            return None, None, False

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