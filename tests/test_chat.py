import allure
import pytest
from base import assert_success, assert_fail, load_yaml
from api import ChatAPI
from service import create_unauthed_client


@allure.epic("AIStudio Mock API")
@allure.feature("聊天模块")
class TestChatCompletions:
    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("基本聊天对话 - 应返回 assistant 回复")
    def test_chat_success(self, creator_chat_api):
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
        resp = creator_chat_api.client.post("/api/v1/chat/completions", json=case["data"])
        assert_fail(resp, case["expected_status"])

    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("使用不同文本模型聊天")
    @pytest.mark.parametrize("model_id", ["m_text_01", "m_text_02", "m_text_03"])
    def test_chat_different_models(self, creator_chat_api, model_id):
        resp = creator_chat_api.completions(
            model_id, [{"role": "user", "content": "Hello"}]
        )
        data = assert_success(resp)
        assert data["data"]["choices"][0]["message"]["role"] == "assistant"

    @allure.story("聊天补全")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录聊天 - 应返回 401")
    def test_chat_unauthorized(self):
        client = create_unauthed_client()
        api = ChatAPI(client)
        resp = api.completions("m_text_01", [{"role": "user", "content": "Hello"}])
        assert_fail(resp, 401)


@allure.epic("AIStudio Mock API")
@allure.feature("聊天模块")
class TestChatHistory:
    @allure.story("聊天历史")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取聊天历史 - 应支持分页")
    def test_get_chat_history(self, creator_chat_api):
        resp = creator_chat_api.history()
        data = assert_success(resp)
        assert "list" in data["data"]
        assert "pagination" in data["data"]

    @allure.story("聊天历史-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 modelId 筛选聊天历史")
    def test_get_chat_history_filter_by_model(self, creator_chat_api):
        resp = creator_chat_api.history(model_id="m_text_01")
        data = assert_success(resp)
        for h in data["data"]["list"]:
            assert h["modelId"] == "m_text_01"

    @allure.story("聊天历史-分页")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("聊天历史分页 page=1&pageSize=5")
    def test_get_chat_history_pagination(self, creator_chat_api):
        resp = creator_chat_api.history(page=1, pageSize=5)
        data = assert_success(resp)
        assert len(data["data"]["list"]) <= 5

    @allure.story("聊天历史")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取历史 - 应返回 401")
    def test_get_chat_history_unauthorized(self):
        client = create_unauthed_client()
        api = ChatAPI(client)
        resp = api.history()
        assert_fail(resp, 401)
