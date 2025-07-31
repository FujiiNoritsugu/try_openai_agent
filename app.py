"""
OpenAIエージェントパイプライン用のStreamlit UI。
"""
import os
import streamlit as st
from dotenv import load_dotenv

from src.ui.pages import display_analysis_page, display_learning_page, display_device_settings_page
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


def main():
    """Streamlit UIのメイン関数。"""
    st.title(settings.app_title)
    
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
