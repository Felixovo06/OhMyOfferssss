import re

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Resume, User
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


def extract_resume_text(content: bytes, filename: str, content_type: str | None) -> str:
    lowered = filename.lower()
    if (content_type and content_type.startswith("text/")) or lowered.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    if content_type == "application/pdf" or lowered.endswith(".pdf"):
        return extract_text_from_pdf_bytes(content)
    raise AppError("UNSUPPORTED_RESUME_FILE", "仅支持 PDF 或文本简历", status_code=422)


def extract_text_from_pdf_bytes(content: bytes) -> str:
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
    return re.sub(r"\s+", " ", readable).strip()


def summarize_resume_text(text: str) -> ResumeSummary:
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
        "MySQL",
        "PostgreSQL",
        "Redis",
        "Docker",
        "Kubernetes",
        "AWS",
        "Linux",
    ]
    lowered = text.lower()
    return [skill for skill in known if skill.lower() in lowered][:12]


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
            school=school[:80],
            degree="",
            major="",
            start_date="",
        )
        for school in schools
    ]


def _extract_projects(lines: list[str], skills: list[str]) -> list[ResumeProject]:
    project_lines = [line for line in lines if "项目" in line][:3]
    return [
        ResumeProject(
            name=line[:80],
            description=line,
            technologies=skills[:5],
            highlights=[],
        )
        for line in project_lines
    ]


def _nearby_description(text: str, keyword: str) -> str:
    index = text.find(keyword)
    if index < 0:
        return ""
    return text[index : index + 180]


def _follow_up_directions(skills: list[str]) -> list[str]:
    if not skills:
        return ["结合简历项目经历追问技术选型", "追问候选人负责范围和结果指标"]
    return [f"{skill} 的项目实践和取舍" for skill in skills[:5]]

