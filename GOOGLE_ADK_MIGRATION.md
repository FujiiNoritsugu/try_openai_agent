# Google ADK移行ガイド

このドキュメントでは、OpenAI Agent SDKからGoogle Agent Development Kit (ADK)への移行について説明します。

## 移行の概要

OpenAI Agent SDKを使用していた感情エージェントパイプラインを、Google ADKを使用するように書き換えました。主な変更点は以下の通りです：

1. **依存関係の更新**: `openai-agents`を`google-adk`に置き換え
2. **エージェント作成方法の変更**: Google ADKの`Agent`クラスを使用
3. **ハンドオフ機構の実装**: `sub_agents`パラメータを使用した自動ルーティング
4. **実行方法の変更**: Google ADKの`Runner`と`SessionService`を使用

## セットアップ

### 1. 環境変数の設定

`.env`ファイルに以下を追加してください：

```bash
# 既存のOpenAI APIキー（互換性のために残す）
OPENAI_API_KEY=your_openai_api_key

# Google Gemini APIキー（新規追加）
GOOGLE_API_KEY=your_google_api_key
```

### 2. 依存関係のインストール

```bash
pip install -e .
```

## 使用方法

### コマンドラインインターフェース

```bash
# Google ADK版を実行
python -m src.google_adk_main
```

### Streamlit UI

```bash
# Google ADK版のUIを起動
streamlit run google_adk_app.py
```

## 主な変更点

### 1. エージェントファクトリー

**旧版 (OpenAI SDK)**:
```python
from agents import Agent
Agent[PipelineContext](
    name="EmotionExtractor",
    instructions=AgentInstructions.EMOTION_EXTRACTOR,
    output_type=OriginalOutput,
)
```

**新版 (Google ADK)**:
```python
from google_adk import Agent
Agent(
    name="EmotionExtractor",
    model="gemini-1.5-flash",
    description="ユーザー入力から感情を抽出するエージェント",
    instruction=AgentInstructions.EMOTION_EXTRACTOR,
    tools=[self._extract_emotion_tool]
)
```

### 2. ハンドオフの実装

**旧版**: `handoffs`パラメータを使用
**新版**: `sub_agents`パラメータを使用し、自動的にルーティング

### 3. パイプライン実行

**旧版**:
```python
from agents import Runner
result = await Runner.run(agent, input, context=context)
```

**新版**:
```python
from google_adk import Runner, SessionService
runner = Runner(agent=agent, session_service=SessionService())
result = await runner.run(input)
```

## ファイル構成

Google ADK版の新しいファイル：

- `/src/agents/google_adk_factory.py` - Google ADKを使用したエージェントファクトリー
- `/src/agents/google_adk_emotion_agents.py` - エージェントインスタンス
- `/src/pipeline/google_adk_emotion_processor.py` - 感情処理ロジック
- `/src/pipeline/google_adk_emotion_classifier.py` - 感情分類ロジック
- `/src/pipeline/google_adk_pipeline.py` - パイプライン実行ロジック
- `/src/google_adk_main.py` - CLIエントリーポイント
- `/google_adk_app.py` - Streamlit UIエントリーポイント

## 注意事項

1. Google ADKはGemini 1.5 Flashモデルを使用しています
2. 構造化された出力の処理方法が異なるため、一部のロジックを調整しています
3. 元のOpenAI SDK版のファイルはそのまま残してあるので、必要に応じて参照できます

## トラブルシューティング

### GOOGLE_API_KEYが設定されていないエラー

`.env`ファイルにGOOGLE_API_KEYを追加してください。

### モデルエラー

Google ADKは`litellm`を使用して複数のモデルをサポートしています。必要に応じて、`model`パラメータを変更できます：
- `gemini-1.5-flash`（デフォルト）
- `gpt-4`（OpenAI APIキーが必要）
- `claude-3-opus`（Anthropic APIキーが必要）

### 非同期実行エラー

Google ADKはasync/awaitパターンを使用します。適切な非同期コンテキストで実行してください。