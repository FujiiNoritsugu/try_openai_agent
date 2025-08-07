"""
Google ADKセッション作成のテスト
"""

import asyncio
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_session_creation():
    # セッションサービスを作成
    session_service = InMemorySessionService()
    
    # セッションサービスの属性を調査
    print("Session service attributes:")
    for attr in dir(session_service):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    # エージェントを作成
    agent = Agent(
        name="TestAgent",
        model="gemini-1.5-flash",
        description="Test agent",
        instruction="Respond to user input"
    )
    
    # ランナーを作成してセッションを開始
    runner = Runner(agent=agent, session_service=session_service, app_name="test_app")
    
    # ランナーの属性を調査
    print("\nRunner attributes:")
    for attr in dir(runner):
        if not attr.startswith('_'):
            print(f"  - {attr}")
    
    # セッションを作成または取得する方法を探す
    session_id = "test_session"
    user_id = "test_user"
    
    # セッションを明示的に作成する方法があるか確認
    if hasattr(session_service, 'create_session'):
        print("\nTrying create_session...")
        session_service.create_session(session_id=session_id, user_id=user_id)
    
    if hasattr(session_service, 'get_or_create_session'):
        print("\nTrying get_or_create_session...")
        session_service.get_or_create_session(session_id=session_id, user_id=user_id)
    
    # セッションの存在を確認
    if hasattr(session_service, 'sessions'):
        print(f"\nCurrent sessions: {session_service.sessions}")
    
    if hasattr(session_service, 'get_session'):
        print("\nTrying get_session...")
        try:
            session = session_service.get_session(session_id=session_id)
            print(f"Session found: {session}")
        except Exception as e:
            print(f"Session not found: {e}")

if __name__ == "__main__":
    asyncio.run(test_session_creation())