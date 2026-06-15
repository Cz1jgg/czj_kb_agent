# CZJ-KB-Agent：个人 RAG 知识库问答系统

> 基于 Python + FastAPI + LangChain + FAISS 构建的轻量化 RAG（检索增强生成）知识库 Agent，支持文档解析、向量存储、智能问答，可对接 Java 服务调用接口。

---

## 功能简介

本项目是一个个人 Demo 级别的 RAG 知识库问答后端服务，核心功能包括：

- **文档解析**：支持 TXT、PDF、DOCX、MD 等多种格式文档的自动解析
- **文本分块**：基于 LangChain RecursiveCharacterTextSplitter 的智能分块
- **向量存储**：使用 FAISS 向量库进行文本向量化和持久化存储
- **智能问答**：结合检索与 LLM 生成，提供精准的知识库问答能力
- **接口服务**：标准化 RESTful API，便于 Java 服务或其他前端集成

---

## 核心特性

| 特性 | 说明 |
|------|------|
| 轻量化设计 | 无需复杂中间件，单进程即可运行 |
| 多格式支持 | TXT / PDF / DOCX / MD / Markdown |
| 向量持久化 | FAISS 本地存储，重启不丢失 |
| OpenAI 兼容 | 支持火山方舟豆包、通义千问、DeepSeek 等 |
| 统一响应格式 | 所有接口返回标准 JSON 结构 |
| 异常捕获完善 | 友好的错误提示，便于排查 |

---

## 技术栈清单

| 类别 | 技术/框架 | 版本要求 |
|------|----------|---------|
| **Web 框架** | FastAPI | >= 0.110.0 |
| **ASGI 服务器** | Uvicorn | >= 0.27.0 |
| **LLM 框架** | LangChain | >= 0.1.10 |
| **向量数据库** | FAISS (CPU) | >= 1.8.0 |
| **PDF 解析** | PyPDF2 | >= 3.0.0 |
| **DOCX 解析** | python-docx | >= 1.1.0 |
| **配置管理** | PyYAML + python-dotenv | >= 6.0 / >= 1.0.0 |
| **数据验证** | Pydantic | >= 2.5.0 |
| **HTTP 客户端** | requests | >= 2.31.0 |
| **运行环境** | Python | >= 3.9 |
| **操作系统** | Windows | 10/11 |

---

## 项目目录结构

```
czj_kb_agent/
├── api/                          # API 路由层
│   ├── v1/                       # v1 版本接口
│   │   ├── health_router.py      # 健康检查接口
│   │   ├── kb_router.py          # 知识库管理接口（上传/重建/列表）
│   │   └── qa_router.py          # 问答接口
│   └── deps.py                   # 依赖注入
│
├── config/                       # 配置文件目录
│   ├── settings.yaml             # 全局配置（服务端口、模型参数、分块配置等）
│   └── prompts.yaml              # 提示词模板配置
│
├── core/                         # 核心业务逻辑
│   ├── config_loader.py          # 配置加载器（yaml + env）
│   ├── document_parser.py        # 文档解析器（TXT/PDF/DOCX）
│   ├── text_splitter.py          # 文本分块器
│   ├── vector_store.py           # FAISS 向量库管理
│   └── rag_chain.py              # RAG 问答链组装
│
├── data/                         # 数据存储目录（运行时生成）
│   ├── documents/                # 上传的原始文档
│   ├── parsed/                   # 解析后的中间产物
│   └── vector_store/             # FAISS 向量库索引文件
│
├── docs/                         # 项目文档
│   └── issue-*.md                # 问题记录与解决方案
│
├── utils/                        # 工具模块
│   ├── logger.py                 # 日志配置
│   └── java_client.py            # Java 服务对接客户端
│
├── embedding_qwen.py             # 自定义通义 Embedding 类
├── main.py                       # FastAPI 应用入口
├── run.bat                       # Windows 一键启动脚本
├── requirements.txt              # Python 依赖清单
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略配置
├── test_kb_api.py                # API 接口测试脚本
└── README.md                     # 项目说明文档
```

---

## 运行环境配置

### 1. 环境要求

- Python >= 3.9
- Windows 10/11（适配路径处理）
- 网络环境可访问 LLM API（火山方舟/通义千问等）

### 2. 创建虚拟环境

```powershell
# 进入项目目录
cd czj_kb_agent

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate
```

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

依赖清单：

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
langchain>=0.1.10
langchain-community>=0.0.25
faiss-cpu>=1.8.0
pyyaml>=6.0
PyPDF2>=3.0.0
python-docx>=1.1.0
python-dotenv>=1.0.0
pydantic>=2.5.0
requests>=2.31.0
```

---

## 环境变量配置

### 1. 复制示例文件

```powershell
copy .env.example .env
```

### 2. 编辑 `.env` 文件

```ini
# =========================================
#  火山方舟豆包 / OpenAI 兼容接口
# =========================================
ARK_API_KEY=your_ark_api_key_here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# =========================================
#  LLM 与 Embedding 模型（可选）
# =========================================
LLM_MODEL=
EMBEDDING_MODEL=

# =========================================
#  服务配置（可选）
# =========================================
SERVER_PORT=
LOG_LEVEL=
```

### 3. 配置项说明

| 变量名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| `ARK_API_KEY` | ✅ | 火山方舟/通义千问 API Key | `sk-xxx...` |
| `OPENAI_BASE_URL` | ❌ | API 接口地址 | `https://ark.cn-beijing.volces.com/api/v3` |
| `LLM_MODEL` | ❌ | LLM 模型名称（留空用 settings.yaml 默认值） | `doubao-lite-128k` |
| `EMBEDDING_MODEL` | ❌ | Embedding 模型名称 | `text-embedding-v3` |
| `SERVER_PORT` | ❌ | 服务端口（默认 8000） | `8000` |
| `LOG_LEVEL` | ❌ | 日志级别 | `INFO` |

---

## 服务启动方式

### 方式一：脚本启动（推荐）

```powershell
# Windows 一键启动
run.bat
```

`run.bat` 内容：
```batch
venv\Scripts\activate && python main.py
```

### 方式二：命令行启动

```powershell
# 激活虚拟环境
venv\Scripts\activate

# 启动服务
python main.py
```

或使用 uvicorn 直接启动：

```powershell
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 启动成功提示

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

---

## 接口文档入口

服务启动后，可通过以下地址访问 API 文档：

| 文档类型 | 地址 |
|----------|------|
| **Swagger UI** | http://127.0.0.1:8000/docs |
| **ReDoc** | http://127.0.0.1:8000/redoc |
| **OpenAPI JSON** | http://127.0.0.1:8000/openapi.json |

---

## 核心接口明细

### 统一响应格式

所有接口均返回以下标准格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码（200 成功，400/404/500 错误） |
| `message` | string | 提示信息 |
| `data` | object | 返回数据（成功时有值） |

---

### 1. 健康检查接口

**GET** `/api/v1/health`

| 属性 | 值 |
|------|-----|
| 请求方式 | GET |
| 功能 | 服务健康检查，供 Java 服务探活 |
| 认证 | 无 |

**请求示例：**

```bash
curl http://127.0.0.1:8000/api/v1/health
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "timestamp": 1718448000
  }
}
```

---

### 2. 文档上传接口

**POST** `/api/v1/kb/upload`

| 属性 | 值 |
|------|-----|
| 请求方式 | POST |
| Content-Type | multipart/form-data |
| 功能 | 上传文档并自动解析、分块、入库 |
| 认证 | 无 |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `file` | file | ✅ | 上传的文档文件 |

**请求示例：**

```bash
curl -X POST -F "file=@document.pdf" http://127.0.0.1:8000/api/v1/kb/upload
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "filename": "document.pdf",
    "saved_path": "data/documents/document.pdf",
    "doc_count": 5,
    "chunk_count": 12,
    "added_to_vector_store": 12
  }
}
```

---

### 3. 索引重建接口

**POST** `/api/v1/kb/rebuild`

| 属性 | 值 |
|------|-----|
| 请求方式 | POST |
| 功能 | 清空并重建向量库索引 |
| 认证 | 无 |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `clear_existing` | bool | ❌ | 是否清空现有索引（默认 true） |

**请求示例：**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/kb/rebuild?clear_existing=true"
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_files": 5,
    "total_docs": 10,
    "total_chunks": 50,
    "failed_files": []
  }
}
```

---

### 4. 文档列表接口

**GET** `/api/v1/kb/list`

| 属性 | 值 |
|------|-----|
| 请求方式 | GET |
| 功能 | 获取已上传的文档列表 |
| 认证 | 无 |

**请求示例：**

```bash
curl http://127.0.0.1:8000/api/v1/kb/list
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "files": [
      {
        "filename": "document.pdf",
        "path": "data/documents/document.pdf",
        "size": 102400,
        "modified_at": "2024-06-15 10:00:00"
      }
    ],
    "total": 1
  }
}
```

---

### 5. 知识库状态接口

**GET** `/api/v1/kb/status`

| 属性 | 值 |
|------|-----|
| 请求方式 | GET |
| 功能 | 获取向量库状态信息 |
| 认证 | 无 |

**请求示例：**

```bash
curl http://127.0.0.1:8000/api/v1/kb/status
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "vector_store_exists": true,
    "doc_count": 50,
    "uploaded_files_count": 5,
    "documents_dir": "data/documents",
    "vector_store_dir": "data/vector_store"
  }
}
```

---

### 6. 问答接口

**POST** `/api/v1/qa/ask`

| 属性 | 值 |
|------|-----|
| 请求方式 | POST |
| Content-Type | application/json |
| 功能 | 基于知识库进行智能问答 |
| 认证 | 无 |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `question` | string | ✅ | 用户问题 |
| `kb_id` | string | ❌ | 知识库 ID（默认 "default"） |
| `top_k` | int | ❌ | 检索文档数（默认 4） |

**请求示例：**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "如何重置密码？", "top_k": 4}'
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "answer": "根据文档说明，重置密码需要...",
    "sources": [
      {
        "id": 0,
        "title": "用户手册.pdf",
        "page": 5,
        "content": "重置密码步骤：1. 点击登录页面的..."
      }
    ]
  }
}
```

---

### 7. 删除文档接口

**DELETE** `/api/v1/kb/doc/{doc_id}`

| 属性 | 值 |
|------|-----|
| 请求方式 | DELETE |
| 功能 | 删除指定文档文件 |
| 认证 | 无 |

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `doc_id` | string | ✅ | 文档文件名（URL 路径参数） |

**请求示例：**

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/kb/doc/document.pdf
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "deleted": "document.pdf",
    "note": "文件已删除，建议调用 rebuild 接口重建索引"
  }
}
```

---

## 完整业务使用流程

### 流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  上传文档   │ ──> │  文档解析   │ ──> │  文本分块   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  用户提问   │ ──> │  向量检索   │ ──> │  LLM 生成   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                      ┌─────────────┐
                                      │  返回答案   │
                                      └─────────────┘
```

### 步骤详解

#### Step 1：启动服务

```powershell
run.bat
```

#### Step 2：上传文档

```bash
# 上传 PDF 文档
curl -X POST -F "file=@knowledge.pdf" http://127.0.0.1:8000/api/v1/kb/upload

# 上传 TXT 文档
curl -X POST -F "file=@notes.txt" http://127.0.0.1:8000/api/v1/kb/upload
```

#### Step 3：检查文档列表

```bash
curl http://127.0.0.1:8000/api/v1/kb/list
```

#### Step 4：重建索引（可选）

```bash
curl -X POST http://127.0.0.1:8000/api/v1/kb/rebuild
```

#### Step 5：进行问答

```bash
curl -X POST http://127.0.0.1:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "文档中提到的核心内容是什么？"}'
```

#### Step 6：查看知识库状态

```bash
curl http://127.0.0.1:8000/api/v1/kb/status
```

---

## 补充注意事项

### 1. 文件目录说明

| 目录 | 说明 | 备注 |
|------|------|------|
| `data/documents/` | 上传的原始文档 | 自动创建 |
| `data/vector_store/` | FAISS 向量库索引 | 包含 `index.faiss` 和 `index.pkl` |
| `data/parsed/` | 解析中间产物 | 可选使用 |
| `logs/` | 日志文件 | 运行时生成 |

**重要：** 删除文档后需调用 `/api/v1/kb/rebuild` 重建索引，否则向量库中仍保留旧数据。

### 2. API Key 安全

- `.env` 文件已在 `.gitignore` 中忽略，不会提交到 Git
- 切勿将 API Key 硬编码在代码中
- 生产环境建议使用环境变量或密钥管理服务

### 3. 向量库说明

- **FAISS 本地存储**：向量库持久化在 `data/vector_store/` 目录
- **重启不丢失**：服务重启后会自动加载已有索引
- **重建索引**：调用 `/api/v1/kb/rebuild` 会清空并重建向量库
- **Embedding 模型**：默认使用通义千问 `text-embedding-v3`

### 4. 支持的文件格式

| 格式 | 扩展名 | 解析方式 |
|------|--------|----------|
| PDF | `.pdf` | PyPDF2 逐页提取 |
| Word | `.docx`, `.doc` | python-docx |
| 文本 | `.txt` | 多编码兼容（UTF-8/GBK） |
| Markdown | `.md`, `.markdown` | 同文本处理 |

### 5. Java 服务对接

本项目提供标准化 RESTful API，Java 服务可通过 HTTP 调用：

```java
// Java 调用示例（使用 HttpClient）
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("http://127.0.0.1:8000/api/v1/qa/ask"))
    .header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString("{\"question\":\"测试问题\"}"))
    .build();
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
```

### 6. 测试脚本

项目提供 API 测试脚本 `test_kb_api.py`，可一键验证所有接口：

```powershell
python test_kb_api.py
```

---

## 常见问题

### Q1：服务启动失败，提示端口被占用？

修改 `config/settings.yaml` 中的 `server.port`，或通过环境变量 `SERVER_PORT` 指定其他端口。

### Q2：上传文档后问答无结果？

检查向量库状态 `/api/v1/kb/status`，确认 `doc_count > 0`。若为 0，调用 `/api/v1/kb/rebuild` 重建索引。

### Q3：Embedding API 报错？

确认 `.env` 中 `ARK_API_KEY` 已正确配置，且 API Key 有效。

### Q4：PDF 解析失败？

部分 PDF 可能加密或损坏，尝试使用未加密的 PDF 或检查文件完整性。

---

## License

MIT License

---

## 联系方式

个人 Demo 项目，仅供学习参考。如有问题，欢迎提交 Issue。