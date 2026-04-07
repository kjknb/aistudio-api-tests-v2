"""api/task_api.py — 任务/生成模块接口封装

【对应接口】
  POST   /api/v1/generate/text       → 提交文本生成任务
  POST   /api/v1/generate/image      → 提交图片生成任务
  GET    /api/v1/tasks/{taskId}       → 查询任务状态
  GET    /api/v1/tasks                → 任务列表（支持筛选和分页）
  PUT    /api/v1/tasks/{taskId}/cancel → 取消任务
  DELETE /api/v1/tasks/{taskId}       → 删除任务

【异步任务流程】
  1. 调用 submit_text/submit_image → 返回 202 + taskId
  2. 轮询 GET /api/v1/tasks/{taskId} → 直到 status 变为 completed/failed
  3. 从响应的 result 字段拿生成结果

【谁在用这个类？】
  - service/task_service.py → submit_and_wait_text/image() 组合了提交+轮询
  - tests/test_tasks.py → 测试生成、查询、取消、删除
  - conftest.py → creator_task_api fixture
"""

from base import APIClient


class TaskAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def submit_text(self, model_id, prompt, parameters=None, project_id=None):
        """提交文本生成任务

        这是异步接口 — 返回 202 + taskId，需要后续轮询获取结果。

        Args:
            model_id:    模型 ID（如 "m_text_01"）
            prompt:      生成提示词
            parameters:  可选参数（temperature, max_tokens 等）
            project_id:  可选，归到某个项目下

        Returns:
            requests.Response（202 + {taskId, status: "processing"}）
        """
        payload = {
            "modelId": model_id,
            "prompt": prompt,
        }
        if parameters:
            payload["parameters"] = parameters
        if project_id:
            payload["projectId"] = project_id
        return self.client.post("/api/v1/generate/text", json=payload)

    def submit_image(self, model_id, prompt, parameters=None, project_id=None):
        """提交图片生成任务

        和 submit_text 类似，但是调用图片生成接口。
        parameters 可以传 size、quality、style 等图片相关参数。

        Args:
            model_id:    图片模型 ID（如 "m_img_01"）
            prompt:      图片描述
            parameters:  可选参数（size, quality, style 等）
            project_id:  可选，归到某个项目下

        Returns:
            requests.Response（202 + {taskId, status: "processing"}）
        """
        payload = {
            "modelId": model_id,
            "prompt": prompt,
        }
        if parameters:
            payload["parameters"] = parameters
        if project_id:
            payload["projectId"] = project_id
        return self.client.post("/api/v1/generate/image", json=payload)

    def get_task(self, task_id):
        """查询任务状态（轮询接口）

        任务状态流转：processing → completed / failed / cancelled

        Args:
            task_id: 任务 ID（由 submit_text/submit_image 返回）

        Returns:
            requests.Response（200 + 任务详情，包含 status、progress、result 等）
        """
        return self.client.get(f"/api/v1/tasks/{task_id}")

    def list_tasks(self, page=1, pageSize=10, status=None, type=None, project_id=None):
        """获取任务列表，支持筛选

        Args:
            page:        页码
            pageSize:    每页数量
            status:      按状态筛选 ("processing"/"completed"/"failed"/"cancelled")
            type:        按类型筛选 ("text"/"image")
            project_id:  按项目筛选

        Returns:
            requests.Response（200 + 分页的任务列表）
        """
        params = {"page": page, "pageSize": pageSize}
        if status:
            params["status"] = status
        if type:
            params["type"] = type
        if project_id:
            params["projectId"] = project_id
        return self.client.get("/api/v1/tasks", params=params)

    def cancel(self, task_id):
        """取消任务

        只能取消 processing 中的任务。
        已完成的任务取消会返回 400。

        Args:
            task_id: 任务 ID

        Returns:
            requests.Response（200 + {status: "cancelled"}，400 如果已完成）
        """
        return self.client.put(f"/api/v1/tasks/{task_id}/cancel")

    def delete(self, task_id):
        """删除任务

        建议先完成或取消任务再删除。

        Args:
            task_id: 任务 ID

        Returns:
            requests.Response（200 表示成功，404 如果不存在）
        """
        return self.client.delete(f"/api/v1/tasks/{task_id}")
