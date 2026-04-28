"""
Minder AI红娘 - 匹配算法测试
测试匹配算法的核心逻辑
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch


# ============================================================
# 匹配算法核心函数（用于测试）
# ============================================================

def calculate_personality_score(profile_a: dict, profile_b: dict) -> float:
    """
    计算性格匹配分数
    基于性格标签的重叠度和互补性
    """
    tags_a = set(profile_a.get("personality_tags", []))
    tags_b = set(profile_b.get("personality_tags", []))

    if not tags_a or not tags_b:
        return 0.0

    # 互补性格对
    complementary_pairs = {
        ("内向", "外向"), ("理性", "感性"), ("安静", "活泼"),
        ("温柔", "坚强"), ("保守", "开放"), ("细心", "大大咧咧"),
    }

    # 相同性格加成
    common = tags_a & tags_b
    same_score = len(common) * 15

    # 互补性格加成
    complement_score = 0
    for pair in complementary_pairs:
        if (pair[0] in tags_a and pair[1] in tags_b) or \
           (pair[1] in tags_a and pair[0] in tags_b):
            complement_score += 10

    # 基础分
    base_score = 40

    total = base_score + same_score + complement_score
    return min(total, 100.0)


def calculate_values_score(profile_a: dict, profile_b: dict) -> float:
    """
    计算三观匹配分数
    基于教育背景、收入水平、城市等
    """
    score = 50.0  # 基础分

    # 教育匹配
    edu_levels = {"高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}
    edu_a = edu_levels.get(profile_a.get("education", ""), 0)
    edu_b = edu_levels.get(profile_b.get("education", ""), 0)

    edu_diff = abs(edu_a - edu_b)
    if edu_diff == 0:
        score += 20
    elif edu_diff == 1:
        score += 10
    else:
        score += 0

    # 城市匹配
    if profile_a.get("city") == profile_b.get("city"):
        score += 15

    # 收入匹配
    income_levels = {
        "10万以下": 1, "10-20万": 2, "20-30万": 3,
        "30-50万": 4, "50-80万": 5, "80万以上": 6
    }
    income_a = income_levels.get(profile_a.get("income_range", ""), 0)
    income_b = income_levels.get(profile_b.get("income_range", ""), 0)

    income_diff = abs(income_a - income_b)
    if income_diff <= 1:
        score += 15
    elif income_diff == 2:
        score += 5

    return min(score, 100.0)


def calculate_lifestyle_score(profile_a: dict, profile_b: dict) -> float:
    """
    计算生活方式匹配分数
    基于兴趣爱好的重叠度
    """
    hobbies_a = set(profile_a.get("hobbies", []))
    hobbies_b = set(profile_b.get("hobbies", []))

    if not hobbies_a or not hobbies_b:
        return 50.0

    # 共同爱好
    common = hobbies_a & hobbies_b
    total = hobbies_a | hobbies_b

    # 重叠度
    overlap_ratio = len(common) / len(total) if total else 0

    # 基础分 + 重叠度加成
    base_score = 40
    overlap_score = overlap_ratio * 60

    return min(base_score + overlap_score, 100.0)


def calculate_overall_score(
    personality_score: float,
    values_score: float,
    lifestyle_score: float,
    weights: dict = None
) -> float:
    """
    计算综合匹配分数
    """
    if weights is None:
        weights = {
            "personality": 0.30,
            "values": 0.40,
            "lifestyle": 0.30,
        }

    overall = (
        personality_score * weights["personality"] +
        values_score * weights["values"] +
        lifestyle_score * weights["lifestyle"]
    )

    return round(overall, 1)


def find_best_matches(
    user_profile: dict,
    candidates: list[dict],
    top_n: int = 5
) -> list[dict]:
    """
    为用户找到最佳匹配
    """
    results = []

    for candidate in candidates:
        if candidate.get("user_id") == user_profile.get("user_id"):
            continue

        personality = calculate_personality_score(user_profile, candidate)
        values = calculate_values_score(user_profile, candidate)
        lifestyle = calculate_lifestyle_score(user_profile, candidate)
        overall = calculate_overall_score(personality, values, lifestyle)

        results.append({
            "user_id": candidate["user_id"],
            "overall_score": overall,
            "personality_score": personality,
            "values_score": values,
            "lifestyle_score": lifestyle,
        })

    # 按综合分数排序
    results.sort(key=lambda x: x["overall_score"], reverse=True)

    return results[:top_n]


# ============================================================
# 测试用例
# ============================================================

class TestPersonalityScore:
    """性格匹配分数测试"""

    def test_identical_tags(self):
        """测试完全相同的性格标签"""
        profile_a = {"personality_tags": ["温柔", "独立", "上进"]}
        profile_b = {"personality_tags": ["温柔", "独立", "上进"]}

        score = calculate_personality_score(profile_a, profile_b)
        assert score == 85.0  # 40 + 3*15

    def test_no_common_tags(self):
        """测试没有共同性格标签"""
        profile_a = {"personality_tags": ["温柔", "独立"]}
        profile_b = {"personality_tags": ["幽默", "阳光"]}

        score = calculate_personality_score(profile_a, profile_b)
        assert score == 40.0  # 只有基础分

    def test_empty_tags(self):
        """测试空标签"""
        profile_a = {"personality_tags": []}
        profile_b = {"personality_tags": ["温柔"]}

        score = calculate_personality_score(profile_a, profile_b)
        assert score == 0.0

    def test_complementary_tags(self):
        """测试互补性格"""
        profile_a = {"personality_tags": ["理性", "安静"]}
        profile_b = {"personality_tags": ["感性", "活泼"]}

        score = calculate_personality_score(profile_a, profile_b)
        assert score == 60.0  # 40 + 2*10

    def test_mixed_tags(self):
        """测试混合标签（相同+互补）"""
        profile_a = {"personality_tags": ["温柔", "理性", "上进"]}
        profile_b = {"personality_tags": ["温柔", "感性", "幽默"]}

        score = calculate_personality_score(profile_a, profile_b)
        # 40 + 1*15(温柔) + 1*10(理性-感性) = 65
        assert score == 65.0

    def test_max_score_capped(self):
        """测试分数上限"""
        profile_a = {"personality_tags": ["a", "b", "c", "d", "e", "f", "g"]}
        profile_b = {"personality_tags": ["a", "b", "c", "d", "e", "f", "g"]}

        score = calculate_personality_score(profile_a, profile_b)
        assert score <= 100.0


class TestValuesScore:
    """三观匹配分数测试"""

    def test_same_city_education(self):
        """测试同城同学历"""
        profile_a = {"city": "北京", "education": "本科", "income_range": "20-30万"}
        profile_b = {"city": "北京", "education": "本科", "income_range": "20-30万"}

        score = calculate_values_score(profile_a, profile_b)
        assert score == 100.0  # 50 + 20 + 15 + 15

    def test_different_city(self):
        """测试不同城市"""
        profile_a = {"city": "北京", "education": "本科", "income_range": "20-30万"}
        profile_b = {"city": "上海", "education": "本科", "income_range": "20-30万"}

        score = calculate_values_score(profile_a, profile_b)
        assert score == 85.0  # 50 + 20 + 0 + 15

    def test_education_gap(self):
        """测试学历差距"""
        profile_a = {"city": "北京", "education": "博士", "income_range": "20-30万"}
        profile_b = {"city": "北京", "education": "大专", "income_range": "20-30万"}

        score = calculate_values_score(profile_a, profile_b)
        assert score == 80.0  # 50 + 0 + 15 + 15

    def test_income_gap(self):
        """测试收入差距"""
        profile_a = {"city": "北京", "education": "本科", "income_range": "80万以上"}
        profile_b = {"city": "北京", "education": "本科", "income_range": "10万以下"}

        score = calculate_values_score(profile_a, profile_b)
        assert score == 85.0  # 50 + 20 + 15 + 0


class TestLifestyleScore:
    """生活方式匹配分数测试"""

    def test_identical_hobbies(self):
        """测试完全相同的爱好"""
        profile_a = {"hobbies": ["旅行", "摄影", "阅读"]}
        profile_b = {"hobbies": ["旅行", "摄影", "阅读"]}

        score = calculate_lifestyle_score(profile_a, profile_b)
        assert score == 100.0  # 40 + 1.0 * 60

    def test_no_common_hobbies(self):
        """测试没有共同爱好"""
        profile_a = {"hobbies": ["旅行", "摄影"]}
        profile_b = {"hobbies": ["编程", "游戏"]}

        score = calculate_lifestyle_score(profile_a, profile_b)
        assert score == 40.0  # 只有基础分

    def test_partial_overlap(self):
        """测试部分重叠"""
        profile_a = {"hobbies": ["旅行", "摄影", "阅读", "音乐"]}
        profile_b = {"hobbies": ["旅行", "摄影", "编程", "游戏"]}

        # 共同: 旅行, 摄影 (2个)
        # 总共: 旅行, 摄影, 阅读, 音乐, 编程, 游戏 (6个)
        # 重叠度: 2/6 = 0.333
        score = calculate_lifestyle_score(profile_a, profile_b)
        assert 55.0 < score < 65.0  # 40 + 0.333 * 60 ≈ 60

    def test_empty_hobbies(self):
        """测试空爱好"""
        profile_a = {"hobbies": []}
        profile_b = {"hobbies": ["旅行"]}

        score = calculate_lifestyle_score(profile_a, profile_b)
        assert score == 50.0  # 默认分


class TestOverallScore:
    """综合分数测试"""

    def test_default_weights(self):
        """测试默认权重"""
        score = calculate_overall_score(80.0, 90.0, 70.0)
        expected = 80 * 0.3 + 90 * 0.4 + 70 * 0.3
        assert score == round(expected, 1)

    def test_custom_weights(self):
        """测试自定义权重"""
        weights = {"personality": 0.5, "values": 0.3, "lifestyle": 0.2}
        score = calculate_overall_score(80.0, 90.0, 70.0, weights)
        expected = 80 * 0.5 + 90 * 0.3 + 70 * 0.2
        assert score == round(expected, 1)

    def test_all_perfect(self):
        """测试满分"""
        score = calculate_overall_score(100.0, 100.0, 100.0)
        assert score == 100.0

    def test_all_zero(self):
        """测试零分"""
        score = calculate_overall_score(0.0, 0.0, 0.0)
        assert score == 0.0


class TestFindBestMatches:
    """最佳匹配测试"""

    @pytest.fixture
    def user_profile(self):
        return {
            "user_id": 1,
            "city": "北京",
            "education": "本科",
            "income_range": "20-30万",
            "hobbies": ["旅行", "摄影", "阅读"],
            "personality_tags": ["温柔", "独立", "上进"],
        }

    @pytest.fixture
    def candidates(self):
        return [
            {
                "user_id": 2,
                "city": "北京",
                "education": "本科",
                "income_range": "20-30万",
                "hobbies": ["旅行", "摄影", "音乐"],
                "personality_tags": ["温柔", "独立", "聪明"],
            },
            {
                "user_id": 3,
                "city": "上海",
                "education": "硕士",
                "income_range": "50-80万",
                "hobbies": ["编程", "游戏", "电影"],
                "personality_tags": ["理性", "聪明", "幽默"],
            },
            {
                "user_id": 4,
                "city": "北京",
                "education": "本科",
                "income_range": "20-30万",
                "hobbies": ["旅行", "摄影", "阅读"],
                "personality_tags": ["温柔", "独立", "上进"],
            },
        ]

    def test_find_matches(self, user_profile, candidates):
        """测试找到匹配"""
        matches = find_best_matches(user_profile, candidates, top_n=3)
        assert len(matches) == 3

    def test_best_match_is_identical(self, user_profile, candidates):
        """测试最佳匹配是完全相同的用户"""
        matches = find_best_matches(user_profile, candidates, top_n=1)
        assert matches[0]["user_id"] == 4

    def test_matches_sorted(self, user_profile, candidates):
        """测试匹配按分数排序"""
        matches = find_best_matches(user_profile, candidates, top_n=3)
        for i in range(len(matches) - 1):
            assert matches[i]["overall_score"] >= matches[i + 1]["overall_score"]

    def test_exclude_self(self, user_profile, candidates):
        """测试排除自己"""
        candidates_with_self = candidates + [user_profile]
        matches = find_best_matches(user_profile, candidates_with_self, top_n=10)
        user_ids = [m["user_id"] for m in matches]
        assert 1 not in user_ids

    def test_top_n_limit(self, user_profile, candidates):
        """测试限制返回数量"""
        matches = find_best_matches(user_profile, candidates, top_n=2)
        assert len(matches) == 2

    def test_empty_candidates(self, user_profile):
        """测试空候选列表"""
        matches = find_best_matches(user_profile, [], top_n=5)
        assert len(matches) == 0

    def test_match_has_all_scores(self, user_profile, candidates):
        """测试匹配结果包含所有分数"""
        matches = find_best_matches(user_profile, candidates, top_n=1)
        match = matches[0]
        assert "overall_score" in match
        assert "personality_score" in match
        assert "values_score" in match
        assert "lifestyle_score" in match


class TestMatchingEdgeCases:
    """边界情况测试"""

    def test_missing_fields(self):
        """测试缺少字段"""
        profile_a = {}
        profile_b = {}

        personality = calculate_personality_score(profile_a, profile_b)
        values = calculate_values_score(profile_a, profile_b)
        lifestyle = calculate_lifestyle_score(profile_a, profile_b)

        assert personality == 0.0
        assert values == 50.0  # 基础分
        assert lifestyle == 50.0  # 默认分

    def test_none_values(self):
        """测试None值"""
        profile_a = {"personality_tags": None, "hobbies": None}
        profile_b = {"personality_tags": ["温柔"], "hobbies": ["旅行"]}

        # 应该不报错
        personality = calculate_personality_score(profile_a, profile_b)
        lifestyle = calculate_lifestyle_score(profile_a, profile_b)

        assert personality == 0.0
        assert lifestyle == 50.0

    def test_large_hobbies_list(self):
        """测试大量爱好"""
        profile_a = {"hobbies": [f"hobby_{i}" for i in range(100)]}
        profile_b = {"hobbies": [f"hobby_{i}" for i in range(50, 150)]}

        score = calculate_lifestyle_score(profile_a, profile_b)
        assert 0 <= score <= 100

    def test_score_range(self):
        """测试所有分数在有效范围内"""
        for _ in range(100):
            import random
            tags_a = random.sample(["温柔", "独立", "上进", "幽默", "阳光", "理性", "感性"], 3)
            tags_b = random.sample(["温柔", "独立", "上进", "幽默", "阳光", "理性", "感性"], 3)

            profile_a = {
                "personality_tags": tags_a,
                "hobbies": random.sample(["旅行", "摄影", "阅读", "音乐", "运动"], 3),
                "city": random.choice(["北京", "上海", "广州"]),
                "education": random.choice(["本科", "硕士", "博士"]),
                "income_range": random.choice(["10-20万", "20-30万", "30-50万"]),
            }
            profile_b = {
                "personality_tags": tags_b,
                "hobbies": random.sample(["旅行", "摄影", "阅读", "音乐", "运动"], 3),
                "city": random.choice(["北京", "上海", "广州"]),
                "education": random.choice(["本科", "硕士", "博士"]),
                "income_range": random.choice(["10-20万", "20-30万", "30-50万"]),
            }

            p_score = calculate_personality_score(profile_a, profile_b)
            v_score = calculate_values_score(profile_a, profile_b)
            l_score = calculate_lifestyle_score(profile_a, profile_b)
            o_score = calculate_overall_score(p_score, v_score, l_score)

            assert 0 <= p_score <= 100
            assert 0 <= v_score <= 100
            assert 0 <= l_score <= 100
            assert 0 <= o_score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
