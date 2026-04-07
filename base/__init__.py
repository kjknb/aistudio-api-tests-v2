"""base/__init__.py — 基础层统一导出

【设计意图】
  让其他模块可以这样导入：
    from base import APIClient, assert_success, load_yaml
  而不需要：
    from base.http_client import APIClient
    from base.assertions import assert_success
  减少导入语句，统一入口。

【导出内容】
  - APIClient    → HTTP 客户端（来自 http_client.py）
  - assert_*     → 断言函数（来自 assertions.py）
  - load_yaml    → 数据加载（来自 data_loader.py）
"""

from .http_client import APIClient
from .assertions import (
    assert_success,
    assert_fail,
    assert_paginated,
    assert_json_schema,
    assert_response_time,
)
from .data_loader import load_yaml, load_json
