"""
Main entry point for the OpenAI agent pipeline.
"""
import asyncio
import json
from dotenv import load_dotenv

from .models.data_models import UserInput
from .pipeline.pipeline import run_pipeline, format_pipeline_results


async def interact():
    """Execute the emotion agent pipeline with sample input and display results."""
    try:
        user_input = UserInput(data="0.8", touched_area="胸")
        
        ctx, error = await run_pipeline(user_input)
        
        if error:
            print(f"Error occurred: {error}")
            return
        
        results = format_pipeline_results(ctx)
        
        print(f"抽出された感情: {results['extracted_emotion']}")
        print(f"元のメッセージ: {results['original_message']}")
        print(f"感情カテゴリ: {results['emotion_category']}")
        print(f"最終メッセージ: {results['final_message']}")
        print(f"コンテキストの内容: {ctx}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Load environment variables and run the interact function."""
    load_dotenv()
    
    asyncio.run(interact())


if __name__ == "__main__":
    main()
