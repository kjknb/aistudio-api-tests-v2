"""认证模块接口封装

对应 Mock 的 5 个接口：
  POST /api/v1/auth/register
  POST /api/v1/auth/login
  POST /api/v1/auth/refresh
  POST /api/v1/auth/logout
  GET  /api/v1/user/profile
"""


class AuthAPI:
    def __init__(self, client):
        """
        Args:
            client: APIClient 实例
        """
        self.client = client

    def register(self, username, password, email, nickname=None):
        """用户注册"""
        payload = {
            "username": username,
            "password": password,
            "email": email,
        }
        if nickname:
            payload["nickname"] = nickname
        return self.client.post("/api/v1/auth/register", json=payload)

    def login(self, username, password):
        """用户登录，返回原始 Response"""
        return self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": password,
        })

    def refresh(self, refresh_token):
        """刷新 access_token"""
        return self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })

    def logout(self):
        """退出登录（需要已设置 token）"""
        return self.client.post("/api/v1/auth/logout")

    def get_profile(self):
        """获取当前用户信息"""
        return self.client.get("/api/v1/user/profile")
