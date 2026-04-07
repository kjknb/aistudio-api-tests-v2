"""base/assertions.py — 通用断言封装

【设计意图】
  测试层统一调用这些断言函数，不要直接写 assert resp.status_code == 200。
  好处：
    1. 断言逻辑集中管理，修改一处影响全局
    2. 错误信息更友好（自动打印实际值）
    3. 返回 data 支持链式调用

【谁在用这些函数？】
  - tests/ 层的所有测试用例
  - service/ 层的业务流程（如 login_as() 里调 assert_success）

【API 响应格式约定】
  成功：{"code": 0, "data": {...}, "message": "success"}
  失败：{"code": <错误码>, "message": "错误描述"}
  分页：{"code": 0, "data": {"list": [...], "pagination": {...}}}

【调用示例】
  data = assert_success(resp)                    # 验证成功，返回 data
  assert_fail(resp, 400)                         # 验证失败 + 状态码
  assert_fail(resp, 401, expected_code=1001)     # 验证失败 + 状态码 + 业务错误码
  assert_paginated(data["data"])                 # 验证分页结构
  assert_response_time(resp, max_seconds=3.0)    # 验证响应时间
"""

import jsonschema


def assert_success(resp, expected_code=0):
    """验证响应为成功格式，返回 resp.json()

    检查两层：
    1. HTTP 状态码 ∈ {200, 201, 202}
    2. 业务 code == expected_code（默认 0 表示成功）

    Args:
        resp:           requests.Response 对象
        expected_code:  期望的业务 code，默认 0

    Returns:
        resp.json() 的结果，方便后续取 data

    用法：
        data = assert_success(resp)
        user = data["data"]["user"]
    """
    assert resp.status_code in (200, 201, 202), \
        f"期望 HTTP 200/201/202, 实际 {resp.status_code}"
    data = resp.json()
    assert data.get("code") == expected_code, \
        f"期望 code={expected_code}, 实际 code={data.get('code')}, message={data.get('message')}"
    return data


def assert_fail(resp, http_status, expected_code=None):
    """验证响应为失败格式，返回 resp.json()

    和 assert_success 对应，用于测试各种错误场景。

    Args:
        resp:          requests.Response 对象
        http_status:   期望的 HTTP 状态码（400/401/403/404/409/429 等）
        expected_code: 可选，期望的业务错误码

    Returns:
        resp.json() 的结果

    用法：
        assert_fail(resp, 401)                        # 验证未认证
        assert_fail(resp, 400, expected_code=1001)    # 验证参数错误 + 业务错误码
    """
    assert resp.status_code == http_status, \
        f"期望 HTTP {http_status}, 实际 {resp.status_code}"
    data = resp.json()
    if expected_code is not None:
        assert data.get("code") == expected_code, \
            f"期望 code={expected_code}, 实际 code={data.get('code')}"
    return data


def assert_paginated(data):
    """验证分页结构（传入 data["data"]，不是完整的响应）

    检查响应中是否有 list 和 pagination 字段，pagination 必须包含：
    page / pageSize / total / totalPages

    Args:
        data: 响应中的 data 字段（dict），包含 list 和 pagination

    用法：
        data = assert_success(resp)
        assert_paginated(data["data"])
    """
    assert "list" in data, "响应缺少 list 字段"
    assert "pagination" in data, "响应缺少 pagination 字段"
    pag = data["pagination"]
    for key in ("page", "pageSize", "total", "totalPages"):
        assert key in pag, f"pagination 缺少 {key} 字段"


def assert_json_schema(instance, schema):
    """JSON Schema 验证 — 严格检查响应结构

    适合对响应结构有严格要求的场景（如契约测试）。

    Args:
        instance: 要验证的数据（通常是 resp.json()["data"]）
        schema:   JSON Schema 定义（dict）

    用法：
        schema = {
            "type": "object",
            "required": ["id", "username", "email"],
            "properties": {
                "id": {"type": "string"},
                "username": {"type": "string"},
                "email": {"type": "string", "format": "email"},
            }
        }
        assert_json_schema(user_data, schema)
    """
    jsonschema.validate(instance=instance, schema=schema)


def assert_response_time(resp, max_seconds=5.0):
    """验证响应时间 — 用于性能测试

    Args:
        resp:         requests.Response 对象
        max_seconds:  最大允许的响应时间，默认 5 秒

    用法：
        assert_response_time(resp, max_seconds=3.0)  # 要求 3 秒内响应
    """
    elapsed = resp.elapsed.total_seconds()
    assert elapsed <= max_seconds, f"响应时间 {elapsed:.3f}s 超过 {max_seconds}s"
