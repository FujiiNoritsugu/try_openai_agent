"""
触覚フィードバック統合の使用例

このスクリプトは、感情分析パイプラインと触覚フィードバックデバイスの統合を
デモンストレーションします。
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

from src.models.data_models import UserInput
from src.devices.pipeline_integration import haptic_feedback


async def main():
    """メイン関数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    load_dotenv()
    
    device_configs = [
        {
            "device_id": "device1",
            "host": "192.168.1.100",  # Arduinoデバイスのホスト（実際の値に変更してください）
            "port": 80
        }
    ]
    
    try:
        logger.info("触覚フィードバックシステムを初期化中...")
        initialized = await haptic_feedback.initialize(device_configs)
        
        if not initialized:
            logger.error("触覚フィードバックシステムの初期化に失敗しました")
            return
            
        logger.info("触覚フィードバックシステムが初期化されました")
        
        user_input = UserInput(
            data="0.7",  # 刺激の強さ（0.0-1.0）
            touched_area="胸",  # 触れられた部位
            gender="男性"  # 性別
        )
        
        logger.info(f"パイプラインを実行中: {user_input}")
        results, device_results = await haptic_feedback.run_pipeline_and_send(user_input)
        
        logger.info(f"パイプライン結果: {results}")
        logger.info(f"デバイス送信結果: {device_results}")
        
        logger.info("デバイスの状態を取得中...")
        status = await haptic_feedback.get_all_device_status()
        logger.info(f"デバイスの状態: {status}")
        
        logger.info("5秒間待機中...")
        await asyncio.sleep(5)
        
        logger.info("振動を停止中...")
        stop_results = await haptic_feedback.stop_all_devices()
        logger.info(f"停止結果: {stop_results}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
    finally:
        logger.info("触覚フィードバックシステムをシャットダウン中...")
        await haptic_feedback.shutdown()
        logger.info("触覚フィードバックシステムがシャットダウンされました")


if __name__ == "__main__":
    asyncio.run(main())
