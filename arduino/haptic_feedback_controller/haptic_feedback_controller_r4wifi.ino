/**
 * 触覚フィードバックコントローラー（Arduino Uno R4 WiFi対応版）
 * 
 * Arduino Uno R4 WiFi用のスケッチで、Youmile GR-YM-222-2振動モジュールを
 * 制御し、WiFi経由で受信した振動パターンを物理的な振動に変換します。
 * WiFiS3とArduinoHttpClientライブラリを使用してWebSocketクライアントとして
 * 動作し、リアルタイム通信と状態報告を行います。
 * 
 * ハードウェア:
 * - Arduino Uno R4 WiFi
 * - Youmile GR-YM-222-2振動モジュール
 * 
 * 必要なライブラリ:
 * - WiFiS3 (Arduino Uno R4 WiFi用)
 * - ArduinoJson (by Benoit Blanchon)
 * - ArduinoHttpClient (by Arduino)
 * 
 * 注意: このスケッチを使用する前に、シリアルモニタを開いてWiFi設定を入力する必要があります。
 * 認証情報はコードに保存されず、実行時にシリアルから入力されます。
 */

#include <WiFiS3.h>
#include <ArduinoJson.h>
#include <ArduinoHttpClient.h>

// WiFi設定
// 認証情報はシリアルから入力されるため、コードには保存されません
char ssid[32];      // WiFi SSID
char password[64];  // WiFi パスワード

// WebSocketサーバー設定
// サーバー情報はシリアルから入力されるため、コードには保存されません
char serverAddress[64]; // WebSocketサーバーのIPアドレス
int serverPort;         // WebSocketサーバーのポート
char wsPath[32];        // WebSocketのパス

// HTTPサーバー設定（ローカルHTTPサーバー）
int httpPort;           // HTTPサーバーのポート
WiFiServer httpServer;  // HTTPサーバーインスタンス

// WebSocketクライアント
WiFiClient wifiClient;
WebSocketClient webSocketClient;
bool wsConnected = false;
unsigned long lastConnectionAttempt = 0;
const unsigned long CONNECTION_RETRY_INTERVAL = 5000; // 5秒ごとに再接続を試みる

// 振動モジュールのピン設定
const int VIBRATION_PIN = 9;  // PWMピン

// デバイス状態
enum DeviceState {
  IDLE,
  PLAYING,
  ERROR
};

DeviceState currentState = IDLE;
String errorMessage = "";

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

// 状態更新の間隔
const unsigned long STATUS_UPDATE_INTERVAL = 1000; // 1秒ごとに状態を更新
unsigned long lastStatusUpdateTime = 0;

// ハートビート設定
const unsigned long HEARTBEAT_INTERVAL = 5000; // 5秒ごとにハートビートを送信
unsigned long lastHeartbeatTime = 0;

// デバイスID
char deviceId[32] = "arduino_haptic_device";

void setup() {
  // シリアル通信の初期化
  Serial.begin(115200);
  while (!Serial) {
    ; // シリアルポートが接続されるのを待つ
  }

  Serial.println("触覚フィードバックコントローラー（Arduino Uno R4 WiFi対応版）");
  Serial.println("初期設定を開始します...");

  // 振動モジュールのピンを出力として設定
  pinMode(VIBRATION_PIN, OUTPUT);
  analogWrite(VIBRATION_PIN, 0);  // 初期状態はオフ

  // WiFi接続
  setupWiFi();

  // サーバー設定
  setupServer();

  // WebSocketクライアントの初期化
  webSocketClient = WebSocketClient(wifiClient, serverAddress, serverPort);
  
  Serial.print("WebSocketサーバー: ");
  Serial.print(serverAddress);
  Serial.print(":");
  Serial.print(serverPort);
  Serial.println(wsPath);

  // HTTPサーバーの初期化と開始
  httpServer = WiFiServer(httpPort);
  httpServer.begin();
  
  Serial.print("ローカルHTTPサーバーが開始されました (ポート ");
  Serial.print(httpPort);
  Serial.println(")");

  Serial.println("初期設定が完了しました");
}

void loop() {
  // WebSocket接続の確認と維持
  checkWebSocketConnection();
  
  // HTTP接続の確認
  checkHttpConnection();
  
  // 振動パターンの再生
  if (isPlaying) {
    playVibrationPattern();
  }
  
  // 定期的な状態更新
  updateStatus();
}

/**
 * WiFi設定を行う
 */
void setupWiFi() {
  Serial.println("=== WiFi設定 ===");
  
  // SSIDの入力
  Serial.println("WiFi SSID: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputSsid = Serial.readStringUntil('\n');
  inputSsid.trim();
  inputSsid.toCharArray(ssid, sizeof(ssid));
  
  // パスワードの入力
  Serial.println("WiFiパスワード: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputPassword = Serial.readStringUntil('\n');
  inputPassword.trim();
  inputPassword.toCharArray(password, sizeof(password));
  
  // WiFi接続の開始
  Serial.print("WiFiに接続中: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  
  // 接続が確立されるまで待機
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    
    // タイムアウト処理（30秒）
    if (millis() - startTime > 30000) {
      Serial.println("\nWiFi接続がタイムアウトしました");
      currentState = ERROR;
      errorMessage = "WiFi接続タイムアウト";
      return;
    }
  }

  Serial.println("");
  Serial.println("WiFiに接続されました");
  Serial.print("IPアドレス: ");
  Serial.println(WiFi.localIP());
}

/**
 * サーバー設定を行う
 */
void setupServer() {
  Serial.println("\n=== サーバー設定 ===");
  
  // WebSocketサーバーアドレスの入力
  Serial.println("WebSocketサーバーアドレス: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputAddress = Serial.readStringUntil('\n');
  inputAddress.trim();
  inputAddress.toCharArray(serverAddress, sizeof(serverAddress));
  
  // WebSocketサーバーポートの入力
  Serial.println("WebSocketサーバーポート: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputPort = Serial.readStringUntil('\n');
  inputPort.trim();
  serverPort = inputPort.toInt();
  
  // WebSocketパスの入力
  Serial.println("WebSocketパス (例: /ws): ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputPath = Serial.readStringUntil('\n');
  inputPath.trim();
  inputPath.toCharArray(wsPath, sizeof(wsPath));
  
  // HTTPサーバーポートの入力
  Serial.println("ローカルHTTPサーバーポート: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputHttpPort = Serial.readStringUntil('\n');
  inputHttpPort.trim();
  httpPort = inputHttpPort.toInt();
  
  // デバイスIDの入力
  Serial.println("デバイスID: ");
  while (!Serial.available()) {
    delay(100);
  }
  
  String inputDeviceId = Serial.readStringUntil('\n');
  inputDeviceId.trim();
  inputDeviceId.toCharArray(deviceId, sizeof(deviceId));
}

/**
 * WebSocket接続を確認し、必要に応じて再接続する
 */
void checkWebSocketConnection() {
  // 接続が確立されていない場合、一定間隔で再接続を試みる
  if (!wsConnected) {
    unsigned long currentTime = millis();
    
    if (currentTime - lastConnectionAttempt >= CONNECTION_RETRY_INTERVAL) {
      lastConnectionAttempt = currentTime;
      
      Serial.println("WebSocketサーバーに接続を試みています...");
      
      if (webSocketClient.begin(wsPath)) {
        Serial.println("WebSocketサーバーに接続されました");
        wsConnected = true;
        
        // 接続成功時に状態を送信
        sendWebSocketStatus();
      } else {
        Serial.println("WebSocket接続に失敗しました");
      }
    }
  } else {
    // 接続が確立されている場合、メッセージの確認
    int messageSize = webSocketClient.parseMessage();
    
    if (messageSize > 0) {
      String data = "";
      
      while (webSocketClient.available()) {
        data += (char)webSocketClient.read();
      }
      
      Serial.print("WebSocketメッセージを受信: ");
      Serial.println(data);
      
      // JSONデータの処理
      if (data.startsWith("{")) {
        parseVibrationPattern(data);
        sendWebSocketMessage("{\"status\":\"ok\",\"message\":\"パターンを受信しました\"}");
      } else if (data == "stop") {
        stopVibrationPattern();
        sendWebSocketMessage("{\"status\":\"ok\",\"message\":\"振動を停止しました\"}");
      } else if (data == "status") {
        sendWebSocketStatus();
      }
    }
    
    // 接続状態の確認
    if (!webSocketClient.connected()) {
      Serial.println("WebSocket接続が切断されました");
      wsConnected = false;
    }
  }
}

/**
 * HTTP接続を確認し、データを処理する
 */
void checkHttpConnection() {
  // 新しいクライアントの確認
  WiFiClient httpClient = httpServer.available();
  
  if (httpClient) {
    Serial.println("新しいHTTPクライアントが接続されました");
    
    // リクエストの読み取り
    String currentLine = "";
    String jsonData = "";
    bool isJson = false;
    String requestType = "";
    String requestPath = "";
    bool requestLineRead = false;
    
    while (httpClient.connected()) {
      if (httpClient.available()) {
        char c = httpClient.read();
        
        // リクエスト行の解析
        if (!requestLineRead) {
          if (c != '\n') {
            currentLine += c;
          } else {
            // リクエスト行を解析
            int firstSpace = currentLine.indexOf(' ');
            int secondSpace = currentLine.indexOf(' ', firstSpace + 1);
            
            if (firstSpace != -1 && secondSpace != -1) {
              requestType = currentLine.substring(0, firstSpace);
              requestPath = currentLine.substring(firstSpace + 1, secondSpace);
            }
            
            currentLine = "";
            requestLineRead = true;
          }
        } else {
          // JSONデータの読み取り
          if (c == '{') {
            isJson = true;
          }
          
          if (isJson) {
            jsonData += c;
          }
          
          if (c == '}' && isJson) {
            isJson = false;
          }
          
          // HTTPリクエストの終了を検出
          if (c == '\n') {
            if (currentLine.length() == 0) {
              // HTTPヘッダーの送信
              httpClient.println("HTTP/1.1 200 OK");
              httpClient.println("Content-type:application/json");
              httpClient.println("Access-Control-Allow-Origin: *");
              httpClient.println("Connection: close");
              httpClient.println();
              
              // リクエストパスに基づいて処理
              if (requestPath == "/pattern" && requestType == "POST" && jsonData.length() > 0) {
                // 振動パターンの処理
                parseVibrationPattern(jsonData);
                httpClient.println("{\"status\":\"ok\",\"message\":\"パターンを受信しました\"}");
              } else if (requestPath == "/status") {
                // デバイス状態の送信
                sendStatusResponse(httpClient);
              } else if (requestPath == "/stop" && requestType == "POST") {
                // 振動の停止
                stopVibrationPattern();
                httpClient.println("{\"status\":\"ok\",\"message\":\"振動を停止しました\"}");
              } else if (requestPath == "/heartbeat") {
                // ハートビートレスポンス
                httpClient.println("{\"status\":\"ok\",\"device_state\":\"" + getStateString() + "\"}");
              } else {
                // 不明なリクエスト
                httpClient.println("{\"status\":\"error\",\"message\":\"不明なリクエストです\"}");
              }
              
              break;
            } else {
              currentLine = "";
            }
          } else if (c != '\r') {
            currentLine += c;
          }
        }
      }
    }
    
    // 接続のクローズ
    httpClient.stop();
    Serial.println("HTTPクライアント切断");
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
    currentState = ERROR;
    errorMessage = String("JSONの解析に失敗: ") + error.c_str();
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
  currentState = PLAYING;
  
  Serial.println("振動パターンの再生を開始します");
  
  // 最初のステップの振動強度を設定
  analogWrite(VIBRATION_PIN, currentPattern.steps[currentStep].intensity);
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
  currentState = IDLE;
  Serial.println("振動パターンの再生を停止しました");
}

/**
 * デバイスの状態を更新し、必要に応じてクライアントに通知する
 */
void updateStatus() {
  unsigned long currentTime = millis();
  
  // 状態更新の間隔をチェック
  if (currentTime - lastStatusUpdateTime >= STATUS_UPDATE_INTERVAL) {
    lastStatusUpdateTime = currentTime;
    
    // WebSocketクライアントに状態を送信
    if (wsConnected) {
      sendWebSocketStatus();
    }
  }
  
  // ハートビートの送信
  if (currentTime - lastHeartbeatTime >= HEARTBEAT_INTERVAL) {
    lastHeartbeatTime = currentTime;
    
    // シリアルにハートビート情報を出力
    Serial.print("ハートビート: ");
    Serial.println(getStateString());
  }
}

/**
 * HTTPクライアントに状態レスポンスを送信する
 */
void sendStatusResponse(WiFiClient &client) {
  // 状態情報のJSONを作成
  DynamicJsonDocument doc(256);
  
  doc["status"] = "ok";
  doc["device_id"] = deviceId;
  doc["device_state"] = getStateString();
  doc["is_playing"] = isPlaying;
  
  if (isPlaying) {
    doc["current_step"] = currentStep;
    doc["total_steps"] = currentPattern.stepCount;
    doc["current_repeat"] = currentRepeat;
    doc["total_repeats"] = currentPattern.repeatCount;
  }
  
  if (currentState == ERROR) {
    doc["error_message"] = errorMessage;
  }
  
  // JSONをシリアル化して送信
  String jsonResponse;
  serializeJson(doc, jsonResponse);
  client.println(jsonResponse);
}

/**
 * WebSocketクライアントに状態を送信する
 */
void sendWebSocketStatus() {
  // 状態情報のJSONを作成
  DynamicJsonDocument doc(256);
  
  doc["type"] = "status";
  doc["device_id"] = deviceId;
  doc["device_state"] = getStateString();
  doc["is_playing"] = isPlaying;
  
  if (isPlaying) {
    doc["current_step"] = currentStep;
    doc["total_steps"] = currentPattern.stepCount;
    doc["current_repeat"] = currentRepeat;
    doc["total_repeats"] = currentPattern.repeatCount;
  }
  
  if (currentState == ERROR) {
    doc["error_message"] = errorMessage;
  }
  
  // JSONをシリアル化して送信
  String jsonResponse;
  serializeJson(doc, jsonResponse);
  sendWebSocketMessage(jsonResponse);
}

/**
 * WebSocketクライアントにメッセージを送信する
 */
void sendWebSocketMessage(String message) {
  if (wsConnected) {
    webSocketClient.beginMessage(TYPE_TEXT);
    webSocketClient.print(message);
    webSocketClient.endMessage();
  }
}

/**
 * 現在の状態を文字列として取得する
 */
String getStateString() {
  switch (currentState) {
    case IDLE:
      return "idle";
    case PLAYING:
      return "playing";
    case ERROR:
      return "error";
    default:
      return "unknown";
  }
}
