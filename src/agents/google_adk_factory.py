"""
Google ADKを使用したエージェントファクトリー。
"""

from typing import Dict, List, Optional, Literal, Any
from google.adk import Agent
from google.adk.tools import ToolContext
import json
from pydantic import BaseModel

from .instructions import AgentInstructions
from ..models.data_models import PipelineContext, HandoffOutput, OriginalOutput, Emotion

AgentType = Literal["joy", "anger", "sorrow", "pleasure", "emotion_extractor"]


class AgentFactory:
    """Google ADKを使用してエージェントを作成するファクトリークラス"""

    def __init__(self):
        self._agents_cache: Dict[str, Agent] = {}

    def _extract_emotion_tool(self, context: ToolContext, user_input: str) -> str:
        """感情を抽出して構造化された応答を返すツール"""
        # ここでLLMの応答を処理する
        # Google ADKはツール内でモデルを呼び出すことができる
        return json.dumps({
            "emotion": {
                "joy": 3,
                "fun": 2,
                "anger": 1,
                "sad": 0
            },
            "message": "応答メッセージ"
        })

    def _classify_emotion_tool(self, context: ToolContext, emotion_data: str) -> str:
        """感情を分類して適切なエージェントを決定するツール"""
        # 感情データを解析して分類
        emotion = json.loads(emotion_data).get("emotion", {})
        
        # 最も高い感情値を持つカテゴリを決定
        max_value = -1
        category = ""
        category_map = {
            "joy": "喜",
            "fun": "楽",
            "anger": "怒",
            "sad": "哀"
        }
        
        for key, value in emotion.items():
            if value > max_value:
                max_value = value
                category = category_map.get(key, "")
        
        return json.dumps({
            "emotion_category": category,
            "message": ""
        })

    def create_emotion_extractor(self) -> Agent:
        """感情抽出エージェントを作成する"""
        if "emotion_extractor" not in self._agents_cache:
            self._agents_cache["emotion_extractor"] = Agent(
                name="EmotionExtractor",
                model="gemini-1.5-flash",
                description="ユーザー入力から感情を抽出するエージェント",
                instruction=AgentInstructions.EMOTION_EXTRACTOR,
                tools=[self._extract_emotion_tool]
            )
        return self._agents_cache["emotion_extractor"]

    def create_joy_agent(self) -> Agent:
        """喜びエージェントを作成する"""
        if "joy" not in self._agents_cache:
            self._agents_cache["joy"] = Agent(
                name="JoyAgent",
                model="gemini-1.5-flash",
                description="喜びの感情を表現するエージェント",
                instruction=AgentInstructions.JOY
            )
        return self._agents_cache["joy"]

    def create_anger_agent(self) -> Agent:
        """怒りエージェントを作成する"""
        if "anger" not in self._agents_cache:
            self._agents_cache["anger"] = Agent(
                name="AngerAgent",
                model="gemini-1.5-flash",
                description="怒りの感情を表現するエージェント",
                instruction=AgentInstructions.ANGER
            )
        return self._agents_cache["anger"]

    def create_sorrow_agent(self) -> Agent:
        """悲しみエージェントを作成する"""
        if "sorrow" not in self._agents_cache:
            self._agents_cache["sorrow"] = Agent(
                name="SorrowAgent",
                model="gemini-1.5-flash",
                description="悲しみの感情を表現するエージェント",
                instruction=AgentInstructions.SORROW
            )
        return self._agents_cache["sorrow"]

    def create_pleasure_agent(self) -> Agent:
        """楽しさエージェントを作成する"""
        if "pleasure" not in self._agents_cache:
            self._agents_cache["pleasure"] = Agent(
                name="PleasureAgent",
                model="gemini-1.5-flash",
                description="楽しさの感情を表現するエージェント",
                instruction=AgentInstructions.PLEASURE
            )
        return self._agents_cache["pleasure"]

    def create_classifier_agent(self) -> Agent:
        """分類エージェントを作成する（サブエージェントを使用）"""
        # Google ADKではsub_agentsパラメータで自動的にハンドオフを処理
        sub_agents = [
            self.create_joy_agent(),
            self.create_anger_agent(),
            self.create_sorrow_agent(),
            self.create_pleasure_agent(),
        ]

        return Agent(
            name="EmotionClassifier",
            model="gemini-1.5-flash",
            description="感情を分類して適切なエージェントにルーティングする",
            instruction=AgentInstructions.CLASSIFIER,
            tools=[self._classify_emotion_tool],
            sub_agents=sub_agents
        )

    def create_emotion_agent_with_gender(
        self, agent_type: AgentType, gender: str
    ) -> Agent:
        """性別を考慮したエージェントを作成する"""
        agent_creators = {
            "joy": self.create_joy_agent,
            "anger": self.create_anger_agent,
            "sorrow": self.create_sorrow_agent,
            "pleasure": self.create_pleasure_agent,
            "emotion_extractor": self.create_emotion_extractor,
        }

        if agent_type not in agent_creators:
            raise ValueError(f"Unknown agent type: {agent_type}")

        base_agent = agent_creators[agent_type]()
        
        # 性別を含む新しい指示で新しいエージェントを作成
        return Agent(
            name=base_agent.name,
            model=base_agent.model,
            description=base_agent.description,
            instruction=base_agent.instruction.format(gender=gender),
            tools=base_agent.tools if hasattr(base_agent, 'tools') else None
        )


# シングルトンインスタンス
agent_factory = AgentFactory()