"""base/http_client.py — 统一的 HTTP 客户端

【设计意图】
  整个框架只通过这一个类发 HTTP 请求。
  好处：
    1. 所有请求自动记录到 Allure 报告（请求 + 响应）
    2. 统一的超时、Header 管理
    3. Token 管理集中化（set_token / clear_token）

【谁在用这个类？】
  - api/ 层的所有 API 类（AuthAPI、ModelAPI 等）都接收一个 APIClient 实例
  - service/ 层通过 login_as() 创建 APIClient 并设置 token
  - conftest.py 的 fixture 创建不同角色的 APIClient

【调用链】
  tests/test_xxx.py
    → api/xxx_api.py（构造 URL 和参数）
      → APIClient.get/post/put/delete（发请求）
        → APIClient._request（统一处理：Allure 记录 + 发送 + 日志）

【设计模式】
  这是一个 Facade 模式：把 requests.Session 的复杂性封装起来，
  上层只调用 get/post/put/delete，不需要关心 Allure 记录等细节。
"""

import json
import allure
import requests
import logging

from config.settings import BASE_URL, TIMEOUT

logger = logging.getLogger(__name__)


class APIClient:
    """统一的 HTTP 客户端，自动记录请求/响应到 Allure 报告

    职责：只负责发请求和记日志，不关心 URL 拼接、参数构造。
    URL 和参数构造由 api/ 层封装。

    使用示例：
        client = APIClient()                    # 创建客户端
        client.set_token("xxx")                 # 设置认证 token
        resp = client.get("/api/v1/models")     # 发 GET 请求
        client.clear_token()                    # 清除 token
    """

    def __init__(self, base_url=BASE_URL):
        # 用 requests.Session 复用 TCP 连接，性能更好
        self.session = requests.Session()
        self.base_url = base_url

        # 设置默认 Header，所有请求都会带上
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def set_token(self, token):
        """设置 Bearer Token（登录后调用）

        调用后所有请求都会自动带上 Authorization header。
        在 service/auth_service.py 的 login_as() 中使用。
        """
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        """清除 Token（用于测试登出后的行为）"""
        self.session.headers.pop("Authorization", None)

    def _request(self, method, path, **kwargs):
        """核心请求方法 — 所有 get/post/put/patch/delete 最终都走这里

        做三件事：
        1. 记录请求到 Allure（URL、Header、参数、Body）
        2. 发送 HTTP 请求
        3. 记录响应到 Allure（状态码、耗时、Body）+ 打印日志

        Args:
            method: HTTP 方法（GET/POST/PUT/PATCH/DELETE）
            path:   API 路径（如 "/api/v1/auth/login"），会拼接 base_url
            **kwargs: 传给 requests.Session.request() 的参数
                      常用的有 json=（请求体）、params=（查询参数）

        Returns:
            requests.Response 对象
        """
        url = f"{self.base_url}{path}"

        # ---- 第 1 步：记录请求到 Allure 报告 ----
        # 这样在 Allure 报告里可以看到每个用例发了什么请求
        req_body = kwargs.get("json")
        req_params = kwargs.get("params")
        allure.attach(
            f"{method.upper()} {url}\n"
            f"Headers: {json.dumps(dict(self.session.headers), indent=2, ensure_ascii=False)}\n"
            f"Params: {json.dumps(req_params, indent=2, ensure_ascii=False) if req_params else 'N/A'}\n"
            f"Body: {json.dumps(req_body, indent=2, ensure_ascii=False) if req_body else 'N/A'}",
            "Request",
            allure.attachment_type.TEXT,
        )

        # ---- 第 2 步：发送请求 ----
        resp = self.session.request(method, url, timeout=TIMEOUT, **kwargs)

        # ---- 第 3 步：记录响应到 Allure + 日志 ----
        try:
            resp_text = json.dumps(resp.json(), indent=2, ensure_ascii=False)
        except Exception:
            # 响应不是 JSON 格式时，截取前 5000 字符
            resp_text = resp.text[:5000]

        allure.attach(
            f"Status: {resp.status_code}\n"
            f"Time: {resp.elapsed.total_seconds():.3f}s\n"
            f"Body: {resp_text[:5000]}",
            "Response",
            allure.attachment_type.TEXT,
        )

        logger.info(f"{method.upper()} {path} -> {resp.status_code} ({resp.elapsed.total_seconds():.3f}s)")
        return resp

    # ---- 便捷方法：上层调用这些，不需要记 method 参数 ----

    def get(self, path, **kwargs):
        """发送 GET 请求"""
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        """发送 POST 请求（通常带 json= 请求体）"""
        return self._request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        """发送 PUT 请求"""
        return self._request("PUT", path, **kwargs)

    def patch(self, path, **kwargs):
        """发送 PATCH 请求"""
        return self._request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        """发送 DELETE 请求"""
        return self._request("DELETE", path, **kwargs)
