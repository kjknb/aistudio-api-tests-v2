"""api/project_api.py — 项目模块接口封装

【对应接口】
  POST   /api/v1/projects          → 创建项目
  GET    /api/v1/projects          → 项目列表（支持分页）
  GET    /api/v1/projects/{id}     → 项目详情
  PUT    /api/v1/projects/{id}     → 更新项目
  DELETE /api/v1/projects/{id}     → 删除项目

【谁在用这个类？】
  - service/project_service.py → 创建项目 + 在项目下提交任务
  - tests/test_projects.py → 测试 CRUD 和权限
  - conftest.py → creator_project_api fixture, temp_project fixture

【项目和任务的关系】
  项目是任务的容器。提交任务时可以指定 projectId，把任务归到某个项目下。
  删除项目时可以选择是否同时删除项目下的任务。
"""

from base import APIClient


class ProjectAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def create(self, name, description=None):
        """创建项目

        Args:
            name:        项目名称
            description: 项目描述（可选）

        Returns:
            requests.Response（201 + 项目信息）
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        return self.client.post("/api/v1/projects", json=payload)

    def list_projects(self, page=1, pageSize=10):
        """获取项目列表（分页）

        Args:
            page:     页码，默认 1
            pageSize: 每页数量，默认 10

        Returns:
            requests.Response（200 + 分页的项目列表）
        """
        return self.client.get("/api/v1/projects", params={
            "page": page,
            "pageSize": pageSize,
        })

    def get_project(self, project_id):
        """获取项目详情

        Args:
            project_id: 项目 ID

        Returns:
            requests.Response（200 + 项目详情，404 如果不存在）
        """
        return self.client.get(f"/api/v1/projects/{project_id}")

    def update(self, project_id, name=None, description=None):
        """更新项目

        Args:
            project_id:  项目 ID
            name:        新名称（可选）
            description: 新描述（可选）

        Returns:
            requests.Response（200 + 更新后的项目信息）
        """
        payload = {}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        return self.client.put(f"/api/v1/projects/{project_id}", json=payload)

    def delete(self, project_id):
        """删除项目

        Args:
            project_id: 项目 ID

        Returns:
            requests.Response（200 表示成功，404 如果不存在）
        """
        return self.client.delete(f"/api/v1/projects/{project_id}")
