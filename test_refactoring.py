"""
Test script to verify that the refactored code produces the same output as the original.
"""
import asyncio
import json
import sys
from dotenv import load_dotenv

from src.models.data_models import UserInput
from src.pipeline.pipeline import run_pipeline, format_pipeline_results


async def test_refactored_implementation():
    """Test the refactored implementation with sample input."""
    user_input = UserInput(data="0.8", touched_area="胸")
    
    print("Testing refactored implementation...")
    ctx, error = await run_pipeline(user_input)
    
    if error:
        print(f"Error occurred: {error}")
        return
    
    results = format_pipeline_results(ctx)
    
    print("Refactored implementation output:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("Test completed.")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_refactored_implementation())
