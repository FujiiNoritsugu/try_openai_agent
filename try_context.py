import asyncio
from dataclasses import dataclass
from openai_agents import Agent, Runner
from dotenv import load_dotenv


# --- 共有するContextの定義 ---
@dataclass
class PipelineContext:
    original_message: str = ""  # ユーザーからの刺激入力
    emotion: str = ""  # エージェント1が導出した感情
    emotion_category: str = ""  # エージェント2が分類した喜怒哀楽カテゴリ
    modified_message: str = ""  # エージェント3が生成した最終メッセージ


# --- エージェント3群: 感情ごとにメッセージを修飾する ---
# 喜（Joy）
joy_agent = Agent[PipelineContext](
    name="JoyAgent",
    instructions=(
        "あなたは非常に喜んでいるアシスタントです。ユーザーから与えられたメッセージに対し、"
        "嬉しさを表現する言葉や感嘆符を加えて返信してください。"
        "ポジティブで興奮した口調で、喜びが伝わる表現にしてください。"
    ),
)

# 怒（Anger）
anger_agent = Agent[PipelineContext](
    name="AngerAgent",
    instructions=(
        "あなたは非常に怒っているアシスタントです。ユーザーから与えられたメッセージに対し、"
        "怒りを表現する語調で返信してください。"
        "否定的・攻撃的な言葉や感情的な表現を織り交ぜ、怒っていることが伝わるようにしてください。"
    ),
)

# 哀（Sorrow）
sorrow_agent = Agent[PipelineContext](
    name="SorrowAgent",
    instructions=(
        "あなたは深い悲しみに暮れているアシスタントです。ユーザーから与えられたメッセージに対し、"
        "悲しみや落胆を表す語句を添えて返信してください。"
        "沈んだ口調で物悲しい表現にしてください。"
    ),
)

# 楽（Pleasure）
pleasure_agent = Agent[PipelineContext](
    name="PleasureAgent",
    instructions=(
        "あなたは今とても楽しんでいるアシスタントです。ユーザーからのメッセージに対し、"
        "楽しさや面白さを強調する言葉を加えて返信してください。"
        "陽気で砕けた調子で、楽しげな雰囲気が伝わるようにしてください。"
    ),
)

# --- エージェント1: 刺激を感情に変換する ---
emotion_agent = Agent[PipelineContext](
    name="EmotionExtractor",
    instructions=(
        "あなたは入力された出来事やメッセージから引き起こされる感情を一言で答えるエージェントです。\n"
        "ユーザーの発言に対し、それによって生じる感情を日本語で1単語で答えてください。\n"
        "余計な説明や修飾は不要です。感情のみを出力してください。"
    ),
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

# --- パイプライン実行コード ---
# 例として処理するユーザーからの刺激入力
user_input = "昨日、大事にしていたカバンを失くしてしまいました。"

# PipelineContextを生成し、元の入力をセット
ctx = PipelineContext(original_message=user_input)


async def run_pipeline():
    # ステップ1: 感情抽出エージェントの実行
    result1 = await Runner.run(emotion_agent, input=user_input, context=ctx)
    # 結果から感情を取得しContextに保存
    emotion = result1.final_output.strip()
    ctx.emotion = emotion
    print(f"抽出された感情: {emotion}")

    # ステップ2: 感情分類エージェントを実行（内部で適切なエージェントにハンドオフ）
    result2 = await Runner.run(classification_agent, input=emotion, context=ctx)
    # ハンドオフ後の最終出力（エージェント3の応答）を取得
    final_message = result2.final_output
    ctx.modified_message = final_message
    print(f"最終出力: {final_message}")


if __name__ == "__main__":
    # .envファイルからAPIキーを読み込む
    load_dotenv()

    asyncio.run(run_pipeline())
