"""tests/test_projects.py — 项目模块测试

【测试覆盖】
  TestCreateProject:  创建项目（正常/缺 name/name 太长/未认证）
  TestListProjects:   项目列表（分页）
  TestProjectDetail:  项目详情（正常/不存在/他人项目权限）
  TestDeleteProject:  删除项目（正常删除+验证/不存在）

【项目和任务的关系】
  项目是任务的容器。详情接口会返回项目下关联的任务列表。
  每个用户只能看到自己的项目（权限隔离）。
"""

import allure
import pytest
from base import assert_success, assert_fail, assert_paginated
from api import ProjectAPI
from service import create_unauthed_client


# ==================== 创建项目 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("项目模块")
class TestCreateProject:
    @allure.story("创建项目")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("正常创建项目 - 应返回 201")
    def test_create_project_success(self, creator_project_api):
        """正常创建项目 — 验证返回 201 + 项目信息

        注意：测试后手动清理（delete），避免脏数据影响其他测试。
        """
        resp = creator_project_api.create("测试项目A", "这是描述")
        assert resp.status_code == 201
        data = assert_success(resp)
        project = data["data"]
        assert project["name"] == "测试项目A"
        assert project["description"] == "这是描述"
        assert "id" in project
        # 清理：测试创建后一定要删除
        creator_project_api.delete(project["id"])

    @allure.story("创建项目")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("创建项目 - 仅 name (description 可选)")
    def test_create_project_without_desc(self, creator_project_api):
        """只传 name，不传 description — 验证 description 是可选字段"""
        resp = creator_project_api.create("无描述项目")
        assert resp.status_code == 201
        data = assert_success(resp)
        creator_project_api.delete(data["data"]["id"])

    @allure.story("创建项目-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("缺少 name - 应返回 400")
    def test_create_project_missing_name(self, creator_project_api):
        """缺少必填字段 name → 400"""
        resp = creator_project_api.client.post("/api/v1/projects", json={"description": "没有名字"})
        assert_fail(resp, 400)

    @allure.story("创建项目-参数校验")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("name 超过 50 字 - 应返回 400")
    def test_create_project_name_too_long(self, creator_project_api):
        """name 超过 50 字符 → 400（边界值测试）"""
        resp = creator_project_api.create("A" * 51)
        assert_fail(resp, 400)

    @allure.story("创建项目")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("未登录创建项目 - 应返回 401")
    def test_create_project_unauthorized(self):
        """未认证创建项目 → 401"""
        client = create_unauthed_client()
        api = ProjectAPI(client)
        resp = api.create("未授权项目")
        assert_fail(resp, 401)


# ==================== 项目列表 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("项目模块")
class TestListProjects:
    @allure.story("项目列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取项目列表 - 应支持分页")
    def test_list_projects(self, creator_project_api):
        """获取项目列表 — 验证分页结构（list + pagination）"""
        resp = creator_project_api.list_projects()
        data = assert_success(resp)
        assert_paginated(data["data"])

    @allure.story("项目列表-分页")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("分页参数 page=1&pageSize=1")
    def test_list_projects_pagination(self, creator_project_api):
        """指定 pageSize=1 — 验证分页参数生效"""
        resp = creator_project_api.list_projects(page=1, pageSize=1)
        data = assert_success(resp)
        assert len(data["data"]["list"]) <= 1
        assert data["data"]["pagination"]["pageSize"] == 1


# ==================== 项目详情 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("项目模块")
class TestProjectDetail:
    @allure.story("项目详情")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("获取项目详情 - 应包含关联任务")
    def test_get_project_detail(self, creator_project_api, temp_project):
        """获取项目详情 — 验证包含项目信息和关联的任务列表

        使用 temp_project fixture（自动创建+自动清理）。
        """
        resp = creator_project_api.get_project(temp_project["id"])
        data = assert_success(resp)
        proj = data["data"]
        assert proj["id"] == temp_project["id"]
        assert proj["name"] == temp_project["name"]
        assert "tasks" in proj

    @allure.story("项目详情")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取不存在的项目 - 应返回 404")
    def test_get_nonexistent_project(self, creator_project_api):
        """查询不存在的项目 → 404"""
        resp = creator_project_api.get_project("proj_not_exist")
        assert_fail(resp, 404)

    @allure.story("项目详情-权限")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("获取他人项目 - 应返回 404")
    def test_get_other_user_project(self, admin_client):
        """用 admin 访问 creator01 的项目 — 验证权限隔离

        不同用户的项目数据应该隔离，admin 不应该看到 creator 的项目。
        注意：这里用 404 而不是 403，是 RESTful 的常见做法（不暴露资源存在性）。
        """
        api = ProjectAPI(admin_client)
        resp = api.get_project("proj_002")
        assert_fail(resp, 404)


# ==================== 删除项目 ====================

@allure.epic("AIStudio Mock API")
@allure.feature("项目模块")
class TestDeleteProject:
    @allure.story("删除项目")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("删除自己的项目 - 应成功")
    def test_delete_project_success(self, creator_project_api):
        """创建 → 删除 → 验证已删除（再查询应返回 404）

        这是一个完整的 CRUD 测试：先创建，再删除，最后验证确实删掉了。
        """
        # 创建
        resp = creator_project_api.create("待删除项目")
        project_id = assert_success(resp)["data"]["id"]
        # 删除
        resp = creator_project_api.delete(project_id)
        assert_success(resp)
        # 验证已删除 — 再查应该 404
        resp = creator_project_api.get_project(project_id)
        assert_fail(resp, 404)

    @allure.story("删除项目")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("删除不存在的项目 - 应返回 404")
    def test_delete_nonexistent_project(self, creator_project_api):
        """删除不存在的项目 → 404"""
        resp = creator_project_api.delete("proj_not_exist")
        assert_fail(resp, 404)
