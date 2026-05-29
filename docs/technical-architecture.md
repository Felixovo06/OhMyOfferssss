# AI 面试抽题网站技术架构

## 1. 架构目标

项目采用前后端分离，并且前后端使用不同语言降低职责混淆：

- 前端：TypeScript / Next.js，负责 UI、交互、状态和用户体验。
- 后端：Python / FastAPI，负责业务逻辑、数据、权限、飞书 API、AI 能力和任务编排。

第一版目标是快速做出可用 MVP，同时保持两边可以独立开发、独立测试、独立部署。

核心原则：

- 前后端只通过 HTTP API 和 OpenAPI 契约协作。
- 前端不直接访问数据库、Redis、飞书 API 或大模型 API。
- 后端不写前端页面逻辑，只提供稳定业务接口。
- 不做 TS shared package 绑定前后端，避免两边职责重新混在一起。
- 后端以 OpenAPI 作为唯一接口事实来源，前端可基于 OpenAPI 生成 API client。
- 所有 AI 能力通过统一 LLM Client 封装。
- 飞书导入和 AI 抽题结果必须支持人工确认。
- PDF 简历优先用文本解析，扫描件再考虑 OCR 或视觉模型兜底。

## 2. 技术选型

### 2.1 前端

- 框架：Next.js App Router
- 语言：TypeScript
- UI：Tailwind CSS + shadcn/ui
- 表单：React Hook Form + Zod
- 请求：TanStack Query
- API Client：基于 OpenAPI 生成，或封装 typed fetch
- 图标：lucide-react
- 状态：优先 URL state + server state，必要时使用 Zustand
- 设计要求：涉及 UI/UX 必须使用 `ui-ux-pro-max`

### 2.2 后端

- 框架：FastAPI
- 语言：Python 3.12+
- 数据模型/校验：Pydantic v2
- ORM：SQLAlchemy 2.0
- 迁移：Alembic
- 数据库：PostgreSQL
- 缓存：Redis
- 异步任务：第一版先用接口状态轮询；后续可接 Celery/RQ/Arq
- 鉴权：JWT + HttpOnly Cookie 或 Bearer Token
- API 文档：FastAPI 自动生成 OpenAPI
- 测试：pytest
- 代码质量：ruff + mypy

### 2.3 AI 与外部服务

- 主要模型：`deepseek4flash`
- 思考模式：关闭
- API：OpenAI-compatible API
- 飞书：企业自建应用 + `tenant_access_token`
- 简历解析：文本型 PDF 直接解析，扫描件 PDF 标记为需要 OCR

### 2.4 基础设施

- PostgreSQL 主机：`39.104.87.235:5432`
- Redis 主机：`39.104.87.235:6379`
- 真实密码和 API Key 只放 `.env` 或部署平台密钥管理，不提交仓库。

## 3. 仓库结构

建议使用 monorepo，但前端和后端保持语言、依赖和运行时隔离。

```text
apps/
  web/
  api/
docs/
```

不设置 `packages/shared` 作为强共享代码。共享边界只通过：

- OpenAPI schema
- API 文档
- 少量人工维护的枚举说明

### 3.1 前端目录

```text
apps/web/
  app/
  components/
    ui/
    layout/
  features/
    auth/
    dashboard/
    groups/
    banks/
    imports/
    resumes/
    interviews/
  lib/
    api/
    query/
    utils/
```

前端约定：

- `app/` 只放路由、layout 和页面入口。
- `features/*` 放业务页面组件、hooks、mock、局部类型。
- `components/ui` 放基础 UI。
- `lib/api` 放 API client，不直接散落 `fetch`。
- UI 可以先用 mock 数据开发，但字段命名要贴近 OpenAPI。
- 涉及 UI/UX 的页面和组件必须用 `ui-ux-pro-max` 设计或评审。

### 3.2 后端目录

```text
apps/api/
  app/
    main.py
    api/
      v1/
        auth.py
        groups.py
        question_banks.py
        questions.py
        imports.py
        resumes.py
        interviews.py
    core/
      config.py
      security.py
      errors.py
    db/
      session.py
      models/
      repositories/
      migrations/
    schemas/
    services/
      auth/
      groups/
      question_banks/
      imports/
      resumes/
      interviews/
      llm/
      feishu/
    clients/
      feishu.py
      llm.py
      redis.py
  tests/
```

后端约定：

- `api/v1` 只处理 HTTP 入参、鉴权上下文和响应。
- `schemas` 放 Pydantic request/response schema。
- `services` 处理业务流程。
- `repositories` 处理数据库读写。
- `clients` 封装外部服务，例如 Feishu Client、LLM Client、Redis Client。
- 数据库迁移只通过 Alembic。

## 4. 模块划分

### 4.1 Auth

职责：

- 登录、退出。
- 获取当前用户。
- 保护 API。
- 管理 token/cookie。

### 4.2 Groups

职责：

- 创建小组。
- 邀请用户加入小组。
- 接受邀请。
- 查询小组成员。
- 校验小组权限。

第一版角色：

- `owner`：管理成员、题库和导入。
- `member`：使用小组题库进行面试。

### 4.3 Question Banks / Questions

职责：

- 题库 CRUD。
- 题目 CRUD。
- 标签管理。
- 难度分数管理。
- 个人题库和小组题库权限校验。
- 给普通面试和客制化面试提供候选题。

### 4.4 Feishu Import

职责：

- 解析飞书文档链接。
- 获取并缓存 `tenant_access_token`。
- 拉取飞书文档 blocks。
- blocks 转 normalized text。
- 创建导入批次。
- 保存 AI 抽取出的待确认题目。
- 确认后写入正式题库。

### 4.5 LLM

职责：

- 统一读取模型配置。
- 默认关闭思考模式。
- 封装结构化输出。
- 处理超时、重试和错误。

能力：

- 飞书内容抽题。
- 标签生成。
- 难度评分。
- 普通面试抽题。
- 简历摘要生成。
- 客制化面试抽题。
- 回答评分。
- 追问生成。
- 会话总结。

### 4.6 Resume

职责：

- PDF 简历上传。
- PDF 文本解析。
- 判断扫描件或图片型 PDF。
- 保存原文和结构化摘要。
- 提供客制化面试上下文。

边界：

- 文本型 PDF 第一版必须支持。
- 扫描件 PDF 第一版可以提示需要 OCR，不强制支持。

### 4.7 Interviews

职责：

- 创建普通面试。
- 创建客制化面试。
- 保存抽题理由。
- 保存回答。
- AI 评分。
- 追问。
- 会话总结。

面试模式：

- `normal`：普通面试，大模型直接基于题库候选题抽题。
- `custom`：客制化面试，大模型基于简历摘要和题库候选题抽题。

## 5. 数据模型

核心表：

- `users`
- `groups`
- `group_members`
- `group_invitations`
- `question_banks`
- `questions`
- `tags`
- `question_tags`
- `feishu_sources`
- `import_batches`
- `import_items`
- `resumes`
- `interview_sessions`
- `interview_questions`
- `interview_answers`

关键字段：

- `question_banks.group_id`：题库所属小组，个人题库为空。
- `questions.difficulty_score`：0 到 100。
- `import_items.status`：待确认、已确认、已丢弃。
- `resumes.parse_status`：解析中、已完成、需要 OCR、失败。
- `interview_sessions.mode`：`normal` 或 `custom`。
- `interview_sessions.resume_id`：客制化面试使用。
- `interview_questions.selection_reason`：大模型抽题理由。
- `interview_answers.ai_feedback_json`：AI 评分和反馈。

## 6. API 规范

### 6.1 基础规范

- API 前缀：`/api/v1`
- 数据格式：JSON
- 时间格式：ISO 8601
- 分页参数：`page`、`page_size`
- 认证方式：HttpOnly Cookie 或 `Authorization: Bearer <token>`
- OpenAPI 地址：`/openapi.json`
- Swagger 地址：`/docs`

统一响应：

```json
{
  "success": true,
  "data": {},
  "request_id": "req_xxx"
}
```

统一错误：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数错误",
    "details": {}
  },
  "request_id": "req_xxx"
}
```

命名约定：

- API JSON 字段使用 `snake_case`，贴合 Python 后端。
- 前端 API client 可以在 UI 层转换成 camelCase，也可以直接使用 snake_case。
- 枚举值使用小写字符串，例如 `normal`、`custom`、`needs_ocr`。

### 6.2 Auth API

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

### 6.3 Group API

```text
GET  /api/v1/groups
POST /api/v1/groups
GET  /api/v1/groups/{group_id}
GET  /api/v1/groups/{group_id}/members
POST /api/v1/groups/{group_id}/invitations
GET  /api/v1/invitations/{token}
POST /api/v1/invitations/{token}/accept
```

### 6.4 Question Bank API

```text
GET    /api/v1/question-banks
POST   /api/v1/question-banks
GET    /api/v1/question-banks/{bank_id}
PATCH  /api/v1/question-banks/{bank_id}
DELETE /api/v1/question-banks/{bank_id}
GET    /api/v1/question-banks/{bank_id}/questions
POST   /api/v1/question-banks/{bank_id}/questions
PATCH  /api/v1/questions/{question_id}
DELETE /api/v1/questions/{question_id}
GET    /api/v1/tags
```

### 6.5 Feishu Import API

```text
POST  /api/v1/imports/feishu
GET   /api/v1/imports/{batch_id}
GET   /api/v1/imports/{batch_id}/items
PATCH /api/v1/import-items/{item_id}
POST  /api/v1/imports/{batch_id}/confirm
```

### 6.6 Resume API

```text
POST /api/v1/resumes
GET  /api/v1/resumes
GET  /api/v1/resumes/{resume_id}
POST /api/v1/resumes/{resume_id}/parse
```

### 6.7 Interview API

```text
POST /api/v1/interviews
GET  /api/v1/interviews/{session_id}
POST /api/v1/interviews/{session_id}/answers
POST /api/v1/interviews/{session_id}/next
POST /api/v1/interviews/{session_id}/finish
GET  /api/v1/interviews/{session_id}/summary
```

创建普通面试：

```json
{
  "mode": "normal",
  "bank_ids": ["bank_1"],
  "tag_ids": ["tag_1"],
  "question_count": 8,
  "difficulty_preference": "medium_to_hard",
  "goal": "准备前端一面",
  "resume_id": null
}
```

创建客制化面试：

```json
{
  "mode": "custom",
  "bank_ids": ["bank_1"],
  "tag_ids": ["tag_1"],
  "question_count": 8,
  "difficulty_preference": "medium_to_hard",
  "goal": "前端开发岗位",
  "resume_id": "resume_1"
}
```

## 7. 代码规范

### 7.1 通用

- 所有外部输入必须用 schema 校验。
- 所有敏感信息从环境变量读取。
- 不在日志中输出密码、token、API Key。
- 错误信息给用户看时要可理解，日志中保留排查信息。
- API 变更必须同步更新 OpenAPI 文档。

### 7.2 前端规范

- 涉及 UI/UX 必须使用 `ui-ux-pro-max`。
- 页面优先使用 feature 组件组合，不在 page 文件里堆复杂逻辑。
- 表单必须有 label、校验提示和提交状态。
- 长耗时操作必须有 loading 状态。
- 列表必须有 empty 状态。
- 错误必须有可读提示。
- 删除、丢弃、批量确认等危险操作必须二次确认。
- 移动端不能出现严重横向溢出。
- 前端通过 OpenAPI client 或统一 API client 调后端，不手写散落请求。

### 7.3 后端规范

- FastAPI router 不写复杂业务逻辑。
- Service 负责业务编排。
- Repository 负责数据访问。
- API 写操作必须校验权限。
- 批量入库必须使用事务。
- 大模型输出必须用 Pydantic schema 校验。
- 飞书 API 调用必须处理分页、限流和权限错误。
- Python 代码必须通过 ruff。
- 关键业务逻辑需要 pytest 覆盖。

### 7.4 协作规范

- 前端和后端可以独立分支开发。
- 后端先提供 OpenAPI 契约和 mock 响应。
- 前端可以先用 mock 数据开发 UI，但字段必须贴近 OpenAPI。
- API 字段变更必须先改 OpenAPI，再通知前端。
- 联调前必须确认接口响应结构稳定。

## 8. 环境变量

### 8.1 后端

```text
DATABASE_URL
REDIS_URL
JWT_SECRET
LLM_MODEL
LLM_THINKING_ENABLED
LLM_API_KEY
LLM_BASE_URL
FEISHU_APP_ID
FEISHU_APP_SECRET
FEISHU_API_BASE_URL
```

### 8.2 前端

```text
NEXT_PUBLIC_API_BASE_URL
```

## 9. 后续演进

- Celery/RQ/Arq 后台任务。
- OCR 或视觉模型支持扫描件 PDF。
- 飞书知识库批量同步。
- 多组织权限。
- 语音面试。
- JD 导入后定制面试计划。
