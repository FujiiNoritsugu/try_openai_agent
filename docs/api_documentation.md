# API ドキュメント

このドキュメントでは、感情分析パイプラインと触覚フィードバックデバイスのAPIエンドポイントについて説明します。

## 概要

APIは、感情分析パイプラインと触覚フィードバックデバイスを外部アプリケーションから利用するためのインターフェースを提供します。RESTful原則に従い、JSONフォーマットでデータをやり取りします。

## ベースURL

```
http://localhost:8000
```

環境変数 `API_HOST` と `API_PORT` を設定することで、ホストとポートを変更できます。

## エンドポイント

### 感情分析

#### 感情分析の実行

```
POST /api/v1/analyze
```

ユーザー入力から感情を抽出・分類し、適切な感情応答を生成します。オプションで、結果を接続された触覚フィードバックデバイスに送信します。

**リクエスト**

```json
{
  "user_input": {
    "data": "0.7",
    "touched_area": "胸",
    "gender": "男性"
  },
  "send_to_devices": true
}
```

**レスポンス**

```json
{
  "extracted_emotion": {
    "joy": 0.8,
    "fun": 0.6,
    "anger": 0.1,
    "sad": 0.2
  },
  "original_message": "胸に触れられて、喜びと楽しさを感じています。",
  "emotion_category": "joy",
  "final_message": "あなたの触れ方に心が躍ります。もっと触れてください。",
  "is_learned_response": false,
  "device_results": {
    "device1": true
  }
}
```

### デバイス管理

#### デバイスリストの取得

```
GET /api/v1/devices
```

登録済みデバイスのリストを取得します。

**レスポンス**

```json
{
  "devices": [
    {
      "device_id": "device1",
      "host": "192.168.1.100",
      "port": 80,
      "ws_path": "/ws"
    }
  ]
}
```

#### デバイスの登録

```
POST /api/v1/devices
```

新しいデバイスを登録します。

**リクエスト**

```json
{
  "device_id": "device2",
  "host": "192.168.1.101",
  "port": 80,
  "ws_path": "/ws"
}
```

**レスポンス**

```json
{
  "device_id": "device2",
  "host": "192.168.1.101",
  "port": 80,
  "ws_path": "/ws"
}
```

#### デバイスの登録解除

```
DELETE /api/v1/devices/{device_id}
```

デバイスの登録を解除します。

**レスポンス**

```json
{
  "message": "デバイス 'device2' の登録を解除しました"
}
```

#### デバイスの初期化

```
POST /api/v1/devices/initialize
```

登録済みデバイスを初期化します。

**レスポンス**

```json
{
  "success": true
}
```

#### デバイスのシャットダウン

```
POST /api/v1/devices/shutdown
```

デバイスをシャットダウンします。

**レスポンス**

```json
{
  "success": true
}
```

#### デバイスの状態取得

```
GET /api/v1/devices/status
```

デバイスの状態を取得します。

**レスポンス**

```json
{
  "devices": [
    {
      "device_id": "device1",
      "device_state": "idle",
      "connected": true,
      "last_updated": "2025-04-17T12:34:56"
    }
  ]
}
```

### 振動制御

#### 振動パターンの送信

```
POST /api/v1/vibration
```

感情パラメータと感情カテゴリに基づいて、接続された触覚フィードバックデバイスに振動パターンを送信します。

**リクエスト**

```json
{
  "emotion": {
    "joy": 0.8,
    "fun": 0.6,
    "anger": 0.1,
    "sad": 0.2
  },
  "emotion_category": "joy",
  "device_ids": ["device1"]
}
```

**レスポンス**

```json
{
  "results": {
    "device1": true
  }
}
```

#### 振動の停止

```
POST /api/v1/vibration/stop
```

接続された触覚フィードバックデバイスの振動を停止します。

**リクエスト**

```json
{
  "device_ids": ["device1"]
}
```

**レスポンス**

```json
{
  "results": {
    "device1": true
  }
}
```

## エラーレスポンス

エラーが発生した場合、APIは適切なHTTPステータスコードとともに以下の形式でエラー情報を返します。

```json
{
  "error": "エラーメッセージ",
  "details": {
    "追加情報": "エラーの詳細"
  }
}
```

## 使用例

### cURLを使用した感情分析

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": {
      "data": "0.7",
      "touched_area": "胸",
      "gender": "男性"
    },
    "send_to_devices": false
  }'
```

### Pythonを使用したデバイス登録と振動パターン送信

```python
import requests
import json

# APIのベースURL
base_url = "http://localhost:8000"

# デバイスの登録
device_data = {
    "device_id": "device1",
    "host": "192.168.1.100",
    "port": 80,
    "ws_path": "/ws"
}
response = requests.post(f"{base_url}/api/v1/devices", json=device_data)
print(f"デバイス登録: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# デバイスの初期化
response = requests.post(f"{base_url}/api/v1/devices/initialize")
print(f"デバイス初期化: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 振動パターンの送信
vibration_data = {
    "emotion": {
        "joy": 0.8,
        "fun": 0.6,
        "anger": 0.1,
        "sad": 0.2
    },
    "emotion_category": "joy",
    "device_ids": ["device1"]
}
response = requests.post(f"{base_url}/api/v1/vibration", json=vibration_data)
print(f"振動パターン送信: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 振動の停止
response = requests.post(f"{base_url}/api/v1/vibration/stop", json={"device_ids": ["device1"]})
print(f"振動停止: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

## 認証

現在、APIは認証を必要としません。本番環境では、適切な認証メカニズムを実装することをお勧めします。
