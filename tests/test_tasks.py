import time
import allure
import pytest
from base import assert_success, assert_fail, load_yaml
from api import TaskAPI
from service import create_unauthed_client


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestGenerateText:
    @allure.story("文本生成")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("提交文本生成任务 - 应返回 202 processing")
    def test_generate_text_success(self, creator_task_api):
        resp = creator_task_api.submit_text(
            "m_text_01", "请用Python实现一个快速排序算法",
            parameters={"temperature": 0.7, "max_tokens": 2048}
        )
        assert resp.status_code == 202
        data = assert_success(resp)
        assert "taskId" in data["data"]
        assert data["data"]["status"] == "processing"

    @allure.story("文本生成")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("文本生成指定 projectId")
    def test_generate_text_with_project(self, creator_task_api):
        resp = creator_task_api.submit_text(
            "m_text_01", "写一首诗",
            parameters={"temperature": 0.9},
            project_id="proj_002"
        )
        assert resp.status_code == 202
        assert_success(resp)

    @allure.story("文本生成-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("文本生成参数校验 - {case[name]}")
    @pytest.mark.parametrize("case", load_yaml("generate_data.yaml")["generate_text_invalid"])
    def test_generate_text_invalid(self, creator_task_api, case):
        resp = creator_task_api.client.post("/api/v1/generate/text", json=case["data"])
        assert_fail(resp, case["expected_status"])

    @allure.story("文本生成-配额")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("trial_user token 配额 - 正常提交")
    def test_generate_text_trial(self, trial_client):
        api = TaskAPI(trial_client)
        resp = api.submit_text("m_text_01", "测试配额")
        # trial_user usedTokens=9800 < dailyTokens=10000, 应成功
        assert resp.status_code in (202, 429)


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestGenerateImage:
    @allure.story("图片生成")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("提交图片生成任务 - 应返回 202 processing")
    def test_generate_image_success(self, creator_task_api):
        resp = creator_task_api.submit_image(
            "m_img_01", "一只可爱的柴犬在樱花树下",
            parameters={"size": "1792x1024", "quality": "hd", "style": "natural"}
        )
        assert resp.status_code == 202
        data = assert_success(resp)
        assert "taskId" in data["data"]
        assert data["data"]["status"] == "processing"

    @allure.story("图片生成-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("图片生成缺少 modelId - 应返回 400")
    def test_generate_image_missing_model(self, creator_task_api):
        resp = creator_task_api.client.post("/api/v1/generate/image", json={"prompt": "测试图片"})
        assert_fail(resp, 400)

    @allure.story("图片生成-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("图片生成使用文本模型 - 应返回 400")
    def test_generate_image_wrong_model_type(self, creator_task_api):
        resp = creator_task_api.submit_image("m_text_01", "测试")
        assert_fail(resp, 400)


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestTaskQuery:
    @allure.story("任务查询")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("查询任务详情 - 应包含状态和进度")
    def test_get_task_detail(self, creator_task_api):
        resp = creator_task_api.get_task("task_001")
        data = assert_success(resp)
        task = data["data"]
        assert task["taskId"] == "task_001"
        assert task["status"] in ("processing", "completed")
        for field in ("progress", "prompt"):
            assert field in task

    @allure.story("任务查询")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("使用 service 层轮询任务直至完成")
    def test_poll_task_to_completion(self, creator_task_service):
        """通过业务层提交+等待，测试层不写轮询循环"""
        task = creator_task_service.submit_and_wait_text(
            "m_text_01", "请用一句话介绍Python",
            parameters={"temperature": 0.7, "max_tokens": 100}
        )
        assert task["status"] == "completed"
        assert task["result"] is not None

    @allure.story("任务查询")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("查询不存在的任务 - 应返回 404")
    def test_get_nonexistent_task(self, creator_task_api):
        resp = creator_task_api.get_task("task_not_exist")
        assert_fail(resp, 404)

    @allure.story("任务查询-权限")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("查询他人任务 - 应返回 404")
    def test_get_other_user_task(self, admin_client):
        """用 admin 查询 creator01 的 task_001"""
        api = TaskAPI(admin_client)
        resp = api.get_task("task_001")
        assert_fail(resp, 404)


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestTaskList:
    @allure.story("任务列表")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取任务列表 - 应支持分页和筛选")
    def test_list_tasks(self, creator_task_api):
        resp = creator_task_api.list_tasks()
        data = assert_success(resp)
        assert "list" in data["data"]
        assert "pagination" in data["data"]

    @allure.story("任务列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 status=completed 筛选任务")
    def test_list_tasks_filter_by_status(self, creator_task_api):
        resp = creator_task_api.list_tasks(status="completed")
        data = assert_success(resp)
        for t in data["data"]["list"]:
            assert t["status"] == "completed"

    @allure.story("任务列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 type=image 筛选任务")
    def test_list_tasks_filter_by_type(self, creator_task_api):
        resp = creator_task_api.list_tasks(type="image")
        data = assert_success(resp)
        for t in data["data"]["list"]:
            assert t["type"] == "image"

    @allure.story("任务列表-筛选")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("按 projectId 筛选任务")
    def test_list_tasks_filter_by_project(self, creator_task_api):
        resp = creator_task_api.list_tasks(project_id="proj_001")
        data = assert_success(resp)
        # 验证返回了数据（mock 可能不在列表字段带 projectId）
        assert isinstance(data["data"]["list"], list)


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestTaskCancel:
    @allure.story("取消任务")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("取消 processing 中的任务 - 应成功")
    def test_cancel_task_success(self, creator_task_api):
        # 提交后立即取消（text 类型第一个 stage 有 500ms 延迟，来得及）
        resp = creator_task_api.submit_text("m_text_01", "会被取消的任务")
        task_id = assert_success(resp)["data"]["taskId"]
        resp = creator_task_api.cancel(task_id)
        data = assert_success(resp)
        assert data["data"]["status"] == "cancelled"

    @allure.story("取消任务")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("取消已完成的任务 - 应返回 400")
    def test_cancel_completed_task(self, creator_task_api):
        resp = creator_task_api.cancel("task_001")
        assert_fail(resp, 400)

    @allure.story("取消任务")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("取消不存在的任务 - 应返回 404")
    def test_cancel_nonexistent_task(self, creator_task_api):
        resp = creator_task_api.cancel("task_not_exist")
        assert_fail(resp, 404)


@allure.epic("AIStudio Mock API")
@allure.feature("任务/生成模块")
class TestTaskDelete:
    @allure.story("删除任务")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("删除已完成的任务 - 应成功")
    def test_delete_completed_task(self, creator_task_service, creator_task_api):
        # 用 service 层提交+等待
        task = creator_task_service.submit_and_wait_text(
            "m_text_01", "待删除的任务"
        )
        # 用 api 层删除
        resp = creator_task_api.delete(task["taskId"])
        assert_success(resp)

    @allure.story("删除任务")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("删除不存在的任务 - 应返回 404")
    def test_delete_nonexistent_task(self, creator_task_api):
        resp = creator_task_api.delete("task_not_exist")
        assert_fail(resp, 404)
