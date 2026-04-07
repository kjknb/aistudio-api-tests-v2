"""api/model_api.py — 模型模块接口封装

【对应接口】
  GET /api/v1/models              → 模型列表（支持筛选）
  GET /api/v1/models/{modelId}    → 模型详情
  GET /api/v1/models/{modelId}/status → 模型实时状态

【筛选参数】
  list_models() 支持的筛选条件：
    type=text|image    → 按类型筛选
    provider=OpenAI    → 按供应商筛选
    status=active      → 按状态筛选
    tags=文本,编程      → 按标签筛选（逗号分隔）

【谁在用这个类？】
  - tests/test_models.py → 测试模型列表、详情、状态
  - conftest.py → creator_model_api fixture
"""

from base import APIClient


class ModelAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def list_models(self, type=None, provider=None, status=None, tags=None):
        """获取模型列表，支持筛选

        筛选参数都是可选的，不传则返回全部模型。

        Args:
            type:     按类型筛选 ("text" / "image")
            provider: 按供应商筛选 ("OpenAI" / "Anthropic" / ...)
            status:   按状态筛选 ("active" / "maintenance" / ...)
            tags:     按标签筛选 ("文本,编程" 逗号分隔)

        Returns:
            requests.Response（200 + 模型列表）
        """
        params = {}
        if type:
            params["type"] = type
        if provider:
            params["provider"] = provider
        if status:
            params["status"] = status
        if tags:
            params["tags"] = tags
        return self.client.get("/api/v1/models", params=params)

    def get_model(self, model_id):
        """获取模型详情

        返回模型的完整信息：名称、供应商、类型、定价、参数配置等。

        Args:
            model_id: 模型 ID（如 "m_text_01"）

        Returns:
            requests.Response（200 + 模型详情，404 如果不存在）
        """
        return self.client.get(f"/api/v1/models/{model_id}")

    def get_model_status(self, model_id):
        """获取模型实时状态

        返回模型的可用性、延迟、队列长度、运行时间等。

        Args:
            model_id: 模型 ID

        Returns:
            requests.Response（200 + 状态信息，404 如果不存在）
        """
        return self.client.get(f"/api/v1/models/{model_id}/status")
