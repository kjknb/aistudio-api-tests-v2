"""任务业务层

封装"提交任务→轮询→拿结果"的完整流程，测试层不需要写轮询循环。
"""
from base import assert_success
from base.helpers import wait_for_task
from api import TaskAPI


class TaskService:
    def __init__(self, client):
        self.api = TaskAPI(client)

    def submit_and_wait_text(self, model_id, prompt, parameters=None,
                             project_id=None, timeout=15):
        """提交文本任务并等待完成，返回任务详情"""
        resp = self.api.submit_text(model_id, prompt, parameters, project_id)
        data = assert_success(resp)
        task_id = data["data"]["taskId"]
        return wait_for_task(self.api.client, task_id, timeout=timeout)

    def submit_and_wait_image(self, model_id, prompt, parameters=None,
                              project_id=None, timeout=30):
        """提交图像任务并等待完成，返回任务详情"""
        resp = self.api.submit_image(model_id, prompt, parameters, project_id)
        data = assert_success(resp)
        task_id = data["data"]["taskId"]
        return wait_for_task(self.api.client, task_id, timeout=timeout)
