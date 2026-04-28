"""
Minder AI Engine Integration Layer
===================================
AI红娘 - 智能婚恋匹配平台

Core AI Engines:
- VoiceEngine: 语音情感分析与人格特征提取
- FaceEngine: 面部表情识别与活体检测
- HealthEngine: 健康评估与基因风险分析
- DigitalAdvisor: 数字红娘与恋爱顾问
- SafetyEngine: 安全防护与诈骗检测
"""

from .voice_analyzer import VoiceEngine
from .face_analyzer import FaceEngine
from .health_engine import HealthEngine
from .digital_advisor import DigitalAdvisor
from .safety_engine import SafetyEngine

__all__ = [
    "VoiceEngine",
    "FaceEngine",
    "HealthEngine",
    "DigitalAdvisor",
    "SafetyEngine",
]

__version__ = "1.0.0"
__author__ = "Minder Team"
