"""
Google ADKを使用した感情エージェント。
"""

from .google_adk_factory import agent_factory

# エージェントインスタンスを作成
emotion_agent = agent_factory.create_emotion_extractor()
joy_agent = agent_factory.create_joy_agent()
anger_agent = agent_factory.create_anger_agent()
sorrow_agent = agent_factory.create_sorrow_agent()
pleasure_agent = agent_factory.create_pleasure_agent()
classification_agent = agent_factory.create_classifier_agent()