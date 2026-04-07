"""api/__init__.py — 接口层统一导出

【设计意图】
  和 base/__init__.py 类似，统一 API 类的导出入口。
  其他模块直接 from api import AuthAPI, ModelAPI 即可。

【各 API 类对应关系】
  AuthAPI   → /api/v1/auth/*       → 认证模块
  ModelAPI  → /api/v1/models/*     → 模型模块
  ProjectAPI→ /api/v1/projects/*   → 项目模块
  TaskAPI   → /api/v1/tasks/*, /api/v1/generate/*  → 任务/生成模块
  ChatAPI   → /api/v1/chat/*       → 聊天模块
  UsageAPI  → /api/v1/usage/*      → 用量统计模块

【所有 API 类的共同点】
  1. 构造函数都接收一个 APIClient 实例
  2. 方法都返回 requests.Response 对象
  3. 不做断言 — 断言留给 tests/ 层
"""

from .auth_api import AuthAPI
from .model_api import ModelAPI
from .project_api import ProjectAPI
from .task_api import TaskAPI
from .chat_api import ChatAPI
from .usage_api import UsageAPI
