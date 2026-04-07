"""tests/test_usage.py — 用量统计模块测试

【测试覆盖】
  TestUsageQuota:  用量配额（creator/admin/trial 各角色 + 未认证）
  TestUsageStats:  用量统计（7d/30d/90d + 未认证）

【测试价值】
  这个模块的测试重点是"不同角色看到不同配额" — 验证权限隔离正确。
  admin 应该看到 enterprise 级配额，trial 应该看到 free 级配额。
"""

import allure
import pytest
from base import assert_success, assert_fail
from api import UsageAPI
from service import create_unauthed_client


# ==================== 用量配额 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("用量统计模块")
class TestUsageQuota:
    @allure.story("用量配额")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取用量配额 - 应返回 plan、quota、usage")
    def test_get_quota(self, creator_usage_api):
        """creator01 的配额 — 验证返回 plan、quota、usage 三层结构

        响应结构：
          {
            "plan": "pro",
            "quota": {dailyTokens, dailyImages, usedTokens, usedImages},
            "usage": {today: {...}, allTime: {...}}
          }
        """
        resp = creator_usage_api.get_quota()
        data = assert_success(resp)
        quota = data["data"]
        assert "plan" in quota
        assert "quota" in quota
        for field in ("dailyTokens", "dailyImages", "usedTokens", "usedImages"):
            assert field in quota["quota"]
        assert "usage" in quota
        assert "today" in quota["usage"]
        assert "allTime" in quota["usage"]

    @allure.story("用量配额")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("admin 的配额应为 enterprise 级别")
    def test_get_quota_admin(self, admin_client):
        """admin 的配额 — 验证 enterprise 级配额（100万 token/天）"""
        api = UsageAPI(admin_client)
        resp = api.get_quota()
        data = assert_success(resp)
        assert data["data"]["plan"] == "enterprise"
        assert data["data"]["quota"]["dailyTokens"] == 1000000

    @allure.story("用量配额")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("trial_user 的配额应为 free 级别")
    def test_get_quota_trial(self, trial_client):
        """trial_user 的配额 — 验证 free 级配额（1万 token/天）"""
        api = UsageAPI(trial_client)
        resp = api.get_quota()
        data = assert_success(resp)
        assert data["data"]["plan"] == "free"
        assert data["data"]["quota"]["dailyTokens"] == 10000

    @allure.story("用量配额")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取配额 - 应返回 401")
    def test_get_quota_unauthorized(self):
        """未认证获取配额 → 401"""
        client = create_unauthed_client()
        api = UsageAPI(client)
        resp = api.get_quota()
        assert_fail(resp, 401)


# ==================== 用量统计 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("用量统计模块")
class TestUsageStats:
    @allure.story("用量统计")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取 7 天统计 - 默认参数")
    def test_get_stats_7d(self, creator_usage_api):
        """7 天统计 — 验证返回 7 天数据，每天包含 tasks/tokens/images/cost"""
        resp = creator_usage_api.get_stats()
        data = assert_success(resp)
        stats = data["data"]
        assert stats["period"] == "7d"
        assert len(stats["data"]) == 7
        for day in stats["data"]:
            for field in ("date", "tasks", "tokens", "images", "cost"):
                assert field in day

    @allure.story("用量统计")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取 30 天统计")
    def test_get_stats_30d(self, creator_usage_api):
        """30 天统计 — 验证返回 30 天数据"""
        resp = creator_usage_api.get_stats(period="30d")
        data = assert_success(resp)
        assert data["data"]["period"] == "30d"
        assert len(data["data"]["data"]) == 30

    @allure.story("用量统计")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取 90 天统计")
    def test_get_stats_90d(self, creator_usage_api):
        """90 天统计 — 验证返回 90 天数据"""
        resp = creator_usage_api.get_stats(period="90d")
        data = assert_success(resp)
        assert data["data"]["period"] == "90d"
        assert len(data["data"]["data"]) == 90

    @allure.story("用量统计")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取统计 - 应返回 401")
    def test_get_stats_unauthorized(self):
        """未认证获取统计 → 401"""
        client = create_unauthed_client()
        api = UsageAPI(client)
        resp = api.get_stats()
        assert_fail(resp, 401)
