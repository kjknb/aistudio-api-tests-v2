"""tests/test_auth.py — 认证模块测试

【测试覆盖】
  TestHealth:       健康检查（BLOCKER 级 — 不过其他测试也不用跑了）
  TestRegister:     注册（正常 + 参数校验 + 冲突）
  TestLogin:        登录（多角色 + 错误凭证 + 缺字段）
  TestRefreshToken: Token 刷新（正常 + 无效 token）
  TestLogout:       登出（登出后 token 应失效）
  TestUserProfile:  用户 Profile（正常 + 未认证）

【Allure 标注体系】
  @allure.epic("AIStudio Mock API")     → 最高层级，标识项目
  @allure.feature("认证模块")            → 模块级
  @allure.story("用户注册")              → 功能点
  @allure.severity(CRITICAL)            → 严重程度
  @allure.title("具体测试标题")           → 报告中显示的标题

【数据驱动示例】
  test_register_invalid 用 @pytest.mark.parametrize + load_yaml 实现：
    - YAML 中定义了 10+ 种非法参数场景
    - 每种场景自动生成一个独立测试用例
    - 新增场景只需改 YAML，不改代码
"""

import allure
import pytest
from base import assert_success, assert_fail, load_yaml
from service import create_unauthed_client
from api import AuthAPI


# ==================== 健康检查 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestHealth:
    @allure.story("健康检查")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("GET /api/health - 健康检查应返回 ok")
    def test_health_check(self, creator_auth_api):
        """健康检查 — 如果这个挂了，其他测试也不用跑了

        验证点：
          - status == "ok"
          - 返回 version、uptime、modules 信息
        """
        resp = creator_auth_api.client.get("/api/health")
        data = assert_success(resp)
        assert data["data"]["status"] == "ok"
        assert "version" in data["data"]
        assert "uptime" in data["data"]
        assert "modules" in data["data"]


# ==================== 注册 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestRegister:
    @allure.story("用户注册")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("正常注册 - 应返回 201")
    def test_register_success(self):
        """正常注册流程

        验证点：
          - HTTP 201
          - 返回 username
          - 不返回 password（安全要求）
        """
        import uuid
        uid = uuid.uuid4().hex[:8]
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register(f"newuser_{uid}", "Test1234", f"newuser_{uid}@example.com", "新用户")
        assert resp.status_code == 201
        data = assert_success(resp)
        assert "username" in data["data"]
        assert "password" not in data["data"]  # 密码不应出现在响应中

    @allure.story("用户注册-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册参数校验 - {case[name]}")
    @pytest.mark.parametrize("case", load_yaml("register_data.yaml")["register_invalid"])
    def test_register_invalid(self, case):
        """数据驱动：各种非法参数注册

        测试数据来自 data/register_data.yaml，覆盖：
          - 缺少必填字段（username/password/email）
          - 用户名长度不合规（太短/太长）
          - 密码强度不足（无大写/无小写/无数字/太短）
          - 邮箱格式错误（缺少@/缺少域名）
        """
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.client.post("/api/v1/auth/register", json=case["data"])
        assert resp.status_code == case["expected_status"]

    @allure.story("用户注册-冲突")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册已存在的用户名 - 应返回 409")
    def test_register_duplicate_username(self):
        """注册已存在的用户名 → 409 Conflict"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register("admin", "Aa123456", "dup@example.com")
        assert_fail(resp, 409)

    @allure.story("用户注册-冲突")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册已存在的邮箱 - 应返回 409")
    def test_register_duplicate_email(self):
        """注册已存在的邮箱 → 409 Conflict"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register("uniquename123", "Aa123456", "admin@aistudio.ai")
        assert_fail(resp, 409)


# ==================== 登录 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestLogin:
    @allure.story("用户登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("正常登录 - 应返回 token 和用户信息")
    def test_login_success(self):
        """creator01 登录 — 验证返回完整 token 信息

        验证点：
          - access_token / refresh_token 都存在
          - token_type == "Bearer"
          - 用户名匹配
          - 计划类型 == "pro"
        """
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("creator01", "Aa123456")
        data = assert_success(resp)
        login_data = data["data"]
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "Bearer"
        assert login_data["user"]["username"] == "creator01"
        assert login_data["user"]["plan"] == "pro"

    @allure.story("用户登录")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("admin 登录 - 应返回 enterprise 计划")
    def test_login_admin(self):
        """admin 登录 — 验证计划类型为 enterprise"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("admin", "Aa123456")
        data = assert_success(resp)
        assert data["data"]["user"]["plan"] == "enterprise"

    @allure.story("用户登录")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("trial_user 登录 - 应返回 free 计划")
    def test_login_trial(self):
        """trial_user 登录 — 验证计划类型为 free"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("trial_user", "Aa123456")
        data = assert_success(resp)
        assert data["data"]["user"]["plan"] == "free"

    @allure.story("用户登录-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("缺少用户名和密码 - 应返回 400")
    def test_login_missing_fields(self):
        """空 body 登录 → 400"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.client.post("/api/v1/auth/login", json={})
        assert_fail(resp, 400)

    @allure.story("用户登录-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("错误的用户名或密码 - 应返回 401")
    def test_login_wrong_credentials(self):
        """错误密码登录 → 401"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("creator01", "WrongPass123")
        assert_fail(resp, 401)


# ==================== Token 刷新 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestRefreshToken:
    @allure.story("刷新Token")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("使用 refresh_token 获取新 access_token")
    def test_refresh_success(self):
        """完整的刷新流程：登录 → 拿 refresh_token → 刷新 → 拿新 access_token"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        # 先登录拿到 refresh_token
        login_resp = auth.login("creator01", "Aa123456")
        login_data = assert_success(login_resp)
        refresh_token = login_data["data"]["refresh_token"]
        # 用 refresh_token 换新的 access_token
        resp = auth.refresh(refresh_token)
        data = assert_success(resp)
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"

    @allure.story("刷新Token")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("无效的 refresh_token - 应返回 401")
    def test_refresh_invalid_token(self):
        """用假的 refresh_token → 401"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.refresh("invalid_token_xyz")
        assert_fail(resp, 401)


# ==================== 登出 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestLogout:
    @allure.story("用户登出")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("正常登出 - Token 应失效")
    def test_logout_success(self):
        """完整的登出验证流程：登录 → 登出 → 用旧 token 访问 → 401

        这个测试体现了"独立 client"的重要性 — 每个测试用独立 client，
        不会污染其他测试的 token 状态。
        """
        # 用独立 client 登录
        client = create_unauthed_client()
        auth = AuthAPI(client)
        login_resp = auth.login("creator01", "Aa123456")
        token = assert_success(login_resp)["data"]["access_token"]
        client.set_token(token)

        # 登出
        resp = auth.logout()
        assert_success(resp)

        # 验证 token 失效 — 再用这个 token 请求 profile 应返回 401
        resp = auth.get_profile()
        assert_fail(resp, 401)


# ==================== 用户 Profile ====================

@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestUserProfile:
    @allure.story("用户信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取用户 profile - 应返回用户信息和配额")
    def test_get_profile(self, creator_auth_api):
        """获取 profile — 验证包含必要字段且不含密码

        验证点：
          - 包含 id, username, nickname, email, plan, quota
          - 不包含 password（安全要求）
        """
        resp = creator_auth_api.get_profile()
        data = assert_success(resp)
        profile = data["data"]
        for field in ("id", "username", "nickname", "email", "plan", "quota"):
            assert field in profile, f"profile 缺少 {field}"
        assert "password" not in profile

    @allure.story("用户信息")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取 profile - 应返回 401")
    def test_get_profile_unauthorized(self):
        """未认证访问 profile → 401"""
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.get_profile()
        assert_fail(resp, 401)
