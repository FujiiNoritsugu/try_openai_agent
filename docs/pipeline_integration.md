# パイプライン統合ガイド

このドキュメントでは、感情分析パイプラインと触覚フィードバックデバイスの統合方法について説明します。

## 概要

パイプライン統合モジュールは、感情分析パイプラインの結果を触覚フィードバックデバイスに送信するための橋渡しとなります。このモジュールを使用することで、感情分析の結果に基づいて適切な振動パターンをArduino Uno R4 WiFiデバイスに送信し、物理的なフィードバックを提供することができます。

## アーキテクチャ

パイプライン統合は以下のコンポーネントで構成されています：

1. **HapticFeedbackIntegration**: 感情分析パイプラインと触覚フィードバックデバイスを統合するメインクラス
2. **WebSocketControllerManager**: 複数のWebSocketコントローラーを管理するクラス
3. **VibrationPatternGenerator**: 感情データに基づいて振動パターンを生成するクラス

これらのコンポーネントが連携して、感情分析の結果を物理的な振動パターンに変換します。

```
感情分析パイプライン → HapticFeedbackIntegration → WebSocketControllerManager → Arduino Uno R4 WiFi
```

## 使用方法

### 1. 初期化

```python
from src.devices.pipeline_integration import haptic_feedback

# デバイス設定
device_configs = [
    {
        "device_id": "device1",
        "host": "192.168.1.100",  # Arduinoデバイスのホスト
        "port": 80
    }
]

# 触覚フィードバックシステムの初期化
await haptic_feedback.initialize(device_configs)
```

### 2. パイプラインの実行と結果の送信

```python
from src.models.data_models import UserInput

# ユーザー入力の作成
user_input = UserInput(
    data="0.7",  # 刺激の強さ（0.0-1.0）
    touched_area="胸",  # 触れられた部位
    gender="男性"  # 性別
)

# パイプラインを実行し、結果を触覚フィードバックデバイスに送信
results, device_results = await haptic_feedback.run_pipeline_and_send(user_input)
```

### 3. デバイスの状態取得

```python
# デバイスの状態を取得
status = await haptic_feedback.get_all_device_status()
```

### 4. 振動の停止

```python
# 振動を停止
await haptic_feedback.stop_all_devices()
```

### 5. シャットダウン

```python
# 触覚フィードバックシステムのシャットダウン
await haptic_feedback.shutdown()
```

## Streamlit UIでの使用

アプリケーションには、触覚フィードバックデバイスを設定・管理するための専用ページが追加されています。

1. **デバイス設定ページ**: デバイスの追加、削除、接続テスト
2. **テスト振動パターン**: 異なる感情カテゴリと強度でテスト振動パターンを送信
3. **感情分析との統合**: 感情分析結果を自動的に触覚フィードバックデバイスに送信

## エラーハンドリング

パイプライン統合モジュールには、以下のエラーハンドリングメカニズムが実装されています：

1. **接続エラー**: デバイスに接続できない場合、適切なエラーメッセージを表示し、通常のパイプラインにフォールバック
2. **送信エラー**: 振動パターンの送信に失敗した場合、再試行メカニズムを使用
3. **デバイス状態エラー**: デバイスの状態を取得できない場合、エラーをログに記録

## 高度な使用例

### 複数デバイスの同時制御

```python
# 複数デバイスの設定
device_configs = [
    {
        "device_id": "device1",
        "host": "192.168.1.100",
        "port": 80
    },
    {
        "device_id": "device2",
        "host": "192.168.1.101",
        "port": 80
    }
]

# 触覚フィードバックシステムの初期化
await haptic_feedback.initialize(device_configs)

# パイプラインを実行し、すべてのデバイスに結果を送信
results, device_results = await haptic_feedback.run_pipeline_and_send(user_input)
```

### カスタム感情データの送信

```python
from src.models.data_models import Emotion, PipelineContext

# カスタム感情データの作成
emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)

# パイプラインコンテキストの作成
ctx = PipelineContext()
ctx.emotion = emotion
ctx.emotion_category = "joy"

# パイプラインコンテキストを処理し、デバイスに送信
results = await haptic_feedback.process_pipeline_result(ctx)
```

## トラブルシューティング

### デバイスに接続できない

1. デバイスのIPアドレスとポートが正しいことを確認
2. デバイスがWiFiネットワークに接続されていることを確認
3. デバイスのファイアウォール設定を確認

### 振動パターンが送信されない

1. デバイスの接続状態を確認
2. 感情データが正しく生成されていることを確認
3. WebSocketの接続状態を確認

### デバイスの状態を取得できない

1. デバイスの接続状態を確認
2. WebSocketの接続状態を確認
3. デバイスのファームウェアが最新であることを確認

## 参考資料

- [WebSocketコントローラー仕様書](/docs/communication_protocol.md)
- [Arduino Uno R4 WiFiコントローラー](/arduino/haptic_feedback_controller/README.md)
- [振動パターン設計ガイド](/docs/vibration_patterns.md)
