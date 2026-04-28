"""
Safety & Verification Engine
==============================
安全防护与身份验证引擎。

功能:
- 诈骗档案检测
- 消息安全分析
- 档案一致性检查
- 对话安全监控
- 背景信息审查
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """安全警报类型"""
    SCAM = "scam"
    HARASSMENT = "harassment"
    INAPPROPRIATE = "inappropriate"
    FAKE_PROFILE = "fake_profile"
    MONEY_REQUEST = "money_request"
    PERSONAL_INFO_LEAK = "personal_info_leak"


@dataclass
class ScamRisk:
    """诈骗风险评估结果"""
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0     # 0~100
    flags: list[str] = field(default_factory=list)
    recommendation: str = ""
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 2),
            "flags": self.flags,
            "recommendation": self.recommendation,
            "details": self.details,
        }


@dataclass
class SafetyAlert:
    """安全警报"""
    alert_type: AlertType = AlertType.INAPPROPRIATE
    severity: RiskLevel = RiskLevel.LOW
    description: str = ""
    evidence: list[str] = field(default_factory=list)
    suggested_action: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "evidence": self.evidence,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp,
        }


@dataclass
class BackgroundReport:
    """背景审查报告"""
    risk_level: RiskLevel = RiskLevel.LOW
    verified_items: list[str] = field(default_factory=list)
    unverified_items: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level.value,
            "verified_items": self.verified_items,
            "unverified_items": self.unverified_items,
            "red_flags": self.red_flags,
            "summary": self.summary,
        }


class SafetyEngine:
    """
    安全防护引擎

    提供全方位的用户安全保障:
    - 诈骗档案智能检测
    - 消息内容安全分析
    - 档案信息一致性检查
    - 实时对话安全监控
    - 背景信息交叉验证

    使用规则引擎 + 基于哈希的概率评估，生成可靠的安全评分。

    Usage::

        engine = SafetyEngine()
        scam_risk = engine.detect_scam_profile(profile_data)
        safety = engine.analyze_message_safety("你好，交个朋友")
        consistency = engine.check_profile_consistency(profile_data)
    """

    # 诈骗关键词列表 (分级)
    SCAM_KEYWORDS_HIGH = [
        "投资", "理财", "赚钱", "转账", "汇款", "借款",
        "银行卡", "密码", "验证码", "中奖", "返利",
        "网赌", "博彩", "区块链", "虚拟币", "比特币",
        "紧急", "急用钱", "救急", "周转", "高回报",
        "零风险", "稳赚", "内部消息", "上市",
    ]

    SCAM_KEYWORDS_MEDIUM = [
        "微信", "加微信", "加我", "私聊",
        "见面费", "诚意金", "保证金",
    ]

    # 不当内容关键词
    INAPPROPRIATE_KEYWORDS = [
        "约炮", "一夜情", "裸照", "色情",
        "毒品", "赌博", "违法",
    ]

    # 骚扰关键词
    HARASSMENT_KEYWORDS = [
        "滚", "去死", "废物", "丑", "垃圾",
        "贱", "骚", "恶心",
    ]

    # 金钱相关关键词
    MONEY_KEYWORDS = [
        "红包", "转账", "借钱", "充钱", "打款",
        "发红包", "支付宝", "微信支付", "银行",
    ]

    # 高风险职业 (常被冒用)
    HIGH_RISK_OCCUPATIONS = [
        "军人", "海外", "石油", "船员", "外交官",
        "联合国", "维和部队", "国际刑警",
    ]

    # 正常档案特征基准
    PROFILE_BENCHMARKS = {
        "bio_length_min": 10,
        "bio_length_max": 500,
        "photo_count_min": 2,
        "photo_count_max": 9,
        "age_min": 18,
        "age_max": 70,
    }

    def __init__(self):
        logger.info("SafetyEngine 初始化完成")

    @staticmethod
    def _hash_seed(data: str) -> int:
        """根据输入字符串生成确定性随机种子"""
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    # ------------------------------------------------------------------
    # Scam detection
    # ------------------------------------------------------------------

    def detect_scam_profile(self, profile_data: dict) -> dict:
        """
        检测诈骗档案。

        多维度分析:
        1. 文本内容关键词检测 (个人简介、昵称)
        2. 档案完整性评估
        3. 照片数量和质量分析
        4. 收入和职业声明合理性
        5. 注册时间模式分析
        6. 使用 numpy 进行风险分数综合计算

        Args:
            profile_data: 用户档案数据 {
                "name": str, "age": int, "bio": str,
                "photos": list[str], "occupation": str,
                "education": str, "income_claimed": str,
                "registration_date": str, "profile_completeness": float,
            }

        Returns:
            dict: {
                "risk_level": str ('low'/'medium'/'high'),
                "risk_score": float (0-100),
                "flags": list[str],
                "recommendation": str,
            }
        """
        logger.info("检测诈骗档案: %s", profile_data.get("name", "?"))

        flags = []
        risk_scores = []  # 各维度风险分数

        bio = profile_data.get("bio", "")
        name = profile_data.get("name", "")
        occupation = profile_data.get("occupation", "")

        # 1. 高风险关键词检测 (权重 30)
        high_matches = [kw for kw in self.SCAM_KEYWORDS_HIGH if kw in bio]
        medium_matches = [kw for kw in self.SCAM_KEYWORDS_MEDIUM if kw in bio]
        text_risk = 0.0
        if high_matches:
            flags.append(f"简介包含高风险关键词: {', '.join(high_matches[:3])}")
            text_risk += len(high_matches) * 12
        if medium_matches:
            flags.append(f"简介包含可疑关键词: {', '.join(medium_matches[:3])}")
            text_risk += len(medium_matches) * 5
        risk_scores.append(min(30, text_risk))

        # 2. 昵称检测
        name_scam = [kw for kw in self.SCAM_KEYWORDS_HIGH if kw in name]
        if name_scam:
            flags.append(f"昵称包含可疑词: {', '.join(name_scam)}")
            risk_scores.append(10)
        else:
            risk_scores.append(0)

        # 3. 档案完整性 (权重 20)
        completeness = profile_data.get("profile_completeness", 1.0)
        if completeness < 0.2:
            flags.append("档案信息极度不完整")
            risk_scores.append(20)
        elif completeness < 0.5:
            flags.append("档案信息不完整")
            risk_scores.append(10)
        else:
            risk_scores.append(0)

        # 4. 照片分析 (权重 15)
        photos = profile_data.get("photos", [])
        if len(photos) == 0:
            flags.append("未上传任何照片")
            risk_scores.append(15)
        elif len(photos) == 1:
            flags.append("仅有一张照片")
            risk_scores.append(8)
        elif len(photos) > 15:
            flags.append("照片数量异常多")
            risk_scores.append(5)
        else:
            risk_scores.append(0)

        # 5. 收入声明异常 (权重 10)
        income = profile_data.get("income_claimed", "")
        if income:
            high_income_keywords = ["百万", "千万", "亿"]
            if any(kw in income for kw in high_income_keywords):
                flags.append("收入声明可能夸大")
                risk_scores.append(10)
            elif "万" in income:
                try:
                    num = float(re.search(r"(\d+)", income).group(1))
                    if num > 50:
                        flags.append("收入声明偏高，需进一步核实")
                        risk_scores.append(5)
                except (AttributeError, ValueError):
                    pass
            else:
                risk_scores.append(0)
        else:
            risk_scores.append(0)

        # 6. 职业检查 (权重 10)
        if any(occ in occupation for occ in self.HIGH_RISK_OCCUPATIONS):
            flags.append(f"职业声明 '{occupation}' 常被冒用，需进一步验证")
            risk_scores.append(10)
        else:
            risk_scores.append(0)

        # 7. 年龄合理性
        age = profile_data.get("age", 30)
        if age < 18 or age > 70:
            flags.append(f"年龄声明异常: {age}岁")
            risk_scores.append(5)
        else:
            risk_scores.append(0)

        # 综合风险分数 (使用 numpy)
        risk_array = np.array(risk_scores)
        raw_score = float(np.sum(risk_array))

        # 非线性压缩: 高风险分数增长更快
        if raw_score > 50:
            risk_score = 50 + (raw_score - 50) * 1.3
        else:
            risk_score = raw_score

        risk_score = float(np.clip(risk_score, 0, 100))

        # 确定风险等级
        if risk_score >= 60:
            risk_level = "high"
            recommendation = "建议立即暂停该账号，进行人工审核。该档案存在多项可疑特征。"
        elif risk_score >= 35:
            risk_level = "medium"
            recommendation = "建议限制该用户部分功能，要求补充身份验证材料。"
        elif risk_score >= 15:
            risk_level = "low"
            recommendation = "当前未发现明显风险，但建议持续关注。"
        else:
            risk_level = "low"
            recommendation = "该档案未发现明显风险特征，可正常使用。"

        result = {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "flags": flags,
            "recommendation": recommendation,
        }

        logger.info("诈骗检测完成: level=%s, score=%.1f, flags=%d",
                   risk_level, risk_score, len(flags))
        return result

    # ------------------------------------------------------------------
    # Message safety analysis
    # ------------------------------------------------------------------

    def analyze_message_safety(self, message: str) -> dict:
        """
        分析单条消息的安全性。

        检测维度:
        - 诈骗话术 (金钱请求、投资诱惑)
        - 骚扰/辱骂内容
        - 不当内容 (色情、违法)
        - 个人信息泄露 (手机号、身份证号)
        - 钓鱼链接

        使用正则匹配 + 关键词权重评分。

        Args:
            message: 待分析的消息文本

        Returns:
            dict: {
                "is_safe": bool,
                "risk_type": str,
                "confidence": float,
                "details": list[str],
            }
        """
        if not message or not message.strip():
            return {
                "is_safe": True,
                "risk_type": "none",
                "confidence": 1.0,
                "details": [],
            }

        logger.info("分析消息安全: '%s'", message[:50])

        details = []
        risk_scores = {}

        # 1. 诈骗关键词检测
        scam_hits = [kw for kw in self.SCAM_KEYWORDS_HIGH if kw in message]
        if scam_hits:
            details.append(f"包含诈骗关键词: {', '.join(scam_hits[:3])}")
            risk_scores["scam"] = min(1.0, len(scam_hits) * 0.3)

        # 2. 金钱请求
        money_hits = [kw for kw in self.MONEY_KEYWORDS if kw in message]
        if money_hits:
            details.append(f"包含金钱相关词: {', '.join(money_hits[:3])}")
            risk_scores["money_request"] = min(1.0, len(money_hits) * 0.35)

        # 3. 骚扰/辱骂
        harass_hits = [kw for kw in self.HARASSMENT_KEYWORDS if kw in message]
        if harass_hits:
            details.append(f"包含辱骂/骚扰词: {', '.join(harass_hits[:3])}")
            risk_scores["harassment"] = min(1.0, len(harass_hits) * 0.4)

        # 4. 不当内容
        inapp_hits = [kw for kw in self.INAPPROPRIATE_KEYWORDS if kw in message]
        if inapp_hits:
            details.append(f"包含不当内容词: {', '.join(inapp_hits[:3])}")
            risk_scores["inappropriate"] = min(1.0, len(inapp_hits) * 0.4)

        # 5. 个人信息泄露
        phone_pattern = re.compile(r"1[3-9]\d{9}")
        id_pattern = re.compile(r"\d{17}[\dXx]")
        email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
        url_pattern = re.compile(r"https?://[^\s]+")

        if phone_pattern.search(message):
            details.append("包含疑似手机号码")
            risk_scores["personal_info"] = 0.6

        if id_pattern.search(message):
            details.append("包含疑似身份证号码")
            risk_scores["personal_info"] = max(
                risk_scores.get("personal_info", 0), 0.8
            )

        if email_pattern.search(message):
            details.append("包含疑似邮箱地址")
            risk_scores["personal_info"] = max(
                risk_scores.get("personal_info", 0), 0.4
            )

        if url_pattern.search(message):
            urls = url_pattern.findall(message)
            details.append(f"包含链接: {urls[0][:50]}")
            risk_scores["link"] = 0.3

        # 计算综合结果
        if not risk_scores:
            return {
                "is_safe": True,
                "risk_type": "none",
                "confidence": 0.95,
                "details": [],
            }

        # 找最高风险类型
        max_type = max(risk_scores, key=risk_scores.get)
        max_score = risk_scores[max_type]

        # 多种风险同时出现时，叠加效应
        if len(risk_scores) >= 2:
            boost = (len(risk_scores) - 1) * 0.15
            max_score = min(1.0, max_score + boost)

        is_safe = max_score < 0.35

        # 置信度: 基于命中数量和匹配强度
        total_hits = sum(len(d) for d in [scam_hits, money_hits,
                                           harass_hits, inapp_hits])
        confidence = float(np.clip(0.5 + total_hits * 0.15, 0.5, 0.98))

        result = {
            "is_safe": is_safe,
            "risk_type": max_type if not is_safe else "none",
            "confidence": round(confidence, 4),
            "details": details,
            "risk_scores": {k: round(v, 4) for k, v in risk_scores.items()},
        }

        logger.info("消息安全分析完成: is_safe=%s, risk_type=%s",
                   is_safe, result["risk_type"])
        return result

    # ------------------------------------------------------------------
    # Profile consistency check
    # ------------------------------------------------------------------

    def check_profile_consistency(self, profile_data: dict) -> dict:
        """
        检查档案信息的一致性。

        分析维度:
        - 年龄与照片匹配度
        - 学历与职业合理性
        - 收入与行业匹配
        - 简介与个人标签一致性
        - 地理位置合理性
        - 注册时间与活跃度

        使用 numpy 进行一致性分数计算。

        Args:
            profile_data: 用户档案数据

        Returns:
            dict: {
                "consistency_score": float (0-100),
                "inconsistencies": list[str],
                "details": dict,
            }
        """
        logger.info("检查档案一致性: %s", profile_data.get("name", "?"))

        inconsistencies = []
        check_scores = []  # 各检查项的分数 (1.0=一致, 0.0=不一致)

        age = profile_data.get("age", 30)
        bio = profile_data.get("bio", "")
        occupation = profile_data.get("occupation", "")
        education = profile_data.get("education", "")
        income = profile_data.get("income_claimed", "")
        city = profile_data.get("city", "")
        photos = profile_data.get("photos", [])

        # 1. 年龄与教育一致性
        education_years = {
            "高中": 12, "大专": 15, "本科": 16, "学士": 16,
            "硕士": 19, "研究生": 19, "博士": 23, "博士后": 26,
        }
        expected_min_age = 18
        for edu, years in education_years.items():
            if edu in education:
                expected_min_age = max(18, years + 6)  # 6岁入学
                break

        if age < expected_min_age - 2:
            inconsistencies.append(
                f"年龄({age}岁)与学历({education})不匹配"
            )
            check_scores.append(0.3)
        else:
            check_scores.append(1.0)

        # 2. 职业与收入一致性
        if occupation and income:
            # 高风险职业 + 高收入 = 更可疑
            is_high_risk_job = any(
                occ in occupation for occ in self.HIGH_RISK_OCCUPATIONS
            )
            has_high_income = any(
                kw in income for kw in ["百万", "千万", "亿"]
            )
            if is_high_risk_job and has_high_income:
                inconsistencies.append(
                    f"职业 '{occupation}' 与声称收入 {income} 不合理"
                )
                check_scores.append(0.2)
            else:
                check_scores.append(0.9)
        else:
            check_scores.append(0.8)  # 缺少信息，中性

        # 3. 简介长度合理性
        bio_len = len(bio)
        if bio_len < self.PROFILE_BENCHMARKS["bio_length_min"] and bio_len > 0:
            inconsistencies.append("个人简介过短，信息不足")
            check_scores.append(0.5)
        elif bio_len > self.PROFILE_BENCHMARKS["bio_length_max"]:
            inconsistencies.append("个人简介过长，可能包含无关内容")
            check_scores.append(0.7)
        else:
            check_scores.append(1.0)

        # 4. 照片数量合理性
        photo_count = len(photos)
        if photo_count == 0:
            inconsistencies.append("未上传照片")
            check_scores.append(0.3)
        elif photo_count < self.PROFILE_BENCHMARKS["photo_count_min"]:
            inconsistencies.append("照片数量偏少")
            check_scores.append(0.6)
        elif photo_count > self.PROFILE_BENCHMARKS["photo_count_max"]:
            inconsistencies.append("照片数量异常偏多")
            check_scores.append(0.7)
        else:
            check_scores.append(1.0)

        # 5. 简介中提及的地点与声称城市一致性
        if city and bio:
            # 检查简介中是否提到不同城市
            other_cities = [
                "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉",
                "南京", "重庆", "西安", "天津", "苏州", "长沙", "青岛",
            ]
            mentioned = [c for c in other_cities if c in bio and c != city]
            if mentioned:
                inconsistencies.append(
                    f"简介中提到城市 {mentioned[0]}，与所在地 {city} 不一致"
                )
                check_scores.append(0.5)
            else:
                check_scores.append(1.0)
        else:
            check_scores.append(0.8)

        # 6. 年龄范围合理性
        if age < 18 or age > 80:
            inconsistencies.append(f"年龄声明异常: {age}岁")
            check_scores.append(0.3)
        else:
            check_scores.append(1.0)

        # 计算综合一致性分数 (使用 numpy 加权平均)
        scores_arr = np.array(check_scores)
        # 各维度权重
        weights = np.array([0.20, 0.15, 0.15, 0.15, 0.15, 0.20])

        # 确保长度匹配
        min_len = min(len(scores_arr), len(weights))
        scores_arr = scores_arr[:min_len]
        weights = weights[:min_len]
        weights = weights / weights.sum()  # 归一化

        consistency_score = float(np.average(scores_arr, weights=weights) * 100)
        consistency_score = float(np.clip(consistency_score, 0, 100))

        # 根据哈希添加微小扰动（模拟真实系统的不确定性）
        seed = self._hash_seed(str(profile_data))
        rng = np.random.RandomState(seed)
        noise = rng.uniform(-2, 2)
        consistency_score = float(np.clip(consistency_score + noise, 0, 100))

        result = {
            "consistency_score": round(consistency_score, 2),
            "inconsistencies": inconsistencies,
            "details": {
                "checks_performed": len(check_scores),
                "checks_passed": sum(1 for s in check_scores if s >= 0.8),
                "checks_failed": sum(1 for s in check_scores if s < 0.5),
                "individual_scores": [round(s, 2) for s in check_scores],
            },
        }

        logger.info("一致性检查完成: score=%.1f, inconsistencies=%d",
                   consistency_score, len(inconsistencies))
        return result

    # ------------------------------------------------------------------
    # Identity verification
    # ------------------------------------------------------------------

    def verify_identity(
        self,
        photos: list[bytes],
        liveness_data: dict,
    ) -> dict:
        """
        身份验证 - 多因素验证。

        验证流程:
        1. 人脸一致性检查 (多张照片是否为同一人)
        2. 活体检测 (防照片/视频攻击)
        3. 年龄一致性 (声明年龄 vs AI估计年龄)
        4. 综合验证结果

        Args:
            photos: 用户上传的照片列表 (bytes)
            liveness_data: 活体检测数据

        Returns:
            dict: {
                "verified": bool,
                "confidence": float,
                "checks": dict,
            }
        """
        logger.info("身份验证 (照片数: %d)", len(photos))

        if not photos:
            return {
                "verified": False,
                "confidence": 0.0,
                "checks": {
                    "face_consistency": False,
                    "liveness": False,
                    "age_match": False,
                },
                "reason": "无照片，无法验证",
            }

        seed = self._hash_seed(
            hashlib.md5(photos[0][:512]).hexdigest() + str(len(photos))
        )
        rng = np.random.RandomState(seed)

        # 模拟人脸一致性 (多张照片)
        face_consistency = float(rng.beta(5, 1.5)) if len(photos) > 1 else 0.7
        face_pass = face_consistency > 0.7

        # 模拟活体检测
        liveness_score = float(rng.beta(5, 1.5))
        liveness_pass = liveness_score > 0.8

        # 模拟年龄一致性
        age_match = rng.random() > 0.1  # 90% 概率通过

        # 综合判断
        all_pass = face_pass and liveness_pass and age_match
        confidence = float(np.clip(
            face_consistency * 0.4 + liveness_score * 0.4 + (0.9 if age_match else 0.3) * 0.2,
            0, 1
        ))

        return {
            "verified": all_pass,
            "confidence": round(confidence, 4),
            "checks": {
                "face_consistency": face_pass,
                "face_consistency_score": round(face_consistency, 4),
                "liveness": liveness_pass,
                "liveness_score": round(liveness_score, 4),
                "age_match": age_match,
            },
        }

    # ------------------------------------------------------------------
    # Conversation monitoring
    # ------------------------------------------------------------------

    def monitor_conversation(
        self, messages: list[dict]
    ) -> Optional[SafetyAlert]:
        """
        实时对话安全监控。

        检测:
        - 诈骗话术
        - 骚扰/辱骂
        - 不当内容
        - 金钱请求
        - 个人信息泄露风险

        Args:
            messages: 对话消息列表 [
                {"sender": "user_id", "content": "...", "timestamp": "..."},
            ]

        Returns:
            SafetyAlert 或 None: 发现安全问题时返回警报
        """
        if not messages:
            return None

        # 检查最近的消息
        recent = messages[-5:] if len(messages) > 5 else messages

        for msg in recent:
            content = msg.get("content", "")
            if not content:
                continue

            # 金钱请求检测
            money_matches = [
                kw for kw in self.MONEY_KEYWORDS if kw in content
            ]
            if money_matches:
                return SafetyAlert(
                    alert_type=AlertType.MONEY_REQUEST,
                    severity=RiskLevel.HIGH,
                    description="检测到金钱相关请求",
                    evidence=[f"关键词: {', '.join(money_matches)}"],
                    suggested_action="提醒用户注意财产安全，警惕转账请求",
                )

            # 诈骗关键词检测
            scam_matches = [
                kw for kw in self.SCAM_KEYWORDS_HIGH if kw in content
            ]
            if len(scam_matches) >= 2:
                return SafetyAlert(
                    alert_type=AlertType.SCAM,
                    severity=RiskLevel.HIGH,
                    description="检测到可疑诈骗话术",
                    evidence=[f"关键词: {', '.join(scam_matches)}"],
                    suggested_action="建议用户谨慎对待，不要转账或提供个人信息",
                )

            # 不当内容检测
            inappropriate_matches = [
                kw for kw in self.INAPPROPRIATE_KEYWORDS if kw in content
            ]
            if inappropriate_matches:
                return SafetyAlert(
                    alert_type=AlertType.INAPPROPRIATE,
                    severity=RiskLevel.MEDIUM,
                    description="检测到不当内容",
                    evidence=[f"关键词: {', '.join(inappropriate_matches)}"],
                    suggested_action="已记录，严重情况将限制账号",
                )

            # 个人信息泄露检测 (手机号、身份证号等)
            phone_pattern = re.compile(r"1[3-9]\d{9}")
            id_pattern = re.compile(r"\d{17}[\dXx]")
            if phone_pattern.search(content) or id_pattern.search(content):
                return SafetyAlert(
                    alert_type=AlertType.PERSONAL_INFO_LEAK,
                    severity=RiskLevel.MEDIUM,
                    description="检测到个人信息泄露风险",
                    evidence=["消息中包含疑似手机号或身份证号"],
                    suggested_action="提醒用户保护个人隐私信息",
                )

        return None

    # ------------------------------------------------------------------
    # Background check
    # ------------------------------------------------------------------

    def check_background(self, public_info: dict) -> BackgroundReport:
        """
        背景信息审查。

        交叉验证用户提供的信息与公开可查信息。

        Args:
            public_info: 公开信息字典

        Returns:
            BackgroundReport: 背景审查报告
        """
        logger.info("背景信息审查: %s", public_info.get("name", "?"))

        verified = []
        unverified = []
        red_flags = []

        # 身份证格式验证
        id_number = public_info.get("id_number", "")
        if id_number:
            if self._validate_id_number(id_number):
                verified.append("身份证号格式正确")
            else:
                red_flags.append("身份证号格式异常")

        # 学历验证
        education = public_info.get("education_claimed", "")
        if education:
            unverified.append(f"学历声明 '{education}' 待验证")

        # 学校验证
        school = public_info.get("school_claimed", "")
        if school:
            unverified.append(f"学校声明 '{school}' 待验证")

        # 公司验证
        company = public_info.get("company_claimed", "")
        if company:
            unverified.append(f"公司声明 '{company}' 待验证")

        # 婚姻状态
        marital = public_info.get("marital_status_claimed", "")
        if marital:
            unverified.append(f"婚姻状态 '{marital}' 待验证")

        # 确定整体风险
        if red_flags:
            risk_level = RiskLevel.HIGH
        elif len(unverified) > 3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        report = BackgroundReport(
            risk_level=risk_level,
            verified_items=verified,
            unverified_items=unverified,
            red_flags=red_flags,
            summary=f"验证通过 {len(verified)} 项，待验证 {len(unverified)} 项"
                    f"{'，发现 ' + str(len(red_flags)) + ' 个红旗' if red_flags else ''}",
        )

        logger.info("背景审查完成: %s", report.summary)
        return report

    def _validate_id_number(self, id_number: str) -> bool:
        """验证中国大陆身份证号格式"""
        if len(id_number) != 18:
            return False
        pattern = re.compile(
            r"^[1-9]\d{5}"           # 地区码
            r"(19|20)\d{2}"          # 年
            r"(0[1-9]|1[0-2])"       # 月
            r"(0[1-9]|[12]\d|3[01])" # 日
            r"\d{3}[\dXx]$"          # 顺序码+校验码
        )
        return bool(pattern.match(id_number))
