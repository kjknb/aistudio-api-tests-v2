"""api/chat_api.py — 聊天模块接口封装

【对应接口】
  POST /api/v1/chat/completions  → 聊天补全（类似 OpenAI Chat API）
  GET  /api/v1/chat/history       → 聊天历史（支持分页和筛选）

【调用链示例 — 聊天补全】
  test_chat_success()
    → ChatAPI.completions("m_text_01", [{"role":"user","content":"你好"}])
      → APIClient.post("/api/v1/chat/completions", json={...})
    → assert data["data"]["choices"][0]["message"]["role"] == "assistant"
"""

from base import APIClient


class ChatAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def completions(self, model_id, messages, parameters=None):
        """聊天补全 — 发送对话，获取 AI 回复

        消息格式和 OpenAI Chat API 类似：
          messages = [
              {"role": "system", "content": "你是一个助手"},
              {"role": "user", "content": "你好"},
              {"role": "assistant", "content": "你好！有什么可以帮你的？"},
              {"role": "user", "content": "介绍一下Docker"},
          ]

        Args:
            model_id:    模型 ID（如 "m_text_01"）
            messages:    对话消息列表
            parameters:  可选参数（temperature, max_tokens 等）

        Returns:
            requests.Response（200 + 补全结果）
        """
        payload = {
            "modelId": model_id,
            "messages": messages,
        }
        if parameters:
            payload["parameters"] = parameters
        return self.client.post("/api/v1/chat/completions", json=payload)

    def history(self, model_id=None, page=1, pageSize=10):
        """获取聊天历史（分页）

        Args:
            model_id:  可选，按模型 ID 筛选
            page:      页码
            pageSize:  每页数量

        Returns:
            requests.Response（200 + 分页的历史列表）
        """
        params = {"page": page, "pageSize": pageSize}
        if model_id:
            params["modelId"] = model_id
        return self.client.get("/api/v1/chat/history", params=params)
