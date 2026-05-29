import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Question, QuestionBank, QuestionTag, Tag, User, new_uuid
from app.db.session import SessionLocal
from app.services.questions.service import difficulty_label_for_score

DEFAULT_OWNER_EMAIL = "1105540105@qq.com"
SOURCE_TYPE = "github_import"


@dataclass(frozen=True)
class SourceConfig:
    source_name: str
    repo_url: str
    repo_dir: Path
    include_root: str


@dataclass
class ParsedQuestion:
    question: str
    answer: str | None
    tags: list[str]
    difficulty_score: int
    source_block_ids: list[str]


@dataclass
class ParsedBank:
    name: str
    description: str
    tags: list[str]
    questions: list[ParsedQuestion]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-email", default=DEFAULT_OWNER_EMAIL)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--sources-root",
        default="/tmp/ohmyoffer_import_sources",
        help="Directory containing JavaGuide-Interview and JavaGuide clones.",
    )
    args = parser.parse_args()

    sources_root = Path(args.sources_root)
    sources = [
        SourceConfig(
            source_name="JavaGuide-Interview",
            repo_url="https://github.com/Snailclimb/JavaGuide-Interview",
            repo_dir=sources_root / "JavaGuide-Interview",
            include_root=".",
        ),
        SourceConfig(
            source_name="JavaGuide AI",
            repo_url="https://github.com/Snailclimb/JavaGuide/tree/main/docs/ai",
            repo_dir=sources_root / "JavaGuide",
            include_root="docs/ai",
        ),
    ]

    parsed_banks: list[ParsedBank] = []
    for source in sources:
        parsed_banks.extend(parse_source(source))

    total_questions = sum(len(bank.questions) for bank in parsed_banks)
    print(f"parsed_banks={len(parsed_banks)} parsed_questions={total_questions}")
    for bank in parsed_banks[:12]:
        print(f"- {bank.name}: {len(bank.questions)}")
    if len(parsed_banks) > 12:
        print(f"... {len(parsed_banks) - 12} more banks")

    if not args.apply:
        print("dry_run=true")
        return

    with SessionLocal() as db:
        owner = get_or_create_owner(db, args.owner_email)
        tags_by_name = {tag.name: tag for tag in db.scalars(select(Tag)).all()}
        created_banks = 0
        created_questions = 0
        skipped_questions = 0
        for parsed_bank in parsed_banks:
            bank, was_created = get_or_create_bank(db, owner, parsed_bank)
            created_banks += int(was_created)
            existing_questions = {
                normalize_key(question.question)
                for question in db.scalars(select(Question).where(Question.bank_id == bank.id))
            }
            question_rows = []
            pending_tag_names: set[str] = set()
            for parsed_question in parsed_bank.questions:
                key = normalize_key(parsed_question.question)
                if key in existing_questions:
                    skipped_questions += 1
                    continue
                question_id = new_uuid()
                question_rows.append(
                    (
                        {
                            "id": question_id,
                            "bank_id": bank.id,
                            "question": parsed_question.question,
                            "answer": parsed_question.answer,
                            "difficulty_score": parsed_question.difficulty_score,
                            "difficulty_label": difficulty_label_for_score(
                                parsed_question.difficulty_score,
                            ),
                            "source_type": SOURCE_TYPE,
                            "source_block_ids": parsed_question.source_block_ids,
                            "enabled": True,
                        },
                        parsed_question.tags,
                    ),
                )
                pending_tag_names.update(tag.strip() for tag in parsed_question.tags if tag.strip())
                existing_questions.add(key)
            ensure_tags(db, pending_tag_names, tags_by_name)
            if question_rows:
                db.execute(insert(Question), [row for row, _tags in question_rows])
                db.execute(
                    insert(QuestionTag),
                    [
                        {"question_id": row["id"], "tag_id": tags_by_name[tag.strip()].id}
                        for row, tags in question_rows
                        for tag in dict.fromkeys(tags)
                        if tag.strip()
                    ],
                )
                created_questions += len(question_rows)
        db.commit()
        print(
            "imported "
            f"created_banks={created_banks} "
            f"created_questions={created_questions} "
            f"skipped_questions={skipped_questions}",
        )


def parse_source(source: SourceConfig) -> list[ParsedBank]:
    root = source.repo_dir / source.include_root if source.include_root != "." else source.repo_dir
    banks: list[ParsedBank] = []
    for file_path in sorted(root.rglob("*.md")):
        relative_path = file_path.relative_to(source.repo_dir).as_posix()
        if should_skip(relative_path):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body = split_frontmatter(text)
        title = frontmatter.get("title") or first_heading(body) or titleize_path(file_path)
        category = frontmatter.get("category")
        base_tags = compact_tags(
            [source.source_name, category, *frontmatter.get("tags", []), *path_tags(relative_path)],
        )
        questions = parse_questions(body, source, relative_path, base_tags)
        if not questions:
            continue
        banks.append(
            ParsedBank(
                name=unique_bank_name(title, source.source_name),
                description=f"从 {source.repo_url} 的 {relative_path} 按 Markdown 标题导入。",
                tags=base_tags[:8],
                questions=questions,
            ),
        )
    return banks


def should_skip(relative_path: str) -> bool:
    name = Path(relative_path).name.lower()
    if name in {"readme.md", "todo.md", "_coverpage.md", "home.md"}:
        return True
    return "/snippets/" in f"/{relative_path}" or "/pictures/" in f"/{relative_path}"


def split_frontmatter(text: str) -> tuple[dict[str, str | list[str]], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4 :]
    data: dict[str, str | list[str]] = {}
    current_list: str | None = None
    for line in raw.splitlines():
        if match := re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line):
            key, value = match.groups()
            current_list = key if not value else None
            data[key] = value.strip().strip("'\"") if value else []
            continue
        if current_list and (item := re.match(r"^\s*-\s*(.+)$", line)):
            values = data.setdefault(current_list, [])
            if isinstance(values, list):
                values.append(item.group(1).strip().strip("'\""))
    if "tag" in data and "tags" not in data:
        data["tags"] = data["tag"]
    return data, body


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if match := re.match(r"^#\s+(.+)$", line.strip()):
            return clean_inline(match.group(1))
    return None


def titleize_path(file_path: Path) -> str:
    return file_path.stem.replace("-", " ").replace("_", " ").strip().title()


def unique_bank_name(title: str, source_name: str) -> str:
    cleaned = clean_inline(title).strip(" -")
    return cleaned if cleaned else source_name


def path_tags(relative_path: str) -> list[str]:
    parts = list(Path(relative_path).parts[:-1])
    ignored = {"docs", "ai"}
    return [part for part in parts if part not in ignored][-3:]


def parse_questions(
    body: str,
    source: SourceConfig,
    relative_path: str,
    base_tags: list[str],
) -> list[ParsedQuestion]:
    lines = body.splitlines()
    questions: list[ParsedQuestion] = []
    current_title: str | None = None
    current_level = 0
    current_start = 0
    current_answer: list[str] = []
    heading_stack: list[str] = []
    seen: set[str] = set()

    def flush() -> None:
        nonlocal current_title, current_start, current_answer
        if not current_title:
            return
        answer = clean_answer("\n".join(current_answer))
        question = normalize_question(current_title)
        key = normalize_key(question)
        if key and key not in seen:
            tags = compact_tags([*base_tags, *heading_stack[-2:]])
            questions.append(
                ParsedQuestion(
                    question=question,
                    answer=answer or None,
                    tags=tags[:12],
                    difficulty_score=difficulty_for(question, answer),
                    source_block_ids=[f"{source.source_name}:{relative_path}:{current_start}"],
                ),
            )
            seen.add(key)
        current_title = None
        current_answer = []

    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        heading = re.match(r"^(#{2,5})\s+(.+)$", line)
        if heading:
            title = clean_inline(heading.group(2))
            level = len(heading.group(1))
            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(title)
            if is_question_heading(title, relative_path):
                flush()
                current_title = title
                current_level = level
                current_start = index
                current_answer = []
            elif current_title and level <= current_level:
                flush()
            elif current_title:
                current_answer.append(raw_line)
            continue

        bullet_question = parse_bullet_question(line)
        if bullet_question and not current_title:
            current_title = bullet_question
            current_level = 6
            current_start = index
            current_answer = []
            continue
        if bullet_question and current_title:
            flush()
            current_title = bullet_question
            current_level = 6
            current_start = index
            current_answer = []
            continue

        if current_title:
            current_answer.append(raw_line)
    flush()
    return questions


def is_question_heading(title: str, relative_path: str) -> bool:
    if relative_path.startswith("docs/ai/interview-questions/"):
        return True
    markers = ("?", "？", "什么", "如何", "怎么", "为什么", "区别", "原理", "介绍", "哪些", "是否")
    if any(marker in title for marker in markers):
        return True
    return len(title) <= 80 and not title.endswith(("总结", "详解", "指南", "合集"))


def parse_bullet_question(line: str) -> str | None:
    match = re.match(r"^(?:[-*+]|\d+[.)])\s+(.+)$", line)
    if not match:
        return None
    text = clean_inline(match.group(1))
    if len(text) > 140:
        return None
    question_markers = ("?", "？", "什么", "如何", "怎么", "为什么", "区别", "哪些")
    if any(marker in text for marker in question_markers):
        return text
    return None


def normalize_question(title: str) -> str:
    title = re.sub(r"^[⭐️\s]+", "", clean_inline(title)).strip(" ：:")
    if title.endswith(("?", "？")):
        return title
    if any(word in title for word in ("区别", "关系", "流程", "原理", "作用", "组成", "场景")):
        return f"{title}是什么？"
    return f"{title}？"


def clean_answer(answer: str) -> str:
    cleaned_lines: list[str] = []
    in_frontmatter = False
    for line in answer.splitlines():
        stripped = line.strip()
        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if stripped.startswith("<!--") or stripped.startswith("!["):
            continue
        if "@include:" in stripped:
            continue
        cleaned_lines.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip("*_#` ")


def compact_tags(values: list[str | list[str] | None]) -> list[str]:
    tags: list[str] = []
    for value in values:
        if not value:
            continue
        if isinstance(value, list):
            tags.extend(str(item) for item in value)
        else:
            tags.append(str(value))
    return [tag[:30] for tag in dict.fromkeys(tag.strip() for tag in tags if tag.strip())]


def difficulty_for(question: str, answer: str) -> int:
    combined = f"{question}\n{answer}"
    if len(combined) > 1600 or any(word in combined for word in ("源码", "底层", "原理", "调优")):
        return 75
    if len(combined) < 260:
        return 35
    return 55


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", "", value.lower().strip(" ?？。"))


def get_or_create_owner(db: Session, email: str) -> User:
    user = db.scalars(select(User).where(User.email == email.lower())).first()
    if user:
        return user
    user = User(
        email=email.lower(),
        name="JavaGuide 导入",
        password_hash=hash_password("change-me-after-import"),
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_bank(
    db: Session,
    owner: User,
    parsed_bank: ParsedBank,
) -> tuple[QuestionBank, bool]:
    bank = db.scalars(
        select(QuestionBank).where(
            QuestionBank.created_by_id == owner.id,
            QuestionBank.name == parsed_bank.name,
        ),
    ).first()
    if bank:
        return bank, False
    bank = QuestionBank(
        name=parsed_bank.name,
        description=parsed_bank.description,
        created_by_id=owner.id,
        default_tags=parsed_bank.tags,
    )
    db.add(bank)
    db.flush()
    return bank, True


def ensure_tags(
    db: Session,
    tag_names: set[str],
    tags_by_name: dict[str, Tag],
) -> None:
    for name in tag_names:
        normalized = name.strip()
        if not normalized or normalized in tags_by_name:
            continue
        tag = Tag(name=normalized)
        db.add(tag)
        db.flush()
        tags_by_name[normalized] = tag


if __name__ == "__main__":
    main()
