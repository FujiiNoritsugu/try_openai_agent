"""
APIアプリケーション

このモジュールは、感情分析パイプラインと触覚フィードバックデバイスの
APIエンドポイントを提供するFastAPIアプリケーションを定義します。
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    DeviceConfig,
    DeviceStatus,
    EmotionAnalysisRequest,
    EmotionAnalysisResponse,
    DeviceListResponse,
    DeviceStatusResponse,
    VibrationRequest,
    VibrationResponse,
    ErrorResponse
)
from ..models.data_models import UserInput, Emotion
from ..devices.pipeline_integration import haptic_feedback
from ..pipeline.pipeline import run_pipeline, format_pipeline_results


logger = logging.getLogger(__name__)

app = FastAPI(
    title="感情分析API",
    description="感情分析パイプラインと触覚フィードバックデバイスのAPIエンドポイント",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

registered_devices: List[DeviceConfig] = []


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("APIサーバーを起動中...")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("APIサーバーをシャットダウン中...")
    if haptic_feedback.is_initialized:
        await haptic_feedback.shutdown()


@app.get("/", response_model=Dict[str, str])
async def root():
    """ルートエンドポイント"""
    return {"message": "感情分析APIへようこそ"}


@app.post("/api/v1/analyze", response_model=EmotionAnalysisResponse, responses={500: {"model": ErrorResponse}})
async def analyze_emotion(request: EmotionAnalysisRequest):
    """
    感情分析を実行するエンドポイント
    
    ユーザー入力から感情を抽出・分類し、適切な感情応答を生成します。
    オプションで、結果を接続された触覚フィードバックデバイスに送信します。
    """
    try:
        if request.send_to_devices and not haptic_feedback.is_initialized and registered_devices:
            await haptic_feedback.initialize([device.dict() for device in registered_devices])
        
        if request.send_to_devices and haptic_feedback.is_initialized:
            formatted_results, device_results = await haptic_feedback.run_pipeline_and_send(request.user_input)
            return EmotionAnalysisResponse(
                **formatted_results,
                device_results=device_results
            )
        else:
            ctx, error = await run_pipeline(request.user_input)
            if error:
                raise HTTPException(status_code=500, detail=f"パイプライン実行中にエラーが発生しました: {str(error)}")
            
            formatted_results = format_pipeline_results(ctx)
            return EmotionAnalysisResponse(**formatted_results)
            
    except Exception as e:
        logger.error(f"感情分析中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/devices", response_model=DeviceListResponse)
async def get_devices():
    """
    登録済みデバイスのリストを取得するエンドポイント
    """
    return DeviceListResponse(devices=registered_devices)


@app.post("/api/v1/devices", response_model=DeviceConfig, responses={400: {"model": ErrorResponse}})
async def register_device(device: DeviceConfig):
    """
    新しいデバイスを登録するエンドポイント
    """
    for existing_device in registered_devices:
        if existing_device.device_id == device.device_id:
            raise HTTPException(status_code=400, detail=f"デバイスID '{device.device_id}' は既に登録されています")
    
    registered_devices.append(device)
    logger.info(f"新しいデバイスを登録しました: {device.device_id}")
    
    return device


@app.delete("/api/v1/devices/{device_id}", response_model=Dict[str, str], responses={404: {"model": ErrorResponse}})
async def unregister_device(device_id: str, background_tasks: BackgroundTasks):
    """
    デバイスの登録を解除するエンドポイント
    """
    for i, device in enumerate(registered_devices):
        if device.device_id == device_id:
            removed_device = registered_devices.pop(i)
            logger.info(f"デバイスの登録を解除しました: {device_id}")
            
            if haptic_feedback.is_initialized:
                background_tasks.add_task(haptic_feedback.websocket_manager.disconnect, device_id)
            
            return {"message": f"デバイス '{device_id}' の登録を解除しました"}
    
    raise HTTPException(status_code=404, detail=f"デバイスID '{device_id}' が見つかりません")


@app.post("/api/v1/devices/initialize", response_model=Dict[str, bool], responses={500: {"model": ErrorResponse}})
async def initialize_devices():
    """
    登録済みデバイスを初期化するエンドポイント
    """
    if not registered_devices:
        raise HTTPException(status_code=400, detail="初期化するデバイスがありません")
    
    try:
        result = await haptic_feedback.initialize([device.dict() for device in registered_devices])
        return {"success": result}
    except Exception as e:
        logger.error(f"デバイス初期化中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/devices/shutdown", response_model=Dict[str, bool], responses={500: {"model": ErrorResponse}})
async def shutdown_devices():
    """
    デバイスをシャットダウンするエンドポイント
    """
    if not haptic_feedback.is_initialized:
        return {"success": True}
    
    try:
        result = await haptic_feedback.shutdown()
        return {"success": result}
    except Exception as e:
        logger.error(f"デバイスシャットダウン中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/devices/status", response_model=DeviceStatusResponse, responses={500: {"model": ErrorResponse}})
async def get_device_status():
    """
    デバイスの状態を取得するエンドポイント
    """
    if not haptic_feedback.is_initialized:
        raise HTTPException(status_code=400, detail="デバイスが初期化されていません")
    
    try:
        status_dict = await haptic_feedback.get_all_device_status()
        
        device_status_list = []
        for device_id, status in status_dict.items():
            if status:
                device_status_list.append(DeviceStatus(
                    device_id=device_id,
                    device_state=status.device_state,
                    connected=True,
                    last_updated=getattr(status, "last_updated", None)
                ))
            else:
                device_status_list.append(DeviceStatus(
                    device_id=device_id,
                    device_state="unknown",
                    connected=False,
                    last_updated=None
                ))
        
        return DeviceStatusResponse(devices=device_status_list)
    except Exception as e:
        logger.error(f"デバイス状態取得中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/vibration", response_model=VibrationResponse, responses={500: {"model": ErrorResponse}})
async def send_vibration(request: VibrationRequest):
    """
    振動パターンを送信するエンドポイント
    
    感情パラメータと感情カテゴリに基づいて、
    接続された触覚フィードバックデバイスに振動パターンを送信します。
    """
    if not haptic_feedback.is_initialized:
        raise HTTPException(status_code=400, detail="デバイスが初期化されていません")
    
    try:
        if request.device_ids:
            results = {}
            for device_id in request.device_ids:
                result = await haptic_feedback.websocket_manager.send(
                    device_id, 
                    request.emotion, 
                    request.emotion_category
                )
                results[device_id] = result
        else:
            results = await haptic_feedback.websocket_manager.send_to_all(
                request.emotion, 
                request.emotion_category
            )
        
        return VibrationResponse(results=results)
    except Exception as e:
        logger.error(f"振動パターン送信中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/vibration/stop", response_model=VibrationResponse, responses={500: {"model": ErrorResponse}})
async def stop_vibration(device_ids: Optional[List[str]] = None):
    """
    振動を停止するエンドポイント
    
    接続された触覚フィードバックデバイスの振動を停止します。
    デバイスIDのリストを指定すると、特定のデバイスのみ停止します。
    """
    if not haptic_feedback.is_initialized:
        raise HTTPException(status_code=400, detail="デバイスが初期化されていません")
    
    try:
        if device_ids:
            results = {}
            for device_id in device_ids:
                result = await haptic_feedback.websocket_manager.stop(device_id)
                results[device_id] = result
        else:
            results = await haptic_feedback.stop_all_devices()
        
        return VibrationResponse(results=results)
    except Exception as e:
        logger.error(f"振動停止中にエラーが発生しました: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
