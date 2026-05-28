export const mockUser = {
  name: "Klot",
  email: "klot@ohmyoffer.dev",
  role: "产品创建者",
};

export const mockGroup = {
  name: "前端冲刺小组",
  scope: "个人空间 + 小组共享题库",
  members: 4,
  invitations: 2,
};

export const dashboardStats = [
  { label: "题库", value: "12", hint: "3 个小组共享" },
  { label: "题目", value: "184", hint: "最近导入 26 题" },
  { label: "练习", value: "37", hint: "近 7 天 9 场" },
  { label: "薄弱标签", value: "React / 浏览器 / 性能", hint: "建议先复习" },
];

export const recentPracticeSessions = [
  {
    title: "普通面试 · 前端基础",
    meta: "18 分钟前 · 9 题 · 72 分",
    status: "进行过追问",
  },
  {
    title: "客制化面试 · 简历驱动",
    meta: "昨天 · 7 题 · 81 分",
    status: "命中项目经历",
  },
  {
    title: "查漏补缺 · JavaScript",
    meta: "3 天前 · 6 题 · 64 分",
    status: "事件循环薄弱",
  },
];

export const banks = [
  {
    name: "前端八股题库",
    scope: "个人",
    questions: 92,
    tags: ["JavaScript", "React", "浏览器"],
  },
  {
    name: "校招高频题库",
    scope: "前端冲刺小组",
    questions: 48,
    tags: ["基础", "算法", "工程化"],
  },
  {
    name: "面试复盘题库",
    scope: "个人",
    questions: 44,
    tags: ["项目", "表达", "总结"],
  },
];

export const feishuBatches = [
  {
    name: "飞书导入批次 #2026-05-28",
    status: "待确认",
    progress: "21 / 31",
    confidence: "0.84",
  },
  {
    name: "飞书导入批次 #2026-05-24",
    status: "已完成",
    progress: "48 / 48",
    confidence: "0.91",
  },
];

export const practiceRoutes = [
  {
    title: "普通面试",
    description: "选择题库、标签和难度，让模型按目标岗位抽题。",
    href: "/practice/normal",
  },
  {
    title: "客制化面试",
    description: "上传简历后，按项目经历和技能栈定制追问。",
    href: "/practice/custom",
  },
  {
    title: "练习总结",
    description: "查看总体评分、薄弱标签和下一轮复习建议。",
    href: "/practice/summaries",
  },
];

export const taskChecklist = [
  "登录后才能进入后台",
  "工作台展示题库、题目、练习和薄弱标签",
  "小组可创建、邀请、查看成员",
  "题库支持搜索、筛选、创建、编辑、删除",
  "飞书导入有进度、预览和确认",
  "普通面试与客制化面试入口清晰",
  "练习过程和总结状态可见",
];
