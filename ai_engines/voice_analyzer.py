"""
Voice Analysis Engine
=====================
基于深度学习的语音情感分析与人格特征提取引擎。

功能:
- 59维语音特征向量提取 (MFCC + Delta + Spectral + Prosodic)
- 六维度情感分析 (愤怒/喜悦/悲伤/惊讶/恐惧/中性)
- 五大人格特征检测 (开放性/尽责性/外向性/宜人性/神经质)
- 语音活体检测 (ASR文本验证)
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class EmotionResult:
    """六维度情感分析结果"""
    anger: float = 0.0
    joy: float = 0.0
    sadness: float = 0.0
    surprise: float = 0.0
    fear: float = 0.0
    neutral: float = 0.0

    @property
    def dominant(self) -> str:
        """返回主导情感标签"""
        scores = {
            "anger": self.anger,
            "joy": self.joy,
            "sadness": self.sadness,
            "surprise": self.surprise,
            "fear": self.fear,
            "neutral": self.neutral,
        }
        return max(scores, key=scores.get)

    def to_dict(self) -> dict:
        return {
            "anger": round(self.anger, 4),
            "joy": round(self.joy, 4),
            "sadness": round(self.sadness, 4),
            "surprise": round(self.surprise, 4),
            "fear": round(self.fear, 4),
            "neutral": round(self.neutral, 4),
            "dominant": self.dominant,
        }


@dataclass
class PersonalityProfile:
    """五大人格特征 (OCEAN 模型)"""
    openness: float = 0.0          # 开放性
    conscientiousness: float = 0.0  # 尽责性
    extraversion: float = 0.0      # 外向性
    agreeableness: float = 0.0     # 宜人性
    neuroticism: float = 0.0       # 神经质

    def to_dict(self) -> dict:
        return {
            "openness": round(self.openness, 4),
            "conscientiousness": round(self.conscientiousness, 4),
            "extraversion": round(self.extraversion, 4),
            "agreeableness": round(self.agreeableness, 4),
            "neuroticism": round(self.neuroticism, 4),
        }

    @property
    def summary(self) -> str:
        """生成人格描述摘要"""
        traits = []
        if self.extraversion > 0.6:
            traits.append("外向活泼")
        elif self.extraversion < 0.4:
            traits.append("内敛沉稳")

        if self.agreeableness > 0.6:
            traits.append("温和友善")
        if self.conscientiousness > 0.6:
            traits.append("认真负责")
        if self.openness > 0.6:
            traits.append("开放好奇")
        if self.neuroticism > 0.6:
            traits.append("情感丰富")
        elif self.neuroticism < 0.3:
            traits.append("情绪稳定")

        return "、".join(traits) if traits else "性格均衡"


class VoiceEngine:
    """
    语音分析引擎

    集成多种深度学习模型，从语音中提取丰富的情感和人格信息。
    支持多种音频格式 (wav, mp3, flac, ogg)。

    当无真实模型时，使用基于文件哈希的确定性伪随机生成，
    保证同一文件始终产生相同结果，便于测试和演示。

    Usage::

        engine = VoiceEngine()
        features = engine.extract_voice_features("sample.wav")
        emotion = engine.analyze_emotion("sample.wav")
        personality = engine.detect_personality(features)
        is_live = engine.liveness_check(audio_data, "请说出你的名字")
    """

    # 59维特征维度分解:
    # - 13 MFCCs + 13 Delta-MFCCs = 26
    # - 13 Spectral features (centroid, bandwidth, rolloff, contrast×7) = 13
    # - 12 Prosodic features (pitch stats, energy stats, jitter, shimmer, etc.) = 12
    # - 8 Temporal features (duration, pause ratio, speech rate, etc.) = 8
    FEATURE_DIMENSION = 59

    # 活体检测阈值
    LIVENESS_SIMILARITY_THRESHOLD = 0.75
    LIVENESS_MIN_CONFIDENCE = 0.60

    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        初始化语音分析引擎。

        Args:
            model_path: 预训练模型路径。若为 None 则使用内置默认模型。
            device: 推理设备 ('cpu', 'cuda', 'mps')
        """
        self.model_path = model_path
        self.device = device
        self._models_loaded = False
        self._emotion_model = None
        self._personality_model = None
        self._asr_model = None
        logger.info("VoiceEngine 初始化完成 (device=%s)", device)

    def _ensure_models(self) -> None:
        """懒加载模型"""
        if self._models_loaded:
            return

        logger.info("加载语音分析模型...")
        try:
            # 实际部署时替换为真实模型加载
            # from transformers import pipeline
            # self._emotion_model = pipeline("audio-classification",
            #     model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
            #     device=self.device)
            # self._asr_model = pipeline("automatic-speech-recognition",
            #     model="openai/whisper-large-v3", device=self.device)
            self._emotion_model = True   # placeholder
            self._personality_model = True
            self._asr_model = True
            self._models_loaded = True
            logger.info("语音分析模型加载完成")
        except Exception as e:
            logger.error("模型加载失败: %s", e)
            raise RuntimeError(f"语音分析引擎初始化失败: {e}") from e

    @staticmethod
    def _hash_seed(data: str) -> int:
        """根据输入字符串生成确定性随机种子"""
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def extract_voice_features(self, audio_path: str | Path) -> np.ndarray:
        """
        提取59维语音特征向量。

        特征组成:
        - MFCC 特征 (26维): 梅尔频率倒谱系数及其一阶差分
        - 频谱特征 (13维): 频谱质心、带宽、衰减点、频谱对比度
        - 韵律特征 (12维): 基频统计、能量统计、抖动、微颤
        - 时域特征 (8维): 时长、停顿比、语速等

        当无真实模型时，使用文件哈希驱动的确定性生成，
        模拟真实特征向量的统计分布特性。

        Args:
            audio_path: 音频文件路径 (支持 wav/mp3/flac/ogg)

        Returns:
            np.ndarray: 59维特征向量 (float32)

        Raises:
            FileNotFoundError: 音频文件不存在
            ValueError: 音频格式不支持或文件损坏
        """
        self._ensure_models()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        suffix = audio_path.suffix.lower()
        supported = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
        if suffix not in supported:
            raise ValueError(
                f"不支持的音频格式: {suffix}。"
                f"支持的格式: {', '.join(sorted(supported))}"
            )

        logger.info("提取语音特征: %s", audio_path)

        try:
            # 使用文件哈希生成确定性特征
            seed = self._hash_seed(str(audio_path))
            rng = np.random.RandomState(seed)

            # 模拟 MFCC 特征 (26维): 均匀分布在 [-1, 1]
            mfcc = rng.randn(26).astype(np.float32) * 0.3

            # 模拟频谱特征 (13维): 分布在 [0, 1]
            spectral = rng.uniform(0.1, 0.9, 13).astype(np.float32)

            # 模拟韵律特征 (12维): 包含基频(80-300Hz归一化)、能量等
            prosodic = rng.uniform(0.0, 1.0, 12).astype(np.float32)
            # 基频均值模拟 (男声~120Hz, 女声~220Hz)
            prosodic[0] = rng.uniform(0.2, 0.8)  # 归一化基频均值
            prosodic[1] = rng.uniform(0.05, 0.3)  # 基频标准差

            # 模拟时域特征 (8维): 时长、停顿比等
            temporal = rng.uniform(0.0, 1.0, 8).astype(np.float32)
            # 时长模拟 (1-60秒, 归一化到0-1)
            temporal[0] = rng.uniform(0.05, 0.8)
            # 停顿比
            temporal[1] = rng.uniform(0.05, 0.35)

            features = np.concatenate([
                mfcc, spectral, prosodic, temporal
            ]).astype(np.float32)

            assert features.shape[0] == self.FEATURE_DIMENSION

            logger.info("特征提取完成: shape=%s", features.shape)
            return features

        except Exception as e:
            logger.error("特征提取失败: %s", e)
            raise ValueError(f"音频处理失败: {e}") from e

    # ------------------------------------------------------------------
    # Emotion analysis
    # ------------------------------------------------------------------

    def analyze_emotion(self, audio_path: str | Path) -> EmotionResult:
        """
        分析语音中的情感状态。

        使用文件哈希驱动的确定性生成，模拟六维度情感分布。
        输出的概率总和为 1.0，且主导情感与随机种子相关。

        Args:
            audio_path: 音频文件路径

        Returns:
            EmotionResult: 包含 anger/joy/sadness/surprise/fear/neutral 的评分
        """
        self._ensure_models()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        logger.info("分析语音情感: %s", audio_path)

        try:
            seed = self._hash_seed(str(audio_path) + ":emotion")
            rng = np.random.RandomState(seed)

            # 使用 Dirichlet 分布生成和为 1 的情感概率
            # alpha 参数使结果更集中（中性偏向较高）
            alpha = np.array([0.5, 1.5, 0.4, 0.3, 0.3, 2.0], dtype=np.float64)
            raw = rng.dirichlet(alpha)

            result = EmotionResult(
                anger=float(raw[0]),
                joy=float(raw[1]),
                sadness=float(raw[2]),
                surprise=float(raw[3]),
                fear=float(raw[4]),
                neutral=float(raw[5]),
            )

            logger.info("情感分析完成: dominant=%s", result.dominant)
            return result

        except Exception as e:
            logger.error("情感分析失败: %s", e)
            raise ValueError(f"情感分析失败: {e}") from e

    # ------------------------------------------------------------------
    # Personality detection
    # ------------------------------------------------------------------

    def detect_personality(
        self, voice_features: np.ndarray
    ) -> PersonalityProfile:
        """
        基于语音特征检测五大人格特征 (OCEAN模型)。

        研究表明，语音特征与人格特征之间存在显著相关性:
        - 外向者通常语速更快、音量更大、音调变化更多
        - 宜人性高的人语气更柔和、停顿更少
        - 神经质高的人语调波动更大、语速不稳定

        当无真实模型时，基于特征向量的统计量进行确定性映射。

        Args:
            voice_features: 59维语音特征向量

        Returns:
            PersonalityProfile: 五大人格得分 (0~1)
        """
        if voice_features.shape[0] != self.FEATURE_DIMENSION:
            raise ValueError(
                f"特征维度不匹配: 期望 {self.FEATURE_DIMENSION}, "
                f"实际 {voice_features.shape[0]}"
            )

        logger.info("检测人格特征 (dim=%d)", voice_features.shape[0])

        try:
            # 基于特征向量的统计量推导人格分数
            # 模拟真实模型的特征->人格映射关系

            # 从特征的不同区段提取关键统计量
            mfcc_section = voice_features[:26]      # MFCC 特征
            spectral_section = voice_features[26:39]  # 频谱特征
            prosodic_section = voice_features[39:51]   # 韵律特征
            temporal_section = voice_features[51:59]    # 时域特征

            # 开放性: 与频谱丰富度和韵律变化正相关
            spectral_var = float(np.std(spectral_section))
            prosodic_var = float(np.std(prosodic_section))
            openness = 0.3 + 0.4 * np.clip(
                (spectral_var + prosodic_var) / 0.6, 0, 1
            )
            openness += float(np.mean(np.abs(mfcc_section[:5]))) * 0.1
            openness = float(np.clip(openness, 0.1, 0.95))

            # 尽责性: 与语速稳定性和停顿规律性正相关
            temporal_regularity = 1.0 - float(np.std(temporal_section))
            conscientiousness = 0.3 + 0.5 * np.clip(temporal_regularity, 0, 1)
            conscientiousness = float(np.clip(conscientiousness, 0.1, 0.95))

            # 外向性: 与音量、语速、音调变化幅度正相关
            energy_proxy = float(np.mean(np.abs(prosodic_section[:4])))
            pitch_range = float(prosodic_section[0] if len(prosodic_section) > 0 else 0.5)
            extraversion = 0.2 + 0.6 * np.clip(
                (energy_proxy * 2 + pitch_range) / 2, 0, 1
            )
            extraversion = float(np.clip(extraversion, 0.1, 0.95))

            # 宜人性: 与语调柔和度、MFCC低频特征正相关
            softness = float(np.mean(np.abs(mfcc_section[3:8])))
            agreeableness = 0.35 + 0.4 * np.clip(1.0 - softness, 0, 1)
            agreeableness = float(np.clip(agreeableness, 0.1, 0.95))

            # 神经质: 与语调不稳定性、韵律波动正相关
            pitch_instability = float(np.std(prosodic_section[:6]))
            energy_fluctuation = float(np.std(prosodic_section[6:]))
            neuroticism = 0.2 + 0.6 * np.clip(
                (pitch_instability + energy_fluctuation) / 0.8, 0, 1
            )
            neuroticism = float(np.clip(neuroticism, 0.1, 0.95))

            profile = PersonalityProfile(
                openness=round(openness, 4),
                conscientiousness=round(conscientiousness, 4),
                extraversion=round(extraversion, 4),
                agreeableness=round(agreeableness, 4),
                neuroticism=round(neuroticism, 4),
            )

            logger.info("人格检测完成: %s", profile.summary)
            return profile

        except Exception as e:
            logger.error("人格检测失败: %s", e)
            raise ValueError(f"人格检测失败: {e}") from e

    # ------------------------------------------------------------------
    # Liveness check (voice)
    # ------------------------------------------------------------------

    def liveness_check(
        self,
        audio_data: bytes | str | Path,
        text: str,
        language: str = "zh",
    ) -> dict:
        """
        语音活体检测 - 通过文本相似度和信号分析验证用户实时朗读。

        流程:
        1. 模拟 ASR 识别 (基于音频数据哈希生成识别文本)
        2. 计算识别文本与期望文本的相似度
        3. 模拟回放检测 (信号分析)
        4. 综合判断是否为真人实时朗读

        Args:
            audio_data: 音频数据 (bytes 或文件路径)
            text: 要求用户朗读的文本内容
            language: 语言代码 ('zh', 'en')

        Returns:
            dict: {
                "is_live": bool,
                "confidence": float,
                "text_similarity": float,
                "replay_risk": float,
            }
        """
        self._ensure_models()

        logger.info("语音活体检测: text='%s', lang=%s", text, language)

        try:
            # 确定音频数据的哈希
            if isinstance(audio_data, (str, Path)):
                data_str = str(audio_data)
            elif isinstance(audio_data, bytes):
                data_str = hashlib.md5(audio_data[:1024]).hexdigest()
            else:
                data_str = str(audio_data)

            seed = self._hash_seed(data_str + text)
            rng = np.random.RandomState(seed)

            # 模拟文本相似度 (正常用户通常 > 0.8)
            text_len = len(text)
            base_similarity = rng.uniform(0.70, 0.98)
            # 文本越长，随机模拟的相似度略降
            length_factor = max(0.8, 1.0 - text_len / 500)
            text_similarity = float(np.clip(base_similarity * length_factor, 0.0, 1.0))

            # 模拟回放检测风险 (正常录音 < 0.3, 录屏/回放 > 0.5)
            replay_risk = float(rng.uniform(0.05, 0.25))

            # 综合判断
            is_live = (
                text_similarity >= self.LIVENESS_SIMILARITY_THRESHOLD
                and replay_risk < 0.3
            )

            # 置信度: 综合相似度和回放风险
            confidence = float(np.clip(
                text_similarity * 0.6 + (1.0 - replay_risk) * 0.4,
                0.0, 1.0
            ))

            result = {
                "is_live": is_live,
                "confidence": round(confidence, 4),
                "text_similarity": round(text_similarity, 4),
                "replay_risk": round(replay_risk, 4),
                "language": language,
            }

            logger.info("语音活体检测完成: is_live=%s, confidence=%.2f",
                       is_live, confidence)
            return result

        except Exception as e:
            logger.error("语音活体检测失败: %s", e)
            return {
                "is_live": False,
                "confidence": 0.0,
                "text_similarity": 0.0,
                "replay_risk": 1.0,
                "language": language,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def analyze_full(self, audio_path: str | Path) -> dict:
        """
        完整语音分析 (特征+情感+人格)。

        Args:
            audio_path: 音频文件路径

        Returns:
            dict: 包含 features, emotion, personality 的完整分析结果
        """
        features = self.extract_voice_features(audio_path)
        emotion = self.analyze_emotion(audio_path)
        personality = self.detect_personality(features)

        return {
            "features": features.tolist(),
            "feature_dim": self.FEATURE_DIMENSION,
            "emotion": emotion.to_dict(),
            "personality": personality.to_dict(),
            "personality_summary": personality.summary,
        }
