"""全局 Fixtures

每个角色独立一个 APIClient 实例，互不干扰。
"""
import uuid
import pytest
from service import login_as, create_unauthed_client
from service.task_service import TaskService
from service.project_service import ProjectService
from api import AuthAPI, ModelAPI, ProjectAPI, TaskAPI, ChatAPI, UsageAPI


# ==================== 角色 Client（session 级别，各角色独立） ====================

@pytest.fixture(scope="session")
def creator_client():
    """creator01 登录，返回独立的 APIClient"""
    client, user = login_as("creator")
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def admin_client():
    """admin 登录，返回独立的 APIClient"""
    client, user = login_as("admin")
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def trial_client():
    """trial_user 登录，返回独立的 APIClient"""
    client, user = login_as("trial")
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def unauthed_client():
    """未认证客户端（用于 401 场景）"""
    client = create_unauthed_client()
    yield client
    client.session.close()


# ==================== API 层 Fixture（直接拿封装好的 API 对象） ====================

@pytest.fixture(scope="session")
def creator_auth_api(creator_client):
    return AuthAPI(creator_client)


@pytest.fixture(scope="session")
def creator_model_api(creator_client):
    return ModelAPI(creator_client)


@pytest.fixture(scope="session")
def creator_project_api(creator_client):
    return ProjectAPI(creator_client)


@pytest.fixture(scope="session")
def creator_task_api(creator_client):
    return TaskAPI(creator_client)


@pytest.fixture(scope="session")
def creator_chat_api(creator_client):
    return ChatAPI(creator_client)


@pytest.fixture(scope="session")
def creator_usage_api(creator_client):
    return UsageAPI(creator_client)


# ==================== 业务层 Fixture ====================

@pytest.fixture(scope="session")
def creator_task_service(creator_client):
    return TaskService(creator_client)


@pytest.fixture(scope="session")
def creator_project_service(creator_client):
    return ProjectService(creator_client)


# ==================== 测试数据 Fixture ====================

@pytest.fixture
def new_user_client():
    """注册一个新用户并返回已登录的 client（每次调用生成新用户）"""
    uid = uuid.uuid4().hex[:8]
    client, user = register_and_login(
        f"testuser_{uid}", "Test1234", f"test_{uid}@example.com", f"测试用户{uid}"
    )
    yield client
    client.session.close()


@pytest.fixture
def temp_project(creator_project_api):
    """创建一个临时项目，测试后自动清理"""
    resp = creator_project_api.create("自动化测试项目", "由测试框架自动创建")
    from base import assert_success
    data = assert_success(resp)
    project = data["data"]
    yield project
    # 清理
    try:
        creator_project_api.delete(project["id"])
    except Exception:
        pass
