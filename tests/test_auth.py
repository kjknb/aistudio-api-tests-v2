import allure
import pytest
from base import assert_success, assert_fail, load_yaml
from service import create_unauthed_client
from api import AuthAPI


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestHealth:
    @allure.story("健康检查")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("GET /api/health - 健康检查应返回 ok")
    def test_health_check(self, creator_auth_api):
        resp = creator_auth_api.client.get("/api/health")
        data = assert_success(resp)
        assert data["data"]["status"] == "ok"
        assert "version" in data["data"]
        assert "uptime" in data["data"]
        assert "modules" in data["data"]


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestRegister:
    @allure.story("用户注册")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("正常注册 - 应返回 201")
    def test_register_success(self):
        import uuid
        uid = uuid.uuid4().hex[:8]
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register(f"newuser_{uid}", "Test1234", f"newuser_{uid}@example.com", "新用户")
        assert resp.status_code == 201
        data = assert_success(resp)
        assert "username" in data["data"]
        assert "password" not in data["data"]

    @allure.story("用户注册-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册参数校验 - {case[name]}")
    @pytest.mark.parametrize("case", load_yaml("register_data.yaml")["register_invalid"])
    def test_register_invalid(self, case):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.client.post("/api/v1/auth/register", json=case["data"])
        assert resp.status_code == case["expected_status"]

    @allure.story("用户注册-冲突")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册已存在的用户名 - 应返回 409")
    def test_register_duplicate_username(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register("admin", "Aa123456", "dup@example.com")
        assert_fail(resp, 409)

    @allure.story("用户注册-冲突")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("注册已存在的邮箱 - 应返回 409")
    def test_register_duplicate_email(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.register("uniquename123", "Aa123456", "admin@aistudio.ai")
        assert_fail(resp, 409)


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestLogin:
    @allure.story("用户登录")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("正常登录 - 应返回 token 和用户信息")
    def test_login_success(self):
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
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("admin", "Aa123456")
        data = assert_success(resp)
        assert data["data"]["user"]["plan"] == "enterprise"

    @allure.story("用户登录")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("trial_user 登录 - 应返回 free 计划")
    def test_login_trial(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("trial_user", "Aa123456")
        data = assert_success(resp)
        assert data["data"]["user"]["plan"] == "free"

    @allure.story("用户登录-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("缺少用户名和密码 - 应返回 400")
    def test_login_missing_fields(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.client.post("/api/v1/auth/login", json={})
        assert_fail(resp, 400)

    @allure.story("用户登录-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("错误的用户名或密码 - 应返回 401")
    def test_login_wrong_credentials(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.login("creator01", "WrongPass123")
        assert_fail(resp, 401)


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestRefreshToken:
    @allure.story("刷新Token")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("使用 refresh_token 获取新 access_token")
    def test_refresh_success(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        # 先登录
        login_resp = auth.login("creator01", "Aa123456")
        login_data = assert_success(login_resp)
        refresh_token = login_data["data"]["refresh_token"]
        # 刷新
        resp = auth.refresh(refresh_token)
        data = assert_success(resp)
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"

    @allure.story("刷新Token")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("无效的 refresh_token - 应返回 401")
    def test_refresh_invalid_token(self):
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.refresh("invalid_token_xyz")
        assert_fail(resp, 401)


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestLogout:
    @allure.story("用户登出")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("正常登出 - Token 应失效")
    def test_logout_success(self):
        # 用独立 client 登录→登出→验证失效
        client = create_unauthed_client()
        auth = AuthAPI(client)
        login_resp = auth.login("creator01", "Aa123456")
        token = assert_success(login_resp)["data"]["access_token"]
        client.set_token(token)

        # 登出
        resp = auth.logout()
        assert_success(resp)

        # 验证 token 失效
        resp = auth.get_profile()
        assert_fail(resp, 401)


@allure.epic("AIStudio Mock API")
@allure.feature("认证模块")
class TestUserProfile:
    @allure.story("用户信息")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取用户 profile - 应返回用户信息和配额")
    def test_get_profile(self, creator_auth_api):
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
        client = create_unauthed_client()
        auth = AuthAPI(client)
        resp = auth.get_profile()
        assert_fail(resp, 401)
