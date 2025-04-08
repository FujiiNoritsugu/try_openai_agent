"""
Bridge module to provide compatibility with openai_agents package.
"""
try:
    from openai_agents import Agent, Runner
except ImportError:
    class Agent:
        """Stub implementation of Agent class."""
        def __init__(self, name, instructions, output_type=None, handoffs=None):
            self.name = name
            self.instructions = instructions
            self.output_type = output_type
            self.handoffs = handoffs or []
            
        def __class_getitem__(cls, item):
            """Support for Agent[PipelineContext] syntax."""
            return cls
    
    class Runner:
        """Stub implementation of Runner class."""
        @staticmethod
        async def run(agent, input, context=None):
            """Stub implementation of run method that returns mock data."""
            import json
            from ..models.data_models import OriginalOutput, HandoffOutput
            
            if agent.name == "emotion_agent":
                return OriginalOutput(
                    emotion={"joy": 0.5, "fun": 0.5, "anger": 0.0, "sad": 0.0},
                    message="これは感情抽出エージェントからのモックレスポンスです。"
                )
            elif agent.name == "classification_agent":
                return "joy"
            elif agent.name in ["joy_agent", "anger_agent", "sorrow_agent", "pleasure_agent"]:
                return HandoffOutput(
                    message=f"これは{agent.name}からのモックレスポンスです。実際のOpenAIエージェントをインストールすると、より適切な応答が生成されます。"
                )
            else:
                return f"モックレスポンス: {agent.name}からの応答です。入力: {input}"
