"""
デバイス設定ページ。
"""

import streamlit as st

from ...models.data_models import Emotion
from ...devices.pipeline_integration import haptic_feedback
from ..utils.async_utils import run_async


def display_device_settings_page() -> None:
    """デバイス設定ページを表示する"""
    st.header("触覚フィードバックデバイス設定")

    st.markdown(
        """
    このページでは、触覚フィードバックデバイスの設定を行います。
    Arduino Uno R4 WiFiデバイスのIPアドレスとポートを設定し、
    感情分析結果に基づいた振動パターンを送信できるようにします。
    """
    )

    initialize_session_state()
    display_registered_devices()
    add_device_form()

    if st.session_state.haptic_devices:
        test_device_connection()

        if st.session_state.haptic_initialized:
            test_vibration_patterns()


def initialize_session_state() -> None:
    """セッション状態を初期化する"""
    if "haptic_devices" not in st.session_state:
        st.session_state.haptic_devices = []

    if "haptic_initialized" not in st.session_state:
        st.session_state.haptic_initialized = False


def display_registered_devices() -> None:
    """登録済みデバイスを表示する"""
    if st.session_state.haptic_devices:
        st.subheader("登録済みデバイス")

        for i, device in enumerate(st.session_state.haptic_devices):
            with st.expander(
                f"デバイス {i+1}: {device['device_id']} ({device['host']}:{device['port']})"
            ):
                st.write(f"デバイスID: {device['device_id']}")
                st.write(f"ホスト: {device['host']}")
                st.write(f"ポート: {device['port']}")

                if st.button(f"デバイス {i+1} を削除", key=f"delete_device_{i}"):
                    st.session_state.haptic_devices.pop(i)
                    st.session_state.haptic_initialized = False
                    st.rerun()
    else:
        st.info(
            "登録済みデバイスはありません。以下のフォームからデバイスを追加してください。"
        )


def add_device_form() -> None:
    """デバイス追加フォームを表示する"""
    st.subheader("デバイスを追加")

    with st.form("add_device_form"):
        device_id = st.text_input(
            "デバイスID", value=f"device{len(st.session_state.haptic_devices) + 1}"
        )
        host = st.text_input("ホスト (IPアドレス)", value="192.168.1.100")
        port = st.number_input("ポート", value=80, min_value=1, max_value=65535)

        submitted = st.form_submit_button("デバイスを追加")

        if submitted:
            new_device = {
                "device_id": device_id,
                "host": host,
                "port": port,
            }

            st.session_state.haptic_devices.append(new_device)
            st.session_state.haptic_initialized = False
            st.success(f"デバイス '{device_id}' が追加されました")
            st.rerun()


def test_device_connection() -> None:
    """デバイス接続テストを実行する"""
    st.subheader("デバイス接続テスト")

    if st.button("接続テスト"):
        with st.spinner("デバイスに接続中..."):
            initialized = run_async(
                haptic_feedback.initialize(st.session_state.haptic_devices)
            )

            if initialized:
                st.session_state.haptic_initialized = True
                st.success("すべてのデバイスに正常に接続しました")

                status = run_async(haptic_feedback.get_all_device_status())

                if status:
                    st.subheader("デバイスの状態")
                    for device_id, device_status in status.items():
                        if device_status:
                            connected = device_status.get("connected", False)
                            playing = device_status.get("playing", False)
                            state = "接続中" if connected else "切断"
                            if connected and playing:
                                state += " (再生中)"
                            st.write(f"デバイス '{device_id}': {state}")
                        else:
                            st.warning(
                                f"デバイス '{device_id}' の状態を取得できませんでした"
                            )
            else:
                st.error(
                    "デバイス接続に失敗しました。ホストとポートの設定を確認してください。"
                )


def test_vibration_patterns() -> None:
    """テスト振動パターンを送信する"""
    st.subheader("テスト振動パターン")

    emotion_category = st.selectbox(
        "感情カテゴリ",
        options=["joy", "anger", "sorrow", "pleasure"],
        format_func=lambda x: {
            "joy": "喜び",
            "anger": "怒り",
            "sorrow": "悲しみ",
            "pleasure": "快楽",
        }.get(x, x),
    )

    intensity = st.slider("感情強度", min_value=0, max_value=5, value=3, step=1)

    if st.button("テストパターンを送信"):
        with st.spinner("振動パターンを送信中..."):
            emotion = Emotion(
                joy=intensity if emotion_category == "joy" else 1,
                fun=intensity if emotion_category == "pleasure" else 1,
                anger=intensity if emotion_category == "anger" else 1,
                sad=intensity if emotion_category == "sorrow" else 1,
            )

            results = run_async(
                haptic_feedback.arduino_manager.send_to_all(emotion, emotion_category)
            )

            if results:
                st.success("テストパターンを送信しました")
                for device_id, success in results.items():
                    if success:
                        st.info(f"デバイス '{device_id}' に正常に送信されました")
                    else:
                        st.warning(f"デバイス '{device_id}' への送信に失敗しました")
            else:
                st.error("テストパターンの送信に失敗しました")
