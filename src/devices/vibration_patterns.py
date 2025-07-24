"""
触覚フィードバックデバイスの振動パターン。

このモジュールは、異なる感情カテゴリに対応する振動パターンを定義し、
感情データに基づいて適切なパターンを生成するジェネレータを提供します。
"""
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import json

from ..models.data_models import Emotion


@dataclass
class VibrationStep:
    """振動パターンの単一ステップ。"""
    intensity: float  # 0.0-1.0 振動強度
    duration: int     # ミリ秒単位の持続時間


@dataclass
class VibrationPattern:
    """
    強度と持続時間のシーケンスを持つ振動パターンを表します。
    
    属性:
        steps: 振動ステップのリスト（強度と持続時間のペア）
        interval: 振動間の時間（ミリ秒）
        repetitions: パターンを繰り返す回数
    """
    steps: List[VibrationStep]
    interval: int  # 振動間の間隔（ミリ秒）
    repetitions: int  # パターンを繰り返す回数
    
    def to_dict(self) -> Dict[str, Any]:
        """パターンをシリアライズ用の辞書に変換します。"""
        return {
            "steps": [{"intensity": step.intensity, "duration": step.duration} 
                     for step in self.steps],
            "interval": self.interval,
            "repetitions": self.repetitions
        }
    
    def to_json(self) -> str:
        """パターンをJSON文字列に変換します。"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VibrationPattern':
        """辞書からVibrationPatternを作成します。"""
        steps = [VibrationStep(step["intensity"], step["duration"]) 
                for step in data["steps"]]
        return cls(
            steps=steps,
            interval=data["interval"],
            repetitions=data["repetitions"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VibrationPattern':
        """JSON文字列からVibrationPatternを作成します。"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class EmotionVibrationPatterns:
    """
    異なる感情カテゴリに対応する振動パターンを定義します。
    
    各感情カテゴリ（喜、怒、哀、楽）には、感情の強度に基づいて
    調整されるベースパターンがあります。
    """
    
    @staticmethod
    def joy_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        喜びの振動パターンを生成します。
        
        喜びは、明るくポジティブなリズミカルで軽い振動で表現されます。
        
        引数:
            intensity_level: 感情の強度（0-5）
            
        戻り値:
            喜びの感情に対応するVibrationPattern
        """
        base_intensity = 0.6
        base_duration = 200  # ms
        base_interval = 100  # ms
        base_repetitions = 3
        
        if intensity_level >= 4:  # High intensity
            intensity = base_intensity + 0.2
            repetitions = 5
        elif intensity_level <= 1:  # Low intensity
            intensity = base_intensity - 0.2
            repetitions = 2
        else:  # Medium intensity
            intensity = base_intensity
            repetitions = base_repetitions
            
        steps = [
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1, base_duration),
            VibrationStep(intensity, base_duration)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=repetitions
        )
    
    @staticmethod
    def anger_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        怒りの振動パターンを生成します。
        
        怒りは、緊張感と強度を伝える強く短い急速な振動で表現されます。
        
        引数:
            intensity_level: 感情の強度（0-5）
            
        戻り値:
            怒りの感情に対応するVibrationPattern
        """
        base_intensity = 0.9
        base_duration = 100  # ms
        base_interval = 50   # ms
        base_repetitions = 4
        
        if intensity_level >= 4:  # High intensity
            intensity = 1.0
            interval = 30  # ms
        elif intensity_level <= 1:  # Low intensity
            intensity = 0.7
            interval = 80  # ms
        else:  # Medium intensity
            intensity = base_intensity
            interval = base_interval
            
        steps = [
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1 if intensity < 1.0 else 1.0, base_duration - 20),
            VibrationStep(intensity, base_duration),
            VibrationStep(intensity + 0.1 if intensity < 1.0 else 1.0, base_duration - 20)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=interval,
            repetitions=base_repetitions
        )
    
    @staticmethod
    def sorrow_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        悲しみの振動パターンを生成します。
        
        悲しみは、静けさと内省を伝える弱くゆっくりとした長い振動で表現されます。
        
        引数:
            intensity_level: 感情の強度（0-5）
            
        戻り値:
            悲しみの感情に対応するVibrationPattern
        """
        base_intensity = 0.4
        base_duration = 500  # ms
        base_interval = 300  # ms
        base_repetitions = 2
        
        if intensity_level >= 4:  # High intensity
            duration = 700  # ms
            interval = 200  # ms
        elif intensity_level <= 1:  # Low intensity
            intensity = 0.2
            duration = 300  # ms
        else:  # Medium intensity
            intensity = base_intensity
            duration = base_duration
            interval = base_interval
            
        steps = [
            VibrationStep(base_intensity, duration),
            VibrationStep(base_intensity - 0.1, duration + 100)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=base_repetitions
        )
    
    @staticmethod
    def pleasure_pattern(intensity_level: int = 3) -> VibrationPattern:
        """
        楽しさの振動パターンを生成します。
        
        楽しさは、リラックスと楽しさを伝える中程度の強さのメロディックな振動パターンで表現されます。
        
        引数:
            intensity_level: 感情の強度（0-5）
            
        戻り値:
            楽しさの感情に対応するVibrationPattern
        """
        base_intensity = 0.5
        base_repetitions = 3
        base_interval = 150  # ms
        
        if intensity_level >= 4:  # High intensity
            max_intensity = 0.7
        elif intensity_level <= 1:  # Low intensity
            max_intensity = 0.5
        else:  # Medium intensity
            max_intensity = 0.6
            
        steps = [
            VibrationStep(base_intensity - 0.1, 250),
            VibrationStep(base_intensity, 300),
            VibrationStep(max_intensity, 350),
            VibrationStep(base_intensity, 300),
            VibrationStep(base_intensity - 0.1, 250)
        ]
        
        return VibrationPattern(
            steps=steps,
            interval=base_interval,
            repetitions=base_repetitions
        )


class VibrationPatternGenerator:
    """
    感情データに基づいて適切な振動パターンを生成します。
    
    このクラスは感情データを分析し、感情状態を最もよく表現する振動パターンを
    作成します。複数の感情が混在する場合の処理も含みます。
    """
    
    @staticmethod
    def get_dominant_emotions(emotion: Emotion, threshold: int = 2) -> List[Tuple[str, int]]:
        """
        感情データから主要な感情を特定します。
        
        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            threshold: 感情を有意とみなす最小値
            
        戻り値:
            (感情名, 強度)のタプルのリスト、強度順にソート
        """
        emotion_values = [
            ("joy", emotion.joy),
            ("fun", emotion.fun),
            ("anger", emotion.anger),
            ("sad", emotion.sad)
        ]
        
        dominant = [(name, value) for name, value in emotion_values if value >= threshold]
        return sorted(dominant, key=lambda x: x[1], reverse=True)
    
    @staticmethod
    def map_emotion_to_category(emotion_name: str) -> str:
        """
        感情パラメータ名を感情カテゴリにマッピングします。
        
        引数:
            emotion_name: 感情パラメータの名前
            
        戻り値:
            感情カテゴリ名
        """
        mapping = {
            "joy": "joy",      # 喜
            "fun": "pleasure", # 楽
            "anger": "anger",  # 怒
            "sad": "sorrow"    # 哀
        }
        return mapping.get(emotion_name, "joy")  # Default to joy if unknown
    
    @staticmethod
    def generate_pattern(emotion: Emotion, emotion_category: Optional[str] = None) -> VibrationPattern:
        """
        感情データとカテゴリに基づいて振動パターンを生成します。
        
        引数:
            emotion: joy、fun、anger、sadの値を持つEmotionオブジェクト
            emotion_category: オプションのカテゴリ指定（joy、anger、sorrow、pleasure）
            
        戻り値:
            感情状態を表現するVibrationPattern
        """
        if emotion_category:
            category = emotion_category.lower()
            
            category_mapping = {
                "喜": "joy",
                "怒": "anger",
                "哀": "sorrow",
                "楽": "pleasure"
            }
            
            if category in category_mapping:
                category = category_mapping[category]
                
            if category == "joy":
                intensity_level = emotion.joy
            elif category == "anger":
                intensity_level = emotion.anger
            elif category == "sorrow":
                intensity_level = emotion.sad
            elif category == "pleasure":
                intensity_level = emotion.fun
            else:
                intensity_level = (emotion.joy + emotion.fun + emotion.anger + emotion.sad) // 4
                
            if category == "joy":
                return EmotionVibrationPatterns.joy_pattern(intensity_level)
            elif category == "anger":
                return EmotionVibrationPatterns.anger_pattern(intensity_level)
            elif category == "sorrow":
                return EmotionVibrationPatterns.sorrow_pattern(intensity_level)
            elif category == "pleasure":
                return EmotionVibrationPatterns.pleasure_pattern(intensity_level)
            else:
                return EmotionVibrationPatterns.joy_pattern(intensity_level)
        
        dominant_emotions = VibrationPatternGenerator.get_dominant_emotions(emotion)
        
        if not dominant_emotions:
            return VibrationPattern(
                steps=[VibrationStep(0.3, 300)],
                interval=200,
                repetitions=1
            )
            
        primary_emotion, primary_intensity = dominant_emotions[0]
        primary_category = VibrationPatternGenerator.map_emotion_to_category(primary_emotion)
        
        if primary_category == "joy":
            return EmotionVibrationPatterns.joy_pattern(primary_intensity)
        elif primary_category == "anger":
            return EmotionVibrationPatterns.anger_pattern(primary_intensity)
        elif primary_category == "sorrow":
            return EmotionVibrationPatterns.sorrow_pattern(primary_intensity)
        elif primary_category == "pleasure":
            return EmotionVibrationPatterns.pleasure_pattern(primary_intensity)
        else:
            return EmotionVibrationPatterns.joy_pattern(primary_intensity)
