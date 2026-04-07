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
    """

    def __init__(self, base_url=BASE_URL):
        self.session = requests.Session()
        self.base_url = base_url
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def set_token(self, token):
        self.session.headers["Authorization"] = f"Bearer {token}"

    def clear_token(self):
        self.session.headers.pop("Authorization", None)

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        # ---- 请求附件 ----
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

        resp = self.session.request(method, url, timeout=TIMEOUT, **kwargs)

        # ---- 响应附件 ----
        try:
            resp_text = json.dumps(resp.json(), indent=2, ensure_ascii=False)
        except Exception:
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

    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self._request("PUT", path, **kwargs)

    def patch(self, path, **kwargs):
        return self._request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)
