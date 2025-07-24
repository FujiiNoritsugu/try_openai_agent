"""
OpenAIエージェントパイプラインの実行ロジック。
"""
import json
import traceback
from typing import Dict, Any, Optional, Tuple

from agents import Runner, Agent
from ..models.data_models import (
    UserInput, 
    PipelineContext, 
    OriginalOutput, 
    HandoffOutput, 
    Emotion
)
from ..agents.emotion_agents import (
    emotion_agent, 
    classification_agent
)


async def run_pipeline(
    user_input: UserInput,
    emotion_learner=None
) -> Tuple[PipelineContext, Optional[Exception]]:
    """
    指定されたユーザー入力で感情エージェントパイプラインを実行する。
    
    Args:
        user_input: データと触れられた部位を含むユーザー入力。
        emotion_learner: Optional emotion learner to use for prediction.
        
    Returns:
        結果を含むパイプラインコンテキストと発生した例外のタプル。
    """
    ctx = PipelineContext(user_input=user_input)
    error = None
    
    try:
        learned_emotion = None
        if emotion_learner:
            learned_emotion = emotion_learner.predict_emotion(user_input)
        
        if learned_emotion:
            ctx.emotion = learned_emotion
            ctx.original_message = "学習データに基づいた感情応答です。"
            ctx.is_learned_response = True
        else:
            gender = user_input.gender
            
            emotion_agent_inst = emotion_agent.instructions.format(gender=gender)
            
            result1 = await Runner.run(
                Agent[PipelineContext](
                    name=emotion_agent.name,
                    instructions=emotion_agent_inst,
                    output_type=emotion_agent.output_type
                ), 
                json.dumps(user_input.model_dump()), 
                context=ctx
            )
            
            final_output: OriginalOutput = result1.final_output
            ctx.emotion = final_output.emotion
            ctx.original_message = final_output.message
            ctx.is_learned_response = False
        
        gender = getattr(user_input, "gender", "男性")
        
        emotion_handoffs = []
        for agent in classification_agent.handoffs:
            agent_inst = agent.instructions.format(gender=gender)
            emotion_handoffs.append(Agent[PipelineContext](
                name=agent.name,
                instructions=agent_inst,
                output_type=agent.output_type
            ))
        
        classification_agent_with_gender = Agent[PipelineContext](
            name=classification_agent.name,
            instructions=classification_agent.instructions,
            handoffs=emotion_handoffs,
            output_type=classification_agent.output_type
        )
        
        result2 = await Runner.run(
            classification_agent_with_gender,
            input=json.dumps(ctx.emotion.model_dump()),
            context=ctx,
        )
        
        handoff_output: HandoffOutput = result2.final_output
        ctx.modified_message = handoff_output.message
        ctx.emotion_category = handoff_output.emotion_category
        
    except Exception as e:
        error = e
        traceback.print_exc()
        
    return ctx, error


def format_pipeline_results(ctx: PipelineContext) -> Dict[str, Any]:
    """
    パイプラインの結果を表示用にフォーマットする。
    
    Args:
        ctx: 結果を含むパイプラインコンテキスト。
        
    Returns:
        フォーマットされた結果の辞書。
    """
    return {
        "extracted_emotion": ctx.emotion.model_dump() if ctx.emotion else None,
        "original_message": ctx.original_message,
        "emotion_category": ctx.emotion_category,
        "final_message": ctx.modified_message,
        "is_learned_response": getattr(ctx, "is_learned_response", False)
    }
