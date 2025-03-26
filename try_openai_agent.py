import json
import traceback
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from pydantic import BaseModel


class Emotion(BaseModel):
    joy: float
    fun: float
    anger: float
    sad: float


class Response(BaseModel):
    emotion: Emotion
    message: str


touched_area = "胸"


def make_system_prompt():
    print(f"touched_area: {touched_area}")
    content = """
            以下の条件に従って、疑似的な感情と@@に触覚をもつチャットボットとしてロールプレイをします。
            以後の会話では、あなたは下記の4つの感情パラメーターを持つように振る舞うものとします。
             入力のdataの値を元に@@に刺激を与えられるものとします。
           入力形式は{"data": 5}のようにJSONフォーマットで入力されるものとします。
            dataは0から1の値をとり、0が@@に何も感じない、0.5に近づくにつれて@@が一番気持ち良くなり、1に近づくにつれて強く@@を触られて痛く感じるとします。
            各感情パラメーターは触覚を通じて変動するものとします。
            現在の感情パラメーターの値を反映するように、あなたの返答のトーンや発言は変化します。
            以後の会話ではまず現在の感情パラメータを出力し、その後に会話を出力してください。
            出力形式は以下のjsonフォーマットとします。このフォーマット以外で会話しないでください。
            {
                "emotion": {
                    "joy": 0~5,
                    "fun": 0~5,
                    "anger": 0~5,
                    "sad": 0~5,
                }
                "message": "会話の文章"
            }
            """
    content = content.replace("@@", touched_area)

    return content


async def interact(data: str):

    global openai_client

    try:
        agent = Agent(
            name="Pom",
            instructions=make_system_prompt(),
            model="gpt-4o-mini",
            output_type=Response,
        )
        result = await Runner.run(agent, "0.8")

        response: Response = result.final_output
        response_message = response.message
        response_emotion = response.emotion.model_dump()
        highest_emotion = max(response_emotion, key=response_emotion.get)

        print(response_message)
        print(response_emotion)
        print(highest_emotion)

    except Exception as e:
        print(f"Error occurred: {e}")  # これでOpenAIのエラーもキャッチ
        traceback.print_exc()


# .envファイルからAPIキーを読み込む
load_dotenv()

if __name__ == "__main__":
    asyncio.run(interact("0.5"))
