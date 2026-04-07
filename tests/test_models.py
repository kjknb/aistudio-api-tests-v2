"""tests/test_models.py — 模型模块测试

【测试覆盖】
  TestModelsList:   模型列表（全量 + 按 type/provider/status/tags 筛选 + 未认证）
  TestModelDetail:  模型详情（文本模型/图片模型/不存在的模型）
  TestModelStatus:  模型状态（正常 + 不存在）

【设计模式】
  筛选测试用了"验证所有返回项都符合条件"的模式：
    for m in data["data"]:
        assert m["type"] == "text"
  这比只检查第一条更严格，确保后端筛选逻辑正确。
"""

import allure
import pytest
from base import assert_success, assert_fail
from api import ModelAPI
from service import create_unauthed_client


# ==================== 模型列表 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelsList:
    @allure.story("模型列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取所有模型列表")
    def test_list_all_models(self, creator_model_api):
        """获取全量模型列表 — 验证数量和必填字段"""
        resp = creator_model_api.list_models()
        data = assert_success(resp)
        models = data["data"]
        assert isinstance(models, list)
        assert len(models) >= 7  # mock 数据至少有 7 个模型
        # 验证每个模型都包含必要字段
        for m in models:
            for field in ("id", "name", "provider", "type", "status", "parameterCount"):
                assert field in m

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 type=text 筛选 - 应只返回文本模型")
    def test_list_models_filter_by_type(self, creator_model_api):
        """按 type=text 筛选 — 验证所有返回项都是文本类型"""
        resp = creator_model_api.list_models(type="text")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["type"] == "text"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 type=image 筛选 - 应只返回图片模型")
    def test_list_models_filter_by_image_type(self, creator_model_api):
        """按 type=image 筛选"""
        resp = creator_model_api.list_models(type="image")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["type"] == "image"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 provider=OpenAI 筛选")
    def test_list_models_filter_by_provider(self, creator_model_api):
        """按供应商筛选"""
        resp = creator_model_api.list_models(provider="OpenAI")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["provider"] == "OpenAI"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 status=active 筛选")
    def test_list_models_filter_by_status(self, creator_model_api):
        """按状态筛选 — 只返回活跃的模型"""
        resp = creator_model_api.list_models(status="active")
        data = assert_success(resp)
        for m in data["data"]:
            assert m["status"] == "active"

    @allure.story("模型列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 tags 筛选 (逗号分隔)")
    def test_list_models_filter_by_tags(self, creator_model_api):
        """按标签筛选 — 标签用逗号分隔，返回的模型至少包含其中一个标签"""
        resp = creator_model_api.list_models(tags="文本,编程")
        data = assert_success(resp)
        for m in data["data"]:
            assert "文本" in m["tags"] or "编程" in m["tags"]

    @allure.story("模型列表")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录获取模型列表 - 应返回 401")
    def test_list_models_unauthorized(self):
        """未认证访问 → 401"""
        client = create_unauthed_client()
        api = ModelAPI(client)
        resp = api.list_models()
        assert_fail(resp, 401)


# ==================== 模型详情 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelDetail:
    @allure.story("模型详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取文本模型详情 - m_text_01")
    def test_get_text_model(self, creator_model_api):
        """获取 GPT-4o 模型详情 — 验证基本信息和定价参数"""
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
        """获取 DALL·E 3 模型详情 — 验证图片特有的 per_image 定价"""
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
        """查询不存在的模型 ID → 404"""
        resp = creator_model_api.get_model("m_not_exist")
        assert_fail(resp, 404)


# ==================== 模型状态 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("模型模块")
class TestModelStatus:
    @allure.story("模型状态")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取模型状态 - 应包含可用性、延迟、队列等")
    def test_get_model_status(self, creator_model_api):
        """获取模型实时状态 — 验证包含可用性、延迟、队列长度等运维指标"""
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
        """查询不存在模型的状态 → 404"""
        resp = creator_model_api.get_model_status("m_not_exist")
        assert_fail(resp, 404)
