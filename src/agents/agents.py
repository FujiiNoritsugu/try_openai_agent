"""
Bridge module to provide compatibility with openai_agents package.
"""
import importlib.util
import sys

spec = importlib.util.find_spec("openai_agents")
if spec is not None:
    from openai_agents import Agent, Runner
else:
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
            from ..models.data_models import OriginalOutput, HandoffOutput, Emotion
            
            class MockResponse:
                def __init__(self, final_output):
                    self.final_output = final_output
            
            if agent.name == "emotion_agent":
                emotion_data = {"joy": 0.5, "fun": 0.5, "anger": 0.0, "sad": 0.0}
                emotion = Emotion(**emotion_data)
                
                mock_output = OriginalOutput(
                    emotion=emotion,
                    message="これは感情抽出エージェントからのモックレスポンスです。"
                )
                return MockResponse(final_output=mock_output)
                
            elif agent.name == "classification_agent":
                mock_output = HandoffOutput(
                    message="これは分類エージェントからのモックレスポンスです。",
                    emotion_category="joy"
                )
                return MockResponse(final_output=mock_output)
                
            elif agent.name in ["joy_agent", "anger_agent", "sorrow_agent", "pleasure_agent"]:
                mock_output = HandoffOutput(
                    message=f"これは{agent.name}からのモックレスポンスです。実際のOpenAIエージェントをインストールすると、より適切な応答が生成されます。",
                    emotion_category=agent.name.replace("_agent", "")
                )
                return MockResponse(final_output=mock_output)
                
            else:
                return MockResponse(
                    final_output=f"モックレスポンス: {agent.name}からの応答です。入力: {input}"
                )
