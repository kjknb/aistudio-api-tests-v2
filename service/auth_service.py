"""认证业务层

封装认证相关的业务流程，测试层直接调用一个方法拿到可用的 client。
"""
from base import APIClient, assert_success
from api import AuthAPI
from config.settings import TEST_USERS


def login_as(role="creator"):
    """以指定角色登录，返回 (APIClient, user_info)

    Args:
        role: "admin" / "creator" / "trial"

    Returns:
        (client, user_info) — client 已设置 token，可直接调用任何 api/
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
    """注册新用户并登录，返回 (APIClient, user_info)"""
    client = APIClient()
    auth_api = AuthAPI(client)

    # 注册
    resp = auth_api.register(username, password, email, nickname)
    assert_success(resp)

    # 登录
    resp = auth_api.login(username, password)
    data = assert_success(resp)
    token = data["data"]["access_token"]
    client.set_token(token)
    return client, data["data"]["user"]


def create_unauthed_client():
    """创建一个不带 token 的客户端（用于测试未认证场景）"""
    return APIClient()
