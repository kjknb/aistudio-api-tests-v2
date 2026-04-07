"""api/auth_api.py — 认证模块接口封装

【对应接口】
  POST /api/v1/auth/register  → 注册新用户
  POST /api/v1/auth/login     → 登录，返回 access_token + refresh_token
  POST /api/v1/auth/refresh   → 用 refresh_token 换新的 access_token
  POST /api/v1/auth/logout    → 登出，使当前 token 失效
  GET  /api/v1/auth/profile   → 获取当前用户信息（需要认证）

【谁在用这个类？】
  - service/auth_service.py → login_as() 调用 login()，register_and_login() 调用 register() + login()
  - tests/test_auth.py → 直接调用各种方法测试认证流程

【调用链示例 — 登录流程】
  test_login_success()
    → AuthAPI.login("creator01", "Aa123456")        # 本类的方法
      → APIClient.post("/api/v1/auth/login", json={...})  # base 层发请求
    → assert_success(resp)                            # 验证响应
"""

from base import APIClient


class AuthAPI:
    def __init__(self, client: APIClient):
        """接收一个 APIClient 实例，后续所有请求都通过它发

        Args:
            client: APIClient 实例（可带 token 也可不带）
        """
        self.client = client

    def register(self, username, password, email, nickname=None):
        """注册新用户

        Args:
            username: 用户名（3-20 字符）
            password: 密码（需包含大小写字母和数字，至少 8 位）
            email:    邮箱
            nickname: 昵称（可选）

        Returns:
            requests.Response（201 表示成功）
        """
        payload = {
            "username": username,
            "password": password,
            "email": email,
        }
        if nickname:
            payload["nickname"] = nickname
        return self.client.post("/api/v1/auth/register", json=payload)

    def login(self, username, password):
        """登录

        返回的 data 包含：
          - access_token:  用于后续请求的 Bearer Token
          - refresh_token: 用于刷新 access_token
          - token_type:    "Bearer"
          - user:          用户信息（id, username, plan 等）

        Args:
            username: 用户名
            password: 密码

        Returns:
            requests.Response（200 + 包含 token 的 body）
        """
        return self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": password,
        })

    def refresh(self, refresh_token):
        """刷新 access_token

        当 access_token 过期时，用 refresh_token 获取新的。
        注意：这个接口不需要 Authorization header。

        Args:
            refresh_token: 登录时返回的 refresh_token

        Returns:
            requests.Response（200 + 新的 access_token）
        """
        return self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })

    def logout(self):
        """登出 — 使当前 token 失效

        需要先通过 client.set_token() 设置 token。
        登出后用同一个 token 请求其他接口应该返回 401。

        Returns:
            requests.Response（200 表示成功）
        """
        return self.client.post("/api/v1/auth/logout")

    def get_profile(self):
        """获取当前登录用户的 profile

        返回用户信息 + 配额信息。
        需要认证 — 未设置 token 时返回 401。

        Returns:
            requests.Response（200 + 用户信息）
        """
        return self.client.get("/api/v1/auth/profile")
