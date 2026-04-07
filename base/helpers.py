"""base/helpers.py — 通用工具函数

【设计意图】
  收纳一些跨模块复用的工具函数，主要是：
    1. wait_for_task() — 轮询任务状态直到完成
    2. retry_request() — 带重试的请求（处理偶发 5xx）

【谁在用这些函数？】
  - service/task_service.py 的 submit_and_wait_text/image() 调用 wait_for_task()
  - retry_request() 目前未被使用，是备用工具

【关于 wait_for_task 的参数】
  第一个参数是 APIClient 实例（不是 TaskAPI），因为它直接调 client.get() 发请求。
  这样设计的好处是不依赖具体的 API 类，更通用。
  （改进方向：可以改为接收 TaskAPI 实例，调 api.get_task() 更符合分层）
"""

import time
import pytest

from base.assertions import assert_success


def wait_for_task(api, task_id, timeout=15, interval=1):
    """轮询任务状态直到 completed/failed/cancelled 或超时

    典型使用场景：
      1. 提交一个文本/图片生成任务 → 返回 taskId
      2. 调用这个函数轮询 GET /api/v1/tasks/{taskId}
      3. 每秒检查一次状态，直到 completed 或超时

    Args:
        api:      APIClient 实例（已带 token）
        task_id:  任务 ID（由 submit_text/submit_image 返回）
        timeout:  超时秒数，默认 15 秒
        interval: 轮询间隔秒数，默认 1 秒

    Returns:
        任务详情 dict（status=completed 时）

    Raises:
        pytest.fail: 超时或任务失败/取消时直接让测试失败

    调用链示例：
      test_poll_task_to_completion()
        → TaskService.submit_and_wait_text()
          → TaskAPI.submit_text()              # 提交任务，拿到 taskId
          → wait_for_task(client, task_id)     # 轮询直到完成
        → assert task["status"] == "completed"
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

    # 超时
    pytest.fail(f"任务 {task_id} 在 {timeout}s 内未完成")


def retry_request(api, method, path, max_retries=3, interval=1, **kwargs):
    """带重试的请求（用于偶发网络问题）

    只对 5xx 错误重试，4xx 等客户端错误不重试（重试也没用）。

    Args:
        api:          APIClient 实例
        method:       HTTP 方法（"GET"/"POST"/...）
        path:         API 路径
        max_retries:  最大重试次数，默认 3
        interval:     重试间隔秒数，默认 1
        **kwargs:     传给 _request 的其他参数

    Returns:
        requests.Response 对象（最后一次请求的响应）

    注意：目前这个函数未被使用，是备用工具。
         如果需要全局重试，可以集成到 APIClient._request() 里。
    """
    for attempt in range(max_retries):
        resp = api._request(method, path, **kwargs)
        if resp.status_code < 500:
            return resp
        if attempt < max_retries - 1:
            time.sleep(interval)
    return resp
