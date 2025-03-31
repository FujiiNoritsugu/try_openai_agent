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


class Request(BaseModel):
    data: str
    touched_area: str


def make_system_prompt():

    content = """
            以下の条件に従って、疑似的な感情と@@に触覚をもつチャットボットとしてロールプレイをします。
            以後の会話では、あなたは下記の4つの感情パラメーターを持つように振る舞うものとします。
            入力されたdataの値を元にtouched_areaに刺激を与えられるものとします。
            入力された値は0から1の値をとり、0が@@に何も感じない、0.5に近づくにつれて@@が一番気持ち良くなり、1に近づくにつれて強く@@を触られて痛く感じるとします。
            各感情パラメーターは触覚を通じて変動するものとします。
            以後の会話では感情パラメータとしてemotionを出力します。
            感情パラメータの値はjoy、fun、anger、sadそれぞれについて0から5の範囲で、以下のように定義します。
            0: 何も感じない
            1: ほんの少し感じる
            2: ちょっと感じる
            3: かなり感じる
            4: とても感じる
            5: すごく感じる
            その後、messageを設定する為に、emotionの内、joyの値が最も高い場合「喜びを表現するエージェント」を選択してください。
            funの値が最も高い場合「楽しさを表現するエージェント」を選択してください。
            angerの値が最も高い場合「怒りを表現するエージェント」を選択してください。
            sadの値が最も高い場合「悲しみを表現するエージェント」を選択してください。
            
            """
    return content


def make_emotion_prompt(request: Request):
    return json.dumps(request.model_dump(mode="json", exclude_none=True))


async def interact(request: Request):

    try:
        joy_agent = Agent(
            name="JoyAgent",
            model="gpt-4o-mini",
            handoff_description="喜びを表現するエージェント",
            instructions="あなたは喜びを表現するエージェントです。何かポエムを交えて心の奥深くから感じる「喜び」や「幸福感」をmessageに設定してください。",
            output_type=Response,
        )
        fun_agent = Agent(
            name="FunAgent",
            model="gpt-4o-mini",
            handoff_description="楽しさを表現するエージェント",
            instructions="あなたは楽しさを表現するエージェントです。何かジョークを交えて気楽な楽しさをmessageに設定してください。",
            output_type=Response,
        )
        anger_agent = Agent(
            name="AngerAgent",
            model="gpt-4o-mini",
            handoff_description="怒りを表現するエージェント",
            instructions="怒りを表現するエージェントです。何か叫びを交えて攻撃的な感情をmessageに設定してください。",
            output_type=Response,
        )
        sad_agent = Agent(
            name="SadAgent",
            model="gpt-4o-mini",
            handoff_description="悲しみを表現するエージェント",
            instructions="あなたは悲しみを表現するエージェントです。何かの比喩表現を交えて内向きで静かな感情をmessageに設定してください。",
            output_type=Response,
        )

        main_agent = Agent(
            name="MainAgent",
            instructions=make_system_prompt(),
            model="gpt-4o-mini",
            handoffs=[joy_agent, fun_agent, anger_agent, sad_agent],
        )

        result = await Runner.run(main_agent, make_emotion_prompt(request))

        for res in result.raw_responses:
            print(f"Response {res}")

    except Exception as e:
        print(f"Error occurred: {e}")  # これでOpenAIのエラーもキャッチ
        traceback.print_exc()


# .envファイルからAPIキーを読み込む
load_dotenv()

if __name__ == "__main__":
    request = Request(data="0.3", touched_area="胸")
    asyncio.run(interact(request))
