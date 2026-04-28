"""
Health Assessment Engine
========================
健康评估引擎。

功能:
- 综合健康评估报告
- 基因风险检测
- 心理健康筛查
- 生活方式评分
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HealthReport:
    """综合健康评估报告"""
    overall_score: float = 0.0       # 综合健康评分 0~100
    physical_score: float = 0.0      # 身体健康评分
    mental_score: float = 0.0        # 心理健康评分
    lifestyle_score: float = 0.0     # 生活方式评分
    genetic_risk: float = 0.0        # 基因风险 0~1
    bmi: Optional[float] = None      # BMI指数
    recommendations: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    @property
    def health_level(self) -> str:
        if self.overall_score >= 85:
            return "优秀"
        elif self.overall_score >= 70:
            return "良好"
        elif self.overall_score >= 55:
            return "一般"
        elif self.overall_score >= 40:
            return "需关注"
        else:
            return "建议就医"

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "physical_score": round(self.physical_score, 1),
            "mental_score": round(self.mental_score, 1),
            "lifestyle_score": round(self.lifestyle_score, 1),
            "genetic_risk": round(self.genetic_risk, 4),
            "bmi": self.bmi,
            "health_level": self.health_level,
            "recommendations": self.recommendations,
            "risk_factors": self.risk_factors,
            "generated_at": self.generated_at,
        }


class HealthEngine:
    """
    健康评估引擎

    通过多维度数据分析，提供全面的健康评估报告。
    帮助用户了解自身健康状况，为匹配提供参考。

    使用 numpy 进行数值计算，基于真实健康评估模型的简化版本。

    Usage::

        engine = HealthEngine()
        report = engine.assess_health(user_data)
        lifestyle = engine.calculate_lifestyle_score(diet=8, exercise=7, sleep=6, ...)
        health_report = engine.generate_health_report(user_data)
    """

    # 心理健康问卷题目数
    MENTAL_HEALTH_QUESTIONS = 20

    # BMI 正常范围
    BMI_NORMAL_MIN = 18.5
    BMI_NORMAL_MAX = 24.0

    # 生活方式评分权重
    LIFESTYLE_WEIGHTS = {
        "diet": 0.25,
        "exercise": 0.25,
        "sleep": 0.20,
        "smoking": 0.15,
        "drinking": 0.15,
    }

    # 通用健康建议库
    DIET_TIPS = [
        "建议增加蔬菜和水果的摄入量，每天至少5份",
        "减少高盐、高油、高糖食物的摄入",
        "增加优质蛋白质摄入：鱼肉、豆类、蛋类",
        "保持规律饮食，避免暴饮暴食",
        "注意补充膳食纤维，促进消化健康",
    ]

    EXERCISE_TIPS = [
        "建议每周进行至少150分钟中等强度有氧运动",
        "增加日常活动量，如步行、爬楼梯",
        "适当进行力量训练，每周2-3次",
        "注意运动前热身和运动后拉伸",
        "选择自己喜欢的运动方式，保持长期习惯",
    ]

    SLEEP_TIPS = [
        "保持规律作息，每天同一时间入睡和起床",
        "睡前1小时避免使用电子设备",
        "营造舒适的睡眠环境，保持安静和黑暗",
        "避免睡前摄入咖啡因和酒精",
        "如有持续失眠问题，建议就医咨询",
    ]

    def __init__(self):
        logger.info("HealthEngine 初始化完成")

    @staticmethod
    def _hash_seed(data: str) -> int:
        """根据输入字符串生成确定性随机种子"""
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    # ------------------------------------------------------------------
    # Comprehensive health assessment
    # ------------------------------------------------------------------

    def assess_health(self, user_data: dict) -> dict:
        """
        综合健康评估。

        基于用户健康数据计算各维度评分，使用加权算法融合多维度评估。
        支持缺失数据时使用人口统计默认值。

        Args:
            user_data: 用户健康数据字典，包含:
                - height_cm (float): 身高(厘米)
                - weight_kg (float): 体重(公斤)
                - age (int): 年龄
                - gender (str): 性别 ('male' / 'female')
                - diet (int): 饮食质量 1~10
                - exercise (int): 运动频率 1~10
                - sleep_hours (float): 每日睡眠小时数
                - smoking (bool): 是否吸烟
                - drinking (int): 饮酒频率 0~10
                - mental_health_answers (list[int]): 心理健康问卷回答
                - genetic_markers (dict): 基因标记 (可选)
                - chronic_conditions (list[str]): 慢性病史 (可选)
                - family_history (list[str]): 家族病史 (可选)

        Returns:
            dict: 综合健康评估报告字典
        """
        logger.info("开始综合健康评估")

        recommendations = []
        risk_factors = []

        # 计算 BMI
        height_m = user_data.get("height_cm", 170) / 100.0
        weight_kg = user_data.get("weight_kg", 65)
        bmi = weight_kg / (height_m ** 2) if height_m > 0 else None

        # 身体健康评分
        physical_score = self._calc_physical_score(user_data, bmi)

        # 心理健康评分
        mental_answers = user_data.get("mental_health_answers", [])
        mental_score = self.mental_health_screen(mental_answers)

        # 生活方式评分
        lifestyle = self.calculate_lifestyle_score(
            diet=user_data.get("diet", 5),
            exercise=user_data.get("exercise", 5),
            sleep=user_data.get("sleep_hours", 7),
            smoking=user_data.get("smoking", False),
            drinking=user_data.get("drinking", 3),
        )

        # 基因风险
        genetic_markers = user_data.get("genetic_markers", {})
        genetic_risk = self._genetic_risk_check(genetic_markers)

        # 生成建议
        if bmi is not None:
            if bmi < self.BMI_NORMAL_MIN:
                recommendations.append("建议适当增加营养摄入，增加体重")
                risk_factors.append("体重偏低 (BMI={:.1f})".format(bmi))
            elif bmi > 28:
                recommendations.append("建议积极减重，控制饮食并增加运动")
                risk_factors.append("肥胖风险 (BMI={:.1f})".format(bmi))
            elif bmi > self.BMI_NORMAL_MAX:
                recommendations.append("建议控制饮食，增加运动量")
                risk_factors.append("体重超标 (BMI={:.1f})".format(bmi))

        if user_data.get("smoking"):
            recommendations.append("强烈建议戒烟，吸烟严重危害健康")
            risk_factors.append("吸烟")

        if user_data.get("drinking", 0) > 7:
            recommendations.append("建议减少饮酒频率，每周饮酒不宜超过2次")
            risk_factors.append("饮酒过量")

        sleep_hours = user_data.get("sleep_hours", 7)
        if sleep_hours < 6:
            recommendations.append("建议保证每天7~8小时睡眠")
            risk_factors.append("睡眠不足 ({:.1f}小时/天)".format(sleep_hours))
        elif sleep_hours > 9:
            recommendations.append("睡眠时间过长，建议检查是否有睡眠障碍")
            risk_factors.append("睡眠过多")

        if mental_score < 60:
            recommendations.append("建议关注心理健康，考虑寻求专业帮助")
            risk_factors.append("心理健康需关注")

        if genetic_risk > 0.3:
            recommendations.append("建议定期进行健康体检，关注家族病史相关疾病")
            risk_factors.append("基因风险较高")

        # 年龄相关建议
        age = user_data.get("age", 30)
        if age > 40:
            recommendations.append("建议每年进行全面体检")
        if age > 50:
            recommendations.append("注意骨密度检测和心血管健康检查")

        if not recommendations:
            recommendations.append("您的健康状况良好，请继续保持！")

        # 综合评分 (加权平均)
        overall = (
            physical_score * 0.30
            + mental_score * 0.25
            + lifestyle * 0.25
            + (1 - genetic_risk) * 100 * 0.20
        )

        report = {
            "overall_score": round(overall, 1),
            "physical_score": round(physical_score, 1),
            "mental_score": round(mental_score, 1),
            "lifestyle_score": round(lifestyle, 1),
            "genetic_risk": round(genetic_risk, 4),
            "bmi": round(bmi, 1) if bmi else None,
            "health_level": self._health_level(overall),
            "recommendations": recommendations,
            "risk_factors": risk_factors,
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info("健康评估完成: 总分=%.1f, 等级=%s",
                   overall, report["health_level"])
        return report

    @staticmethod
    def _health_level(score: float) -> str:
        """根据分数判断健康等级"""
        if score >= 85:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 55:
            return "一般"
        elif score >= 40:
            return "需关注"
        else:
            return "建议就医"

    def _calc_physical_score(self, user_data: dict, bmi: Optional[float]) -> float:
        """
        计算身体健康评分。

        考虑因素: 年龄、BMI、慢性病史、家族病史。
        使用 numpy 进行分数计算。
        """
        age = user_data.get("age", 30)
        base = 70.0

        # 年龄因素: 使用高斯衰减函数
        # 25-35岁最优，偏离越远扣分越多
        age_penalty = 8.0 * (1.0 - np.exp(-((age - 30) ** 2) / (2 * 15.0 ** 2)))
        score = base + 15.0 - age_penalty  # 基础分 + 最高加分 - 年龄衰减

        # BMI 因素: 正态分布评分 (最优BMI=21.5)
        if bmi is not None:
            bmi_score = 15.0 * np.exp(-((bmi - 21.5) ** 2) / (2 * 4.0 ** 2))
            score += bmi_score

        # 慢性病扣分
        conditions = user_data.get("chronic_conditions", [])
        condition_penalty = len(conditions) * 5.0
        score -= condition_penalty

        # 家族病史扣分 (较小)
        family_history = user_data.get("family_history", [])
        family_penalty = len(family_history) * 2.0
        score -= family_penalty

        return float(np.clip(score, 0, 100))

    # ------------------------------------------------------------------
    # Genetic risk assessment
    # ------------------------------------------------------------------

    def _genetic_risk_check(self, genetic_markers: dict) -> float:
        """
        基因风险评估。

        基于已知的疾病相关基因标记，计算综合基因风险分数。

        Args:
            genetic_markers: 基因标记字典，例如:
                {
                    "BRCA1": "normal",
                    "APOE4": "carrier",
                    "LRRK2": "normal",
                }

        Returns:
            float: 综合风险分数 0~1 (0=无风险, 1=最高风险)
        """
        if not genetic_markers:
            return 0.15  # 无数据时返回基线风险

        logger.info("基因风险评估 (标记数: %d)", len(genetic_markers))

        # 基因标记风险权重
        risk_weights = {
            "BRCA1": {"carrier": 0.3, "mutant": 0.8, "normal": 0.0},
            "BRCA2": {"carrier": 0.25, "mutant": 0.75, "normal": 0.0},
            "APOE4": {"carrier": 0.2, "mutant": 0.5, "normal": 0.0},
            "LRRK2": {"carrier": 0.15, "mutant": 0.4, "normal": 0.0},
            "TP53": {"carrier": 0.3, "mutant": 0.7, "normal": 0.0},
            "MLH1": {"carrier": 0.2, "mutant": 0.6, "normal": 0.0},
            "ATM": {"carrier": 0.1, "mutant": 0.35, "normal": 0.0},
        }

        risks = []
        for marker, status in genetic_markers.items():
            if marker in risk_weights:
                weight = risk_weights[marker].get(status, 0.0)
                risks.append(weight)

        if not risks:
            return 0.15

        # 使用 numpy 计算加权风险 (考虑非线性叠加)
        risk_array = np.array(risks)
        # 多个风险因子非线性叠加: 1 - Π(1 - r_i)
        combined_risk = 1.0 - np.prod(1.0 - risk_array)
        risk = float(np.clip(combined_risk, 0.0, 1.0))

        logger.info("基因风险评估完成: risk=%.4f", risk)
        return round(risk, 4)

    # ------------------------------------------------------------------
    # Mental health screening
    # ------------------------------------------------------------------

    def mental_health_screen(self, answers: list[int]) -> float:
        """
        心理健康筛查 (基于 PHQ-9 / GAD-7 改编)。

        使用加权评分算法，某些题目权重更高（如自杀倾向、严重焦虑）。

        Args:
            answers: 问卷回答列表，每个答案为 0~3 分
                0 = 从不, 1 = 有时, 2 = 经常, 3 = 总是

        Returns:
            float: 心理健康评分 0~100 (100=最健康)
        """
        if not answers:
            return 70.0  # 无数据返回默认值

        logger.info("心理健康筛查 (题目数: %d)", len(answers))

        # 限制答案范围
        clamped = [min(max(int(a), 0), 3) for a in answers]

        # 使用 numpy 加权评分
        n = len(clamped)
        answers_arr = np.array(clamped, dtype=np.float64)

        # 权重设计: 前几题（抑郁情绪）和后几题（焦虑/自杀倾向）权重更高
        if n >= 10:
            weights = np.ones(n)
            weights[:3] = 1.2   # 抑郁核心症状
            weights[-3:] = 1.3  # 焦虑/自杀倾向
            weights = weights / weights.sum() * n  # 归一化
        else:
            weights = np.ones(n)

        # 加权严重度
        weighted_sum = float(np.sum(answers_arr * weights))
        max_possible = float(np.sum(3.0 * weights))
        severity = weighted_sum / max_possible if max_possible > 0 else 0

        # 非线性转换: 严重程度越高，扣分越多
        # 使用 sigmoid 形曲线
        score = 100.0 * (1.0 - severity ** 0.8)
        score = float(np.clip(score, 0, 100))

        logger.info("心理健康评分: %.1f", score)
        return round(score, 1)

    # ------------------------------------------------------------------
    # Lifestyle scoring
    # ------------------------------------------------------------------

    def calculate_lifestyle_score(
        self,
        diet: int = 5,
        exercise: int = 5,
        sleep: float = 7.0,
        smoking: bool = False,
        drinking: int = 3,
    ) -> float:
        """
        生活方式评分。

        使用多维度加权算法，考虑各因素的非线性影响。
        睡眠使用钟形函数评估（7-8小时最优）。

        Args:
            diet: 饮食质量 1~10
            exercise: 运动频率 1~10
            sleep: 每日睡眠小时数
            smoking: 是否吸烟
            drinking: 饮酒频率 0~10

        Returns:
            float: 生活方式评分 0~100
        """
        logger.info("生活方式评分: diet=%d, exercise=%d, sleep=%.1f, "
                     "smoking=%s, drinking=%d",
                     diet, exercise, sleep, smoking, drinking)

        # 饮食评分: 使用 sigmoid 映射到 0-100
        diet_clamped = max(0, min(10, diet))
        diet_score = 100.0 / (1.0 + np.exp(-1.2 * (diet_clamped - 5)))

        # 运动评分: 类似 sigmoid
        exercise_clamped = max(0, min(10, exercise))
        exercise_score = 100.0 / (1.0 + np.exp(-1.0 * (exercise_clamped - 5)))

        # 睡眠评分: 钟形函数 (最优 7.5 小时)
        sleep_score = 100.0 * np.exp(-((sleep - 7.5) ** 2) / (2 * 1.5 ** 2))

        # 吸烟扣分: 非线性惩罚
        smoking_score = 30.0 if smoking else 90.0

        # 饮酒评分: 越少越好，但少量饮酒(1-2)影响很小
        drinking_clamped = max(0, min(10, drinking))
        drinking_score = 100.0 * np.exp(-0.15 * drinking_clamped ** 1.5)

        # 加权汇总
        scores = np.array([diet_score, exercise_score, sleep_score,
                          smoking_score, drinking_score])
        weights = np.array([
            self.LIFESTYLE_WEIGHTS["diet"],
            self.LIFESTYLE_WEIGHTS["exercise"],
            self.LIFESTYLE_WEIGHTS["sleep"],
            self.LIFESTYLE_WEIGHTS["smoking"],
            self.LIFESTYLE_WEIGHTS["drinking"],
        ])

        final_score = float(np.sum(scores * weights))
        final_score = float(np.clip(final_score, 0, 100))

        logger.info("生活方式评分: %.1f (diet=%.0f, exercise=%.0f, "
                    "sleep=%.0f, smoke=%.0f, drink=%.0f)",
                    final_score, diet_score, exercise_score,
                    sleep_score, smoking_score, drinking_score)
        return round(final_score, 1)

    # 兼容旧接口
    def lifestyle_score(self, **kwargs) -> float:
        """向后兼容的接口"""
        return self.calculate_lifestyle_score(**kwargs)

    # ------------------------------------------------------------------
    # Health report generation
    # ------------------------------------------------------------------

    def generate_health_report(self, user_data: dict) -> dict:
        """
        生成综合健康报告。

        在 assess_health 基础上增加详细的风险因子分析和个性化建议。
        使用 numpy 进行风险概率计算。

        Args:
            user_data: 用户健康数据（同 assess_health）

        Returns:
            dict: {
                "scores": dict,            # 各维度评分
                "recommendations": list,   # 个性化建议
                "risk_factors": list,      # 风险因子
                "detail_analysis": dict,   # 详细分析
            }
        """
        # 先获取基础评估
        base = self.assess_health(user_data)

        # 详细分析
        age = user_data.get("age", 30)
        gender = user_data.get("gender", "unknown")
        height = user_data.get("height_cm", 170)
        weight = user_data.get("weight_kg", 65)
        bmi = base.get("bmi")

        # 身体成分分析 (简化版)
        body_analysis = {}
        if bmi is not None:
            if bmi < 18.5:
                body_analysis["body_type"] = "偏瘦"
                body_analysis["body_advice"] = "建议增加热量摄入和力量训练"
            elif bmi < 24:
                body_analysis["body_type"] = "正常"
                body_analysis["body_advice"] = "体型良好，请继续保持"
            elif bmi < 28:
                body_analysis["body_type"] = "偏胖"
                body_analysis["body_advice"] = "建议控制饮食并增加有氧运动"
            else:
                body_analysis["body_type"] = "肥胖"
                body_analysis["body_advice"] = "建议寻求营养师指导，制定减重计划"

        # 健康年龄估算 (基于生活方式)
        health_age = age  # 基础
        lifestyle = base.get("lifestyle_score", 70)
        if lifestyle > 80:
            health_age = max(18, age - int((lifestyle - 70) / 10))
        elif lifestyle < 50:
            health_age = age + int((60 - lifestyle) / 10)

        # 预期健康寿命贡献因子
        longevity_factors = {
            "smoking": -8.0 if user_data.get("smoking") else 0.0,
            "exercise": 4.0 if user_data.get("exercise", 5) >= 7 else -2.0,
            "diet": 3.0 if user_data.get("diet", 5) >= 7 else -1.0,
            "sleep": 2.0 if 6.5 <= user_data.get("sleep_hours", 7) <= 8.5 else -2.0,
            "drinking": -3.0 if user_data.get("drinking", 3) > 6 else 0.0,
        }

        # 个性化建议: 从建议库中选取最相关的
        personalized_tips = []
        if user_data.get("diet", 5) < 6:
            personalized_tips.append(self.DIET_TIPS[0])
        if user_data.get("exercise", 5) < 5:
            personalized_tips.append(self.EXERCISE_TIPS[0])
        if not (6.5 <= user_data.get("sleep_hours", 7) <= 8.5):
            personalized_tips.append(self.SLEEP_TIPS[0])

        report = {
            "scores": {
                "overall": base["overall_score"],
                "physical": base["physical_score"],
                "mental": base["mental_score"],
                "lifestyle": base["lifestyle_score"],
                "genetic_risk": base["genetic_risk"],
                "bmi": base["bmi"],
            },
            "health_level": base["health_level"],
            "recommendations": base["recommendations"] + personalized_tips,
            "risk_factors": base["risk_factors"],
            "detail_analysis": {
                "body": body_analysis,
                "health_age": health_age,
                "longevity_factors": longevity_factors,
            },
            "generated_at": base["generated_at"],
        }

        logger.info("健康报告生成完成: 总分=%.1f", base["overall_score"])
        return report
