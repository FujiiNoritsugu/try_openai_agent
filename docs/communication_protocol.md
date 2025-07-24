# 通信プロトコル仕様書

## 概要

このドキュメントでは、感情分析アプリケーションとArduino Uno R4 WiFiベースの触覚フィードバックデバイス間の通信プロトコルを定義します。このプロトコルは、HTTPとWebSocketの両方のインターフェースを提供し、振動パターンの送信と状態監視を可能にします。

## 通信方式

### 1. HTTP通信

基本的な通信には、HTTPリクエスト/レスポンスモデルを使用します。

#### エンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|--------|------|
| `/pattern`   | POST   | 振動パターンを送信する |
| `/status`    | GET    | デバイスの状態を取得する |
| `/stop`      | POST   | 振動を停止する |

#### リクエスト/レスポンスフォーマット

すべてのリクエストとレスポンスはJSON形式です。

##### 振動パターン送信 (`/pattern`)

リクエスト:
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

レスポンス:
```json
{
  "status": "ok",
  "message": "パターンを受信しました"
}
```

##### 状態取得 (`/status`)

レスポンス:
```json
{
  "status": "ok",
  "device_state": "playing",
  "is_playing": true,
  "current_step": 1,
  "total_steps": 3,
  "current_repeat": 0,
  "total_repeats": 3
}
```

##### 振動停止 (`/stop`)

レスポンス:
```json
{
  "status": "ok",
  "message": "振動を停止しました"
}
```

### 2. WebSocket通信

リアルタイムの通信と状態更新には、WebSocketプロトコルを使用します。

#### 接続

WebSocket接続は以下のURLで確立されます：
```
ws://<device-ip>/ws
```

#### メッセージタイプ

##### クライアントからサーバーへ

1. **振動パターン送信**
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

2. **状態要求**
```
status
```

3. **停止コマンド**
```
stop
```

##### サーバーからクライアントへ

1. **コマンド応答**
```json
{
  "status": "ok",
  "message": "パターンを受信しました"
}
```

2. **状態更新**
```json
{
  "type": "status",
  "device_state": "playing",
  "is_playing": true,
  "current_step": 1,
  "total_steps": 3,
  "current_repeat": 0,
  "total_repeats": 3
}
```

## データモデル

### 振動パターン

振動パターンは以下の要素で構成されます：

- **steps**: 振動ステップの配列
  - **intensity**: 振動強度（0-100）
  - **duration**: 持続時間（ミリ秒）
- **interval**: ステップ間の間隔（ミリ秒）
- **repeat_count**: 繰り返し回数（0の場合は無限ループ）

### デバイス状態

デバイスの状態は以下の要素で構成されます：

- **device_state**: デバイスの状態（"idle", "playing", "error"）
- **is_playing**: 振動パターンが再生中かどうか
- **current_step**: 現在のステップ（再生中の場合）
- **total_steps**: 総ステップ数（再生中の場合）
- **current_repeat**: 現在の繰り返し回数（再生中の場合）
- **total_repeats**: 総繰り返し回数（再生中の場合）
- **error_message**: エラーメッセージ（エラー状態の場合）

## エラーハンドリング

### エラーレスポンス

エラーが発生した場合、以下の形式でレスポンスが返されます：

```json
{
  "status": "error",
  "message": "エラーメッセージ"
}
```

### 一般的なエラーコード

| エラーメッセージ | 説明 |
|--------------|------|
| "JSONの解析に失敗しました" | 無効なJSON形式のリクエスト |
| "不明なリクエストです" | サポートされていないエンドポイントまたはコマンド |
| "パラメータが不足しています" | 必要なパラメータが提供されていない |

## 再接続と回復メカニズム

### クライアント側の再接続ロジック

1. WebSocket接続が切断された場合、クライアントは指数バックオフ戦略を使用して再接続を試みます。
2. 最初の再接続は1秒後に試み、その後は最大30秒まで待機時間を倍増させます。
3. 10回の再接続試行後も接続できない場合は、エラーを報告します。

### サーバー側の回復メカニズム

1. クライアント接続が切断された場合、サーバーは現在の状態を保持します。
2. 再接続時に、サーバーは現在の状態をクライアントに送信します。
3. 振動パターンの再生中に接続が切断された場合、パターンの再生は継続されます。

## 実装例

### Pythonクライアント

```python
import asyncio
import aiohttp
import json

async def connect_to_device(host, port=80):
    # WebSocket接続
    session = aiohttp.ClientSession()
    ws = await session.ws_connect(f"ws://{host}:{port}/ws")
    
    # 振動パターンの送信
    pattern = {
        "steps": [
            {"intensity": 50, "duration": 200},
            {"intensity": 80, "duration": 300}
        ],
        "interval": 100,
        "repeat_count": 3
    }
    await ws.send_json(pattern)
    
    # 応答の受信
    response = await ws.receive_json()
    print(f"応答: {response}")
    
    # 状態の監視
    await ws.send_str("status")
    status = await ws.receive_json()
    print(f"状態: {status}")
    
    # 切断
    await ws.close()
    await session.close()

asyncio.run(connect_to_device("192.168.1.100"))
```

### Arduino実装

```cpp
// WebSocketメッセージの処理
void handleWebSocketMessage(String data) {
  if (data.startsWith("{")) {
    // JSONデータの処理
    parseVibrationPattern(data);
    sendWebSocketMessage("{\"status\":\"ok\",\"message\":\"パターンを受信しました\"}");
  } else if (data == "stop") {
    stopVibrationPattern();
    sendWebSocketMessage("{\"status\":\"ok\",\"message\":\"振動を停止しました\"}");
  } else if (data == "status") {
    sendWebSocketStatus();
  }
}
```

## セキュリティ考慮事項

1. このプロトコルは、信頼されたローカルネットワーク内での使用を前提としています。
2. 公共ネットワークで使用する場合は、TLS/SSLを使用したセキュアな接続（HTTPS/WSS）を検討してください。
3. 実際の実装では、認証メカニズムの追加を検討してください。

## 将来の拡張

1. **双方向通信の強化**: デバイスからのイベント通知機能
2. **バッチ処理**: 複数の振動パターンをキューに入れる機能
3. **パターンライブラリ**: 名前付きパターンの保存と呼び出し機能
4. **デバイス設定**: デバイスの設定を変更する機能
