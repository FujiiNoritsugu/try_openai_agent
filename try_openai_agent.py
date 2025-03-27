import json
import traceback
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from pydantic import BaseModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


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
            以後の会話ではまず現在の感情パラメータを出力し、感情パラメータの値に対応するエージェントに振り分けた後、メッセージを出力してください。
            感情パラメータの値は0から5の範囲で、以下のように定義します。
            0: 何も感じない
            1: ほんの少し感じる
            2: ちょっと感じる
            3: かなり感じる
            4: とても感じる
            5: すごく感じる
            感情パラメータの値が最も高いものを「最も強い感情」とし、以下の対応で他のエージェントに振り分けてください。
            1. joyが最も高い場合は、あなたは「喜びを表現するエージェント」に振り分けてください。
            2. funが最も高い場合は、あなたは「楽しさを表現するエージェント」に振り分けてください。
            3. angerが最も高い場合は、あなたは「怒りを表現するエージェント」に振り分けてください。
            4. sadが最も高い場合は、あなたは「悲しみを表現するエージェント」に振り分けてください。
            5. 感情パラメータが同じ場合は、joy>fun>anger>sadの順で優先順位をつけてください。
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
        joy_agent = Agent(
            name="JoyAgent",
            model="gpt-4o-mini",
            output_type=Response,
            handoff_description="喜びを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは喜びを表現するエージェントです。何かポエムを交えて心の奥深くから感じる「喜び」や「幸福感」をメッセージに追加してください。",
            ),
        )
        fun_agent = Agent(
            name="FunAgent",
            model="gpt-4o-mini",
            output_type=Response,
            handoff_description="楽しさを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは楽しさを表現するエージェントです。何かジョークを交えて気楽な楽しさをメッセージに追加してください。",
            ),
        )
        anger_agent = Agent(
            name="AngerAgent",
            model="gpt-4o-mini",
            output_type=Response,
            handoff_description="怒りを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは怒りを表現するエージェントです。何か叫びを交えて攻撃的な感情をメッセージに追加してください。",
            ),
        )
        sad_agent = Agent(
            name="SadAgent",
            model="gpt-4o-mini",
            output_type=Response,
            handoff_description="悲しみを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは悲しみを表現するエージェントです。何かの比喩表現を交えて内向きで静かな感情をメッセージに追加してください。",
            ),
        )

        main_agent = Agent(
            name="MainAgent",
            instructions=prompt_with_handoff_instructions(make_system_prompt()),
            model="gpt-4o-mini",
            handoffs=[joy_agent, fun_agent, anger_agent, sad_agent],
            output_type=Response,
        )

        result = await Runner.run(main_agent, "0.9")

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
