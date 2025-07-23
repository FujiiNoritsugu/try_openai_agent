# CLAUDE.md

このファイルは、このリポジトリのコードを扱う際のClaude Code (claude.ai/code) へのガイダンスを提供します。

## プロジェクト概要

感情エージェントパイプラインアプリケーション：
- ユーザー入力（刺激の強さと触れられた部位）から感情を抽出
- 感情を日本語のカテゴリ（喜怒哀楽）に分類
- 専門化されたエージェントを使用して適切な感情応答を生成

## コマンド

### 開発環境のセットアップ
```bash
# 依存関係のインストール（UVパッケージマネージャーを使用）
pip install -e .

# 環境設定
# .envファイルを作成し、以下を設定: OPENAI_API_KEY=your_api_key
```

### アプリケーションの実行
```bash
# コマンドラインインターフェース
python -m src.main

# Streamlit UI（推奨）
streamlit run app.py
```

### コード品質
```bash
# Blackでコードをフォーマット
black src/

# テストの実行
pytest
```

## アーキテクチャ

### エージェントパイプラインフロー
1. **ユーザー入力**: 刺激の強さ（0-1の浮動小数点数）+ 体の部位
2. **EmotionExtractorAgent** → 4つの感情（joy, fun, anger, sad）を抽出
3. **EmotionClassifierAgent** → 喜/怒/哀/楽にカテゴライズ
4. **感情応答エージェント** → JoyAgent/AngerAgent/SorrowAgent/PleasureAgentが最終応答を生成

### 主要コンポーネント
- `src/models/`: 型安全なデータ処理のためのPydanticモデル
- `src/agents/`: openai-agentsを使用した個別エージェント実装
- `src/pipeline/`: パイプラインオーケストレーションロジック
- `app.py`: インタラクティブな人体可視化を含むStreamlit UI

### エージェントハンドオフパターン
ClassifierAgentは適切な感情エージェントにルーティングするためにハンドオフを使用：
```python
return agent_registry.get_handoff(agent_name)
```

## 重要事項

- Python 3.12以上が必要
- すべてのエージェントはOpenAIのGPT-4モデルを使用
- 体の部位は日本語（頭、胸、お腹など）
- UIには部位選択のためのインタラクティブな人体画像が含まれる
- 環境変数OPENAI_API_KEYの設定が必須