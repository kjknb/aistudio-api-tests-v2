"""service/project_service.py — 项目业务层

【设计意图】
  封装"创建项目 → 在项目下提交任务 → 清理项目"等组合流程。
  测试层只需要调一个方法，不需要手动编排多步操作。

【谁在用这个类？】
  - conftest.py → creator_project_service fixture
  - tests/test_projects.py → 测试项目+任务的组合场景

【调用链示例 — 创建项目并在项目下提交任务】
  test_create_project_with_task()
    → ProjectService.create_project_with_task("测试项目", "m_text_01", "写首诗")
      → ProjectAPI.create("测试项目")          # 创建项目
      → TaskAPI.submit_text("m_text_01", "写一首诗", project_id=project["id"])
                                             # 在项目下提交任务
    → 返回 (project, task)
"""

from base import assert_success
from api import ProjectAPI, TaskAPI


class ProjectService:
    def __init__(self, client):
        """接收已认证的 APIClient

        Args:
            client: 已设置 token 的 APIClient（由 login_as() 创建）
        """
        self.project_api = ProjectAPI(client)
        self.task_api = TaskAPI(client)

    def create_project(self, name, description=None):
        """创建项目并返回项目信息

        Args:
            name:        项目名称
            description: 项目描述（可选）

        Returns:
            项目信息 dict（包含 id, name, description 等）
        """
        resp = self.project_api.create(name, description)
        data = assert_success(resp)
        return data["data"]

    def create_project_with_task(self, name, model_id, prompt,
                                 parameters=None, description=None):
        """创建项目并在项目下提交一个文本任务

        一步完成"建项目 + 提交任务"两个操作。

        Args:
            name:        项目名称
            model_id:    模型 ID
            prompt:      生成提示词
            parameters:  可选参数
            description: 项目描述（可选）

        Returns:
            (project, task) — 项目信息和任务信息
        """
        project = self.create_project(name, description)
        resp = self.task_api.submit_text(
            model_id, prompt, parameters, project_id=project["id"]
        )
        task_data = assert_success(resp)
        return project, task_data["data"]

    def cleanup_project(self, project_id):
        """删除项目（清理用，通常在 fixture 的 teardown 中调用）

        用 try/except 包裹，避免清理失败影响测试结果。

        Args:
            project_id: 要删除的项目 ID
        """
        try:
            self.project_api.delete(project_id)
        except Exception:
            pass
