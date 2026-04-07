"""YAML / JSON 测试数据加载"""
import os
import json
import yaml

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_yaml(filename):
    """从 data/ 目录加载 YAML 文件"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(filename):
    """从 data/ 目录加载 JSON 文件"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)
