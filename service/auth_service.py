"""service/auth_service.py — 认证业务层

【设计意图】
  封装认证相关的业务流程。测试层只需要调一个方法就能拿到已认证的 client。
  不需要关心"先 login → 拿 token → set token"这些步骤。

【谁在用这些函数？】
  - conftest.py → creator_client / admin_client / trial_client fixture 调用 login_as()
  - conftest.py → new_user_client fixture 调用 register_and_login()
  - tests/ 层 → 测试 401 场景时调用 create_unauthed_client()

【调用链示例 — 创建一个已认证的 client】
  conftest.py: creator_client fixture
    → login_as("creator")
      → APIClient()                                    # 创建空 client
      → AuthAPI(client).login("creator01", "Aa123456") # 登录拿 token
      → client.set_token(token)                        # 设置 token
    → 返回 (client, user_info)

  之后测试用例通过 fixture 拿到 creator_client，直接调任何 API 都自带认证。
"""

from base import APIClient, assert_success
from api import AuthAPI
from config.settings import TEST_USERS


def login_as(role="creator"):
    """以指定角色登录，返回 (APIClient, user_info)

    这是整个框架最核心的入口函数之一 — 所有需要认证的测试都间接依赖它。

    Args:
        role: "admin" / "creator" / "trial"（对应 settings.py 中的 TEST_USERS）

    Returns:
        (client, user_info)
        - client: 已设置 token 的 APIClient，可直接调任何 API
        - user_info: 用户信息 dict（id, username, plan 等）
    """
    user = TEST_USERS[role]
    client = APIClient()
    auth_api = AuthAPI(client)
    resp = auth_api.login(user["username"], user["password"])
    data = assert_success(resp)
    token = data["data"]["access_token"]
    client.set_token(token)
    return client, data["data"]["user"]


def register_and_login(username, password, email, nickname=None):
    """注册新用户并登录，返回 (APIClient, user_info)

    用于需要全新用户身份的测试（如测试配额从零开始）。

    Args:
        username: 用户名
        password: 密码
        email:    邮箱
        nickname: 昵称（可选）

    Returns:
        (client, user_info) — client 已设置 token
    """
    client = APIClient()
    auth_api = AuthAPI(client)

    # 第 1 步：注册
    resp = auth_api.register(username, password, email, nickname)
    assert_success(resp)

    # 第 2 步：登录
    resp = auth_api.login(username, password)
    data = assert_success(resp)
    token = data["data"]["access_token"]
    client.set_token(token)
    return client, data["data"]["user"]


def create_unauthed_client():
    """创建一个不带 token 的客户端（用于测试未认证场景）

    专门用于测试 401 相关的用例：
      - 未登录访问需要认证的接口
      - 登出后用旧 token 访问

    Returns:
        未设置 token 的 APIClient
    """
    return APIClient()
