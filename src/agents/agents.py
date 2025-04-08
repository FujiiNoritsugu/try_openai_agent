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
            """Stub implementation of run method."""
            raise NotImplementedError(
                "Runner.run is not implemented. Please install openai_agents package."
            )
