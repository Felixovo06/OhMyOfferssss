import importlib
import re
from typing import Any

from fastapi import UploadFile
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import InterviewSession, Resume, User
from app.db.repositories.resumes import ResumeRepository
from app.schemas.resumes import (
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeSummary,
)


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.resumes = ResumeRepository(db)

    def list_resumes(self, user: User) -> list[Resume]:
        return self.resumes.list_for_user(user.id)

    def get_resume(self, user: User, resume_id: str) -> Resume:
        resume = self.resumes.get(resume_id)
        if resume is None:
            raise AppError("RESUME_NOT_FOUND", "简历不存在", status_code=404)
        if resume.created_by_id != user.id:
            raise AppError("FORBIDDEN", "无权访问该简历", status_code=403)
        return resume

    async def upload_resume(self, user: User, file: UploadFile) -> Resume:
        filename = file.filename or "resume.pdf"
        content = await file.read()
        if not content:
            raise AppError("EMPTY_RESUME_FILE", "简历文件不能为空", status_code=422)
        if len(content) > 8 * 1024 * 1024:
            raise AppError("RESUME_FILE_TOO_LARGE", "简历文件不能超过 8MB", status_code=422)

        resume = self.resumes.create(
            user_id=user.id,
            filename=filename,
            content_type=file.content_type,
            file_size=len(content),
        )
        try:
            text = extract_resume_text(content, filename, file.content_type)
            resume.raw_text = text
            resume.is_scanned = len(text.strip()) < 30
            if resume.is_scanned:
                resume.status = "failed"
                resume.error_message = "未能解析出文本内容，可能是扫描件或图片型 PDF"
            else:
                resume.summary_json = summarize_resume_text(text).model_dump()
                resume.status = "completed"
                resume.error_message = None
        except Exception as exc:  # noqa: BLE001
            resume.status = "failed"
            resume.is_scanned = None
            resume.error_message = f"简历解析失败：{exc}"
        self.db.commit()
        return self.get_resume(user, resume.id)

    def delete_resume(self, user: User, resume_id: str) -> None:
        resume = self.get_resume(user, resume_id)
        self.db.execute(
            update(InterviewSession)
            .where(InterviewSession.resume_id == resume.id)
            .values(resume_id=None),
        )
        self.db.delete(resume)
        self.db.commit()


def extract_resume_text(content: bytes, filename: str, content_type: str | None) -> str:
    lowered = filename.lower()
    if (content_type and content_type.startswith("text/")) or lowered.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    if content_type == "application/pdf" or lowered.endswith(".pdf"):
        return extract_text_from_pdf_bytes(content)
    raise AppError("UNSUPPORTED_RESUME_FILE", "仅支持 PDF 或文本简历", status_code=422)


def extract_text_from_pdf_bytes(content: bytes) -> str:
    structured_text = _extract_pdf_text_with_pymupdf(content)
    if len(structured_text.strip()) >= 30:
        return structured_text

    decoded = content.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^()]*)\)\s*Tj", decoded)
    chunks.extend(
        part
        for array in re.findall(r"\[(.*?)\]\s*TJ", decoded, flags=re.DOTALL)
        for part in re.findall(r"\(([^()]*)\)", array)
    )
    if chunks:
        return "\n".join(_decode_pdf_text(chunk) for chunk in chunks)
    readable = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff@.+#:/,，。；;（）()\-\s]", " ", decoded)
    readable = re.sub(r"\s+", " ", readable).strip()
    if _looks_like_pdf_binary_noise(readable):
        return ""
    return readable


def _extract_pdf_text_with_pymupdf(content: bytes) -> str:
    try:
        fitz: Any = importlib.import_module("fitz")
        document = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text("text", sort=True).strip() for page in document]
    except Exception:  # noqa: BLE001
        return ""
    return normalize_resume_text("\n".join(page for page in pages if page))


def _looks_like_pdf_binary_noise(text: str) -> bool:
    if text.startswith("PDF-") or "/Type /XObject" in text:
        return True
    binary_markers = (" obj ", " endobj ", " stream ", " endstream ")
    pdf_tokens = sum(text.count(token) for token in binary_markers)
    return pdf_tokens >= 4


def normalize_resume_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    normalized: list[str] = []
    for line in lines:
        if not line:
            if normalized and normalized[-1]:
                normalized.append("")
            continue
        normalized.append(line)
    return "\n".join(normalized).strip()


def summarize_resume_text(text: str) -> ResumeSummary:
    text = normalize_resume_text(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    compact = "\n".join(lines)
    email = _first_match(r"[\w.+-]+@[\w.-]+\.\w+", compact)
    phone = _first_match(r"(?:\+?86[-\s]?)?1[3-9]\d{9}", compact)
    skills = _extract_skills(compact)
    return ResumeSummary(
        name=_guess_name(lines, email),
        email=email or "",
        phone=phone,
        skills=skills,
        experience=_extract_experience(lines),
        education=_extract_education(lines),
        projects=_extract_projects(lines, skills),
        follow_up_directions=_follow_up_directions(skills),
    )


def _decode_pdf_text(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .replace(r"\n", "\n")
        .replace(r"\r", "\n")
    )


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(0) if match else None


def _last_match(pattern: str, text: str) -> str | None:
    matches = re.findall(pattern, text)
    return matches[-1] if matches else None


def _guess_name(lines: list[str], email: str | None) -> str:
    for line in lines[:8]:
        if email and email in line:
            continue
        cleaned = re.sub(r"(姓名|Name|电话|邮箱|Email)[:：]", "", line, flags=re.I).strip()
        if 1 < len(cleaned) <= 24 and not re.search(r"[@\d]", cleaned):
            return cleaned
    return "候选人"


def _extract_skills(text: str) -> list[str]:
    known = [
        "Python",
        "Java",
        "Go",
        "JavaScript",
        "TypeScript",
        "React",
        "Vue",
        "Next.js",
        "Node.js",
        "FastAPI",
        "Django",
        "Spring",
        "Spring Boot",
        "SpringBoot",
        "SpringCloudAlibaba",
        "MyBatis",
        "Mybatis",
        "MybatisPlus",
        "MySQL",
        "PostgreSQL",
        "pgvector",
        "Redis",
        "Redisson",
        "RocketMQ",
        "Sentinel",
        "ShardingSphere",
        "SharingSphere",
        "EasyExcel",
        "XXL-Job",
        "Apache Tika",
        "Docker",
        "Kubernetes",
        "AWS",
        "Linux",
        "JVM",
        "AOP",
        "IOC",
        "ThreadLocal",
        "CompletableFuture",
        "SSE",
        "Lua",
        "Canal",
        "Agent",
        "MCP",
        "Claude Code",
    ]
    lowered = text.lower()
    aliases = {
        "SpringBoot": "Spring Boot",
        "Mybatis": "MyBatis",
        "MybatisPlus": "MyBatis-Plus",
        "SharingSphere": "ShardingSphere",
    }
    skills = [aliases.get(skill, skill) for skill in known if skill.lower() in lowered]
    return list(dict.fromkeys(skills))[:18]


def _extract_experience(lines: list[str]) -> list[ResumeExperience]:
    joined = "\n".join(lines)
    companies = [
        line
        for line in lines
        if any(keyword in line for keyword in ("公司", "科技", "集团", "Inc", "Ltd"))
    ][:3]
    return [
        ResumeExperience(
            company=company[:80],
            title="",
            start_date="",
            description=_nearby_description(joined, company),
        )
        for company in companies
    ]


def _extract_education(lines: list[str]) -> list[ResumeEducation]:
    schools = [line for line in lines if any(keyword in line for keyword in ("大学", "学院"))][:2]
    return [
        ResumeEducation(
            school=_first_match(r"[\u4e00-\u9fffA-Za-z]+(?:大学|学院)(?:\([^)]+\))?", school)
            or school[:80],
            degree=_first_match(r"(本科|硕士|博士|专科)", school) or "",
            major=_first_match(r"[\u4e00-\u9fffA-Za-z]+专业", school) or "",
            start_date=_first_match(r"\d{4}\.\d{2}", school) or "",
            end_date=_last_match(r"\d{4}\.\d{2}", school),
        )
        for school in schools
    ]


def _extract_projects(lines: list[str], skills: list[str]) -> list[ResumeProject]:
    projects: list[ResumeProject] = []
    for index, line in enumerate(lines):
        if not _looks_like_project_title(line):
            continue
        block = _collect_until_next_project(lines, index)
        description = _line_after_prefix(block, "项目简介") or " ".join(block[:3])
        tech_line = _line_after_prefix(block, "技术栈")
        techs = _extract_skills(tech_line or " ".join(block)) or skills[:8]
        highlights = [
            _strip_list_marker(item)
            for item in block
            if item != line and not item.startswith(("项目简介", "技术栈", "技术亮点"))
        ][:6]
        projects.append(
            ResumeProject(
                name=re.split(r"\s{2,}", line)[0][:80],
                description=description[:300],
                technologies=techs[:10],
                highlights=highlights,
            ),
        )
        if len(projects) >= 4:
            break
    if not projects:
        project_lines = [line for line in lines if "项目" in line][:3]
        projects = [
            ResumeProject(
                name=line[:80],
                description=line,
                technologies=skills[:5],
                highlights=[],
            )
            for line in project_lines
        ]
    return projects


def _nearby_description(text: str, keyword: str) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    return text[index : index + 180]


def _looks_like_project_title(line: str) -> bool:
    if line in {"项目经历", "技术亮点"}:
        return False
    has_date = bool(re.search(r"\d{4}\.\d{2}\s*-\s*(?:\d{4}\.\d{2}|至今)", line))
    has_role = any(role in line for role in ("后端开发", "前端开发", "全栈", "开发"))
    return has_date and has_role


def _collect_until_next_project(lines: list[str], start_index: int) -> list[str]:
    block = [lines[start_index]]
    for line in lines[start_index + 1 :]:
        if line in {"荣誉证书", "教育背景", "专业技能"}:
            break
        if _looks_like_project_title(line):
            break
        block.append(line)
    return block


def _line_after_prefix(lines: list[str], prefix: str) -> str | None:
    for line in lines:
        if line.startswith(prefix):
            return line.split("：", 1)[-1].strip()
    return None


def _strip_list_marker(line: str) -> str:
    return re.sub(r"^[\s·•\-*]+", "", line).strip()


def _follow_up_directions(skills: list[str]) -> list[str]:
    if not skills:
        return ["结合简历项目经历追问技术选型", "追问候选人负责范围和结果指标"]
    return [f"{skill} 的项目实践和取舍" for skill in skills[:5]]
