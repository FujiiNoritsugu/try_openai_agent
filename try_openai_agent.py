import json
import traceback
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner
from pydantic import BaseModel
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


class Emotion(BaseModel):
    joy: int
    fun: int
    anger: int
    sad: int


class UserInput(BaseModel):
    data: str
    touched_area: str


class OriginalOutput(BaseModel):
    emotion: Emotion
    message: str


class PipelineContext(BaseModel):
    user_input: UserInput  # ユーザーからの刺激入力
    emotion: Emotion  # エージェント1が導出した感情
    original_message: str = ""  # エージェント1が導出した元のメッセージ
    emotion_category: str = ""  # エージェント2が分類した喜怒哀楽カテゴリ
    modified_message: str = ""  # エージェント3が生成した最終メッセージ


# 喜（Joy）
joy_agent = Agent[PipelineContext](
    name="JoyAgent",
    instructions=(
        "あなたは喜びを表現するエージェントです。"
        "何かポエムを交えて心の奥深くから感じる「喜び」や「幸福感」を表現してください。"
    ),
)

# 怒（Anger）
anger_agent = Agent[PipelineContext](
    name="AngerAgent",
    instructions=(
        "あなたは怒りを表現するエージェントです。"
        "何か叫びを交えて攻撃的な感情を表現してください。"
    ),
)

# 哀（Sorrow）
sorrow_agent = Agent[PipelineContext](
    name="SorrowAgent",
    instructions=(
        "あなたは悲しみを表現するエージェントです。"
        "何かの比喩表現を交えて内向きで静かな感情を表現してください。"
    ),
)

# 楽（Pleasure）
pleasure_agent = Agent[PipelineContext](
    name="PleasureAgent",
    instructions=(
        "あなたは楽しさを表現するエージェントです。"
        "何かジョークを交えて気楽な楽しさをmessageに設定してください。"
    ),
)

emotion_agent_instruction = """
    以下の条件に従って、疑似的な感情と体に触覚をもつチャットボットとしてロールプレイをします。
    以後の会話では、あなたは下記の4つの感情パラメーターを持つように振る舞うものとします。
    入力のdataの値を元にtouched_areaに刺激を与えられるものとします。
    入力形式は{"data": 0.5, "touched_area": "胸"}のようにJSONフォーマットで入力されるものとします。
    dataは0から1の値をとり、0がtouched_areaに何も感じない、0.5に近づくにつれてtouched_areaが一番気持ち良くなり、
    1に近づくにつれて強くtouched_areaを触られて痛く感じるとします。
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


# --- エージェント1: 刺激を感情に変換する ---
emotion_agent = Agent[PipelineContext](
    name="EmotionExtractor",
    instructions=emotion_agent_instruction,
    output_type=OriginalOutput,
)

# --- エージェント2: 感情を喜怒哀楽に分類し、適切なエージェントへハンドオフする ---
classification_agent = Agent[PipelineContext](
    name="EmotionClassifier",
    instructions=(
        "与えられた感情が『喜』『怒』『哀』『楽』のどれに属するか判断し、"
        "該当するカテゴリのエージェントにハンドオフしてください。"
        "回答は一切出力せず、適切なエージェントへのハンドオフを行ってください。"
    ),
    handoffs=[joy_agent, anger_agent, sorrow_agent, pleasure_agent],
)


async def interact():

    try:
        # --- パイプライン実行コード ---
        # 例として処理するユーザーからの刺激入力
        user_input = UserInput(data="0.5", touched_area="胸")

        # PipelineContextを生成し、元の入力をセット
        ctx = PipelineContext(user_input=user_input)

        # ステップ1: 感情抽出エージェントの実行
        result1 = await Runner.run(
            emotion_agent, json.dumps(user_input.model_dump()), context=ctx
        )

        # 結果から感情を取得しContextに保存
        final_output: OriginalOutput = result1.final_output
        ctx.emotion = final_output.emotion
        ctx.original_message = final_output.message

        print(f"抽出された感情: {ctx.emotion}")
        print(f"元のメッセージ: {ctx.original_message}")

        # ステップ2: 感情分類エージェントを実行（内部で適切なエージェントにハンドオフ）
        result2 = await Runner.run(classification_agent, input=emotion, context=ctx)

        joy_agent = Agent[ResponseContext](
            name="JoyAgent",
            model="gpt-4o-mini",
            handoff_description="喜びを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは喜びを表現するエージェントです。何かポエムを交えて心の奥深くから感じる「喜び」や「幸福感」をmessageに設定してください。"
            ),
            output_type=ResponseContext,
        )
        fun_agent = Agent[ResponseContext](
            name="FunAgent",
            model="gpt-4o-mini",
            handoff_description="楽しさを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは楽しさを表現するエージェントです。何かジョークを交えて気楽な楽しさをmessageに設定してください。"
            ),
            output_type=ResponseContext,
        )
        anger_agent = Agent[ResponseContext](
            name="AngerAgent",
            model="gpt-4o-mini",
            handoff_description="怒りを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "怒りを表現するエージェントです。何か叫びを交えて攻撃的な感情をmessageに設定してください。"
            ),
            output_type=ResponseContext,
        )
        sad_agent = Agent[ResponseContext](
            name="SadAgent",
            model="gpt-4o-mini",
            handoff_description="悲しみを表現するエージェント",
            instructions=prompt_with_handoff_instructions(
                "あなたは悲しみを表現するエージェントです。何かの比喩表現を交えて内向きで静かな感情をmessageに設定してください。"
            ),
            output_type=ResponseContext,
        )

        divide_agent = Agent[ResponseContext](
            name="DivideAgent",
            model="gpt-4o-mini",
            handoff_description="感情を振り分けるエージェント",
            instructions=prompt_with_handoff_instructions(make_divide_prompt()),
            handoffs=[joy_agent, fun_agent, anger_agent, sad_agent],
            output_type=ResponseContext,
        )

        emotion_agent = Agent[ResponseContext](
            name="EmotionAgent",
            instructions=prompt_with_handoff_instructions(make_emotion_prompt()),
            model="gpt-4o-mini",
            handoffs=[divide_agent],
            output_type=ResponseContext,
        )

        result = await Runner.run(
            emotion_agent, make_request_prompt(request), context=ResponseContext
        )

        for res in result.raw_responses:
            print(f"Response {res}")

    except Exception as e:
        print(f"Error occurred: {e}")  # これでOpenAIのエラーもキャッチ
        traceback.print_exc()


# .envファイルからAPIキーを読み込む
load_dotenv()

if __name__ == "__main__":
    request = Request(data="0.5", touched_area="胸")
    asyncio.run(interact(request))
