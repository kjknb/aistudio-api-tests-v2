"""模型模块接口封装

对应 Mock 的 3 个接口：
  GET /api/v1/models
  GET /api/v1/models/:id
  GET /api/v1/models/:id/status
"""


class ModelAPI:
    def __init__(self, client):
        self.client = client

    def list_models(self, type=None, provider=None, status=None, tags=None):
        """获取模型列表，支持筛选"""
        params = {}
        if type:
            params["type"] = type
        if provider:
            params["provider"] = provider
        if status:
            params["status"] = status
        if tags:
            params["tags"] = tags
        return self.client.get("/api/v1/models", params=params or None)

    def get_model(self, model_id):
        """获取模型详情（含参数 schema）"""
        return self.client.get(f"/api/v1/models/{model_id}")

    def get_model_status(self, model_id):
        """获取模型可用性"""
        return self.client.get(f"/api/v1/models/{model_id}/status")
