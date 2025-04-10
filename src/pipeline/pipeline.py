"""
Pipeline execution logic for the OpenAI agent pipeline.
"""
import json
import traceback
from typing import Dict, Any, Optional, Tuple

from agents import Runner
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
    Execute the emotion agent pipeline with the given user input.
    
    Args:
        user_input: The user input containing data and touched area.
        emotion_learner: Optional emotion learner to use for prediction.
        
    Returns:
        A tuple containing the pipeline context with results and any exception that occurred.
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
            emotion_agent_with_gender = emotion_agent.model_copy(update={"instructions": emotion_agent_inst})
            
            result1 = await Runner.run(
                emotion_agent_with_gender, 
                json.dumps(user_input.model_dump()), 
                context=ctx
            )
            
            final_output: OriginalOutput = result1.final_output
            ctx.emotion = final_output.emotion
            ctx.original_message = final_output.message
            ctx.is_learned_response = False
        
        classification_agent_inst = classification_agent.instructions
        classification_agent_with_gender = classification_agent.model_copy()
        
        emotion_handoffs = []
        for agent in classification_agent.handoffs:
            agent_inst = agent.instructions.format(gender=gender)
            emotion_handoffs.append(agent.model_copy(update={"instructions": agent_inst}))
        
        classification_agent_with_gender.handoffs = emotion_handoffs
        
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
    Format the pipeline results for display.
    
    Args:
        ctx: The pipeline context with results.
        
    Returns:
        A dictionary with formatted results.
    """
    return {
        "extracted_emotion": ctx.emotion.model_dump() if ctx.emotion else None,
        "original_message": ctx.original_message,
        "emotion_category": ctx.emotion_category,
        "final_message": ctx.modified_message,
        "is_learned_response": getattr(ctx, "is_learned_response", False)
    }
