"""项目模块接口封装

对应 Mock 的 4 个接口：
  POST   /api/v1/projects
  GET    /api/v1/projects
  GET    /api/v1/projects/:id
  DELETE /api/v1/projects/:id
"""


class ProjectAPI:
    def __init__(self, client):
        self.client = client

    def create(self, name, description=None):
        """创建项目"""
        payload = {"name": name}
        if description:
            payload["description"] = description
        return self.client.post("/api/v1/projects", json=payload)

    def list(self, page=1, pageSize=10):
        """获取项目列表"""
        return self.client.get("/api/v1/projects", params={
            "page": page,
            "pageSize": pageSize,
        })

    def get_detail(self, project_id):
        """获取项目详情（含关联任务）"""
        return self.client.get(f"/api/v1/projects/{project_id}")

    def delete(self, project_id):
        """删除项目"""
        return self.client.delete(f"/api/v1/projects/{project_id}")
