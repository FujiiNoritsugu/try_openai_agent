"""
OpenAIエージェントパイプラインの実行ロジック。
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
    user_input: UserInput
) -> Tuple[PipelineContext, Optional[Exception]]:
    """
    指定されたユーザー入力で感情エージェントパイプラインを実行する。
    
    Args:
        user_input: データと触れられた部位を含むユーザー入力。
        
    Returns:
        結果を含むパイプラインコンテキストと発生した例外のタプル。
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
    }
