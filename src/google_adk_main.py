"""
Google ADKエージェントパイプラインのメインエントリーポイント。
"""

import asyncio
import json
from dotenv import load_dotenv
import os

from .models.data_models import UserInput
from .pipeline.google_adk_pipeline import run_pipeline, format_pipeline_results


async def interact():
    """サンプル入力で感情エージェントパイプラインを実行し、結果を表示する。"""
    try:
        user_input = UserInput(data="0.8", touched_area="胸")

        ctx, error = await run_pipeline(user_input)

        if error:
            print(f"エラーが発生しました: {error}")
            return

        results = format_pipeline_results(ctx)

        print(f"抽出された感情: {results['extracted_emotion']}")
        print(f"元のメッセージ: {results['original_message']}")
        print(f"感情カテゴリ: {results['emotion_category']}")
        print(f"最終メッセージ: {results['final_message']}")
        print(f"コンテキストの内容: {ctx}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


def main():
    """環境変数を読み込み、interact関数を実行する。"""
    load_dotenv()
    
    # Google ADK用の環境変数設定
    # Gemini APIキーが設定されていることを確認
    if not os.getenv("GOOGLE_API_KEY"):
        print("警告: GOOGLE_API_KEYが設定されていません。.envファイルに追加してください。")
    
    asyncio.run(interact())


if __name__ == "__main__":
    main()