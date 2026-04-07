"""base/data_loader.py — 测试数据加载

【设计意图】
  测试数据统一放在 data/ 目录，用 YAML 格式管理。
  好处：
    1. 测试数据和代码分离，非开发人员也能改数据
    2. YAML 比 JSON 更易读（支持注释、多行字符串）
    3. 配合 @pytest.mark.parametrize 实现数据驱动测试

【谁在用这些函数？】
  - tests/ 层的测试用例：load_yaml("register_data.yaml")["register_invalid"]
  - base/__init__.py 做了 re-export，所以可以直接 from base import load_yaml

【数据驱动的工作流】
  1. 在 data/xxx_data.yaml 里写测试数据
  2. 测试用例用 load_yaml() 加载
  3. 用 @pytest.mark.parametrize 展开成多个测试

【目录结构约定】
  load_yaml("chat_data.yaml")  →  实际读取 data/chat_data.yaml
  路径相对于项目根目录的 data/ 文件夹
"""

import os
import json
import yaml

# 定位 data/ 目录的绝对路径
# __file__ = base/data_loader.py
# dirname(__file__) = base/
# dirname(dirname(__file__)) = 项目根目录/
# 拼上 data/ = 项目根目录/data/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_yaml(filename):
    """从 data/ 目录加载 YAML 文件

    Args:
        filename: 文件名（不含路径），如 "register_data.yaml"

    Returns:
        YAML 解析后的 Python 对象（通常是 dict 或 list）

    用法：
        cases = load_yaml("register_data.yaml")["register_invalid"]
        for case in cases:
            print(case["name"], case["data"], case["expected_status"])
    """
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(filename):
    """从 data/ 目录加载 JSON 文件

    和 load_yaml 类似，用于 JSON 格式的测试数据。

    Args:
        filename: 文件名（不含路径），如 "test_cases.json"

    Returns:
        JSON 解析后的 Python 对象
    """
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)
