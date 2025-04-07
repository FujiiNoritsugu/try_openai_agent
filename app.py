"""
Streamlit UI for the OpenAI agent pipeline.
"""
import asyncio
import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import pandas as pd

from src.models.data_models import UserInput
from src.pipeline.pipeline import run_pipeline, format_pipeline_results


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
    
    body_map = load_body_map()
    
    if 'selected_body_part' not in st.session_state:
        st.session_state.selected_body_part = "胸"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        clicked = st.image(image, use_column_width=True)
        
        if clicked:
            st.markdown("画像上の部位をクリックしてください（以下のボタンで部位を選択できます）")
            
            buttons_col1, buttons_col2, buttons_col3 = st.columns(3)
            
            with buttons_col1:
                if st.button("頭部"):
                    st.session_state.selected_body_part = "頭"
                if st.button("顔"):
                    st.session_state.selected_body_part = "顔"
                if st.button("首"):
                    st.session_state.selected_body_part = "首"
                if st.button("肩"):
                    st.session_state.selected_body_part = "肩"
            
            with buttons_col2:
                if st.button("腕"):
                    st.session_state.selected_body_part = "腕"
                if st.button("手"):
                    st.session_state.selected_body_part = "手"
                if st.button("胸"):
                    st.session_state.selected_body_part = "胸"
                if st.button("腹"):
                    st.session_state.selected_body_part = "腹"
            
            with buttons_col3:
                if st.button("腰"):
                    st.session_state.selected_body_part = "腰"
                if st.button("臀部"):
                    st.session_state.selected_body_part = "臀部"
                if st.button("脚"):
                    st.session_state.selected_body_part = "脚"
                if st.button("足"):
                    st.session_state.selected_body_part = "足"
    
    with col2:
        st.subheader("選択された部位")
        st.markdown(f"**{st.session_state.selected_body_part}**")
        st.caption(body_parts_desc[st.session_state.selected_body_part])
        
        st.markdown("### 部位の説明")
        for part, desc in body_parts_desc.items():
            if part == st.session_state.selected_body_part:
                st.markdown(f"**{part}**: {desc}")
    
    return st.session_state.selected_body_part


def main():
    """Main function for the Streamlit UI."""
    st.title("感情エージェントパイプライン")
    st.markdown("""
    このアプリケーションは、ユーザー入力（刺激の強さと触れられた部位）から感情を抽出・分類し、
    適切な感情応答を生成します。
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
    
    touched_area = clickable_body_part_selector()
    
    if st.button("感情を分析"):
        with st.spinner("感情を分析中..."):
            user_input = UserInput(data=str(data_value), touched_area=touched_area)
            
            ctx, error = run_async(run_pipeline(user_input))
            
            if error:
                st.error(f"エラーが発生しました: {error}")
            else:
                results = format_pipeline_results(ctx)
                
                st.header("結果")
                
                st.subheader("抽出された感情")
                st.json(results["extracted_emotion"])
                
                st.subheader("元のメッセージ")
                st.write(results["original_message"])
                
                st.subheader("感情カテゴリ")
                st.write(results["emotion_category"])
                
                st.subheader("最終メッセージ")
                st.write(results["final_message"])


if __name__ == "__main__":
    load_dotenv()
    
    main()
