/**
 * 触覚フィードバックコントローラー（シリアル通信版）
 * 
 * Arduino Uno R4用のスケッチで、Youmile GR-YM-222-2振動モジュールを
 * 制御し、USBシリアル経由で受信した振動パターンを物理的な振動に変換します。
 * 
 * ハードウェア:
 * - Arduino Uno R4
 * - Youmile GR-YM-222-2振動モジュール
 * 
 * 通信:
 * - USBシリアル通信（115200 bps）
 * - JSON形式でコマンドを受信
 */

#include <ArduinoJson.h>

// 振動モジュールのピン設定
const int VIBRATION_PIN = 9;  // PWMピン (Arduino UNO R4: 3,5,6,9,10,11がPWM対応)

// 振動パターンの最大ステップ数
const int MAX_STEPS = 10;

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

// シリアル通信バッファ
String inputBuffer = "";

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

  Serial.println("シリアル通信モード: 準備完了");
  Serial.println("JSON形式のコマンドを待っています...");
}

/**
 * 指定されたピンがPWM対応かチェック
 */
bool isPWMPin(int pin) {
  // Arduino UNO R4のPWM対応ピン
  int pwmPins[] = {3, 5, 6, 9, 10, 11};
  for (int i = 0; i < 6; i++) {
    if (pin == pwmPins[i]) return true;
  }
  return false;
}

void loop() {
  // シリアル通信からのデータを読み込む
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    // 改行文字が来たらコマンドを処理
    if (c == '\n') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    } else if (c != '\r') {  // キャリッジリターンは無視
      inputBuffer += c;
      
      // バッファオーバーフロー防止
      if (inputBuffer.length() > 1000) {
        Serial.println("エラー: 入力バッファオーバーフロー");
        inputBuffer = "";
      }
    }
  }
  
  // 振動パターンの更新
  vibrationController.update();
}

/**
 * 受信したコマンドを処理する
 */
void processCommand(String command) {
  Serial.print("受信したコマンド: ");
  Serial.println(command);
  
  // JSONコマンドの解析
  if (command.startsWith("{")) {
    parseVibrationPattern(command);
  } else {
    Serial.println("エラー: 無効なコマンド形式");
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