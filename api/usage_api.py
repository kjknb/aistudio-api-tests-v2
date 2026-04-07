"""api/usage_api.py — 用量统计模块接口封装

【对应接口】
  GET /api/v1/usage/quota  → 获取配额与已用量
  GET /api/v1/usage/stats  → 获取用量统计数据

【不同角色的配额差异】
  admin (enterprise) → dailyTokens=1000000, dailyImages=10000
  creator (pro)      → dailyTokens=100000,  dailyImages=1000
  trial (free)       → dailyTokens=10000,   dailyImages=10

【谁在用这个类？】
  - tests/test_usage.py → 测试配额查询、统计查询、角色差异
  - conftest.py → creator_usage_api fixture
"""

from base import APIClient


class UsageAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def get_quota(self):
        """获取配额与用量

        返回：
          - plan: 用户计划（enterprise/pro/free）
          - quota: 配额信息（dailyTokens, dailyImages, usedTokens, usedImages）
          - usage: 用量统计（today, allTime）

        Returns:
            requests.Response（200 + 配额信息）
        """
        return self.client.get("/api/v1/usage/quota")

    def get_stats(self, period="7d"):
        """获取用量统计

        返回按天统计的用量数据，用于绘制趋势图。

        Args:
            period: 统计周期 "7d" / "30d" / "90d"

        Returns:
            requests.Response（200 + {period, data: [{date, tasks, tokens, images, cost}, ...]}）
        """
        return self.client.get("/api/v1/usage/stats", params={"period": period})
