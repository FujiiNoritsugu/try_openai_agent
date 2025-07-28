/**
 * 触覚フィードバックコントローラー
 * 
 * Arduino Uno R4 WiFi用のスケッチで、Youmile GR-YM-222-2振動モジュールを
 * 制御し、WiFi経由で受信した振動パターンを物理的な振動に変換します。
 * 
 * ハードウェア:
 * - Arduino Uno R4 WiFi
 * - Youmile GR-YM-222-2振動モジュール
 * 
 * 設定:
 * config.hファイルを作成して、以下の内容を記述してください：
 * #define WIFI_SSID "your_wifi_ssid"
 * #define WIFI_PASSWORD "your_wifi_password"
 */

#include <WiFiS3.h>
#include <ArduinoJson.h>
#include "config.h"  // WiFi設定ファイル

// WiFi設定
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

// サーバー設定
WiFiServer server(80);
WiFiClient client;

// 振動モジュールのピン設定
const int VIBRATION_PIN = 9;  // PWMピン (Arduino UNO R4 WiFi: 3,5,6,9,10,11がPWM対応)

// 振動パターンの最大ステップ数
const int MAX_STEPS = 10;  // メモリ効率のため削減

// 振動パターンの構造体
struct VibrationStep {
  int intensity;    // 振動強度 (0-255)
  int duration;     // 持続時間 (ミリ秒)
};

struct VibrationPattern {
  VibrationStep steps[MAX_STEPS];  // 振動ステップの配列
  int stepCount;                   // ステップ数
  int interval;                    // ステップ間の間隔 (ミリ秒)
  int repeatCount;                 // 繰り返し回数
};

// 振動コントローラークラス
class VibrationController {
private:
  VibrationPattern pattern;
  bool playing;
  unsigned long lastStepTime;
  unsigned long intervalStartTime;
  int currentStep;
  int currentRepeat;
  bool inInterval;
  
public:
  VibrationController() : playing(false), lastStepTime(0), intervalStartTime(0), 
                         currentStep(0), currentRepeat(0), inInterval(false) {}
  
  void setPattern(const VibrationPattern& newPattern) {
    pattern = newPattern;
  }
  
  void start() {
    currentStep = 0;
    currentRepeat = 0;
    playing = true;
    inInterval = false;
    lastStepTime = millis();
    
    // 最初のステップの振動を開始
    if (pattern.stepCount > 0) {
      analogWrite(VIBRATION_PIN, pattern.steps[0].intensity);
      Serial.print("開始ステップ: 0, 強度: ");
      Serial.println(pattern.steps[0].intensity);
    }
    
    Serial.println("振動パターンの再生を開始します");
  }
  
  void stop() {
    playing = false;
    analogWrite(VIBRATION_PIN, 0);
    Serial.println("振動パターンの再生を停止しました");
  }
  
  bool isPlaying() { return playing; }
  
  void update() {
    if (!playing) return;
    
    unsigned long currentTime = millis();
    
    // インターバル中の処理
    if (inInterval) {
      if (currentTime - intervalStartTime >= pattern.interval) {
        inInterval = false;
        lastStepTime = currentTime;
      }
      return;
    }
    
    // 現在のステップの持続時間が経過したかチェック
    if (currentTime - lastStepTime >= pattern.steps[currentStep].duration) {
      // 次のステップに進む
      currentStep++;
      
      // すべてのステップが完了したかチェック
      if (currentStep >= pattern.stepCount) {
        currentStep = 0;
        currentRepeat++;
        
        // すべての繰り返しが完了したかチェック
        if (currentRepeat >= pattern.repeatCount && pattern.repeatCount > 0) {
          stop();
          return;
        }
        
        // ステップ間の間隔を開始
        if (pattern.interval > 0) {
          inInterval = true;
          intervalStartTime = currentTime;
          analogWrite(VIBRATION_PIN, 0);  // インターバル中は振動を停止
          return;
        }
      }
      
      // 新しいステップの振動強度を設定
      if (currentStep < pattern.stepCount) {
        analogWrite(VIBRATION_PIN, pattern.steps[currentStep].intensity);
        Serial.print("ステップ: ");
        Serial.print(currentStep);
        Serial.print(", 強度: ");
        Serial.println(pattern.steps[currentStep].intensity);
      }
      lastStepTime = currentTime;
    }
  }
};

// グローバルインスタンス
VibrationController vibrationController;

// WiFi接続状態
enum WiFiState {
  WIFI_DISCONNECTED,
  WIFI_CONNECTING,
  WIFI_CONNECTED
};

WiFiState wifiState = WIFI_DISCONNECTED;
unsigned long lastWiFiCheckTime = 0;
const unsigned long WIFI_CHECK_INTERVAL = 5000;  // 5秒ごとにチェック

void setup() {
  // シリアル通信の初期化
  Serial.begin(115200);
  while (!Serial) {
    ; // シリアルポートが接続されるのを待つ
  }

  // PWMピンの検証
  if (!isPWMPin(VIBRATION_PIN)) {
    Serial.println("エラー: 指定されたピンはPWM非対応です");
    while(1);  // 停止
  }

  // 振動モジュールのピンを出力として設定
  pinMode(VIBRATION_PIN, OUTPUT);
  analogWrite(VIBRATION_PIN, 0);  // 初期状態はオフ

  // WiFi接続
  connectToWiFi();

  // サーバーの開始
  server.begin();
  Serial.println("サーバーが開始されました");
}

/**
 * 指定されたピンがPWM対応かチェック
 */
bool isPWMPin(int pin) {
  // Arduino UNO R4 WiFiのPWM対応ピン
  int pwmPins[] = {3, 5, 6, 9, 10, 11};
  for (int i = 0; i < 6; i++) {
    if (pin == pwmPins[i]) return true;
  }
  return false;
}

void loop() {
  // WiFi接続状態の確認
  checkWiFiConnection();
  
  // クライアント接続の確認
  if (wifiState == WIFI_CONNECTED) {
    checkClientConnection();
  }
  
  // 振動パターンの更新
  vibrationController.update();
}

/**
 * WiFiに接続する
 */
void connectToWiFi() {
  Serial.print("WiFiに接続中: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  wifiState = WIFI_CONNECTING;
  
  // 接続試行（最大30秒）
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 30000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiState = WIFI_CONNECTED;
    Serial.println("");
    Serial.println("WiFiに接続されました");
    
    // IPアドレスが割り当てられるまで待機（最大5秒）
    unsigned long ipWaitStart = millis();
    while (WiFi.localIP() == IPAddress(0,0,0,0) && millis() - ipWaitStart < 5000) {
      delay(100);
    }
    
    Serial.print("IPアドレス: ");
    Serial.println(WiFi.localIP());
    
    // IPアドレスが取得できなかった場合の警告
    if (WiFi.localIP() == IPAddress(0,0,0,0)) {
      Serial.println("警告: IPアドレスの取得に失敗しました");
      Serial.println("DHCPサーバーの設定を確認してください");
    }
  } else {
    wifiState = WIFI_DISCONNECTED;
    Serial.println("");
    Serial.println("WiFi接続に失敗しました");
  }
}

/**
 * WiFi接続状態をチェックし、必要に応じて再接続する
 */
void checkWiFiConnection() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastWiFiCheckTime >= WIFI_CHECK_INTERVAL) {
    lastWiFiCheckTime = currentTime;
    
    if (WiFi.status() != WL_CONNECTED && wifiState != WIFI_CONNECTING) {
      Serial.println("WiFi接続が切断されました。再接続を試みます...");
      connectToWiFi();
    }
  }
}

/**
 * クライアント接続を確認し、データを処理する
 */
void checkClientConnection() {
  // 新しいクライアントの確認
  client = server.available();
  
  if (client) {
    Serial.println("新しいクライアントが接続されました");
    
    // HTTPリクエストの解析
    String requestLine = "";
    String currentLine = "";
    String jsonData = "";
    int contentLength = 0;
    bool isPost = false;
    bool headerComplete = false;
    unsigned long requestStartTime = millis();
    
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        
        if (!headerComplete) {
          if (c == '\n') {
            // 最初の行でHTTPメソッドを確認
            if (requestLine.length() == 0) {
              requestLine = currentLine;
              if (requestLine.startsWith("POST")) {
                isPost = true;
              }
            }
            
            // Content-Lengthヘッダーの確認
            if (currentLine.startsWith("Content-Length: ")) {
              contentLength = currentLine.substring(16).toInt();
            }
            
            // ヘッダーの終了を検出
            if (currentLine.length() == 0) {
              headerComplete = true;
              
              // POSTリクエストの場合、ボディを読み取る
              if (isPost && contentLength > 0) {
                jsonData.reserve(contentLength);
                int bytesRead = 0;
                unsigned long bodyReadStart = millis();
                while (bytesRead < contentLength && millis() - bodyReadStart < 2000) {
                  if (client.available()) {
                    jsonData += (char)client.read();
                    bytesRead++;
                  }
                }
              }
              break;  // ヘッダー処理完了後はループを抜ける
            }
            currentLine = "";
          } else if (c != '\r') {
            currentLine += c;
          }
        }
      }
      
      // タイムアウトチェック（5秒）
      if (millis() - requestStartTime > 5000) {
        break;
      }
    }
    
    // レスポンスの送信
    client.println("HTTP/1.1 200 OK");
    client.println("Content-type: application/json");
    client.println("Connection: close");
    client.println("Access-Control-Allow-Origin: *");
    client.println();
    
    // JSONデータの処理
    if (jsonData.length() > 0) {
      if (parseVibrationPattern(jsonData)) {
        client.println("{\"status\":\"ok\",\"message\":\"Pattern received\"}");
      } else {
        client.println("{\"status\":\"error\",\"message\":\"Invalid pattern\"}");
      }
    } else {
      client.println("{\"status\":\"ok\",\"message\":\"No data\"}");
    }
    
    // 接続のクローズ
    client.stop();
    Serial.println("クライアント切断");
  }
}

/**
 * 受信したJSONデータから振動パターンを解析する
 */
bool parseVibrationPattern(String jsonData) {
  // 動的なJSONバッファサイズの計算
  const size_t capacity = JSON_OBJECT_SIZE(4) + 
                         JSON_ARRAY_SIZE(MAX_STEPS) + 
                         MAX_STEPS * JSON_OBJECT_SIZE(2) + 
                         jsonData.length();
  
  DynamicJsonDocument doc(capacity);
  
  // JSONデータの解析
  DeserializationError error = deserializeJson(doc, jsonData);
  
  // 解析エラーの確認
  if (error) {
    Serial.print("JSONの解析に失敗しました: ");
    Serial.println(error.c_str());
    return false;
  }
  
  // 必須フィールドの確認
  if (!doc.containsKey("steps") || !doc["steps"].is<JsonArray>()) {
    Serial.println("エラー: 'steps'フィールドが見つかりません");
    return false;
  }
  
  // 振動パターンの作成
  VibrationPattern newPattern;
  newPattern.stepCount = min((int)doc["steps"].size(), MAX_STEPS);
  newPattern.interval = doc["interval"] | 0;  // デフォルト値0
  newPattern.repeatCount = doc["repeat_count"] | 1;  // デフォルト値1
  
  Serial.print("受信したパターン: ステップ数=");
  Serial.print(newPattern.stepCount);
  Serial.print(", 繰り返し=");
  Serial.print(newPattern.repeatCount);
  Serial.print(", 間隔=");
  Serial.println(newPattern.interval);
  
  // 各ステップの解析
  for (int i = 0; i < newPattern.stepCount; i++) {
    int intensity = doc["steps"][i]["intensity"] | 0;
    newPattern.steps[i].intensity = map(constrain(intensity, 0, 100), 0, 100, 0, 255);
    newPattern.steps[i].duration = doc["steps"][i]["duration"] | 100;  // デフォルト100ms
    
    Serial.print("ステップ ");
    Serial.print(i);
    Serial.print(": 強度=");
    Serial.print(intensity);
    Serial.print("% -> PWM値=");
    Serial.print(newPattern.steps[i].intensity);
    Serial.print(", 持続時間=");
    Serial.println(newPattern.steps[i].duration);
  }
  
  // パターンの設定と再生開始
  vibrationController.setPattern(newPattern);
  vibrationController.start();
  
  return true;
}