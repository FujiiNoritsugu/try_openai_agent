"""
パイプライン統合のテスト
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.data_models import UserInput, Emotion, PipelineContext
from src.devices.pipeline_integration import HapticFeedbackIntegration, haptic_feedback


@pytest.fixture
def mock_websocket_manager():
    """WebSocketControllerManagerのモック"""
    manager = AsyncMock()
    manager.initialize = AsyncMock(return_value=True)
    manager.connect_all = AsyncMock(return_value={"device1": True})
    manager.disconnect_all = AsyncMock(return_value={"device1": True})
    manager.send_to_all = AsyncMock(return_value={"device1": True})
    manager.get_all_status = AsyncMock(return_value={"device1": {"device_state": "idle"}})
    manager.stop_all = AsyncMock(return_value={"device1": True})
    return manager


@pytest.fixture
def integration(mock_websocket_manager):
    """HapticFeedbackIntegrationのインスタンス"""
    with patch("src.devices.pipeline_integration.WebSocketControllerManager", return_value=mock_websocket_manager):
        integration = HapticFeedbackIntegration()
        return integration


@pytest.mark.asyncio
async def test_initialize(integration, mock_websocket_manager):
    """初期化のテスト"""
    device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
    
    result = await integration.initialize(device_configs)
    
    assert result is True
    mock_websocket_manager.initialize.assert_called_once_with(device_configs)
    mock_websocket_manager.connect_all.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown(integration, mock_websocket_manager):
    """シャットダウンのテスト"""
    await integration.shutdown()
    
    mock_websocket_manager.disconnect_all.assert_called_once()


@pytest.mark.asyncio
async def test_process_pipeline_result(integration, mock_websocket_manager):
    """パイプライン結果の処理テスト"""
    ctx = PipelineContext()
    ctx.emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)
    ctx.emotion_category = "joy"
    
    device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
    await integration.initialize(device_configs)
    
    result = await integration.process_pipeline_result(ctx)
    
    assert result == {"device1": True}
    mock_websocket_manager.send_to_all.assert_called_once_with(ctx.emotion, ctx.emotion_category)


@pytest.mark.asyncio
async def test_run_pipeline_and_send(integration, mock_websocket_manager):
    """パイプライン実行と送信のテスト"""
    async def mock_run_pipeline(user_input, emotion_learner=None):
        ctx = PipelineContext()
        ctx.emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)
        ctx.emotion_category = "joy"
        return ctx, None
    
    with patch("src.devices.pipeline_integration.run_pipeline", mock_run_pipeline):
        device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
        await integration.initialize(device_configs)
        
        user_input = UserInput(data="0.7", touched_area="胸", gender="男性")
        
        ctx, device_results = await integration.run_pipeline_and_send(user_input)
        
        assert ctx.emotion.joy == 0.8
        assert ctx.emotion_category == "joy"
        assert device_results == {"device1": True}
        mock_websocket_manager.send_to_all.assert_called_once_with(ctx.emotion, ctx.emotion_category)


@pytest.mark.asyncio
async def test_get_all_device_status(integration, mock_websocket_manager):
    """デバイス状態取得のテスト"""
    device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
    await integration.initialize(device_configs)
    
    status = await integration.get_all_device_status()
    
    assert status == {"device1": {"device_state": "idle"}}
    mock_websocket_manager.get_all_status.assert_called_once()


@pytest.mark.asyncio
async def test_stop_all_devices(integration, mock_websocket_manager):
    """デバイス停止のテスト"""
    device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
    await integration.initialize(device_configs)
    
    result = await integration.stop_all_devices()
    
    assert result == {"device1": True}
    mock_websocket_manager.stop_all.assert_called_once()


@pytest.mark.asyncio
async def test_singleton_instance():
    """シングルトンインスタンスのテスト"""
    instance1 = haptic_feedback
    instance2 = haptic_feedback
    
    assert instance1 is instance2


@pytest.mark.asyncio
async def test_error_handling(integration, mock_websocket_manager):
    """エラーハンドリングのテスト"""
    mock_websocket_manager.connect_all.return_value = {"device1": False}
    
    device_configs = [{"device_id": "device1", "host": "192.168.1.100", "port": 80}]
    result = await integration.initialize(device_configs)
    
    assert result is False
    
    mock_websocket_manager.send_to_all.return_value = {"device1": False}
    
    ctx = PipelineContext()
    ctx.emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)
    ctx.emotion_category = "joy"
    
    result = await integration.process_pipeline_result(ctx)
    
    assert result == {"device1": False}
