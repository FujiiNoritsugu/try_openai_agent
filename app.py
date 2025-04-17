"""
Streamlit UI for the OpenAI agent pipeline.
"""
import asyncio
import os
import json
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
from uuid import uuid4
from datetime import datetime

from src.models.data_models import UserInput, Emotion
from src.models.feedback_models import UserFeedback
from src.pipeline.pipeline import run_pipeline, format_pipeline_results
from src.learning.feedback_collector import FeedbackCollector
from src.learning.emotion_learner import EmotionLearner
from src.devices.pipeline_integration import haptic_feedback


def run_async(coroutine):
    """Run an async function from a synchronous context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)


def load_body_map():
    """人体画像のクリック可能な領域のマップを読み込む"""
    map_file = os.path.join("static", "images", "body_map.txt")
    body_map = []
    
    with open(map_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(',')
                if len(parts) == 5:
                    body_map.append({
                        'part': parts[0],
                        'x1': int(parts[1]),
                        'y1': int(parts[2]),
                        'x2': int(parts[3]),
                        'y2': int(parts[4])
                    })
    
    return body_map


def clickable_body_part_selector():
    """クリック可能な人体画像を使った部位選択インターフェース"""
    st.markdown("### 触れられた部位を選択")
    
    body_parts_desc = {
        "頭": "頭部（頭頂部、後頭部など）",
        "顔": "顔（額、頬、顎など）",
        "首": "首（前面、後面、側面）",
        "肩": "肩（左右の肩、肩甲骨など）",
        "腕": "腕（上腕、前腕など）",
        "手": "手（手のひら、指、手首など）",
        "胸": "胸部（胸骨、乳房など）",
        "腹": "腹部（上腹部、下腹部など）",
        "腰": "腰部（腰椎周辺）",
        "臀部": "臀部（お尻）",
        "脚": "脚（太もも、ふくらはぎなど）",
        "足": "足（足首、足の裏、指など）"
    }
    
    image_path = os.path.join("static", "images", "human_body.png")
    if not os.path.exists(image_path):
        st.error("人体画像が見つかりません。")
        return "胸"  # デフォルト値を返す
    
    image = Image.open(image_path)
    
    if 'selected_body_part' not in st.session_state:
        st.session_state.selected_body_part = "胸"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(image, use_container_width=True)
        st.markdown("以下のボタンで部位を選択してください")
        
        buttons_col1, buttons_col2, buttons_col3 = st.columns(3)
        
        with buttons_col1:
            if st.button("頭", key="btn_head"):
                st.session_state.selected_body_part = "頭"
            if st.button("顔", key="btn_face"):
                st.session_state.selected_body_part = "顔"
            if st.button("首", key="btn_neck"):
                st.session_state.selected_body_part = "首"
            if st.button("肩", key="btn_shoulder"):
                st.session_state.selected_body_part = "肩"
        
        with buttons_col2:
            if st.button("腕", key="btn_arm"):
                st.session_state.selected_body_part = "腕"
            if st.button("手", key="btn_hand"):
                st.session_state.selected_body_part = "手"
            if st.button("胸", key="btn_chest"):
                st.session_state.selected_body_part = "胸"
            if st.button("腹", key="btn_abdomen"):
                st.session_state.selected_body_part = "腹"
        
        with buttons_col3:
            if st.button("腰", key="btn_waist"):
                st.session_state.selected_body_part = "腰"
            if st.button("臀部", key="btn_hip"):
                st.session_state.selected_body_part = "臀部"
            if st.button("脚", key="btn_leg"):
                st.session_state.selected_body_part = "脚"
            if st.button("足", key="btn_foot"):
                st.session_state.selected_body_part = "足"
    
    with col2:
        st.subheader("選択された部位")
        st.markdown(f"**{st.session_state.selected_body_part}**")
        st.caption(body_parts_desc[st.session_state.selected_body_part])
        
        st.markdown("### 部位の説明")
        st.markdown(f"**{st.session_state.selected_body_part}**: {body_parts_desc[st.session_state.selected_body_part]}")
    
    return st.session_state.selected_body_part


def display_emotion_visualization(emotion_data):
    """感情データの可視化を表示する"""
    if emotion_data and isinstance(emotion_data, dict) and all(k in emotion_data for k in ["joy", "fun", "anger", "sad"]):
        st.subheader("感情レーダーチャート")
        
        chart_data = pd.DataFrame(
            {
                "感情": ["喜び", "楽しさ", "怒り", "悲しみ"],
                "値": [emotion_data["joy"], emotion_data["fun"], emotion_data["anger"], emotion_data["sad"]],
            }
        )
        
        st.write("感情パラメータの視覚化:")
        
        st.bar_chart(chart_data.set_index("感情"))
        
        dominant_emotion = max(emotion_data.items(), key=lambda x: x[1])
        st.write(f"最も強い感情: **{dominant_emotion[0]}** (強さ: {dominant_emotion[1]})")
        
        positive = emotion_data["joy"] + emotion_data["fun"]
        negative = emotion_data["anger"] + emotion_data["sad"]
        
        st.write(f"ポジティブ感情 (喜び+楽しさ): **{positive}**")
        st.write(f"ネガティブ感情 (怒り+悲しみ): **{negative}**")


def collect_feedback(user_input, emotion, results):
    """ユーザーからのフィードバックを収集する"""
    st.subheader("フィードバック")
    st.write("この感情応答の正確さを評価してください:")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        accuracy_rating = st.slider(
            "正確さ評価", 
            min_value=1, 
            max_value=5, 
            value=3, 
            step=1,
            help="1: 全く正確でない, 5: 非常に正確"
        )
        
        comments = st.text_area(
            "コメント (任意)",
            placeholder="この感情応答についてのコメントを入力してください..."
        )
    
    with col2:
        st.write("期待する感情値 (任意):")
        expected_joy = st.slider("喜び", min_value=0, max_value=5, value=emotion.joy, step=1)
        expected_fun = st.slider("楽しさ", min_value=0, max_value=5, value=emotion.fun, step=1)
        expected_anger = st.slider("怒り", min_value=0, max_value=5, value=emotion.anger, step=1)
        expected_sad = st.slider("悲しみ", min_value=0, max_value=5, value=emotion.sad, step=1)
    
    if st.button("フィードバックを送信"):
        feedback = UserFeedback(
            user_input=user_input,
            generated_emotion=emotion,
            accuracy_rating=accuracy_rating,
            expected_emotion={
                "joy": expected_joy,
                "fun": expected_fun,
                "anger": expected_anger,
                "sad": expected_sad
            },
            comments=comments if comments else None
        )
        
        feedback_collector = FeedbackCollector()
        feedback_collector.add_feedback(feedback)
        
        emotion_learner = EmotionLearner(feedback_collector)
        emotion_learner.update_patterns()
        
        st.success("フィードバックが送信されました。ありがとうございます！")
        
        if st.checkbox("学習パターンを表示"):
            st.json(json.loads(json.dumps(
                emotion_learner.learning_data.emotion_patterns,
                default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o)
            )))


def display_learning_stats():
    """学習データの統計を表示する"""
    feedback_collector = FeedbackCollector()
    emotion_learner = EmotionLearner(feedback_collector)
    
    st.subheader("学習データの統計")
    
    feedback_count = len(feedback_collector.learning_data.feedback_history)
    st.write(f"収集されたフィードバック: **{feedback_count}**")
    
    pattern_count = len(emotion_learner.learning_data.emotion_patterns)
    st.write(f"学習されたパターン: **{pattern_count}**")
    
    if pattern_count > 0:
        area_patterns = {}
        for pattern in emotion_learner.learning_data.emotion_patterns:
            area = pattern.touched_area
            if area not in area_patterns:
                area_patterns[area] = 0
            area_patterns[area] += 1
        
        st.write("部位ごとのパターン数:")
        for area, count in area_patterns.items():
            st.write(f"- {area}: {count}")
        
        if emotion_learner.learning_data.emotion_patterns:
            most_confident = max(
                emotion_learner.learning_data.emotion_patterns,
                key=lambda p: p.confidence
            )
            st.write(f"最も信頼度の高いパターン: **{most_confident.touched_area}** (信頼度: {most_confident.confidence:.2f})")


def main():
    """Main function for the Streamlit UI."""
    st.title("感情エージェントパイプライン")
    
    st.sidebar.title("ナビゲーション")
    page = st.sidebar.radio("ページを選択", ["感情分析", "学習データ", "デバイス設定"])
    
    if page == "感情分析":
        st.markdown("""
        このアプリケーションは、ユーザー入力（刺激の強さと触れられた部位）から感情を抽出・分類し、
        適切な感情応答を生成します。フィードバックを提供することで、システムの学習を支援できます。
        触覚フィードバックデバイスが接続されている場合は、感情に応じた振動パターンが送信されます。
        """)

        st.header("入力")
        
        data_value = st.slider(
            "刺激の強さ", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.5, 
            step=0.1,
            help="0.0: 何も感じない, 0.5: 最も気持ちいい, 1.0: 痛みを感じる"
        )
        
        gender = st.radio(
            "性別",
            options=["男性", "女性", "その他"],
            index=0,
            horizontal=True,
            help="システムが回答する際の性別を選択します"
        )
        
        touched_area = clickable_body_part_selector()
        
        use_learning = st.checkbox("学習データを使用", value=True, help="チェックすると、過去のフィードバックに基づいた学習データを使用します")
        
        use_haptic_feedback = st.checkbox("触覚フィードバックを使用", value=True, help="チェックすると、感情分析結果を触覚フィードバックデバイスに送信します")
        
        if st.button("感情を分析"):
            with st.spinner("感情を分析中..."):
                user_input = UserInput(data=str(data_value), touched_area=touched_area, gender=gender)
                
                emotion_learner = None
                if use_learning:
                    feedback_collector = FeedbackCollector()
                    emotion_learner = EmotionLearner(feedback_collector)
                
                if use_haptic_feedback and "haptic_devices" in st.session_state and st.session_state.haptic_devices:
                    try:
                        if not hasattr(st.session_state, "haptic_initialized") or not st.session_state.haptic_initialized:
                            st.session_state.haptic_initialized = run_async(haptic_feedback.initialize(st.session_state.haptic_devices))
                            
                        if st.session_state.haptic_initialized:
                            results, device_results = run_async(haptic_feedback.run_pipeline_and_send(user_input, emotion_learner))
                            
                            if device_results:
                                st.success("触覚フィードバックデバイスに振動パターンを送信しました")
                                for device_id, success in device_results.items():
                                    if success:
                                        st.info(f"デバイス '{device_id}' に正常に送信されました")
                                    else:
                                        st.warning(f"デバイス '{device_id}' への送信に失敗しました")
                            
                            ctx = None
                            error = None
                        else:
                            st.warning("触覚フィードバックシステムの初期化に失敗しました。通常のパイプラインを使用します。")
                            ctx, error = run_async(run_pipeline(user_input, emotion_learner))
                            results = format_pipeline_results(ctx) if not error else None
                    except Exception as e:
                        st.error(f"触覚フィードバック処理中にエラーが発生しました: {str(e)}")
                        ctx, error = run_async(run_pipeline(user_input, emotion_learner))
                        results = format_pipeline_results(ctx) if not error else None
                else:
                    ctx, error = run_async(run_pipeline(user_input, emotion_learner))
                    results = format_pipeline_results(ctx) if not error else None
                
                if error:
                    st.error(f"エラーが発生しました: {error}")
                elif results:
                    st.header("結果")
                    
                    if results.get("is_learned_response", False):
                        st.info("この応答は学習データに基づいています")
                    
                    st.subheader("抽出された感情")
                    emotion_data = results["extracted_emotion"]
                    st.json(emotion_data)
                    
                    display_emotion_visualization(emotion_data)
                    
                    st.subheader("元のメッセージ")
                    st.write(results["original_message"])
                    
                    st.subheader("感情カテゴリ")
                    st.write(results["emotion_category"])
                    
                    st.subheader("最終メッセージ")
                    st.write(results["final_message"])
                    
                    if emotion_data:
                        emotion = Emotion(**emotion_data)
                        collect_feedback(user_input, emotion, results)
    
    elif page == "学習データ":
        st.header("学習データ")
        
        st.markdown("""
        このページでは、システムが収集したフィードバックと学習したパターンを確認できます。
        ユーザーからのフィードバックに基づいて、システムは刺激と感情の関係を学習します。
        """)
        
        display_learning_stats()
        
        st.subheader("最近のフィードバック")
        feedback_collector = FeedbackCollector()
        recent_feedback = feedback_collector.get_recent_feedback(5)
        
        if recent_feedback:
            for i, feedback in enumerate(recent_feedback):
                with st.expander(f"フィードバック {i+1} ({feedback.timestamp.strftime('%Y-%m-%d %H:%M')})"):
                    st.write(f"部位: {feedback.user_input.touched_area}")
                    st.write(f"刺激の強さ: {feedback.user_input.data}")
                    st.write(f"正確さ評価: {feedback.accuracy_rating}/5")
                    
                    st.write("生成された感情:")
                    st.json(feedback.generated_emotion.model_dump())
                    
                    if feedback.expected_emotion:
                        st.write("期待された感情:")
                        st.json(feedback.expected_emotion)
                    
                    if feedback.comments:
                        st.write(f"コメント: {feedback.comments}")
        else:
            st.info("まだフィードバックがありません。感情分析ページでフィードバックを提供してください。")
        
        st.subheader("学習されたパターン")
        emotion_learner = EmotionLearner(feedback_collector)
        
        if emotion_learner.learning_data.emotion_patterns:
            for i, pattern in enumerate(emotion_learner.learning_data.emotion_patterns):
                with st.expander(f"パターン {i+1} ({pattern.touched_area}, 強さ: {pattern.stimulus_intensity:.1f})"):
                    st.write(f"部位: {pattern.touched_area}")
                    st.write(f"刺激の強さ: {pattern.stimulus_intensity:.2f}")
                    st.write(f"信頼度: {pattern.confidence:.2f}")
                    st.write(f"サンプル数: {pattern.sample_count}")
                    
                    st.write("感情値:")
                    st.json(pattern.emotion_values)
        else:
            st.info("まだ学習パターンがありません。感情分析ページでフィードバックを提供してください。")
            
    elif page == "デバイス設定":
        st.header("触覚フィードバックデバイス設定")
        
        st.markdown("""
        このページでは、触覚フィードバックデバイスの設定を行います。
        Arduino Uno R4 WiFiデバイスのIPアドレスとポートを設定し、
        感情分析結果に基づいた振動パターンを送信できるようにします。
        """)
        
        if "haptic_devices" not in st.session_state:
            st.session_state.haptic_devices = []
            
        if "haptic_initialized" not in st.session_state:
            st.session_state.haptic_initialized = False
            
        if st.session_state.haptic_devices:
            st.subheader("登録済みデバイス")
            
            for i, device in enumerate(st.session_state.haptic_devices):
                with st.expander(f"デバイス {i+1}: {device['device_id']} ({device['host']}:{device['port']})"):
                    st.write(f"デバイスID: {device['device_id']}")
                    st.write(f"ホスト: {device['host']}")
                    st.write(f"ポート: {device['port']}")
                    st.write(f"WebSocketパス: {device.get('ws_path', '/ws')}")
                    
                    if st.button(f"デバイス {i+1} を削除", key=f"delete_device_{i}"):
                        st.session_state.haptic_devices.pop(i)
                        st.session_state.haptic_initialized = False
                        st.experimental_rerun()
        else:
            st.info("登録済みデバイスはありません。以下のフォームからデバイスを追加してください。")
            
        st.subheader("デバイスを追加")
        
        with st.form("add_device_form"):
            device_id = st.text_input("デバイスID", value=f"device{len(st.session_state.haptic_devices) + 1}")
            host = st.text_input("ホスト (IPアドレス)", value="192.168.1.100")
            port = st.number_input("ポート", value=80, min_value=1, max_value=65535)
            ws_path = st.text_input("WebSocketパス", value="/ws")
            
            submitted = st.form_submit_button("デバイスを追加")
            
            if submitted:
                new_device = {
                    "device_id": device_id,
                    "host": host,
                    "port": port,
                    "ws_path": ws_path
                }
                
                st.session_state.haptic_devices.append(new_device)
                st.session_state.haptic_initialized = False
                st.success(f"デバイス '{device_id}' が追加されました")
                st.experimental_rerun()
                
        if st.session_state.haptic_devices:
            st.subheader("デバイス接続テスト")
            
            if st.button("接続テスト"):
                with st.spinner("デバイスに接続中..."):
                    initialized = run_async(haptic_feedback.initialize(st.session_state.haptic_devices))
                    
                    if initialized:
                        st.session_state.haptic_initialized = True
                        st.success("すべてのデバイスに正常に接続しました")
                        
                        status = run_async(haptic_feedback.get_all_device_status())
                        
                        if status:
                            st.subheader("デバイスの状態")
                            for device_id, device_status in status.items():
                                if device_status:
                                    st.write(f"デバイス '{device_id}': {device_status.device_state}")
                                else:
                                    st.warning(f"デバイス '{device_id}' の状態を取得できませんでした")
                    else:
                        st.error("デバイス接続に失敗しました。ホストとポートの設定を確認してください。")
                        
            if st.session_state.haptic_initialized:
                st.subheader("テスト振動パターン")
                
                emotion_category = st.selectbox(
                    "感情カテゴリ",
                    options=["joy", "anger", "sorrow", "pleasure"],
                    format_func=lambda x: {
                        "joy": "喜び",
                        "anger": "怒り",
                        "sorrow": "悲しみ",
                        "pleasure": "快楽"
                    }.get(x, x)
                )
                
                intensity = st.slider("感情強度", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
                
                if st.button("テストパターンを送信"):
                    with st.spinner("振動パターンを送信中..."):
                        emotion = Emotion(
                            joy=intensity if emotion_category == "joy" else 0.1,
                            fun=intensity if emotion_category == "pleasure" else 0.1,
                            anger=intensity if emotion_category == "anger" else 0.1,
                            sad=intensity if emotion_category == "sorrow" else 0.1
                        )
                        
                        results = run_async(haptic_feedback.websocket_manager.send_to_all(emotion, emotion_category))
                        
                        if results:
                            st.success("テストパターンを送信しました")
                            for device_id, success in results.items():
                                if success:
                                    st.info(f"デバイス '{device_id}' に正常に送信されました")
                                else:
                                    st.warning(f"デバイス '{device_id}' への送信に失敗しました")
                        else:
                            st.error("テストパターンの送信に失敗しました")
                            
                if st.button("振動を停止"):
                    with st.spinner("振動を停止中..."):
                        results = run_async(haptic_feedback.stop_all_devices())
                        
                        if results:
                            st.success("振動を停止しました")
                        else:
                            st.error("振動停止に失敗しました")


if __name__ == "__main__":
    load_dotenv()
    
    os.makedirs("data/feedback", exist_ok=True)
    
    main()
