# AI 面试抽题网站技术架构

## 1. 架构目标

项目采用前后端分离架构。前端专注页面、交互、状态和用户体验；后端专注业务能力、数据、权限、飞书 API、AI 能力和任务编排。

第一版目标是快速做出可用 MVP，同时保持后续可拆分、可联调、可部署。

核心原则：

- 前端和后端通过 HTTP API 契约协作。
- 前端不直接访问数据库、Redis、飞书 API 或大模型 API。
- 后端不关心页面细节，只提供稳定业务接口。
- 所有 AI 能力通过统一 LLM Client 封装。
- 飞书导入和 AI 抽题结果必须支持人工确认。
- PDF 简历优先用文本解析，扫描件再考虑 OCR 或视觉模型兜底。

## 2. 技术选型

### 2.1 前端

- 框架：Next.js App Router
- 语言：TypeScript
- UI：Tailwind CSS + shadcn/ui
- 表单：React Hook Form + Zod
- 请求：TanStack Query 或 SWR
- 图标：lucide-react
- 状态：优先 URL state + server state，必要时使用 Zustand
- 设计要求：涉及 UI/UX 必须使用 `ui-ux-pro-max`

### 2.2 后端

- 框架：NestJS
- 语言：TypeScript
- ORM：Prisma
- 数据库：PostgreSQL
- 缓存：Redis
- 队列：第一版可不用队列，长任务先用状态轮询；后续可接 BullMQ
- 鉴权：JWT + HttpOnly Cookie 或 Bearer Token
- API 文档：OpenAPI / Swagger
- 校验：Zod 或 class-validator，建议统一使用 Zod schema

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

建议使用 monorepo，便于前后端共享类型和 schema。

```text
apps/
  web/
    app/
    components/
    features/
    lib/
  api/
    src/
      modules/
      common/
      infra/
packages/
  shared/
    src/
      schemas/
      types/
docs/
```

### 3.1 前端目录

```text
apps/web/
  app/
  components/ui/
  components/layout/
  features/
    auth/
    dashboard/
    groups/
    banks/
    imports/
    resumes/
    interviews/
  lib/api/
  lib/query/
```

前端约定：

- `app/` 只放路由、layout 和页面入口。
- `features/*` 放业务页面组件、hooks、mock、局部类型。
- `components/ui` 放基础 UI。
- `lib/api` 放 API client，不直接散落 `fetch`。
- 涉及 UI/UX 的页面和组件必须用 `ui-ux-pro-max` 设计或评审。

### 3.2 后端目录

```text
apps/api/src/
  modules/
    auth/
    groups/
    question-banks/
    questions/
    imports/
    resumes/
    interviews/
    llm/
    feishu/
  common/
    guards/
    filters/
    pipes/
    schemas/
  infra/
    prisma/
    redis/
    config/
```

后端约定：

- 每个业务模块包含 controller、service、repository、schema。
- controller 只处理 HTTP 入参、鉴权上下文和响应。
- service 处理业务流程。
- repository 处理数据库读写。
- 外部服务通过 client 封装，例如 Feishu Client、LLM Client。

### 3.3 共享包

```text
packages/shared/src/
  schemas/
  types/
  constants/
```

共享内容：

- API request/response schema。
- 枚举，例如面试模式、难度标签、导入状态。
- 通用类型，例如分页、错误结构。

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
- 分页参数：`page`、`pageSize`
- 认证方式：HttpOnly Cookie 或 `Authorization: Bearer <token>`

统一响应：

```json
{
  "success": true,
  "data": {},
  "requestId": "req_xxx"
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
  "requestId": "req_xxx"
}
```

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
GET  /api/v1/groups/:groupId
GET  /api/v1/groups/:groupId/members
POST /api/v1/groups/:groupId/invitations
GET  /api/v1/invitations/:token
POST /api/v1/invitations/:token/accept
```

### 6.4 Question Bank API

```text
GET    /api/v1/question-banks
POST   /api/v1/question-banks
GET    /api/v1/question-banks/:bankId
PATCH  /api/v1/question-banks/:bankId
DELETE /api/v1/question-banks/:bankId
GET    /api/v1/question-banks/:bankId/questions
POST   /api/v1/question-banks/:bankId/questions
PATCH  /api/v1/questions/:questionId
DELETE /api/v1/questions/:questionId
GET    /api/v1/tags
```

### 6.5 Feishu Import API

```text
POST  /api/v1/imports/feishu
GET   /api/v1/imports/:batchId
GET   /api/v1/imports/:batchId/items
PATCH /api/v1/import-items/:itemId
POST  /api/v1/imports/:batchId/confirm
```

### 6.6 Resume API

```text
POST /api/v1/resumes
GET  /api/v1/resumes
GET  /api/v1/resumes/:resumeId
POST /api/v1/resumes/:resumeId/parse
```

### 6.7 Interview API

```text
POST /api/v1/interviews
GET  /api/v1/interviews/:sessionId
POST /api/v1/interviews/:sessionId/answers
POST /api/v1/interviews/:sessionId/next
POST /api/v1/interviews/:sessionId/finish
GET  /api/v1/interviews/:sessionId/summary
```

创建面试请求：

```json
{
  "mode": "normal",
  "bankIds": ["bank_1"],
  "tagIds": ["tag_1"],
  "questionCount": 8,
  "difficultyPreference": "medium_to_hard",
  "goal": "准备前端一面",
  "resumeId": null
}
```

客制化面试：

```json
{
  "mode": "custom",
  "bankIds": ["bank_1"],
  "tagIds": ["tag_1"],
  "questionCount": 8,
  "difficultyPreference": "medium_to_hard",
  "goal": "前端开发岗位",
  "resumeId": "resume_1"
}
```

## 7. 代码规范

### 7.1 通用

- 全项目使用 TypeScript。
- 禁止 `any` 泛滥，确实需要时必须局部说明。
- 所有外部输入必须用 schema 校验。
- 所有敏感信息从环境变量读取。
- 不在日志中输出密码、token、API Key。
- 错误信息给用户看时要可理解，日志中保留排查信息。

### 7.2 前端规范

- 涉及 UI/UX 必须使用 `ui-ux-pro-max`。
- 页面优先使用 feature 组件组合，不在 page 文件里堆复杂逻辑。
- 表单必须有 label、校验提示和提交状态。
- 长耗时操作必须有 loading 状态。
- 列表必须有 empty 状态。
- 错误必须有可读提示。
- 删除、丢弃、批量确认等危险操作必须二次确认。
- 移动端不能出现严重横向溢出。

### 7.3 后端规范

- Controller 不写复杂业务逻辑。
- Service 负责业务编排。
- Repository 负责数据访问。
- API 写操作必须校验权限。
- 批量入库必须使用事务。
- 大模型输出必须校验结构。
- 飞书 API 调用必须处理分页、限流和权限错误。

### 7.4 Git 与协作

- 前端和后端可以独立分支开发。
- API 变更必须同步更新共享 schema 和技术文档。
- 前端可以先用 mock 数据开发 UI，但字段必须贴近 API schema。
- 联调前必须确认接口响应结构稳定。

## 8. 环境变量

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

## 9. 后续演进

- BullMQ 后台任务。
- OCR 或视觉模型支持扫描件 PDF。
- 飞书知识库批量同步。
- 多组织权限。
- 语音面试。
- JD 导入后定制面试计划。
