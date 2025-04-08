"""
Pipeline execution logic for the OpenAI agent pipeline.
"""
import json
import traceback
from typing import Dict, Any, Optional, Tuple

try:
    from openai_agents import Runner
except ImportError:
    from ..agents.agents import Runner
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
    user_input: UserInput
) -> Tuple[PipelineContext, Optional[Exception]]:
    """
    Execute the emotion agent pipeline with the given user input.
    
    Args:
        user_input: The user input containing data and touched area.
        
    Returns:
        A tuple containing the pipeline context with results and any exception that occurred.
    """
    ctx = PipelineContext(user_input=user_input)
    error = None
    
    try:
        result1 = await Runner.run(
            emotion_agent, 
            json.dumps(user_input.model_dump()), 
            context=ctx
        )
        
        final_output: OriginalOutput = result1.final_output
        ctx.emotion = final_output.emotion
        ctx.original_message = final_output.message
        
        if ctx.emotion is None:
            error = Exception("Emotion extraction failed")
            return ctx, error
            
        result2 = await Runner.run(
            classification_agent,
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
    try:
        extracted_emotion = ctx.emotion.model_dump() if ctx.emotion else None
    except Exception as e:
        extracted_emotion = {"error": f"Failed to extract emotion: {str(e)}"}
        
    return {
        "extracted_emotion": extracted_emotion,
        "original_message": ctx.original_message or "",
        "emotion_category": ctx.emotion_category or "",
        "final_message": ctx.modified_message or "",
    }
