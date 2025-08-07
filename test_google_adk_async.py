"""
Google ADK実装のテストスクリプト（非同期版）
"""

import asyncio
import json
from dotenv import load_dotenv
import os

# 環境変数を読み込む
load_dotenv()

# Google ADKモジュールをインポート
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_async():
    # エージェントを作成
    test_agent = Agent(
        name="TestAgent",
        model="gemini-1.5-flash",
        description="テスト用エージェント",
        instruction="ユーザーの入力に対して簡単な応答を返してください。"
    )
    
    # セッションサービスとランナーを作成
    session_service = InMemorySessionService()
    runner = Runner(agent=test_agent, session_service=session_service, app_name="test_app")
    
    # メッセージを作成
    message = types.Content(parts=[types.Part(text="こんにちは")])
    
    try:
        # 非同期実行を試す
        print("非同期実行を開始...")
        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=message
        ):
            print(f"イベント受信: {event}")
            events.append(event)
        
        print(f"✓ 非同期実行に成功: {len(events)}個のイベント")
        
    except Exception as e:
        print(f"✗ 非同期実行に失敗: {e}")
        print(f"エラーの型: {type(e)}")

# 実行
if __name__ == "__main__":
    asyncio.run(test_async())