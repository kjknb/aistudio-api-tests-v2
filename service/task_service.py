"""service/task_service.py — 任务业务层

【设计意图】
  封装"提交任务 → 轮询 → 拿结果"的完整流程。
  测试层不需要写轮询循环 — 调一个方法就能拿到最终结果。

【核心价值】
  如果没有这个 service，测试代码要这样写：
    resp = task_api.submit_text(...)
    task_id = resp.json()["data"]["taskId"]
    while True:
        resp = task_api.get_task(task_id)
        if resp.json()["data"]["status"] == "completed":
            break
        time.sleep(1)

  有了 TaskService，只需要：
    task = task_service.submit_and_wait_text(...)

【谁在用这个类？】
  - conftest.py → creator_task_service fixture
  - tests/test_tasks.py → test_poll_task_to_completion, test_delete_completed_task

【调用链示例 — 提交并等待文本生成完成】
  test_poll_task_to_completion()
    → TaskService.submit_and_wait_text("m_text_01", "介绍Python")
      → TaskAPI.submit_text("m_text_01", "介绍Python")  # POST /api/v1/generate/text
        → APIClient.post()                                # 发请求
      → wait_for_task(client, task_id)                    # 轮询 GET /api/v1/tasks/{id}
        → while status != "completed": sleep(1)           # 每秒检查一次
      → 返回任务详情 dict（status="completed", result={...}）
    → assert task["status"] == "completed"
"""

from base import assert_success
from base.helpers import wait_for_task
from api import TaskAPI


class TaskService:
    def __init__(self, client):
        """接收已认证的 APIClient

        Args:
            client: 已设置 token 的 APIClient
        """
        self.api = TaskAPI(client)

    def submit_and_wait_text(self, model_id, prompt, parameters=None,
                             project_id=None, timeout=15):
        """提交文本任务并等待完成，返回任务详情

        这是最常用的方法 — 测试层不需要关心轮询逻辑。

        Args:
            model_id:    模型 ID
            prompt:      生成提示词
            parameters:  可选参数
            project_id:  可选，归到某个项目下
            timeout:     超时秒数，默认 15

        Returns:
            任务详情 dict（status="completed", result={...}）
        """
        resp = self.api.submit_text(model_id, prompt, parameters, project_id)
        data = assert_success(resp)
        task_id = data["data"]["taskId"]
        return wait_for_task(self.api.client, task_id, timeout=timeout)

    def submit_and_wait_image(self, model_id, prompt, parameters=None,
                              project_id=None, timeout=30):
        """提交图片任务并等待完成，返回任务详情

        图片生成通常比文本慢，所以默认 timeout=30 秒。

        Args:
            model_id:    图片模型 ID
            prompt:      图片描述
            parameters:  可选参数（size, quality, style）
            project_id:  可选，归到某个项目下
            timeout:     超时秒数，默认 30

        Returns:
            任务详情 dict（status="completed", result={...}）
        """
        resp = self.api.submit_image(model_id, prompt, parameters, project_id)
        data = assert_success(resp)
        task_id = data["data"]["taskId"]
        return wait_for_task(self.api.client, task_id, timeout=timeout)
