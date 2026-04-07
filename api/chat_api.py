"""聊天模块接口封装

对应 Mock 的 2 个接口：
  POST /api/v1/chat/completions
  GET  /api/v1/chat/history
"""


class ChatAPI:
    def __init__(self, client):
        self.client = client

    def completions(self, model_id, messages, parameters=None):
        """多轮对话"""
        payload = {
            "modelId": model_id,
            "messages": messages,
        }
        if parameters:
            payload["parameters"] = parameters
        return self.client.post("/api/v1/chat/completions", json=payload)

    def history(self, page=1, pageSize=20, model_id=None):
        """获取对话历史"""
        params = {"page": page, "pageSize": pageSize}
        if model_id:
            params["modelId"] = model_id
        return self.client.get("/api/v1/chat/history", params=params)
