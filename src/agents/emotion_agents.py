"""
OpenAIエージェントパイプライン用の感情エージェント。
"""
from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from ..models.data_models import PipelineContext, HandoffOutput, OriginalOutput

EMOTION_AGENT_INSTRUCTION = """
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

JOY_AGENT_INSTRUCTION = (
    "あなたは喜びを表現するエージェントです。"
    "何かポエムを交えて心の奥深くから感じる「喜び」や「幸福感」をmessageに出力してください"
)

ANGER_AGENT_INSTRUCTION = (
    "あなたは怒りを表現するエージェントです。"
    "何か叫びを交えて攻撃的な感情をmessageに出力してください"
)

SORROW_AGENT_INSTRUCTION = (
    "あなたは悲しみを表現するエージェントです。"
    "何かの比喩表現を交えて内向きで静かな感情をmessageに出力してください。"
)

PLEASURE_AGENT_INSTRUCTION = (
    "あなたは楽しさを表現するエージェントです。"
    "何かジョークを交えて気楽な楽しさをmessageに出力してください。"
)

CLASSIFICATION_AGENT_INSTRUCTION = (
    "与えられた感情が『喜』『怒』『哀』『楽』のどれに属するか判断し、"
    "emotion_categoryに判断した感情を『喜』『怒』『哀』『楽』のいずれかで出力してください。"
    "このエージェントではmessageには一切出力せず、ハンドオフを行うエージェントに設定してもらってください。"
    "その後、該当するカテゴリのエージェントにハンドオフしてください。"
    "適切なエージェントへのハンドオフを行ってください。"
)

joy_agent = Agent[PipelineContext](
    name="JoyAgent",
    instructions=JOY_AGENT_INSTRUCTION,
    output_type=HandoffOutput,
)

anger_agent = Agent[PipelineContext](
    name="AngerAgent",
    instructions=ANGER_AGENT_INSTRUCTION,
    output_type=HandoffOutput,
)

sorrow_agent = Agent[PipelineContext](
    name="SorrowAgent",
    instructions=SORROW_AGENT_INSTRUCTION,
    output_type=HandoffOutput,
)

pleasure_agent = Agent[PipelineContext](
    name="PleasureAgent",
    instructions=PLEASURE_AGENT_INSTRUCTION,
    output_type=HandoffOutput,
)

emotion_agent = Agent[PipelineContext](
    name="EmotionExtractor",
    instructions=EMOTION_AGENT_INSTRUCTION,
    output_type=OriginalOutput,
)

classification_agent = Agent[PipelineContext](
    name="EmotionClassifier",
    instructions=CLASSIFICATION_AGENT_INSTRUCTION,
    handoffs=[joy_agent, anger_agent, sorrow_agent, pleasure_agent],
    output_type=HandoffOutput,
)
