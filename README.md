# AIStudio 接口自动化测试框架

> 基于 **requests + pytest + allure** 的 API 自动化测试框架  
> 用于测试 AIStudio Mock API 的认证、模型、项目、任务、聊天、用量统计等模块

---

## 📁 项目结构

```
aistudio-api-tests/
├── api/                    # 🔌 接口层 — 封装 HTTP 请求，只关心 URL 和参数
│   ├── __init__.py         #   统一导出所有 API 类
│   ├── auth_api.py         #   认证相关：注册、登录、登出、Token 刷新
│   ├── chat_api.py         #   聊天补全、聊天历史
│   ├── model_api.py        #   模型列表、模型详情、模型状态
│   ├── project_api.py      #   项目 CRUD
│   ├── task_api.py         #   任务提交、查询、取消、删除
│   └── usage_api.py        #   用量配额、用量统计
│
├── base/                   # 🧱 基础层 — 通用工具，被所有层复用
│   ├── __init__.py         #   统一导出
│   ├── http_client.py      #   HTTP 客户端（requests.Session 封装 + Allure 记录）
│   ├── assertions.py       #   通用断言（成功/失败/分页/JSON Schema/响应时间）
│   ├── data_loader.py      #   YAML/JSON 测试数据加载
│   └── helpers.py          #   工具函数（任务轮询、请求重试）
│
├── config/                 # ⚙️ 配置层
│   └── settings.py         #   环境变量、Base URL、测试账号、已知模型 ID
│
├── data/                   # 📊 测试数据 — YAML 格式，数据驱动
│   ├── register_data.yaml  #   注册场景：正常 + 各种非法参数
│   ├── chat_data.yaml      #   聊天场景：单轮/多轮 + 参数校验
│   └── generate_data.yaml  #   生成场景：文本/图片生成 + 参数校验
│
├── service/                # 🏭 业务层 — 编排多个 API 调用，封装业务流程
│   ├── __init__.py         #   统一导出
│   ├── auth_service.py     #   登录/注册业务流程（返回已认证的 client）
│   ├── project_service.py  #   项目+任务组合流程
│   └── task_service.py     #   提交任务→轮询→拿结果
│
├── tests/                  # 🧪 测试层 — 只写场景，不写轮询/参数构造
│   ├── test_auth.py        #   认证模块测试（健康检查/注册/登录/Token/登出/Profile）
│   ├── test_models.py      #   模型模块测试（列表/筛选/详情/状态）
│   ├── test_projects.py    #   项目模块测试（CRUD + 权限）
│   ├── test_tasks.py       #   任务模块测试（生成/查询/列表/取消/删除）
│   ├── test_chat.py        #   聊天模块测试（补全/多轮/历史/分页）
│   └── test_usage.py       #   用量模块测试（配额/统计/角色差异）
│
├── conftest.py             # 🔧 全局 Fixtures（角色 client、API 对象、临时数据）
├── pytest.ini              #   pytest 配置
├── requirements.txt        #   Python 依赖
├── Makefile                #   快捷命令
└── README.md               #   你正在看的这个文件
```

---

## 🏗️ 架构设计 — 三层模型

```
┌─────────────────────────────────────────────────┐
│                   tests/  测试层                  │
│  只关心：测什么场景、期望什么结果                      │
│  不关心：URL 怎么拼、参数怎么构造、任务怎么轮询          │
└──────────────────────┬──────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────┐
│                 service/  业务层                   │
│  封装业务流程：登录→拿 token、提交→轮询→拿结果         │
│  组合多个 API 调用，暴露一个方法给测试层               │
└──────────────────────┬──────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────┐
│                   api/  接口层                    │
│  封装 HTTP 请求：URL 拼接、参数构造、调用 http_client  │
│  每个 API 类对应一个业务域（auth/model/task/...）     │
└──────────────────────┬──────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────┐
│                   base/  基础层                   │
│  APIClient: 发请求 + Allure 记录                  │
│  断言工具、数据加载、轮询/重试                       │
└─────────────────────────────────────────────────┘
```

**调用链示例 — "提交文本生成任务并等完成"：**

```
test_poll_task_to_completion()
  → TaskService.submit_and_wait_text()        # service 层
    → TaskAPI.submit_text()                    # api 层 → POST /api/v1/generate/text
      → APIClient.post() → _request()         # base 层 → 发 HTTP + Allure 记录
    → wait_for_task()                          # base 层 → 轮询 GET /api/v1/tasks/{id}
  → 返回任务详情 dict
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
make install
# 或手动
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 全量运行
make test

# 详细输出（打印 print 和日志）
make test-verbose

# 只跑某个模块
pytest tests/test_auth.py -v

# 只跑某个用例
pytest tests/test_auth.py::TestLogin::test_login_success -v

# 按 marker 运行
pytest -m "not slow" -v
```

### 3. 生成 Allure 报告

```bash
# 需要先安装 allure-commandline
# macOS: brew install allure
# Linux: 参考 https://docs.qameta.io/allure/#_installing_a_commandline

make report
# 会自动打开浏览器展示报告
```

### 4. 切换环境

```bash
# 默认 dev（localhost:3000）
pytest

# 切到 staging
TEST_ENV=staging pytest
```

---

## 🧪 测试覆盖情况

| 模块 | 覆盖场景 | 用例数 |
|------|---------|--------|
| **认证** | 健康检查、注册(正常/参数校验/冲突)、登录(多角色/错误凭证)、Token 刷新、登出、Profile | ~15 |
| **模型** | 列表(全量/按类型/按 provider/按状态/按 tags)、详情(文本/图片/不存在)、状态 | ~12 |
| **项目** | CRUD、项目下提交任务、权限隔离 | ~10 |
| **任务** | 文本生成、图片生成、任务查询、轮询、列表筛选、取消、删除 | ~15 |
| **聊天** | 单轮/多轮对话、参数校验、多模型、历史分页 | ~10 |
| **用量** | 配额(多角色)、统计(7d/30d/90d)、权限 | ~8 |

---

## 🔑 核心概念

### Fixture 体系

```
conftest.py 定义的 Fixtures：

creator_client ──→ creator_auth_api
               ──→ creator_model_api
               ──→ creator_project_api
               ──→ creator_task_api
               ──→ creator_chat_api
               ──→ creator_usage_api
               ──→ creator_task_service
               ──→ creator_project_service

admin_client   ──→ 直接在测试中用
trial_client   ──→ 直接在测试中用

unauthed_client        → 测试 401 场景
new_user_client        → 每次调用注册新用户（function 级隔离）
temp_project           → 创建临时项目 + 自动清理
```

### 数据驱动

测试数据放 `data/*.yaml`，用 `load_yaml()` 加载 + `@pytest.mark.parametrize` 驱动：

```python
@pytest.mark.parametrize("case", load_yaml("register_data.yaml")["register_invalid"])
def test_register_invalid(self, case):
    resp = auth.client.post("/api/v1/auth/register", json=case["data"])
    assert resp.status_code == case["expected_status"]
```

新增测试数据只需改 YAML，不用改代码。

---

## 🛠️ Makefile 命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装 Python 依赖 |
| `make test` | 运行全部测试 |
| `make test-verbose` | 详细模式运行 |
| `make report` | 生成并打开 Allure 报告 |
| `make clean` | 清理报告和缓存 |

---

## 📝 学习笔记

### 这个框架教你什么？

1. **分层思想** — 接口/业务/测试三层分离，各层只关心自己的事
2. **数据驱动** — 测试数据和测试逻辑解耦，扩展用例零代码改动
3. **Fixture 复用** — pytest fixture 按角色/session 隔离，避免重复登录
4. **Allure 报告** — 自动记录请求/响应，报告可读性强
5. **业务封装** — 轮询、重试等通用逻辑收拢到 service/base 层

### 怎么加新模块？

1. `api/` 新建 `xxx_api.py`，封装接口调用
2. `api/__init__.py` 添加导出
3. `data/` 新建 `xxx_data.yaml`，写测试数据
4. （可选）`service/` 新建 `xxx_service.py`，封装业务流程
5. `tests/` 新建 `test_xxx.py`，写测试用例
6. `conftest.py` 添加对应的 fixture
