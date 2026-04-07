# config/settings.py — 全局配置
#
# 【设计意图】
#   所有环境相关的配置集中在这里，其他模块不要自己硬编码 URL 或账号。
#   通过环境变量 TEST_ENV 切换环境（dev / staging / CI）。
#
# 【谁在用这个文件？】
#   - base/http_client.py → 读取 BASE_URL 和 TIMEOUT
#   - service/auth_service.py → 读取 TEST_USERS 做登录
#   - api/model_api.py 等 → 间接通过 http_client 使用 BASE_URL

import os

# 从环境变量读取当前环境，默认 "dev"
# 用法：TEST_ENV=staging pytest
ENV = os.getenv("TEST_ENV", "dev")

# 各环境的 Base URL 映射
# 新增环境只需在这里加一行
BASE_URLS = {
    "dev": "http://localhost:3000",
    "staging": "http://staging.example.com",
}

# 当前环境的 Base URL，找不到就 fallback 到 dev
BASE_URL = BASE_URLS.get(ENV, "http://localhost:3000")

# HTTP 请求超时时间（秒）
TIMEOUT = 15

# 测试账号 — 不同角色有不同的权限
# ⚠️ 生产项目建议从环境变量读取密码，不要提交明文到 Git
#    例如：os.getenv("TEST_ADMIN_PASSWORD", "Aa123456")
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "Aa123456",        # enterprise 计划
    },
    "creator": {
        "username": "creator01",
        "password": "Aa123456",        # pro 计划
    },
    "trial": {
        "username": "trial_user",
        "password": "Aa123456",        # free 计划（有配额限制）
    },
}

# 已知模型 ID — 用于测试参数化和数据校验
KNOWN_MODELS = {
    "text": ["m_text_01", "m_text_02", "m_text_03"],
    "image": ["m_img_01", "m_img_02", "m_img_03", "m_img_04"],
}
