"""
Google ADK実装のテストスクリプト
"""

import asyncio
import json
from dotenv import load_dotenv
import os

# 環境変数を読み込む
load_dotenv()

# Google ADKモジュールをインポート
try:
    from google.adk import Agent, Runner
    from google.adk.sessions import InMemorySessionService
    print("✓ Google ADKモジュールのインポートに成功")
except Exception as e:
    print(f"✗ Google ADKモジュールのインポートに失敗: {e}")
    exit(1)

# エージェントを作成
try:
    test_agent = Agent(
        name="TestAgent",
        model="gemini-1.5-flash",
        description="テスト用エージェント",
        instruction="ユーザーの入力に対して簡単な応答を返してください。"
    )
    print("✓ エージェントの作成に成功")
except Exception as e:
    print(f"✗ エージェントの作成に失敗: {e}")
    exit(1)

# セッションサービスとランナーを作成
try:
    session_service = InMemorySessionService()
    runner = Runner(agent=test_agent, session_service=session_service, app_name="test_app")
    print("✓ ランナーの作成に成功")
except Exception as e:
    print(f"✗ ランナーの作成に失敗: {e}")
    exit(1)

# テスト実行
async def test_run():
    try:
        from google.genai import types
        # メッセージを作成
        message = types.Content(parts=[types.Part(text="こんにちは")])
        
        # エージェントを実行
        events = list(runner.run(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        ))
        
        print(f"✓ エージェントの実行に成功")
        if events:
            for event in events:
                print(f"イベント: {event}")
    except Exception as e:
        print(f"✗ エージェントの実行に失敗: {e}")

# 環境変数の確認
if not os.getenv("GOOGLE_API_KEY"):
    print("⚠ 警告: GOOGLE_API_KEYが設定されていません")
    print("  .envファイルに以下を追加してください:")
    print("  GOOGLE_API_KEY=your_google_api_key")

# 非同期関数を実行
if __name__ == "__main__":
    asyncio.run(test_run())