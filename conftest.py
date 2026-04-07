"""conftest.py — 全局 Fixtures

【设计意图】
  pytest 的 fixture 是"测试的准备工作" — 在测试运行前创建好需要的对象。
  conftest.py 里的 fixture 自动被所有测试发现，不需要 import。

【Fixture 层级】
  scope="session" → 整个测试进程只执行一次（适合登录，避免重复请求）
  scope="function" → 每个测试方法执行一次（适合临时数据，保证隔离）

【Fixture 依赖关系图】
  login_as("creator")
    └→ creator_client ─┬→ creator_auth_api
                       ├→ creator_model_api
                       ├→ creator_project_api
                       ├→ creator_task_api
                       ├→ creator_chat_api
                       ├→ creator_usage_api
                       ├→ creator_task_service
                       └→ creator_project_service

  login_as("admin")    → admin_client（直接在测试中用）
  login_as("trial")    → trial_client（直接在测试中用）
  create_unauthed_client() → unauthed_client（测 401 场景）
  register_and_login()     → new_user_client（每次新用户，function 级）
  creator_project_api.create() → temp_project（自动清理）

【为什么 API fixture 依赖 client fixture？】
  因为每个 API 类（AuthAPI, ModelAPI 等）的构造函数都接收 APIClient。
  这样所有 API 共享同一个 HTTP 连接和 token，不需要重复登录。
"""

import uuid
import pytest
from service import login_as, create_unauthed_client
from service.task_service import TaskService
from service.project_service import ProjectService
from api import AuthAPI, ModelAPI, ProjectAPI, TaskAPI, ChatAPI, UsageAPI


# ==================== 角色 Client（session 级别，各角色独立） ====================
# 每个角色一个独立的 APIClient，互不干扰。
# scope="session" 意味着整个测试进程只登录一次，后续复用。

@pytest.fixture(scope="session")
def creator_client():
    """creator01 登录，返回独立的 APIClient

    这是使用最多的 fixture — 大部分测试用例都通过它间接获取 API 对象。
    """
    client, user = login_as("creator")
    yield client           # yield 之前是 setup，之后是 teardown
    client.session.close() # teardown：关闭 HTTP 连接


@pytest.fixture(scope="session")
def admin_client():
    """admin 登录，返回独立的 APIClient

    用于测试管理员权限的场景（如查询他人任务应返回 404）。
    """
    client, user = login_as("admin")
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def trial_client():
    """trial_user 登录，返回独立的 APIClient

    用于测试 free 用户的配额限制。
    """
    client, user = login_as("trial")
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def unauthed_client():
    """未认证客户端（用于 401 场景）

    不设置 token，专门用于测试：
      - 未登录访问需要认证的接口
      - 验证接口确实要求认证
    """
    client = create_unauthed_client()
    yield client
    client.session.close()


# ==================== API 层 Fixture（直接拿封装好的 API 对象） ====================
# 这些 fixture 在 client 的基础上创建 API 对象。
# 测试用例通过参数注入直接拿到 API 对象，不需要自己创建。
#
# 命名规则：{角色}_{模块}_api
# 例如：creator_auth_api = AuthAPI(creator_client)

@pytest.fixture(scope="session")
def creator_auth_api(creator_client):
    """认证 API 对象（已用 creator01 的 token）"""
    return AuthAPI(creator_client)


@pytest.fixture(scope="session")
def creator_model_api(creator_client):
    """模型 API 对象"""
    return ModelAPI(creator_client)


@pytest.fixture(scope="session")
def creator_project_api(creator_client):
    """项目 API 对象"""
    return ProjectAPI(creator_client)


@pytest.fixture(scope="session")
def creator_task_api(creator_client):
    """任务 API 对象"""
    return TaskAPI(creator_client)


@pytest.fixture(scope="session")
def creator_chat_api(creator_client):
    """聊天 API 对象"""
    return ChatAPI(creator_client)


@pytest.fixture(scope="session")
def creator_usage_api(creator_client):
    """用量 API 对象"""
    return UsageAPI(creator_client)


# ==================== 业务层 Fixture ====================
# 业务层 fixture 封装了更复杂的流程（如提交+轮询）。
# 测试用例需要测试组合流程时使用。

@pytest.fixture(scope="session")
def creator_task_service(creator_client):
    """任务业务层（提交+轮询+拿结果）"""
    return TaskService(creator_client)


@pytest.fixture(scope="session")
def creator_project_service(creator_client):
    """项目业务层（创建项目+提交任务+清理）"""
    return ProjectService(creator_client)


# ==================== 测试数据 Fixture ====================
# 这些是 function 级 fixture — 每个测试方法都会创建新的实例。
# 用于需要数据隔离的场景（避免测试间互相影响）。

@pytest.fixture
def new_user_client():
    """注册一个新用户并返回已登录的 client（每次调用生成新用户）

    每次调用都会生成一个唯一用户名（用 uuid），确保不会冲突。
    用于测试新用户的配额、权限等场景。

    注意：scope 是 function（默认），每个测试方法都会注册一个新用户。
    """
    uid = uuid.uuid4().hex[:8]
    client, user = register_and_login(
        f"testuser_{uid}", "Test1234", f"test_{uid}@example.com", f"测试用户{uid}"
    )
    yield client
    client.session.close()


@pytest.fixture
def temp_project(creator_project_api):
    """创建一个临时项目，测试后自动清理

    使用流程：
      1. setup：创建项目
      2. yield 项目信息给测试用例
      3. teardown：删除项目（用 try/except 防止清理失败影响测试结果）

    用法：
      def test_something(temp_project):
          project_id = temp_project["id"]
          # ... 测试逻辑 ...
    """
    resp = creator_project_api.create("自动化测试项目", "由测试框架自动创建")
    from base import assert_success
    data = assert_success(resp)
    project = data["data"]
    yield project
    # teardown：清理
    try:
        creator_project_api.delete(project["id"])
    except Exception:
        pass
