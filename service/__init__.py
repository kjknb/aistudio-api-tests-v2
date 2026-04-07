"""service/__init__.py — 业务层统一导出

【设计意图】
  方便其他模块直接 from service import login_as, TaskService 等。
  业务层的核心价值：把多个 API 调用组合成一个业务流程，让测试层不用写样板代码。
"""

from .auth_service import login_as, register_and_login, create_unauthed_client
from .task_service import TaskService
from .project_service import ProjectService
