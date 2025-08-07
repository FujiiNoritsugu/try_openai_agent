"""
Google ADK用のグローバルセッションマネージャー。
"""

from google.adk.sessions import InMemorySessionService


class SessionManager:
    """シングルトンパターンでセッションサービスを管理するクラス"""
    
    _instance = None
    _session_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._session_service = InMemorySessionService()
        return cls._instance
    
    @property
    def session_service(self):
        """共有セッションサービスを取得"""
        return self._session_service


# グローバルセッションマネージャーインスタンス
session_manager = SessionManager()