"""通用断言封装

所有断言函数统一返回 data，方便链式调用。
测试层只调用这些函数，不直接写 assert resp.status_code == 200。
"""
import jsonschema


def assert_success(resp, expected_code=0):
    """验证响应为成功格式，返回 resp.json()"""
    assert resp.status_code in (200, 201, 202), \
        f"期望 HTTP 200/201/202, 实际 {resp.status_code}"
    data = resp.json()
    assert data.get("code") == expected_code, \
        f"期望 code={expected_code}, 实际 code={data.get('code')}, message={data.get('message')}"
    return data


def assert_fail(resp, http_status, expected_code=None):
    """验证响应为失败格式，返回 resp.json()"""
    assert resp.status_code == http_status, \
        f"期望 HTTP {http_status}, 实际 {resp.status_code}"
    data = resp.json()
    if expected_code is not None:
        assert data.get("code") == expected_code, \
            f"期望 code={expected_code}, 实际 code={data.get('code')}"
    return data


def assert_paginated(data):
    """验证分页结构（传入 data["data"]）"""
    assert "list" in data, "响应缺少 list 字段"
    assert "pagination" in data, "响应缺少 pagination 字段"
    pag = data["pagination"]
    for key in ("page", "pageSize", "total", "totalPages"):
        assert key in pag, f"pagination 缺少 {key} 字段"


def assert_json_schema(instance, schema):
    """JSON Schema 验证"""
    jsonschema.validate(instance=instance, schema=schema)


def assert_response_time(resp, max_seconds=5.0):
    """验证响应时间"""
    elapsed = resp.elapsed.total_seconds()
    assert elapsed <= max_seconds, f"响应时间 {elapsed:.3f}s 超过 {max_seconds}s"
