"""
Streamlit UI for the OpenAI agent pipeline.
"""
import asyncio
import streamlit as st
from dotenv import load_dotenv

from src.models.data_models import UserInput
from src.pipeline.pipeline import run_pipeline, format_pipeline_results


def run_async(coroutine):
    """Run an async function from a synchronous context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)


def human_body_part_selector():
    """人体アイコンを使った部位選択インターフェース"""
    st.markdown("### 触れられた部位を選択")
    
    body_parts = {
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
    
    human_icon = """
        頭
        |
    肩-顔-肩
     |  |  |
    腕 首 腕
     |  |  |
    手 胸 手
        |
        腹
        |
        腰
        |
       臀部
       /  \\
     脚    脚
     |      |
     足    足
    """
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.code(human_icon, language=None)
    
    with col2:
        selected_part = st.radio(
            "部位を選択",
            options=list(body_parts.keys()),
            index=list(body_parts.keys()).index("胸"),
            key="body_part_selector"
        )
        st.caption(f"選択: {selected_part} - {body_parts[selected_part]}")
    
    return selected_part


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
    
    touched_area = human_body_part_selector()
    
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
