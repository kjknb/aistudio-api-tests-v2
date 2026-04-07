import allure
import pytest
from base import assert_success, assert_fail
from api import ModelAPI
from service import create_unauthed_client


@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelsList:
    @allure.story("模型列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取所有模型列表")
    def test_list_all_models(self, creator_model_api):
        resp = creator_model_api.list_models()
        data = assert_success(resp)
        models = data["data"]
        assert isinstance(models, list)
        assert len(models) >= 7
        for m in models:
            for field in ("id", "name", "provider", "type", "status", "parameterCount"):
                assert field in m

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 type=text 筛选 - 应只返回文本模型")
    def test_list_models_filter_by_type(self, creator_model_api):
        resp = creator_model_api.list_models(type="text")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["type"] == "text"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 type=image 筛选 - 应只返回图片模型")
    def test_list_models_filter_by_image_type(self, creator_model_api):
        resp = creator_model_api.list_models(type="image")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["type"] == "image"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 provider=OpenAI 筛选")
    def test_list_models_filter_by_provider(self, creator_model_api):
        resp = creator_model_api.list_models(provider="OpenAI")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["provider"] == "OpenAI"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 status=active 筛选")
    def test_list_models_filter_by_status(self, creator_model_api):
        resp = creator_model_api.list_models(status="active")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["status"] == "active"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 tags 筛选 (逗号分隔)")
    def test_list_models_filter_by_tags(self, creator_model_api):
        resp = creator_model_api.list_models(tags="文本,编程")
        data = assert_success(resp)
        for m in data["data"]:
            assert "文本" in m["tags"] or "编程" in m["tags"]

    @allure.story("模型列表")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取模型列表 - 应返回 401")
    def test_list_models_unauthorized(self):
        client = create_unauthed_client()
        api = ModelAPI(client)
        resp = api.list_models()
        assert_fail(resp, 401)


@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelDetail:
    @allure.story("模型详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取文本模型详情 - m_text_01")
    def test_get_text_model(self, creator_model_api):
        resp = creator_model_api.get_model("m_text_01")
        data = assert_success(resp)
        model = data["data"]
        assert model["id"] == "m_text_01"
        assert model["type"] == "text"
        assert model["name"] == "GPT-4o"
        assert "pricing" in model
        assert "parameters" in model

    @allure.story("模型详情")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取图片模型详情 - m_img_01")
    def test_get_image_model(self, creator_model_api):
        resp = creator_model_api.get_model("m_img_01")
        data = assert_success(resp)
        model = data["data"]
        assert model["id"] == "m_img_01"
        assert model["type"] == "image"
        assert model["name"] == "DALL·E 3"
        assert "per_image" in model["pricing"]

    @allure.story("模型详情")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取不存在的模型 - 应返回 404")
    def test_get_nonexistent_model(self, creator_model_api):
        resp = creator_model_api.get_model("m_not_exist")
        assert_fail(resp, 404)


@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelStatus:
    @allure.story("模型状态")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取模型状态 - 应包含可用性、延迟、队列等")
    def test_get_model_status(self, creator_model_api):
        resp = creator_model_api.get_model_status("m_text_01")
        data = assert_success(resp)
        status = data["data"]
        assert status["modelId"] == "m_text_01"
        assert status["status"] == "active"
        assert isinstance(status["available"], bool)
        for field in ("latency", "queueLength", "uptime"):
            assert field in status

    @allure.story("模型状态")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取不存在模型的状态 - 应返回 404")
    def test_get_nonexistent_model_status(self, creator_model_api):
        resp = creator_model_api.get_model_status("m_not_exist")
        assert_fail(resp, 404)
