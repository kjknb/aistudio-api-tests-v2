"""任务/生成模块接口封装

对应 Mock 的 6 个接口：
  POST   /api/v1/generate/text
  POST   /api/v1/generate/image
  GET    /api/v1/tasks/:id
  GET    /api/v1/tasks
  PUT    /api/v1/tasks/:id/cancel
  DELETE /api/v1/tasks/:id
"""


class TaskAPI:
    def __init__(self, client):
        self.client = client

    def submit_text(self, model_id, prompt, parameters=None, project_id=None):
        """提交文本生成任务"""
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
        """提交图像生成任务"""
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
        """查询任务状态（轮询接口）"""
        return self.client.get(f"/api/v1/tasks/{task_id}")

    def list_tasks(self, page=1, pageSize=10, status=None, type=None, project_id=None):
        """获取任务列表，支持筛选"""
        params = {"page": page, "pageSize": pageSize}
        if status:
            params["status"] = status
        if type:
            params["type"] = type
        if project_id:
            params["projectId"] = project_id
        return self.client.get("/api/v1/tasks", params=params)

    def cancel(self, task_id):
        """取消任务"""
        return self.client.put(f"/api/v1/tasks/{task_id}/cancel")

    def delete(self, task_id):
        """删除任务"""
        return self.client.delete(f"/api/v1/tasks/{task_id}")
