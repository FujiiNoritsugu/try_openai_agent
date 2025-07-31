"""
人体部位選択コンポーネント。
"""

import os
import streamlit as st
from PIL import Image
from typing import Dict, List


def load_body_map() -> List[Dict[str, any]]:
    """人体画像のクリック可能な領域のマップを読み込む"""
    map_file = os.path.join("static", "images", "body_map.txt")
    body_map = []

    with open(map_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(",")
                if len(parts) == 5:
                    body_map.append(
                        {
                            "part": parts[0],
                            "x1": int(parts[1]),
                            "y1": int(parts[2]),
                            "x2": int(parts[3]),
                            "y2": int(parts[4]),
                        }
                    )

    return body_map


def clickable_body_part_selector() -> str:
    """クリック可能な人体画像を使った部位選択インターフェース"""
    from ...config import settings

    st.markdown("### 触れられた部位を選択")

    body_parts_desc = settings.ui.body_parts

    image_path = os.path.join("static", "images", "human_body.png")
    if not os.path.exists(image_path):
        st.error("人体画像が見つかりません。")
        return settings.ui.default_body_part  # デフォルト値を返す

    image = Image.open(image_path)

    if "selected_body_part" not in st.session_state:
        st.session_state.selected_body_part = settings.ui.default_body_part

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
        st.markdown(
            f"**{st.session_state.selected_body_part}**: {body_parts_desc[st.session_state.selected_body_part]}"
        )

    return st.session_state.selected_body_part
