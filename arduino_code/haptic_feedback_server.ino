/*
  Arduino Uno R4 WiFi - 触覚フィードバックサーバー
  
  このスケッチは、WiFi経由でHTTPリクエストを受信し、
  振動モーターを制御するためのWebサーバーを提供します。
*/

#include <WiFiS3.h>
#include <ArduinoJson.h>

// WiFi設定（あなたの環境に合わせて変更してください）
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// ハードウェア設定
const int VIBRATION_PIN = 9;  // PWM対応ピン（振動モーター接続）
const int LED_PIN = LED_BUILTIN;  // ステータス表示用LED

// サーバー設定
WiFiServer server(80);
int status = WL_IDLE_STATUS;

// 振動制御用変数
bool isPlaying = false;
unsigned long patternStartTime = 0;
int currentStep = 0;
int currentRepeat = 0;

// パターンデータ構造
struct VibrationStep {
  int intensity;  // 0-100
  int duration;   // ミリ秒
};

struct VibrationPattern {
  VibrationStep steps[10];  // 最大10ステップ
  int stepCount;
  int interval;
  int repeatCount;
} currentPattern;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // シリアルポートの接続を待つ
  }

  // ピンの初期化
  pinMode(VIBRATION_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // WiFi接続
  Serial.println("WiFiに接続中...");
  
  if (WiFi.begin(ssid, password) != WL_CONNECTED) {
    Serial.println("WiFi接続に失敗しました");
    while (true) {
      digitalWrite(LED_PIN, HIGH);
      delay(200);
      digitalWrite(LED_PIN, LOW);
      delay(200);
    }
  }

  // IP アドレスの表示
  Serial.println("WiFi接続成功!");
  Serial.print("IP アドレス: ");
  Serial.println(WiFi.localIP());

  // Webサーバー開始
  server.begin();
  Serial.println("Webサーバーが開始されました");
  
  digitalWrite(LED_PIN, HIGH);  // 接続成功を示すLED点灯
}

void loop() {
  // 振動パターンの更新
  updateVibrationPattern();
  
  // クライアントからの接続を待つ
  WiFiClient client = server.available();
  
  if (client) {
    handleClient(client);
  }
}

void handleClient(WiFiClient client) {
  Serial.println("新しいクライアントが接続されました");
  
  String currentLine = "";
  String requestBody = "";
  String requestMethod = "";
  String requestPath = "";
  bool isPostRequest = false;
  bool readingBody = false;
  int contentLength = 0;
  
  while (client.connected()) {
    if (client.available()) {
      char c = client.read();
      
      if (!readingBody) {
        if (c == '\n') {
          if (currentLine.length() == 0) {
            // ヘッダー終了、ボディ読み取り開始
            if (isPostRequest && contentLength > 0) {
              readingBody = true;
            } else {
              break;  // GET リクエストの場合はレスポンス送信
            }
          } else {
            // ヘッダー行の解析
            if (currentLine.startsWith("GET ")) {
              requestMethod = "GET";
              int spaceIndex = currentLine.indexOf(' ', 4);
              requestPath = currentLine.substring(4, spaceIndex);
            } else if (currentLine.startsWith("POST ")) {
              requestMethod = "POST";
              isPostRequest = true;
              int spaceIndex = currentLine.indexOf(' ', 5);
              requestPath = currentLine.substring(5, spaceIndex);
            } else if (currentLine.startsWith("Content-Length: ")) {
              contentLength = currentLine.substring(16).toInt();
            }
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }
      } else {
        // ボディの読み取り
        requestBody += c;
        if (requestBody.length() >= contentLength) {
          break;
        }
      }
    }
  }
  
  // リクエストの処理
  if (requestPath == "/status") {
    handleStatusRequest(client);
  } else if (requestPath == "/pattern" && requestMethod == "POST") {
    handlePatternRequest(client, requestBody);
  } else {
    handleNotFound(client);
  }
  
  // 接続を閉じる
  client.stop();
  Serial.println("クライアントが切断されました");
}

void handleStatusRequest(WiFiClient client) {
  Serial.println("ステータスリクエストを処理中");
  
  // JSON レスポンスの作成
  DynamicJsonDocument doc(200);
  doc["status"] = "ok";
  doc["device_state"] = isPlaying ? "playing" : "idle";
  doc["is_playing"] = isPlaying;
  doc["current_step"] = currentStep;
  doc["total_steps"] = currentPattern.stepCount;
  doc["current_repeat"] = currentRepeat;
  doc["total_repeats"] = currentPattern.repeatCount;
  
  String response;
  serializeJson(doc, response);
  
  sendHttpResponse(client, 200, "application/json", response);
}

void handlePatternRequest(WiFiClient client, String body) {
  Serial.println("パターンリクエストを処理中");
  Serial.println("受信データ: " + body);
  
  // JSON の解析
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, body);
  
  if (error) {
    Serial.println("JSON解析エラー");
    sendHttpResponse(client, 400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid JSON\"}");
    return;
  }
  
  // パターンデータの抽出
  JsonArray steps = doc["steps"];
  int interval = doc["interval"] | 100;
  int repeatCount = doc["repeat_count"] | 1;
  
  if (steps.size() == 0 || steps.size() > 10) {
    Serial.println("無効なステップ数");
    sendHttpResponse(client, 400, "application/json", "{\"status\":\"error\",\"message\":\"Invalid step count\"}");
    return;
  }
  
  // パターンの設定
  currentPattern.stepCount = steps.size();
  currentPattern.interval = interval;
  currentPattern.repeatCount = repeatCount;
  
  for (int i = 0; i < steps.size(); i++) {
    JsonObject step = steps[i];
    currentPattern.steps[i].intensity = step["intensity"] | 0;
    currentPattern.steps[i].duration = step["duration"] | 100;
    
    // 範囲チェック
    if (currentPattern.steps[i].intensity < 0) currentPattern.steps[i].intensity = 0;
    if (currentPattern.steps[i].intensity > 100) currentPattern.steps[i].intensity = 100;
    if (currentPattern.steps[i].duration < 10) currentPattern.steps[i].duration = 10;
  }
  
  // パターン再生開始
  startVibrationPattern();
  
  Serial.println("パターンの再生を開始しました");
  sendHttpResponse(client, 200, "application/json", "{\"status\":\"ok\",\"message\":\"Pattern started\"}");
}

void handleNotFound(WiFiClient client) {
  sendHttpResponse(client, 404, "text/plain", "Not Found");
}

void sendHttpResponse(WiFiClient client, int statusCode, String contentType, String content) {
  client.println("HTTP/1.1 " + String(statusCode) + " " + getStatusText(statusCode));
  client.println("Content-Type: " + contentType);
  client.println("Content-Length: " + String(content.length()));
  client.println("Access-Control-Allow-Origin: *");
  client.println("Connection: close");
  client.println();
  client.print(content);
}

String getStatusText(int code) {
  switch (code) {
    case 200: return "OK";
    case 400: return "Bad Request";
    case 404: return "Not Found";
    default: return "Unknown";
  }
}

void startVibrationPattern() {
  isPlaying = true;
  patternStartTime = millis();
  currentStep = 0;
  currentRepeat = 0;
}

void updateVibrationPattern() {
  if (!isPlaying || currentPattern.stepCount == 0) {
    analogWrite(VIBRATION_PIN, 0);
    return;
  }
  
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - patternStartTime;
  
  // 現在のステップの開始時間を計算
  unsigned long stepStartTime = 0;
  for (int i = 0; i < currentStep; i++) {
    stepStartTime += currentPattern.steps[i].duration;
    if (i < currentStep - 1) {
      stepStartTime += currentPattern.interval;
    }
  }
  
  // 現在のステップを実行中か確認
  if (elapsedTime >= stepStartTime && elapsedTime < stepStartTime + currentPattern.steps[currentStep].duration) {
    // 振動強度を設定（0-100 を 0-255 に変換）
    int intensity = map(currentPattern.steps[currentStep].intensity, 0, 100, 0, 255);
    analogWrite(VIBRATION_PIN, intensity);
  } else if (elapsedTime >= stepStartTime + currentPattern.steps[currentStep].duration) {
    // 現在のステップ完了
    analogWrite(VIBRATION_PIN, 0);
    
    if (elapsedTime >= stepStartTime + currentPattern.steps[currentStep].duration + currentPattern.interval) {
      // 次のステップへ
      currentStep++;
      
      if (currentStep >= currentPattern.stepCount) {
        // パターン完了、次の繰り返しへ
        currentRepeat++;
        
        if (currentRepeat >= currentPattern.repeatCount) {
          // 全ての繰り返し完了
          isPlaying = false;
          currentStep = 0;
          currentRepeat = 0;
          Serial.println("パターンの再生が完了しました");
        } else {
          // 次の繰り返し開始
          currentStep = 0;
          patternStartTime = currentTime;
        }
      }
    }
  } else {
    // 間隔中
    analogWrite(VIBRATION_PIN, 0);
  }
}