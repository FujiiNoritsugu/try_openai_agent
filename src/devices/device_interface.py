"""
Device interface for haptic feedback device.

This module provides an interface for communicating with the haptic feedback device
and sending vibration patterns based on emotion analysis results.
"""
from typing import Dict, Any, Optional
import json
import asyncio
import logging

from ..models.data_models import Emotion, PipelineContext
from .vibration_patterns import VibrationPattern, VibrationPatternGenerator


class HapticDeviceInterface:
    """
    Interface for communicating with haptic feedback devices.
    
    This class provides methods to send vibration patterns to connected
    haptic devices based on emotion analysis results.
    """
    
    def __init__(self, device_id: str = "default", host: str = "localhost", port: int = 8765):
        """
        Initialize the haptic device interface.
        
        Args:
            device_id: Identifier for the device
            host: Host address for the device communication
            port: Port for the device communication
        """
        self.device_id = device_id
        self.host = host
        self.port = port
        self.connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> bool:
        """
        Establish connection with the haptic device.
        
        In a real implementation, this would establish a connection
        with the physical device. For now, it's a placeholder.
        
        Returns:
            True if connection successful, False otherwise
        """
        self.logger.info(f"Connecting to haptic device {self.device_id} at {self.host}:{self.port}")
        
        await asyncio.sleep(0.5)
        
        self.connected = True
        self.logger.info(f"Connected to haptic device {self.device_id}")
        return True
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the haptic device.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.connected:
            return True
            
        self.logger.info(f"Disconnecting from haptic device {self.device_id}")
        
        await asyncio.sleep(0.2)
        
        self.connected = False
        self.logger.info(f"Disconnected from haptic device {self.device_id}")
        return True
    
    async def send_pattern(self, pattern: VibrationPattern) -> bool:
        """
        Send a vibration pattern to the device.
        
        Args:
            pattern: The vibration pattern to send
            
        Returns:
            True if pattern was sent successfully, False otherwise
        """
        if not self.connected:
            self.logger.warning("Cannot send pattern: device not connected")
            return False
            
        pattern_json = pattern.to_json()
        
        self.logger.info(f"Sending pattern to device {self.device_id}: {pattern_json}")
        
        await asyncio.sleep(0.3)
        
        self.logger.info(f"Pattern sent successfully to device {self.device_id}")
        return True
    
    async def send_emotion(self, emotion: Emotion, emotion_category: Optional[str] = None) -> bool:
        """
        Generate and send a vibration pattern based on emotion data.
        
        Args:
            emotion: Emotion object with joy, fun, anger, and sad values
            emotion_category: Optional emotion category override
            
        Returns:
            True if pattern was generated and sent successfully, False otherwise
        """
        pattern = VibrationPatternGenerator.generate_pattern(emotion, emotion_category)
        
        return await self.send_pattern(pattern)
    
    async def process_pipeline_context(self, ctx: PipelineContext) -> bool:
        """
        Process pipeline context and send appropriate vibration pattern.
        
        This method extracts emotion data and category from the pipeline context
        and sends the appropriate vibration pattern to the device.
        
        Args:
            ctx: Pipeline context with emotion data and category
            
        Returns:
            True if pattern was sent successfully, False otherwise
        """
        if not ctx.emotion:
            self.logger.warning("Cannot process context: no emotion data")
            return False
            
        return await self.send_emotion(ctx.emotion, ctx.emotion_category)


class HapticFeedbackManager:
    """
    Manager for haptic feedback devices.
    
    This class provides a high-level interface for managing haptic devices
    and sending emotion-based feedback.
    """
    
    def __init__(self):
        """Initialize the haptic feedback manager."""
        self.devices = {}
        self.logger = logging.getLogger(__name__)
    
    def register_device(self, device_id: str, host: str = "localhost", port: int = 8765) -> HapticDeviceInterface:
        """
        Register a new haptic device.
        
        Args:
            device_id: Identifier for the device
            host: Host address for the device
            port: Port for the device
            
        Returns:
            The registered device interface
        """
        device = HapticDeviceInterface(device_id, host, port)
        self.devices[device_id] = device
        self.logger.info(f"Registered haptic device: {device_id}")
        return device
    
    def get_device(self, device_id: str) -> Optional[HapticDeviceInterface]:
        """
        Get a registered device by ID.
        
        Args:
            device_id: Identifier for the device
            
        Returns:
            The device interface if found, None otherwise
        """
        return self.devices.get(device_id)
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all registered devices.
        
        Returns:
            Dictionary mapping device IDs to connection success status
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.connect()
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """
        Disconnect from all registered devices.
        
        Returns:
            Dictionary mapping device IDs to disconnection success status
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.disconnect()
        return results
    
    async def send_to_all(self, emotion: Emotion, emotion_category: Optional[str] = None) -> Dict[str, bool]:
        """
        Send emotion data to all connected devices.
        
        Args:
            emotion: Emotion object with joy, fun, anger, and sad values
            emotion_category: Optional emotion category override
            
        Returns:
            Dictionary mapping device IDs to send success status
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.send_emotion(emotion, emotion_category)
        return results
    
    async def process_pipeline_context(self, ctx: PipelineContext) -> Dict[str, bool]:
        """
        Process pipeline context and send to all connected devices.
        
        Args:
            ctx: Pipeline context with emotion data and category
            
        Returns:
            Dictionary mapping device IDs to send success status
        """
        results = {}
        for device_id, device in self.devices.items():
            results[device_id] = await device.process_pipeline_context(ctx)
        return results


haptic_manager = HapticFeedbackManager()
