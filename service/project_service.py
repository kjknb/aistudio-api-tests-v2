"""项目业务层

封装"创建项目→在项目下提交任务→清理项目"等组合流程。
"""
from base import assert_success
from api import ProjectAPI, TaskAPI


class ProjectService:
    def __init__(self, client):
        self.project_api = ProjectAPI(client)
        self.task_api = TaskAPI(client)

    def create_project(self, name, description=None):
        """创建项目并返回项目信息"""
        resp = self.project_api.create(name, description)
        data = assert_success(resp)
        return data["data"]

    def create_project_with_task(self, name, model_id, prompt,
                                 parameters=None, description=None):
        """创建项目并在项目下提交一个文本任务"""
        project = self.create_project(name, description)
        resp = self.task_api.submit_text(
            model_id, prompt, parameters, project_id=project["id"]
        )
        task_data = assert_success(resp)
        return project, task_data["data"]

    def cleanup_project(self, project_id):
        """删除项目（清理用）"""
        try:
            self.project_api.delete(project_id)
        except Exception:
            pass
