"""
APIサーバー起動スクリプト

このスクリプトは、感情分析パイプラインと触覚フィードバックデバイスの
APIサーバーを起動するためのコマンドラインエントリーポイントです。
"""
from src.api.server import main

if __name__ == "__main__":
    main()
