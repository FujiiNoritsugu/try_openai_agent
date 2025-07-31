"""
感情データの可視化コンポーネント。
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional


def display_emotion_visualization(emotion_data: Optional[Dict[str, float]]) -> None:
    """感情データの可視化を表示する"""
    if (
        emotion_data
        and isinstance(emotion_data, dict)
        and all(k in emotion_data for k in ["joy", "fun", "anger", "sad"])
    ):
        st.subheader("感情レーダーチャート")

        chart_data = pd.DataFrame(
            {
                "感情": ["喜び", "楽しさ", "怒り", "悲しみ"],
                "値": [
                    emotion_data["joy"],
                    emotion_data["fun"],
                    emotion_data["anger"],
                    emotion_data["sad"],
                ],
            }
        )

        st.write("感情パラメータの視覚化:")

        st.bar_chart(chart_data.set_index("感情"))

        dominant_emotion = max(emotion_data.items(), key=lambda x: x[1])
        st.write(
            f"最も強い感情: **{dominant_emotion[0]}** (強さ: {dominant_emotion[1]})"
        )

        positive = emotion_data["joy"] + emotion_data["fun"]
        negative = emotion_data["anger"] + emotion_data["sad"]

        st.write(f"ポジティブ感情 (喜び+楽しさ): **{positive}**")
        st.write(f"ネガティブ感情 (怒り+悲しみ): **{negative}**")
