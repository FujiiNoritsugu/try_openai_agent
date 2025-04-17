"""
APIエンドポイントのテスト
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.api.app import app
from src.models.data_models import Emotion, UserInput


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


@pytest.fixture
def mock_haptic_feedback():
    """HapticFeedbackIntegrationのモック"""
    mock = AsyncMock()
    mock.is_initialized = False
    mock.initialize = AsyncMock(return_value=True)
    mock.shutdown = AsyncMock(return_value=True)
    mock.get_all_device_status = AsyncMock(return_value={"device1": {"device_state": "idle"}})
    mock.stop_all_devices = AsyncMock(return_value={"device1": True})
    mock.run_pipeline_and_send = AsyncMock(return_value=(
        {
            "extracted_emotion": {"joy": 0.8, "fun": 0.6, "anger": 0.1, "sad": 0.2},
            "original_message": "テストメッセージ",
            "emotion_category": "joy",
            "final_message": "最終メッセージ",
            "is_learned_response": False
        },
        {"device1": True}
    ))
    mock.websocket_manager = AsyncMock()
    mock.websocket_manager.send_to_all = AsyncMock(return_value={"device1": True})
    mock.websocket_manager.send = AsyncMock(return_value=True)
    mock.websocket_manager.stop = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_run_pipeline():
    """run_pipelineのモック"""
    class MockContext:
        def __init__(self):
            self.emotion = Emotion(joy=0.8, fun=0.6, anger=0.1, sad=0.2)
            self.original_message = "テストメッセージ"
            self.emotion_category = "joy"
            self.modified_message = "最終メッセージ"
            self.is_learned_response = False
    
    async def mock_run(*args, **kwargs):
        return MockContext(), None
    
    return mock_run


def test_root(client):
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "感情分析APIへようこそ"}


@pytest.mark.asyncio
async def test_analyze_emotion(client, mock_run_pipeline):
    """感情分析エンドポイントのテスト"""
    with patch("src.api.app.run_pipeline", mock_run_pipeline):
        response = client.post(
            "/api/v1/analyze",
            json={
                "user_input": {
                    "data": "0.7",
                    "touched_area": "胸",
                    "gender": "男性"
                },
                "send_to_devices": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["emotion_category"] == "joy"
        assert data["final_message"] == "最終メッセージ"
        assert data["is_learned_response"] is False


@pytest.mark.asyncio
async def test_analyze_emotion_with_devices(client, mock_haptic_feedback):
    """デバイス送信付き感情分析エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = True
        
        response = client.post(
            "/api/v1/analyze",
            json={
                "user_input": {
                    "data": "0.7",
                    "touched_area": "胸",
                    "gender": "男性"
                },
                "send_to_devices": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "device_results" in data
        assert data["device_results"] == {"device1": True}


def test_get_devices(client):
    """デバイスリスト取得エンドポイントのテスト"""
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    assert "devices" in response.json()


def test_register_device(client):
    """デバイス登録エンドポイントのテスト"""
    response = client.post(
        "/api/v1/devices",
        json={
            "device_id": "test_device",
            "host": "192.168.1.100",
            "port": 80,
            "ws_path": "/ws"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "test_device"
    assert data["host"] == "192.168.1.100"


def test_register_duplicate_device(client):
    """重複デバイス登録エンドポイントのテスト"""
    client.post(
        "/api/v1/devices",
        json={
            "device_id": "duplicate_device",
            "host": "192.168.1.100",
            "port": 80,
            "ws_path": "/ws"
        }
    )
    
    response = client.post(
        "/api/v1/devices",
        json={
            "device_id": "duplicate_device",
            "host": "192.168.1.101",
            "port": 80,
            "ws_path": "/ws"
        }
    )
    
    assert response.status_code == 400
    assert "error" in response.json()


def test_unregister_device(client):
    """デバイス登録解除エンドポイントのテスト"""
    client.post(
        "/api/v1/devices",
        json={
            "device_id": "device_to_remove",
            "host": "192.168.1.100",
            "port": 80,
            "ws_path": "/ws"
        }
    )
    
    response = client.delete("/api/v1/devices/device_to_remove")
    
    assert response.status_code == 200
    assert "message" in response.json()


def test_unregister_nonexistent_device(client):
    """存在しないデバイス登録解除エンドポイントのテスト"""
    response = client.delete("/api/v1/devices/nonexistent_device")
    
    assert response.status_code == 404
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_initialize_devices(client, mock_haptic_feedback):
    """デバイス初期化エンドポイントのテスト"""
    client.post(
        "/api/v1/devices",
        json={
            "device_id": "device_to_initialize",
            "host": "192.168.1.100",
            "port": 80,
            "ws_path": "/ws"
        }
    )
    
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        response = client.post("/api/v1/devices/initialize")
        
        assert response.status_code == 200
        assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_initialize_devices_no_devices(client):
    """デバイスなし初期化エンドポイントのテスト"""
    app.state.registered_devices = []
    
    response = client.post("/api/v1/devices/initialize")
    
    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_shutdown_devices(client, mock_haptic_feedback):
    """デバイスシャットダウンエンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = True
        
        response = client.post("/api/v1/devices/shutdown")
        
        assert response.status_code == 200
        assert response.json() == {"success": True}


@pytest.mark.asyncio
async def test_get_device_status(client, mock_haptic_feedback):
    """デバイス状態取得エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = True
        
        response = client.get("/api/v1/devices/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data


@pytest.mark.asyncio
async def test_get_device_status_not_initialized(client, mock_haptic_feedback):
    """未初期化デバイス状態取得エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = False
        
        response = client.get("/api/v1/devices/status")
        
        assert response.status_code == 400
        assert "error" in response.json()


@pytest.mark.asyncio
async def test_send_vibration(client, mock_haptic_feedback):
    """振動パターン送信エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = True
        
        response = client.post(
            "/api/v1/vibration",
            json={
                "emotion": {
                    "joy": 0.8,
                    "fun": 0.6,
                    "anger": 0.1,
                    "sad": 0.2
                },
                "emotion_category": "joy",
                "device_ids": ["device1"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


@pytest.mark.asyncio
async def test_send_vibration_not_initialized(client, mock_haptic_feedback):
    """未初期化振動パターン送信エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = False
        
        response = client.post(
            "/api/v1/vibration",
            json={
                "emotion": {
                    "joy": 0.8,
                    "fun": 0.6,
                    "anger": 0.1,
                    "sad": 0.2
                },
                "emotion_category": "joy"
            }
        )
        
        assert response.status_code == 400
        assert "error" in response.json()


@pytest.mark.asyncio
async def test_stop_vibration(client, mock_haptic_feedback):
    """振動停止エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = True
        
        response = client.post(
            "/api/v1/vibration/stop",
            json={"device_ids": ["device1"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


@pytest.mark.asyncio
async def test_stop_vibration_not_initialized(client, mock_haptic_feedback):
    """未初期化振動停止エンドポイントのテスト"""
    with patch("src.api.app.haptic_feedback", mock_haptic_feedback):
        mock_haptic_feedback.is_initialized = False
        
        response = client.post("/api/v1/vibration/stop")
        
        assert response.status_code == 400
        assert "error" in response.json()
