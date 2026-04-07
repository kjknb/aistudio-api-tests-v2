"""用量统计模块接口封装

对应 Mock 的 2 个接口：
  GET /api/v1/usage/quota
  GET /api/v1/usage/stats
"""


class UsageAPI:
    def __init__(self, client):
        self.client = client

    def get_quota(self):
        """获取配额与用量"""
        return self.client.get("/api/v1/usage/quota")

    def get_stats(self, period="7d"):
        """获取用量统计

        Args:
            period: "7d" / "30d" / "90d"
        """
        return self.client.get("/api/v1/usage/stats", params={"period": period})
