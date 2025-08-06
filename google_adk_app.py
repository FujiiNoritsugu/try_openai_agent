"""
Google ADKを使用したStreamlit UI。
"""
import os
import streamlit as st
from dotenv import load_dotenv

from src.ui.pages import display_learning_page, display_device_settings_page
from src.ui.pages.google_adk_emotion_analysis import display_analysis_page
from src.config import settings
from src.utils import setup_logging


def initialize_app():
    """アプリケーションを初期化する"""
    # ロギングの設定
    setup_logging(
        log_level=settings.logging.log_level,
        log_file=settings.logging.log_file,
        log_format=settings.logging.log_format
    )
    
    # 必要なディレクトリの作成
    os.makedirs("data/feedback", exist_ok=True)
    os.makedirs("data/learning", exist_ok=True)
    if settings.logging.log_file:
        os.makedirs(os.path.dirname(settings.logging.log_file), exist_ok=True)

    # 環境変数の確認
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("注意: GOOGLE_API_KEYが設定されていません。.envファイルに追加してください。")


def main():
    """Streamlit UIのメイン関数。"""
    st.title(settings.app_title + " (Google ADK版)")
    
    st.sidebar.title("ナビゲーション")
    page = st.sidebar.radio("ページを選択", ["感情分析", "学習データ", "デバイス設定"])
    
    if page == "感情分析":
        display_analysis_page()
    elif page == "学習データ":
        display_learning_page()
    elif page == "デバイス設定":
        display_device_settings_page()


if __name__ == "__main__":
    load_dotenv()
    initialize_app()
    main()