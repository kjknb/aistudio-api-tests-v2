import os

ENV = os.getenv("TEST_ENV", "dev")

BASE_URLS = {
    "dev": "http://localhost:3000",
    "staging": "http://staging.example.com",
}

BASE_URL = BASE_URLS.get(ENV, "http://localhost:3000")
TIMEOUT = 15

# 测试账号
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "Aa123456",
    },
    "creator": {
        "username": "creator01",
        "password": "Aa123456",
    },
    "trial": {
        "username": "trial_user",
        "password": "Aa123456",
    },
}

# 已知模型 ID
KNOWN_MODELS = {
    "text": ["m_text_01", "m_text_02", "m_text_03"],
    "image": ["m_img_01", "m_img_02", "m_img_03", "m_img_04"],
}
