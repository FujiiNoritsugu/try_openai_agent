#!/usr/bin/env python3
"""
WiFi触覚フィードバックテストスクリプト

このスクリプトは、ArduinoデバイスとのHTTP通信をテストします。
Arduino Uno R4 WiFiにhaptic_feedback_controller.inoがアップロード済みであることを前提とします。
"""

import asyncio
import sys
import os

# プロジェクトのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.devices.arduino_controller import ArduinoController, ArduinoControllerConfig
from src.devices.vibration_patterns import VibrationPattern, VibrationStep


async def test_wifi_communication():
    """WiFi通信のテスト"""

    # ArduinoのIPアドレスを設定（必要に応じて変更してください）
    ARDUINO_IP = "192.168.43.166"  # ← あなたのArduinoのIPアドレスに変更してください
    ARDUINO_PORT = 80

    print(f"Arduino WiFi触覚フィードバックテスト")
    print(f"接続先: {ARDUINO_IP}:{ARDUINO_PORT}")
    print("-" * 50)

    # コントローラーの設定と初期化
    config = ArduinoControllerConfig(
        host=ARDUINO_IP, port=ARDUINO_PORT, timeout=5.0, retry_count=3, retry_delay=1.0
    )

    controller = ArduinoController(config)

    try:
        # 1. 接続テスト
        print("\n1. デバイスへの接続...")
        connected = await controller.connect()

        if not connected:
            print("❌ デバイスへの接続に失敗しました")
            print("以下を確認してください:")
            print("  - ArduinoのIPアドレスが正しいか")
            print("  - Arduinoがネットワークに接続されているか")
            print("  - haptic_feedback_controller.inoがアップロードされているか")
            return

        print("✅ デバイスに接続しました")

        # 2. 振動パターンのテスト
        print("\n2. 振動パターンのテスト...")

        # テストパターン1: 短い振動
        print("\n   テスト1: 短い振動（3回）")
        pattern1 = VibrationPattern(
            steps=[
                VibrationStep(intensity=0.8, duration_ms=200),
                VibrationStep(intensity=0, duration_ms=100),
                VibrationStep(intensity=0.8, duration_ms=200),
                VibrationStep(intensity=0, duration_ms=100),
                VibrationStep(intensity=0.8, duration_ms=200),
            ],
            interval_ms=0,
            repeat_count=1,
        )

        success = await controller.send_pattern(pattern1)
        if success:
            print("   ✅ パターン1送信成功")
        else:
            print("   ❌ パターン1送信失敗")

        await asyncio.sleep(2)

        # テストパターン2: 徐々に強くなる振動
        print("\n   テスト2: 徐々に強くなる振動")
        pattern2 = VibrationPattern(
            steps=[
                VibrationStep(intensity=0.2, duration_ms=500),
                VibrationStep(intensity=0.4, duration_ms=500),
                VibrationStep(intensity=0.6, duration_ms=500),
                VibrationStep(intensity=0.8, duration_ms=500),
                VibrationStep(intensity=1.0, duration_ms=1000),
            ],
            interval_ms=0,
            repeat_count=1,
        )

        success = await controller.send_pattern(pattern2)
        if success:
            print("   ✅ パターン2送信成功")
        else:
            print("   ❌ パターン2送信失敗")

        await asyncio.sleep(4)

        # テストパターン3: パルス振動
        print("\n   テスト3: パルス振動（繰り返し）")
        pattern3 = VibrationPattern(
            steps=[
                VibrationStep(intensity=1.0, duration_ms=100),
                VibrationStep(intensity=0, duration_ms=100),
            ],
            interval_ms=500,
            repeat_count=5,
        )

        success = await controller.send_pattern(pattern3)
        if success:
            print("   ✅ パターン3送信成功")
        else:
            print("   ❌ パターン3送信失敗")

        await asyncio.sleep(5)

        # 3. 振動停止テスト
        print("\n3. 振動停止...")
        stopped = await controller.stop()
        if stopped:
            print("✅ 振動を停止しました")
        else:
            print("❌ 振動停止に失敗しました")

        # 4. ステータス確認
        print("\n4. デバイスステータス確認...")
        status = await controller.get_status()
        if status:
            print(f"✅ ステータス取得成功:")
            print(f"   接続状態: {'接続中' if status.get('connected') else '切断'}")
            print(f"   再生中: {'はい' if status.get('playing') else 'いいえ'}")
        else:
            print("❌ ステータス取得失敗")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")

    finally:
        # 5. 切断
        print("\n5. デバイスから切断...")
        disconnected = await controller.disconnect()
        if disconnected:
            print("✅ デバイスから切断しました")
        else:
            print("❌ 切断に失敗しました")

    print("\n" + "-" * 50)
    print("テスト完了")


if __name__ == "__main__":
    print("=" * 50)
    print("Arduino WiFi触覚フィードバック通信テスト")
    print("=" * 50)

    # イベントループを実行
    asyncio.run(test_wifi_communication())
