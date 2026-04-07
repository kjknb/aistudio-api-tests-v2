"""tests/test_chat.py — 聊天模块测试

【测试覆盖】
  TestChatCompletions: 聊天补全（单轮/多轮/参数校验/多模型/未认证）
  TestChatHistory:     聊天历史（获取/筛选/分页/未认证）

【和 OpenAI API 的关系】
  这个模块的接口设计和 OpenAI Chat API 几乎一样：
    messages = [{"role": "user", "content": "..."}]
    parameters = {"temperature": 0.7}
  如果你熟悉 OpenAI 的 chat completions，这个模块的测试就很直观。
"""

import allure
import pytest
from base import assert_success, assert_fail, load_yaml
from api import ChatAPI
from service import create_unauthed_client


# ==================== 聊天补全 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("聊天模块")
class TestChatCompletions:
    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("基本聊天对话 - 应返回 assistant 回复")
    def test_chat_success(self, creator_chat_api):
        """基本的单轮对话 — 发送 user 消息，验证返回 assistant 回复

        验证点：
          - choices 数组非空
          - 第一条 choice 的 role == "assistant"
          - finish_reason == "stop"（正常结束）
          - 包含 usage 统计
        """
        resp = creator_chat_api.completions(
            "m_text_01",
            [{"role": "user", "content": "你好，请介绍一下你自己"}],
            parameters={"temperature": 0.7}
        )
        data = assert_success(resp)
        result = data["data"]
        assert "choices" in result
        assert len(result["choices"]) > 0
        assert result["choices"][0]["message"]["role"] == "assistant"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert "usage" in result

    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("多轮对话 - system + user + assistant + user")
    def test_chat_multi_turn(self, creator_chat_api):
        """多轮对话 — 验证带上下文的对话能力

        消息链：system → user → assistant → user
        这是典型的多轮对话场景，AI 需要理解上下文。
        """
        resp = creator_chat_api.completions(
            "m_text_01",
            [
                {"role": "system", "content": "你是一个乐于助人的AI助手"},
                {"role": "user", "content": "请解释一下Docker是什么"},
                {"role": "assistant", "content": "Docker是一个开源的容器化平台..."},
                {"role": "user", "content": "那它和虚拟机有什么区别呢？"},
            ],
            parameters={"temperature": 0.5}
        )
        data = assert_success(resp)
        assert data["data"]["choices"][0]["message"]["role"] == "assistant"

    @allure.story("聊天补全-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("聊天参数校验 - {case[name]}")
    @pytest.mark.parametrize("case", load_yaml("chat_data.yaml")["chat_invalid"])
    def test_chat_invalid(self, creator_chat_api, case):
        """数据驱动：各种非法参数的聊天请求

        测试数据来自 data/chat_data.yaml，覆盖：
          - 缺少 modelId
          - 缺少 messages
          - messages 为空数组
          - modelId 为图片类型（应该用文本模型聊天）
        """
        resp = creator_chat_api.client.post("/api/v1/chat/completions", json=case["data"])
        assert_fail(resp, case["expected_status"])

    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("使用不同文本模型聊天")
    @pytest.mark.parametrize("model_id", ["m_text_01", "m_text_02", "m_text_03"])
    def test_chat_different_models(self, creator_chat_api, model_id):
        """用不同模型聊天 — 验证所有文本模型都支持聊天功能

        用 @pytest.mark.parametrize 展开成 3 个独立测试。
        """
        resp = creator_chat_api.completions(
            model_id, [{"role": "user", "content": "Hello"}]
        )
        data = assert_success(resp)
        assert data["data"]["choices"][0]["message"]["role"] == "assistant"

    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录聊天 - 应返回 401")
    def test_chat_unauthorized(self):
        """未认证访问聊天接口 → 401"""
        client = create_unauthed_client()
        api = ChatAPI(client)
        resp = api.completions("m_text_01", [{"role": "user", "content": "Hello"}])
        assert_fail(resp, 401)


# ==================== 聊天历史 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("聊天模块")
class TestChatHistory:
    @allure.story("聊天历史")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取聊天历史 - 应支持分页")
    def test_get_chat_history(self, creator_chat_api):
        """获取聊天历史 — 验证分页结构"""
        resp = creator_chat_api.history()
        data = assert_success(resp)
        assert "list" in data["data"]
        assert "pagination" in data["data"]

    @allure.story("聊天历史-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 modelId 筛选聊天历史")
    def test_get_chat_history_filter_by_model(self, creator_chat_api):
        """按 modelId 筛选 — 验证所有返回项都匹配"""
        resp = creator_chat_api.history(model_id="m_text_01")
        data = assert_success(resp)
        for h in data["data"]["list"]:
            assert h["modelId"] == "m_text_01"

    @allure.story("聊天历史-分页")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("聊天历史分页 page=1&pageSize=5")
    def test_get_chat_history_pagination(self, creator_chat_api):
        """分页参数生效 — 请求 5 条，返回不应超过 5 条"""
        resp = creator_chat_api.history(page=1, pageSize=5)
        data = assert_success(resp)
        assert len(data["data"]["list"]) <= 5

    @allure.story("聊天历史")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取历史 - 应返回 401")
    def test_get_chat_history_unauthorized(self):
        """未认证获取历史 → 401"""
        client = create_unauthed_client()
        api = ChatAPI(client)
        resp = api.history()
        assert_fail(resp, 401)
