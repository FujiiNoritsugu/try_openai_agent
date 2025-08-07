"""
エージェントファクトリー。
"""

from typing import Dict, List, Optional, Literal
from agents import Agent

from .instructions import AgentInstructions
from ..models.data_models import PipelineContext, HandoffOutput, OriginalOutput

AgentType = Literal["joy", "anger", "sorrow", "pleasure", "emotion_extractor"]


class AgentFactory:
    """エージェントを作成するファクトリークラス"""

    def __init__(self):
        self._agents_cache: Dict[str, Agent] = {}

    def create_emotion_extractor(self) -> Agent[PipelineContext]:
        """感情抽出エージェントを作成する"""
        if "emotion_extractor" not in self._agents_cache:
            self._agents_cache["emotion_extractor"] = Agent[PipelineContext](
                name="EmotionExtractor",
                instructions=AgentInstructions.EMOTION_EXTRACTOR,
                output_type=OriginalOutput,
                model="gpt-5",
            )
        return self._agents_cache["emotion_extractor"]

    def create_joy_agent(self) -> Agent[PipelineContext]:
        """喜びエージェントを作成する"""
        if "joy" not in self._agents_cache:
            self._agents_cache["joy"] = Agent[PipelineContext](
                name="JoyAgent",
                instructions=AgentInstructions.JOY,
                output_type=HandoffOutput,
                model="gpt-5",
            )
        return self._agents_cache["joy"]

    def create_anger_agent(self) -> Agent[PipelineContext]:
        """怒りエージェントを作成する"""
        if "anger" not in self._agents_cache:
            self._agents_cache["anger"] = Agent[PipelineContext](
                name="AngerAgent",
                instructions=AgentInstructions.ANGER,
                output_type=HandoffOutput,
                model="gpt-5",
            )
        return self._agents_cache["anger"]

    def create_sorrow_agent(self) -> Agent[PipelineContext]:
        """悲しみエージェントを作成する"""
        if "sorrow" not in self._agents_cache:
            self._agents_cache["sorrow"] = Agent[PipelineContext](
                name="SorrowAgent",
                instructions=AgentInstructions.SORROW,
                output_type=HandoffOutput,
                model="gpt-5",
            )
        return self._agents_cache["sorrow"]

    def create_pleasure_agent(self) -> Agent[PipelineContext]:
        """楽しさエージェントを作成する"""
        if "pleasure" not in self._agents_cache:
            self._agents_cache["pleasure"] = Agent[PipelineContext](
                name="PleasureAgent",
                instructions=AgentInstructions.PLEASURE,
                output_type=HandoffOutput,
                model="gpt-5",
            )
        return self._agents_cache["pleasure"]

    def create_classifier_agent(
        self, handoff_agents: Optional[List[Agent[PipelineContext]]] = None
    ) -> Agent[PipelineContext]:
        """分類エージェントを作成する"""
        if handoff_agents is None:
            handoff_agents = [
                self.create_joy_agent(),
                self.create_anger_agent(),
                self.create_sorrow_agent(),
                self.create_pleasure_agent(),
            ]

        return Agent[PipelineContext](
            name="EmotionClassifier",
            instructions=AgentInstructions.CLASSIFIER,
            handoffs=handoff_agents,
            output_type=HandoffOutput,
            model="gpt-5",
        )

    def create_emotion_agent_with_gender(
        self, agent_type: AgentType, gender: str
    ) -> Agent[PipelineContext]:
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

        return Agent[PipelineContext](
            name=base_agent.name,
            instructions=base_agent.instructions.format(gender=gender),
            output_type=base_agent.output_type,
            model="gpt-5",
        )


# シングルトンインスタンス
agent_factory = AgentFactory()
