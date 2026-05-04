# xAgent - AI Agent 智能体系统

一个功能完整的 AI Agent 系统，采用前后端分离架构，支持多 LLM 后端、工具调用、记忆管理、多 Agent 协作等核心能力。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│                  Nginx (Port 8088)               │
│              反向代理 & 负载均衡                    │
├────────────────────┬────────────────────────────┤
│   Frontend (React) │    Backend (FastAPI)        │
│   - 对话界面        │    - Agent 引擎             │
│   - Agent 管理      │    - LLM 适配层             │
│   - 工具管理        │    - 工具系统               │
│   - 系统监控        │    - 记忆管理               │
│                    │    - 可观测性               │
├────────────────────┴────────────────────────────┤
│          PostgreSQL  │  Redis  │  ChromaDB       │
└─────────────────────────────────────────────────┘
```

## ✨ 核心能力

### 1. 模块化架构
- 前后端分离，React + FastAPI
- 插件化工具系统，支持动态注册
- 可插拔 LLM 后端

### 2. 规划与推理
- ReAct (Think → Plan → Act → Observe → Reflect) 推理循环
- 自动任务分解与动态重规划
- 周期性反思机制

### 3. 工具使用
- 内置工具：网页搜索、计算器、代码执行、文件读取
- MCP (Model Context Protocol) 协议支持
- 沙箱执行环境，超时与权限控制
- 人机协作审批流程

### 4. 记忆系统
- **短期记忆**：对话上下文，Token 感知窗口管理
- **长期记忆**：ChromaDB 向量存储，语义检索
- **工作记忆**：任务状态、计划、观察、反思

### 5. LLM 后端
- OpenAI (GPT-4, GPT-3.5-turbo 等)
- Anthropic (Claude 3.5, Claude 3 等)
- 本地模型 (Ollama, vLLM, LM Studio)

### 6. 多 Agent 协作
- 依赖感知的并行执行
- 信号量并发控制
- Pipeline 流水线模式

### 7. 可观测性
- 结构化日志 (structlog)
- 执行追踪 (Trace/Span)
- Prometheus 指标监控

### 8. 流程控制
- 人机协作 (Human-in-the-Loop)
- 错误恢复与重试
- 并发执行控制

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- (可选) OpenAI API Key 或 Anthropic API Key

### 1. 克隆项目

```bash
git clone <repo-url>
cd xAgent
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 访问系统

打开浏览器访问 **http://localhost:8088**

## 📁 项目结构

```
xAgent/
├── backend/                    # 后端 Python 应用
│   ├── app/
│   │   ├── agent/              # Agent 引擎
│   │   │   ├── engine.py       # 核心 ReAct 循环
│   │   │   ├── planner.py      # 任务规划器
│   │   │   └── orchestrator.py # 多 Agent 编排
│   │   ├── api/                # API 路由
│   │   │   ├── chat.py         # 对话接口
│   │   │   ├── agents.py       # Agent CRUD
│   │   │   ├── tools.py        # 工具管理
│   │   │   └── system.py       # 系统监控
│   │   ├── llm/                # LLM 适配层
│   │   │   ├── openai_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   └── local_provider.py
│   │   ├── memory/             # 记忆系统
│   │   │   ├── short_term.py   # 短期记忆
│   │   │   ├── long_term.py    # 长期记忆 (ChromaDB)
│   │   │   └── working.py      # 工作记忆
│   │   ├── models/             # 数据库模型
│   │   ├── observability/      # 可观测性
│   │   ├── tools/              # 工具系统
│   │   │   ├── builtin/        # 内置工具
│   │   │   ├── sandbox.py      # 沙箱执行
│   │   │   ├── manager.py      # 工具管理器
│   │   │   └── mcp.py          # MCP 协议
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   └── main.py             # FastAPI 入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # 前端 React 应用
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   ├── pages/              # 页面组件
│   │   │   ├── ChatPage.js     # 对话页面
│   │   │   ├── AgentsPage.js   # Agent 管理
│   │   │   ├── ToolsPage.js    # 工具管理
│   │   │   └── MonitorPage.js  # 系统监控
│   │   ├── services/           # API 服务
│   │   ├── store/              # 状态管理 (Zustand)
│   │   └── App.js              # 路由入口
│   ├── Dockerfile
│   └── package.json
├── nginx/                      # Nginx 反向代理
│   └── nginx.conf
├── docker-compose.yml          # Docker 编排
├── .env.example                # 环境变量模板
└── README.md
```

## 🔌 API 接口

### 对话
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息 |
| POST | `/api/chat/stream` | 流式发送消息 (SSE) |
| GET | `/api/chat/conversations` | 获取对话列表 |
| GET | `/api/chat/conversations/:id` | 获取对话详情 |
| DELETE | `/api/chat/conversations/:id` | 删除对话 |

### Agent 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents` | 获取 Agent 列表 |
| POST | `/api/agents` | 创建 Agent |
| GET | `/api/agents/:id` | 获取 Agent 详情 |
| PUT | `/api/agents/:id` | 更新 Agent |
| DELETE | `/api/agents/:id` | 删除 Agent |
| GET | `/api/agents/:id/executions` | 获取执行历史 |

### 工具
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tools` | 获取工具列表 |
| POST | `/api/tools/execute` | 执行工具 |
| POST | `/api/tools/approve/:id` | 批准工具执行 |
| POST | `/api/tools/reject/:id` | 拒绝工具执行 |

### 系统
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/health` | 健康检查 |
| GET | `/api/system/stats` | 系统统计 |
| GET | `/api/system/traces` | 执行追踪 |
| GET | `/api/system/metrics` | Prometheus 指标 |

## 🛠️ 开发指南

### 本地开发（不使用 Docker）

**后端：**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm start
```

### 添加自定义工具

在 `backend/app/tools/builtin/` 下创建新文件：

```python
from app.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的自定义工具"
    parameters = {
        "input": {
            "type": "string",
            "description": "输入参数",
            "required": True
        }
    }

    async def execute(self, **kwargs) -> ToolResult:
        result = do_something(kwargs["input"])
        return ToolResult(success=True, data=result)
```

然后在 `builtin/__init__.py` 中注册。

### 添加新的 LLM 提供商

继承 `BaseLLMProvider` 并实现 `chat()` 和 `chat_stream()` 方法，然后在 `factory.py` 中注册。

## 📊 监控

- **系统监控面板**：http://localhost:8088/monitor
- **Prometheus 指标**：http://localhost:8088/api/system/metrics
- **健康检查**：http://localhost:8088/api/system/health

## 📝 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18, Tailwind CSS, Zustand, React Router |
| 后端 | Python 3.11, FastAPI, SQLAlchemy (async), Pydantic |
| 数据库 | PostgreSQL 15, Redis 7 |
| 向量存储 | ChromaDB |
| 部署 | Docker, Docker Compose, Nginx |
| 可观测性 | structlog, Prometheus |

## 📄 License

MIT License
