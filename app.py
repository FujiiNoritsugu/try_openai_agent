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
    
    body_parts = ["頭", "顔", "首", "肩", "腕", "手", "胸", "腹", "腰", "臀部", "脚", "足"]
    touched_area = st.selectbox("触れられた部位", body_parts, index=body_parts.index("胸"))
    
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
