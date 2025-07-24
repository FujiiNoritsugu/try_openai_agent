# 触覚フィードバックコントローラー

このArduinoスケッチは、感情分析結果に基づいて振動パターンを生成する触覚フィードバックデバイスのコントローラーです。

## ハードウェア要件

- **Arduino Uno R4 WiFi**
- **Youmile GR-YM-222-2振動モジュール**

## 配線図

振動モジュールをArduinoに接続するには、以下の配線を行います：

1. 振動モジュールの**VCC**ピンを、Arduino Uno R4 WiFiの**5V**ピンに接続します。
2. 振動モジュールの**GND**ピンを、Arduino Uno R4 WiFiの**GND**ピンに接続します。
3. 振動モジュールの**IN**ピンを、Arduino Uno R4 WiFiの**D9**ピン（PWM対応）に接続します。

## セットアップ手順

1. Arduino IDEをインストールします。
2. 必要なライブラリをインストールします：
   - WiFiS3
   - ArduinoJson

3. スケッチ内のWiFi設定を編集します：
   ```cpp
   const char* ssid = "your_wifi_ssid";      // WiFi SSID
   const char* password = "your_wifi_password";  // WiFi パスワード
   ```

4. スケッチをArduino Uno R4 WiFiにアップロードします。
5. シリアルモニターを開き、デバイスがWiFiに接続されていることを確認します。
6. デバイスのIPアドレスをメモします（シリアルモニターに表示されます）。

## 使用方法

### HTTPリクエスト

振動パターンを送信するには、以下のようなJSONデータをHTTP POSTリクエストで送信します：

```json
{
  "steps": [
    {"intensity": 50, "duration": 200},
    {"intensity": 80, "duration": 300},
    {"intensity": 30, "duration": 150}
  ],
  "interval": 100,
  "repeat_count": 3
}
```

- **steps**: 振動ステップの配列（最大20ステップ）
  - **intensity**: 振動強度（0-100）
  - **duration**: 持続時間（ミリ秒）
- **interval**: ステップ間の間隔（ミリ秒）
- **repeat_count**: 繰り返し回数（0の場合は無限ループ）

### Pythonインターフェース

このリポジトリには、Arduinoコントローラーと通信するためのPythonインターフェース（`src/devices/arduino_controller.py`）が含まれています。

```python
from src.devices.arduino_controller import arduino_manager

# コントローラーの登録
controller = arduino_manager.register_controller("device1", "192.168.1.100")

# 接続
await arduino_manager.connect_all()

# 感情データの送信
from src.models.data_models import Emotion
emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)
await controller.send_emotion(emotion, "joy")

# 切断
await arduino_manager.disconnect_all()
```

## トラブルシューティング

- **WiFi接続の問題**: WiFiの認証情報が正しいことを確認してください。
- **振動モジュールが動作しない**: 配線を確認し、PWMピン（D9）が正しく接続されていることを確認してください。
- **通信エラー**: ArduinoのIPアドレスが正しく設定されていることを確認してください。

## ライセンス

このプロジェクトは、プロジェクトのメインリポジトリのライセンスに従います。

## 検証用Curlコマンド

  curl -X POST http://192.168.43.166 \
    -H "Content-Type: application/json" \
    -d '{
      "steps": [
        {"intensity": 50, "duration": 200},
        {"intensity": 100, "duration": 300},
        {"intensity": 75, "duration": 150}
      ],
      "interval": 100,
      "repeat_count": 3
    }'

  または、1行で実行する場合：

  curl -X POST http://192.168.43.166 -H "Content-Type: application/json" -d
  '{"steps":[{"intensity":50,"duration":200},{"intensity":100,"duration":300},{"intensity":75,"duration":150}],"interval":100,"repeat_count":3}'

  テスト用の異なるパターン例：

  # 短い振動パターン
  curl -X POST http://192.168.43.166 -H "Content-Type: application/json" -d '{"steps":[{"intensity":100,"duration":100}],"interval":0,"repeat_count":5}'

  # 徐々に強くなるパターン
  curl -X POST http://192.168.43.166 -H "Content-Type: application/json" -d '{"steps":[{"intensity":25,"duration":200},{"intensity":50,"duration":200},{"i
  ntensity":75,"duration":200},{"intensity":100,"duration":200}],"interval":50,"repeat_count":2}'
