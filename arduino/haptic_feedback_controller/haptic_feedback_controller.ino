/**
 * 触覚フィードバックコントローラー
 * 
 * Arduino Uno R4 WiFi用のスケッチで、Youmile GR-YM-222-2振動モジュールを
 * 制御し、WiFi経由で受信した振動パターンを物理的な振動に変換します。
 * 
 * ハードウェア:
 * - Arduino Uno R4 WiFi
 * - Youmile GR-YM-222-2振動モジュール
 */

#include <WiFiS3.h>
#include <ArduinoJson.h>

// WiFi設定
const char* ssid = "your_wifi_ssid";      // WiFi SSID
const char* password = "your_wifi_password";  // WiFi パスワード

// サーバー設定
WiFiServer server(80);
WiFiClient client;

// 振動モジュールのピン設定
const int VIBRATION_PIN = 9;  // PWMピン

// 振動パターンの最大ステップ数
const int MAX_STEPS = 20;

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

// 現在のパターン
VibrationPattern currentPattern;
bool isPlaying = false;
unsigned long lastStepTime = 0;
int currentStep = 0;
int currentRepeat = 0;

void setup() {
  // シリアル通信の初期化
  Serial.begin(115200);
  while (!Serial) {
    ; // シリアルポートが接続されるのを待つ
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

void loop() {
  // クライアント接続の確認
  checkClientConnection();
  
  // 振動パターンの再生
  if (isPlaying) {
    playVibrationPattern();
  }
}

/**
 * WiFiに接続する
 */
void connectToWiFi() {
  Serial.print("WiFiに接続中: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  
  // 接続が確立されるまで待機
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFiに接続されました");
  Serial.print("IPアドレス: ");
  Serial.println(WiFi.localIP());
}

/**
 * クライアント接続を確認し、データを処理する
 */
void checkClientConnection() {
  // 新しいクライアントの確認
  client = server.available();
  
  if (client) {
    Serial.println("新しいクライアントが接続されました");
    
    // リクエストの読み取り
    String currentLine = "";
    String jsonData = "";
    bool isJson = false;
    
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        
        // JSONデータの読み取り
        if (c == '{') {
          isJson = true;
        }
        
        if (isJson) {
          jsonData += c;
        }
        
        if (c == '}' && isJson) {
          isJson = false;
          parseVibrationPattern(jsonData);
          break;
        }
        
        // HTTPリクエストの終了を検出
        if (c == '\n') {
          if (currentLine.length() == 0) {
            // HTTPヘッダーの送信
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:application/json");
            client.println("Connection: close");
            client.println();
            break;
          } else {
            currentLine = "";
          }
        } else if (c != '\r') {
          currentLine += c;
        }
      }
    }
    
    // レスポンスの送信
    client.println("{\"status\":\"ok\"}");
    
    // 接続のクローズ
    client.stop();
    Serial.println("クライアント切断");
  }
}

/**
 * 受信したJSONデータから振動パターンを解析する
 */
void parseVibrationPattern(String jsonData) {
  // JSONバッファの作成
  DynamicJsonDocument doc(1024);
  
  // JSONデータの解析
  DeserializationError error = deserializeJson(doc, jsonData);
  
  // 解析エラーの確認
  if (error) {
    Serial.print("JSONの解析に失敗しました: ");
    Serial.println(error.c_str());
    return;
  }
  
  // 振動パターンの解析
  currentPattern.stepCount = min((int)doc["steps"].size(), MAX_STEPS);
  currentPattern.interval = doc["interval"];
  currentPattern.repeatCount = doc["repeat_count"];
  
  // 各ステップの解析
  for (int i = 0; i < currentPattern.stepCount; i++) {
    currentPattern.steps[i].intensity = map(doc["steps"][i]["intensity"], 0, 100, 0, 255);
    currentPattern.steps[i].duration = doc["steps"][i]["duration"];
  }
  
  // パターン再生の開始
  startVibrationPattern();
}

/**
 * 振動パターンの再生を開始する
 */
void startVibrationPattern() {
  currentStep = 0;
  currentRepeat = 0;
  isPlaying = true;
  lastStepTime = millis();
  
  Serial.println("振動パターンの再生を開始します");
}

/**
 * 振動パターンを再生する
 */
void playVibrationPattern() {
  unsigned long currentTime = millis();
  
  // 現在のステップの持続時間が経過したかチェック
  if (currentTime - lastStepTime >= currentPattern.steps[currentStep].duration) {
    // 次のステップに進む
    currentStep++;
    
    // すべてのステップが完了したかチェック
    if (currentStep >= currentPattern.stepCount) {
      currentStep = 0;
      currentRepeat++;
      
      // すべての繰り返しが完了したかチェック
      if (currentRepeat >= currentPattern.repeatCount && currentPattern.repeatCount > 0) {
        // パターン再生の停止
        stopVibrationPattern();
        return;
      }
      
      // ステップ間の間隔を追加
      delay(currentPattern.interval);
    }
    
    // 新しいステップの振動強度を設定
    analogWrite(VIBRATION_PIN, currentPattern.steps[currentStep].intensity);
    lastStepTime = currentTime;
    
    Serial.print("ステップ: ");
    Serial.print(currentStep);
    Serial.print(", 強度: ");
    Serial.println(currentPattern.steps[currentStep].intensity);
  }
}

/**
 * 振動パターンの再生を停止する
 */
void stopVibrationPattern() {
  isPlaying = false;
  analogWrite(VIBRATION_PIN, 0);  // 振動をオフにする
  Serial.println("振動パターンの再生を停止しました");
}
