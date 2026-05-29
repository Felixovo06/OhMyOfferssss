import type { QuestionBank, Question } from "@/types/bank"
import type { ImportBatch, ImportItem } from "@/types/import"
import type { InterviewSession, InterviewQuestion, InterviewSummary, InterviewConfig } from "@/types/interview"
import type { Resume } from "@/types/resume"

function delay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

let nextId = 1
function genId() {
  return `mock_${nextId++}`
}

const mockBanks: QuestionBank[] = [
  {
    id: "bank_1",
    name: "前端基础",
    description: "HTML, CSS, JavaScript 基础面试题",
    owner_id: "user_1",
    question_count: 12,
    tags: ["HTML", "CSS", "JavaScript"],
    created_at: "2026-05-01T00:00:00Z",
    updated_at: "2026-05-20T00:00:00Z",
  },
  {
    id: "bank_2",
    name: "React 深入",
    description: "React 核心概念、Hooks、性能优化",
    owner_id: "user_1",
    group_id: "group_1",
    question_count: 8,
    tags: ["React", "Hooks", "性能优化"],
    created_at: "2026-05-10T00:00:00Z",
    updated_at: "2026-05-22T00:00:00Z",
  },
  {
    id: "bank_3",
    name: "算法与数据结构",
    description: "常见面试算法题",
    owner_id: "user_1",
    question_count: 0,
    tags: ["算法"],
    created_at: "2026-05-25T00:00:00Z",
    updated_at: "2026-05-25T00:00:00Z",
  },
]

const mockQuestions: Record<string, Question[]> = {
  bank_1: [
    {
      id: "q_1",
      bank_id: "bank_1",
      content: "请解释 CSS 中的 BFC (Block Formatting Context) 是什么？如何创建？",
      answer: "BFC 是块级格式化上下文，是一个独立的渲染区域。创建方式包括：overflow 不为 visible、float、position absolute/fixed、display inline-block/flex/grid 等。",
      tags: ["CSS"],
      difficulty: 3,
      status: "active",
      created_at: "2026-05-01T00:00:00Z",
      updated_at: "2026-05-01T00:00:00Z",
    },
    {
      id: "q_2",
      bank_id: "bank_1",
      content: "JavaScript 中 var、let 和 const 的区别是什么？",
      answer: "var 有函数作用域和变量提升；let 和 const 有块级作用域，没有变量提升（暂时性死区）；const 声明常量，不能重新赋值。",
      tags: ["JavaScript"],
      difficulty: 1,
      status: "active",
      created_at: "2026-05-02T00:00:00Z",
      updated_at: "2026-05-02T00:00:00Z",
    },
    {
      id: "q_3",
      bank_id: "bank_1",
      content: "请解释事件委托（Event Delegation）的原理和应用场景。",
      answer: "事件委托利用事件冒泡机制，将子元素的事件处理挂载到父元素上。适合动态列表、大量相似元素等场景。",
      tags: ["JavaScript"],
      difficulty: 2,
      status: "active",
      created_at: "2026-05-03T00:00:00Z",
      updated_at: "2026-05-03T00:00:00Z",
    },
  ],
  bank_2: [
    {
      id: "q_4",
      bank_id: "bank_2",
      content: "React 中 useEffect 的依赖数组是如何工作的？",
      answer: "useEffect 在依赖项变化时执行回调。空数组 [] 只在挂载时执行；不传数组则在每次渲染时执行；传入依赖则在依赖变化时执行。",
      tags: ["React", "Hooks"],
      difficulty: 2,
      status: "active",
      created_at: "2026-05-10T00:00:00Z",
      updated_at: "2026-05-10T00:00:00Z",
    },
    {
      id: "q_5",
      bank_id: "bank_2",
      content: "React 中 key 属性的作用是什么？",
      answer: "key 帮助 React 识别哪些元素发生变化，用于优化 diff 算法，确保列表更新时的正确性和性能。",
      tags: ["React"],
      difficulty: 1,
      status: "disabled",
      created_at: "2026-05-11T00:00:00Z",
      updated_at: "2026-05-15T00:00:00Z",
    },
  ],
}

const mockImportBatches: ImportBatch[] = [
  {
    id: "import_1",
    source_url: "https://example.feishu.cn/doc/abc123",
    status: "completed",
    total_count: 5,
    confirmed_count: 3,
    created_at: "2026-05-20T00:00:00Z",
    updated_at: "2026-05-20T00:10:00Z",
  },
  {
    id: "import_2",
    source_url: "https://example.feishu.cn/doc/def456",
    status: "processing",
    total_count: 8,
    confirmed_count: 0,
    created_at: "2026-05-25T00:00:00Z",
    updated_at: "2026-05-25T00:02:00Z",
  },
]

const mockImportItems: Record<string, ImportItem[]> = {
  import_1: [
    {
      id: "item_1",
      batch_id: "import_1",
      question_content: "Vue.js 中 v-if 和 v-show 的区别是什么？",
      question_answer: "v-if 是条件渲染，切换时会销毁/重建元素；v-show 是 CSS display 切换。",
      tags: ["Vue"],
      difficulty: 1,
      status: "confirmed",
      confidence: 0.95,
    },
    {
      id: "item_2",
      batch_id: "import_1",
      question_content: "请解释 Vuex 的状态管理流程。",
      question_answer: "组件通过 dispatch action，action 通过 commit mutation，mutation 修改 state，state 响应式更新组件。",
      tags: ["Vue", "状态管理"],
      difficulty: 2,
      status: "confirmed",
      confidence: 0.92,
    },
    {
      id: "item_3",
      batch_id: "import_1",
      question_content: "CSS Flexbox 中 justify-content 和 align-items 的区别？",
      tags: ["CSS"],
      difficulty: 1,
      status: "confirmed",
      confidence: 0.88,
    },
    {
      id: "item_4",
      batch_id: "import_1",
      question_content: "HTTP 和 HTTPS 的区别是什么？详细说明 SSL/TLS 握手过程。",
      question_answer: "HTTPS 在 HTTP 基础上增加了 SSL/TLS 加密层。握手过程包括：ClientHello、ServerHello、证书验证、密钥交换、加密通信。",
      tags: ["网络"],
      difficulty: 3,
      status: "rejected",
      confidence: 0.65,
    },
    {
      id: "item_5",
      batch_id: "import_1",
      question_content: "请比较 RESTful API 和 GraphQL 的异同。",
      tags: ["API"],
      difficulty: 3,
      status: "pending",
      confidence: 0.72,
    },
  ],
  import_2: [
    {
      id: "item_6",
      batch_id: "import_2",
      question_content: "请解释 JavaScript 中的闭包（Closure）。",
      tags: ["JavaScript"],
      difficulty: 2,
      status: "pending",
      confidence: 0.9,
    },
  ],
}

export const mockBankApi = {
  getBanks: async () => {
    await delay()
    return [...mockBanks]
  },
  getBank: async (id: string) => {
    await delay()
    const bank = mockBanks.find((b) => b.id === id)
    if (!bank) throw new Error("题库不存在")
    return { ...bank }
  },
  createBank: async (data: { name: string; description?: string; group_id?: string }) => {
    await delay(600)
    const bank: QuestionBank = {
      id: genId(),
      name: data.name,
      description: data.description,
      owner_id: "user_1",
      question_count: 0,
      tags: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockBanks.unshift(bank)
    mockQuestions[bank.id] = []
    return bank
  },
  updateBank: async (id: string, data: { name?: string; description?: string }) => {
    await delay()
    const bank = mockBanks.find((b) => b.id === id)
    if (!bank) throw new Error("题库不存在")
    if (data.name !== undefined) bank.name = data.name
    if (data.description !== undefined) bank.description = data.description
    bank.updated_at = new Date().toISOString()
    return { ...bank }
  },
  deleteBank: async (id: string) => {
    await delay()
    const idx = mockBanks.findIndex((b) => b.id === id)
    if (idx === -1) throw new Error("题库不存在")
    mockBanks.splice(idx, 1)
    delete mockQuestions[id]
  },
  getQuestions: async (bankId: string, _filters?: { keyword?: string; difficulty?: number; tags?: string[]; status?: string }) => {
    await delay()
    let list = [...(mockQuestions[bankId] || [])]
    if (_filters?.keyword) {
      list = list.filter((q) => q.content.includes(_filters!.keyword!))
    }
    if (_filters?.difficulty) {
      list = list.filter((q) => q.difficulty === _filters!.difficulty)
    }
    if (_filters?.status) {
      list = list.filter((q) => q.status === _filters!.status)
    }
    return list
  },
  createQuestion: async (bankId: string, data: { content: string; answer?: string; tags?: string[]; difficulty?: number }) => {
    await delay(600)
    const question: Question = {
      id: genId(),
      bank_id: bankId,
      content: data.content,
      answer: data.answer,
      tags: data.tags || [],
      difficulty: data.difficulty || 1,
      status: "active",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    if (!mockQuestions[bankId]) mockQuestions[bankId] = []
    mockQuestions[bankId].unshift(question)
    const bank = mockBanks.find((b) => b.id === bankId)
    if (bank) bank.question_count = mockQuestions[bankId].length
    return question
  },
  updateQuestion: async (id: string, data: { content?: string; answer?: string; tags?: string[]; difficulty?: number; status?: string }) => {
    await delay()
    for (const list of Object.values(mockQuestions)) {
      const q = list.find((q) => q.id === id)
      if (q) {
        if (data.content !== undefined) q.content = data.content
        if (data.answer !== undefined) q.answer = data.answer
        if (data.tags !== undefined) q.tags = data.tags
        if (data.difficulty !== undefined) q.difficulty = data.difficulty
        if (data.status !== undefined) q.status = data.status as "active" | "disabled"
        q.updated_at = new Date().toISOString()
        return { ...q }
      }
    }
    throw new Error("题目不存在")
  },
  deleteQuestion: async (id: string) => {
    await delay()
    for (const [bankId, list] of Object.entries(mockQuestions)) {
      const idx = list.findIndex((q) => q.id === id)
      if (idx !== -1) {
        list.splice(idx, 1)
        const bank = mockBanks.find((b) => b.id === bankId)
        if (bank) bank.question_count = list.length
        return
      }
    }
    throw new Error("题目不存在")
  },
}

export const mockImportApi = {
  getBatches: async () => {
    await delay()
    return [...mockImportBatches]
  },
  getBatch: async (id: string) => {
    await delay()
    const batch = mockImportBatches.find((b) => b.id === id)
    if (!batch) throw new Error("导入批次不存在")
    return {
      batch: { ...batch },
      items: [...(mockImportItems[id] || [])],
    }
  },
  createImport: async (data: { url: string; bank_id?: string }) => {
    await delay(1500)
    const batch: ImportBatch = {
      id: genId(),
      source_url: data.url,
      bank_id: data.bank_id,
      status: "processing",
      total_count: 3,
      confirmed_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockImportBatches.unshift(batch)
    mockImportItems[batch.id] = [
      {
        id: genId(),
        batch_id: batch.id,
        question_content: "AI 从文档中抽取的示例题目 1",
        difficulty: 2,
        tags: ["示例"],
        status: "pending",
        confidence: 0.85,
      },
      {
        id: genId(),
        batch_id: batch.id,
        question_content: "AI 从文档中抽取的示例题目 2",
        question_answer: "这是参考答案",
        difficulty: 3,
        tags: ["示例"],
        status: "pending",
        confidence: 0.92,
      },
    ]
    return batch
  },
  confirmItem: async (itemId: string) => {
    await delay()
    for (const items of Object.values(mockImportItems)) {
      const item = items.find((i) => i.id === itemId)
      if (item) {
        item.status = "confirmed"
        const batch = mockImportBatches.find((b) => b.id === item.batch_id)
        if (batch) {
          batch.confirmed_count = items.filter((i) => i.status === "confirmed").length
          if (batch.confirmed_count === batch.total_count) batch.status = "completed"
        }
        return
      }
    }
    throw new Error("导入项不存在")
  },
  rejectItem: async (itemId: string) => {
    await delay()
    for (const items of Object.values(mockImportItems)) {
      const item = items.find((i) => i.id === itemId)
      if (item) {
        item.status = "rejected"
        return
      }
    }
    throw new Error("导入项不存在")
  },
  rejectAll: async (batchId: string) => {
    await delay()
    const items = mockImportItems[batchId]
    if (!items) throw new Error("导入批次不存在")
    let rejectedCount = 0
    items.forEach((i) => {
      if (i.status === "pending") {
        i.status = "rejected"
        rejectedCount += 1
      }
    })
    return { rejected_count: rejectedCount }
  },
  confirmAll: async (batchId: string) => {
    await delay()
    const items = mockImportItems[batchId]
    if (!items) throw new Error("导入批次不存在")
    items.forEach((i) => {
      if (i.status === "pending") i.status = "confirmed"
    })
    const batch = mockImportBatches.find((b) => b.id === batchId)
    if (batch) {
      batch.confirmed_count = items.filter((i) => i.status === "confirmed").length
      if (batch.confirmed_count >= batch.total_count) batch.status = "completed"
    }
  },
}

let interviewCounter = 1
const mockSessions: InterviewSession[] = []
const mockSessionQuestions: Record<string, InterviewQuestion[]> = {}

export const mockInterviewApi = {
  createSession: async (config: InterviewConfig) => {
    await delay(1200)
    const id = `interview_${interviewCounter++}`
    const session: InterviewSession = {
      id,
      bank_ids: config.bank_ids,
      tags: config.tags || [],
      difficulty: config.difficulty,
      question_count: config.question_count,
      goal: config.goal,
      mode: config.mode,
      resume_id: config.resume_id,
      status: "pending",
      current_index: 0,
      total_questions: config.question_count,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockSessions.unshift(session)

    const questions: InterviewQuestion[] = [
      {
        id: `iq_${id}_1`,
        session_id: id,
        question_id: "q_1",
        index: 0,
        content: "请解释 CSS 中的 BFC (Block Formatting Context) 是什么？如何创建？",
        tags: ["CSS"],
        difficulty: 3,
        ai_reason: "BFC 是前端面试中的高频考点，能考察候选人对 CSS 渲染机制的理解深度。本题适合作为开场题，难度适中。",
        status: "pending",
      },
      {
        id: `iq_${id}_2`,
        session_id: id,
        question_id: "q_2",
        index: 1,
        content: "JavaScript 中 var、let 和 const 的区别是什么？请结合作用域和变量提升说明。",
        tags: ["JavaScript"],
        difficulty: 1,
        ai_reason: "ES6 变量声明是 JavaScript 基础中的核心概念，几乎所有前端岗位都会考察。本题难度较低，适合作为热身。",
        status: "pending",
      },
      {
        id: `iq_${id}_3`,
        session_id: id,
        question_id: "q_3",
        index: 2,
        content: "请解释事件委托（Event Delegation）的原理和应用场景。",
        tags: ["JavaScript"],
        difficulty: 2,
        ai_reason: "事件委托是性能优化的重要手段，同时能考察候选人对 DOM 事件流的理解。与前面两道题形成递进。",
        status: "pending",
      },
    ]
    mockSessionQuestions[id] = questions
    return session
  },
  getSession: async (id: string) => {
    await delay()
    const session = mockSessions.find((s) => s.id === id)
    if (!session) throw new Error("面试会话不存在")
    return {
      session: { ...session },
      questions: [...(mockSessionQuestions[id] || [])],
    }
  },
  startSession: async (id: string) => {
    await delay(300)
    const session = mockSessions.find((s) => s.id === id)
    if (!session) throw new Error("面试会话不存在")
    session.status = "in_progress"
    session.updated_at = new Date().toISOString()
    return { ...session }
  },
  submitAnswer: async (sessionId: string, questionId: string, answer: string) => {
    await delay(1500)
    const questions = mockSessionQuestions[sessionId]
    const question = questions?.find((q) => q.id === questionId)
    if (!question) throw new Error("题目不存在")
    question.answer = answer
    question.status = "answered"
    question.score = Math.floor(Math.random() * 3) + 6
    question.feedback = {
      score: question.score,
      missing_points: [
        "可以更具体地结合浏览器渲染流程说明",
        "缺少实际项目中的性能影响数据",
      ],
      reference_answer:
        question.content.includes("BFC")
          ? "BFC（Block Formatting Context）是块级格式化上下文，是一个独立的渲染区域。创建方式：overflow 不为 visible（如 hidden、auto、scroll）、float 不为 none、position 为 absolute 或 fixed、display 为 inline-block、flex、grid、flow-root 等。BFC 的主要特性：内部盒子垂直排列、外边距折叠、BFC 区域不会与浮动元素重叠、计算高度时包含浮动元素。"
          : question.content.includes("var")
            ? "var 有函数作用域和变量提升，可以在声明前访问（undefined）；let 和 const 有块级作用域和暂时性死区，声明前访问会报 ReferenceError；const 声明常量，基本类型值不可变，引用类型引用不可变但属性可变。建议优先使用 const，需要重新赋值时用 let，不再使用 var。"
            : "事件委托（Event Delegation）利用事件冒泡机制，将子元素的事件监听器挂载到父元素上。当子元素触发事件时，事件会冒泡到父元素，通过 event.target 判断实际触发元素。适用场景：动态列表（如无限滚动加载）、大量相似元素（如表格行）、需要统一管理的事件处理。优点：减少内存占用、动态元素自动生效、代码更简洁。",
    }
    return question
  },
  nextQuestion: async (sessionId: string) => {
    await delay(300)
    const session = mockSessions.find((s) => s.id === sessionId)
    if (!session) throw new Error("面试会话不存在")
    session.current_index += 1
    if (session.current_index >= session.total_questions) {
      session.status = "completed"
    }
    session.updated_at = new Date().toISOString()
    return { ...session }
  },
  getSummary: async (id: string) => {
    await delay(600)
    const session = mockSessions.find((s) => s.id === id)
    if (!session) throw new Error("面试会话不存在")
    const questions = mockSessionQuestions[id] || []
    const answeredQuestions = questions.filter((q) => q.status === "answered")
    const totalScore = answeredQuestions.reduce((sum, q) => sum + (q.score || 0), 0)
    const overallScore = answeredQuestions.length > 0
      ? Math.round(totalScore / answeredQuestions.length)
      : 0

    const summary: InterviewSummary = {
      session: { ...session },
      questions: questions.map((q) => ({ ...q })),
      overall_score: overallScore,
      weak_tags: ["CSS 渲染机制", "浏览器性能优化"],
      recommendations: [
        "建议重点复习 CSS 布局和渲染原理，特别是 BFC、层叠上下文和重排重绘",
        "JavaScript 事件机制掌握较好，可以进一步学习自定义事件和事件循环",
        "建议多练习将理论知识结合项目经验表述，展示工程化思维",
      ],
    }
    return summary
  },
}

let resumeCounter = 1
const mockResumes: Resume[] = [
  {
    id: "resume_1",
    filename: "张三_前端工程师_简历.pdf",
    status: "completed",
    is_scanned: false,
    summary: {
      name: "张三",
      email: "zhangsan@example.com",
      phone: "138-0000-0000",
      skills: ["JavaScript", "TypeScript", "React", "Vue.js", "Node.js", "Next.js", "CSS/Tailwind", "Webpack", "Git", "Docker"],
      experience: [
        {
          company: "字节跳动",
          title: "前端高级工程师",
          start_date: "2022-03",
          end_date: null,
          description: "负责抖音电商平台前端架构设计，主导了商品详情页的性能优化（LCP 降低 40%）。带领 3 人小团队完成微前端架构迁移。",
        },
        {
          company: "阿里巴巴",
          title: "前端工程师",
          start_date: "2019-07",
          end_date: "2022-02",
          description: "参与淘宝商家后台开发，负责订单管理和数据分析模块。使用 React + TypeScript 重构了遗留 jQuery 系统。",
        },
      ],
      education: [
        {
          school: "浙江大学",
          degree: "本科",
          major: "计算机科学与技术",
          start_date: "2015-09",
          end_date: "2019-06",
        },
      ],
      projects: [
        {
          name: "电商平台微前端改造",
          description: "基于 Module Federation 实现微前端架构，支持多团队独立开发部署",
          technologies: ["Webpack 5", "React", "Module Federation"],
          highlights: ["首屏加载时间减少 35%", "团队发布效率提升 3 倍"],
        },
      ],
      follow_up_directions: [
        "React 性能优化经验（useMemo、React.memo、虚拟列表）",
        "前端工程化和构建工具链（Webpack 配置、Vite 对比）",
        "团队管理和跨部门协作经验",
      ],
    },
    created_at: "2026-05-28T00:00:00Z",
    updated_at: "2026-05-28T00:00:10Z",
  },
]

export const mockResumeApi = {
  getResumes: async () => {
    await delay()
    return [...mockResumes]
  },
  getResume: async (id: string) => {
    await delay()
    const resume = mockResumes.find((r) => r.id === id)
    if (!resume) throw new Error("简历不存在")
    return { ...resume, summary: resume.summary ? { ...resume.summary } : undefined }
  },
  uploadResume: async (file: File) => {
    await delay(800)
    const id = `resume_${++resumeCounter}`
    const resume: Resume = {
      id,
      filename: file.name,
      status: "parsing",
      is_scanned: file.name.includes("scan") || file.name.includes("图片"),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mockResumes.unshift(resume)

    setTimeout(() => {
      const r = mockResumes.find((x) => x.id === id)
      if (r) {
        r.status = "completed"
        r.summary = {
          name: "新候选人",
          email: "candidate@example.com",
          skills: ["JavaScript", "React", "Node.js"],
          experience: [
            { company: "某互联网公司", title: "前端工程师", start_date: "2021-01", end_date: null, description: "负责核心产品前端开发" },
          ],
          education: [
            { school: "某大学", degree: "本科", major: "计算机相关专业", start_date: "2017-09", end_date: "2021-06" },
          ],
          projects: [],
          follow_up_directions: ["深入前端框架原理", "系统设计能力"],
        }
        r.updated_at = new Date().toISOString()
      }
    }, 3000)

    return resume
  },
}
