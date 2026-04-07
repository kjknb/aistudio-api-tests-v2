"""通用工具函数"""
import time
import pytest

from base.assertions import assert_success


def wait_for_task(api, task_id, timeout=15, interval=1):
    """轮询任务状态直到 completed/failed/cancelled 或超时

    Args:
        api: APIClient 实例（已带 token）
        task_id: 任务 ID
        timeout: 超时秒数
        interval: 轮询间隔秒数

    Returns:
        任务详情 dict

    Raises:
        pytest.fail: 超时或任务失败
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = api.get(f"/api/v1/tasks/{task_id}")
        data = assert_success(resp)
        status = data["data"]["status"]
        if status == "completed":
            return data["data"]
        elif status == "failed":
            pytest.fail(f"任务 {task_id} 失败: {data['data'].get('error')}")
        elif status == "cancelled":
            pytest.fail(f"任务 {task_id} 已被取消")
        time.sleep(interval)
    pytest.fail(f"任务 {task_id} 在 {timeout}s 内未完成")


def retry_request(api, method, path, max_retries=3, interval=1, **kwargs):
    """带重试的请求（用于偶发网络问题）"""
    for attempt in range(max_retries):
        resp = api._request(method, path, **kwargs)
        if resp.status_code < 500:
            return resp
        if attempt < max_retries - 1:
            time.sleep(interval)
    return resp
