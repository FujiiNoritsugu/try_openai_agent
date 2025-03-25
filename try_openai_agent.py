from openai import OpenAI
import json
import traceback
import asyncio

SPEAKER_ID_CHATGPT = 0
FETCH_INTERVAL = 1  # 1秒ごとにリクエストを送信

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
        system_prompt = make_system_prompt()
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": data,
                },
            ],
        )
        temp = completion.choices[0].message.content
        print(temp)
        response = json.loads(temp)
        response_message = response["message"]
        response_emotion = response["emotion"]
        highest_emotion = max(response_emotion, key=response_emotion.get)

        print(response_message)
        print(highest_emotion)

    except Exception as e:
        print(f"Error occurred: {e}")  # これでOpenAIのエラーもキャッチ
        traceback.print_exc()


# メイン処理
# ファイルを開く
with open("../chat_gpt_api_key", "r") as file:
    # ファイルからデータを読み込む
    data = file.read().strip()

global openai_client
openai_client = OpenAI(api_key=data)


if __name__ == "__main__":
    asyncio.run(interact(0.5))
