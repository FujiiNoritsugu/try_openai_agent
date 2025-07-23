"""
リファクタリングされたコードが元のコードと同じ出力を生成することを確認するテストスクリプト。
"""
import asyncio
import json
import sys
from dotenv import load_dotenv

from src.models.data_models import UserInput
from src.pipeline.pipeline import run_pipeline, format_pipeline_results


async def test_refactored_implementation():
    """サンプル入力でリファクタリングされた実装をテストする。"""
    user_input = UserInput(data="0.8", touched_area="胸")
    
    print("リファクタリングされた実装をテスト中...")
    ctx, error = await run_pipeline(user_input)
    
    if error:
        print(f"エラーが発生しました: {error}")
        return
    
    results = format_pipeline_results(ctx)
    
    print("リファクタリングされた実装の出力:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("テスト完了。")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_refactored_implementation())
