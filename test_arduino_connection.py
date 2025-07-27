#!/usr/bin/env python3
"""
Arduino接続テストスクリプト

このスクリプトは、Arduino Uno R4 WiFiとの接続をテストし、
振動パターンを送信する機能を確認します。
"""

import asyncio
import os
import sys
import logging
from typing import Optional

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.devices.arduino_controller import ArduinoController, ArduinoControllerConfig
from src.devices.vibration_patterns import VibrationStep, VibrationPattern, EmotionVibrationPatterns
from src.models.data_models import Emotion

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_basic_connection(controller: ArduinoController) -> bool:
    """基本的な接続テストを行います。"""
    logger.info("=== 基本接続テスト ===")
    
    try:
        # 接続テスト
        logger.info("Arduinoに接続中...")
        success = await controller.connect()
        
        if success:
            logger.info("✅ 接続成功!")
            return True
        else:
            logger.error("❌ 接続失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 接続エラー: {e}")
        return False


async def test_simple_vibration(controller: ArduinoController) -> bool:
    """シンプルな振動パターンをテストします。"""
    logger.info("=== シンプル振動テスト ===")
    
    try:
        # シンプルなパターンを作成
        pattern = VibrationPattern(
            steps=[
                VibrationStep(intensity=0.5, duration_ms=500),
                VibrationStep(intensity=0.0, duration_ms=200),
                VibrationStep(intensity=0.8, duration_ms=300),
            ],
            interval_ms=100,
            repeat_count=2
        )
        
        logger.info("振動パターンを送信中...")
        success = await controller.send_pattern(pattern)
        
        if success:
            logger.info("✅ パターン送信成功!")
            logger.info("振動を確認してください（約3秒間）")
            await asyncio.sleep(4)  # パターン完了まで待機
            return True
        else:
            logger.error("❌ パターン送信失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 振動テストエラー: {e}")
        return False


async def test_emotion_patterns(controller: ArduinoController) -> bool:
    """感情ベースの振動パターンをテストします。"""
    logger.info("=== 感情パターンテスト ===")
    
    emotions_to_test = [
        ("喜び", Emotion(joy=0.8, fun=0.3, anger=0.1, sad=0.1)),
        ("怒り", Emotion(joy=0.1, fun=0.1, anger=0.9, sad=0.2)),
        ("悲しみ", Emotion(joy=0.1, fun=0.0, anger=0.2, sad=0.8)),
        ("楽しさ", Emotion(joy=0.6, fun=0.9, anger=0.0, sad=0.0)),
    ]
    
    for emotion_name, emotion in emotions_to_test:
        try:
            logger.info(f"{emotion_name}の感情パターンを送信中...")
            success = await controller.send_emotion(emotion)
            
            if success:
                logger.info(f"✅ {emotion_name}パターン送信成功!")
                logger.info("振動を確認してください...")
                await asyncio.sleep(3)  # 次のパターンまで待機
            else:
                logger.error(f"❌ {emotion_name}パターン送信失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ {emotion_name}テストエラー: {e}")
            return False
    
    return True


async def test_stress_patterns(controller: ArduinoController) -> bool:
    """ストレステスト用のパターンを送信します。"""
    logger.info("=== ストレステスト ===")
    
    try:
        # 複雑なパターンを作成
        complex_pattern = VibrationPattern(
            steps=[
                VibrationStep(intensity=0.2, duration_ms=100),
                VibrationStep(intensity=0.4, duration_ms=150),
                VibrationStep(intensity=0.6, duration_ms=200),
                VibrationStep(intensity=0.8, duration_ms=250),
                VibrationStep(intensity=1.0, duration_ms=300),
                VibrationStep(intensity=0.8, duration_ms=250),
                VibrationStep(intensity=0.6, duration_ms=200),
                VibrationStep(intensity=0.4, duration_ms=150),
                VibrationStep(intensity=0.2, duration_ms=100),
            ],
            interval_ms=50,
            repeat_count=3
        )
        
        logger.info("複雑な振動パターンを送信中...")
        success = await controller.send_pattern(complex_pattern)
        
        if success:
            logger.info("✅ 複雑パターン送信成功!")
            logger.info("長い振動シーケンスを確認してください（約10秒間）")
            await asyncio.sleep(12)
            return True
        else:
            logger.error("❌ 複雑パターン送信失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ ストレステストエラー: {e}")
        return False


async def interactive_test(controller: ArduinoController):
    """インタラクティブなテストモードです。"""
    logger.info("=== インタラクティブテスト ===")
    logger.info("利用可能なコマンド:")
    logger.info("  1: 弱い振動")
    logger.info("  2: 中程度の振動")
    logger.info("  3: 強い振動")
    logger.info("  4: 喜びパターン")
    logger.info("  5: 怒りパターン")
    logger.info("  6: 悲しみパターン")
    logger.info("  7: 楽しさパターン")
    logger.info("  q: 終了")
    
    while True:
        try:
            command = input("\nコマンドを入力してください: ").strip()
            
            if command == 'q':
                break
            elif command == '1':
                pattern = VibrationPattern(
                    steps=[VibrationStep(intensity=0.3, duration_ms=500)],
                    interval_ms=0,
                    repeat_count=1
                )
                await controller.send_pattern(pattern)
                logger.info("弱い振動を送信しました")
                
            elif command == '2':
                pattern = VibrationPattern(
                    steps=[VibrationStep(intensity=0.6, duration_ms=500)],
                    interval_ms=0,
                    repeat_count=1
                )
                await controller.send_pattern(pattern)
                logger.info("中程度の振動を送信しました")
                
            elif command == '3':
                pattern = VibrationPattern(
                    steps=[VibrationStep(intensity=1.0, duration_ms=500)],
                    interval_ms=0,
                    repeat_count=1
                )
                await controller.send_pattern(pattern)
                logger.info("強い振動を送信しました")
                
            elif command == '4':
                emotion = Emotion(joy=0.8, fun=0.3, anger=0.1, sad=0.1)
                await controller.send_emotion(emotion)
                logger.info("喜びパターンを送信しました")
                
            elif command == '5':
                emotion = Emotion(joy=0.1, fun=0.1, anger=0.9, sad=0.2)
                await controller.send_emotion(emotion)
                logger.info("怒りパターンを送信しました")
                
            elif command == '6':
                emotion = Emotion(joy=0.1, fun=0.0, anger=0.2, sad=0.8)
                await controller.send_emotion(emotion)
                logger.info("悲しみパターンを送信しました")
                
            elif command == '7':
                emotion = Emotion(joy=0.6, fun=0.9, anger=0.0, sad=0.0)
                await controller.send_emotion(emotion)
                logger.info("楽しさパターンを送信しました")
                
            else:
                logger.info("無効なコマンドです")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"エラー: {e}")


async def main():
    """メイン関数"""
    logger.info("Arduino接続テストを開始します")
    
    # ArduinoのIPアドレスを取得
    arduino_ip = input("ArduinoのIPアドレスを入力してください (例: 192.168.1.100): ").strip()
    if not arduino_ip:
        logger.error("IPアドレスが入力されていません")
        return
    
    # 設定を作成
    config = ArduinoControllerConfig(
        host=arduino_ip,
        port=80,
        timeout=10.0,
        retry_count=3,
        retry_delay=1.0
    )
    
    # コントローラーを作成
    controller = ArduinoController(config)
    
    try:
        # 基本接続テスト
        if not await test_basic_connection(controller):
            logger.error("基本接続テストに失敗しました。プログラムを終了します。")
            return
        
        # テストメニュー
        while True:
            print("\n" + "="*50)
            print("Arduino振動テストメニュー")
            print("="*50)
            print("1. シンプル振動テスト")
            print("2. 感情パターンテスト")
            print("3. ストレステスト")
            print("4. インタラクティブテスト")
            print("5. 終了")
            
            choice = input("\n選択してください (1-5): ").strip()
            
            if choice == '1':
                await test_simple_vibration(controller)
            elif choice == '2':
                await test_emotion_patterns(controller)
            elif choice == '3':
                await test_stress_patterns(controller)
            elif choice == '4':
                await interactive_test(controller)
            elif choice == '5':
                break
            else:
                print("無効な選択です")
        
    except KeyboardInterrupt:
        logger.info("テストが中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
    finally:
        # 切断
        await controller.disconnect()
        logger.info("テストを終了しました")


if __name__ == "__main__":
    asyncio.run(main())