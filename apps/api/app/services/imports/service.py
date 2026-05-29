import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.clients.feishu import FeishuClient, extract_feishu_text
from app.clients.llm import ExtractedQuestion, LLMClient
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import ImportBatch, ImportItem, QuestionBank, User
from app.db.repositories.imports import ImportRepository
from app.db.session import SessionLocal
from app.schemas.imports import FeishuImportRequest, GithubImportRequest, ImportItemUpdate
from app.schemas.question_banks import QuestionBankCreate
from app.schemas.questions import QuestionCreate
from app.services.question_banks.service import QuestionBankService
from app.services.questions.service import QuestionService, difficulty_label_for_score


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.imports = ImportRepository(db)
        self.banks = QuestionBankService(db)
        self.questions = QuestionService(db)
        self.feishu = FeishuClient()
        self.llm = LLMClient()

    def import_feishu(self, user: User, payload: FeishuImportRequest) -> ImportBatch:
        bank_id = payload.bank_id or self._create_default_import_bank(user).id
        self.banks.get_accessible_bank(user, bank_id)
        document_type, document_id = self.feishu.parse_document_url(payload.url)
        source = self.imports.create_source(payload.url, document_id, document_type)
        raw_blocks = self.feishu.fetch_document_blocks(document_id, document_type)
        normalized_text = normalize_feishu_blocks(raw_blocks)
        extracted = self.llm.extract_questions_from_text(normalized_text)
        batch = self.imports.create_batch(
            bank_id,
            source.id,
            user.id,
            raw_blocks,
            normalized_text,
            extracted.model_dump(),
            "pending_confirmation",
        )
        for item in extracted.items:
            self.imports.create_item(
                batch.id,
                item.question,
                item.answer,
                item.tags,
                item.difficulty_score,
                item.difficulty_label,
                item.source_block_ids,
                round(item.confidence * 100),
                item.notes,
            )
        self.db.commit()
        return self.get_batch_for_user(user, batch.id)

    def import_github_markdown(self, user: User, payload: GithubImportRequest) -> ImportBatch:
        bank_id = payload.bank_id or self._create_default_github_bank(user).id
        self.banks.get_accessible_bank(user, bank_id)
        repo_url, ref, include_paths = normalize_github_import_target(
            payload.repo_url,
            payload.ref,
            payload.include_paths,
        )
        source = self.imports.create_source(
            repo_url,
            github_document_id(repo_url, ref, include_paths),
            "github_markdown",
        )
        normalized_payload = payload.model_copy(
            update={"repo_url": repo_url, "ref": ref, "include_paths": include_paths},
        )
        raw_blocks, normalized_text, items = extract_github_markdown_questions(normalized_payload)
        batch = self.imports.create_batch(
            bank_id,
            source.id,
            user.id,
            raw_blocks,
            normalized_text,
            {"items": [item.model_dump() for item in items]},
            "pending_confirmation",
        )
        for item in items:
            self.imports.create_item(
                batch.id,
                item.question,
                item.answer,
                item.tags,
                item.difficulty_score,
                item.difficulty_label,
                item.source_block_ids,
                round(item.confidence * 100),
                item.notes,
            )
        self.db.commit()
        return self.get_batch_for_user(user, batch.id)

    def queue_feishu_import(self, user: User, payload: FeishuImportRequest) -> ImportBatch:
        bank_id = payload.bank_id or self._create_default_import_bank(user).id
        self.banks.get_accessible_bank(user, bank_id)
        document_type, document_id = self.feishu.parse_document_url(payload.url)
        source = self.imports.create_source(payload.url, document_id, document_type)
        batch = self.imports.create_batch(
            bank_id,
            source.id,
            user.id,
            {},
            "",
            {},
            "processing",
        )
        self.db.commit()
        return self.get_batch_for_user(user, batch.id)

    def list_batches(self, user: User) -> list[ImportBatch]:
        banks = self.banks.list_banks(user)
        return self.imports.list_batches_for_banks([bank.id for bank in banks])

    def get_batch_for_user(self, user: User, batch_id: str) -> ImportBatch:
        batch = self.imports.get_batch(batch_id)
        if batch is None:
            raise AppError("IMPORT_BATCH_NOT_FOUND", "导入批次不存在", status_code=404)
        self.banks.get_accessible_bank(user, batch.bank_id)
        return batch

    def list_items(self, user: User, batch_id: str) -> list[ImportItem]:
        self.get_batch_for_user(user, batch_id)
        return self.imports.list_items(batch_id)

    def update_item(self, user: User, item_id: str, payload: ImportItemUpdate) -> ImportItem:
        item = self.imports.get_item(item_id)
        if item is None:
            raise AppError("IMPORT_ITEM_NOT_FOUND", "导入项不存在", status_code=404)
        self.get_batch_for_user(user, item.batch_id)
        if payload.question is not None:
            item.question = payload.question
        if payload.answer is not None:
            item.answer = payload.answer
        if payload.tags is not None:
            item.tags = payload.tags
        if payload.difficulty_score is not None:
            item.difficulty_score = payload.difficulty_score
        if payload.difficulty_label is not None:
            item.difficulty_label = payload.difficulty_label
        if payload.status is not None:
            if payload.status not in {"pending", "discarded"}:
                raise AppError("INVALID_IMPORT_ITEM_STATUS", "导入项状态无效", status_code=422)
            item.status = payload.status
        self.db.commit()
        return item

    def reject_item(self, user: User, item_id: str) -> ImportItem:
        return self.update_item(user, item_id, ImportItemUpdate(status="discarded"))

    def reject_batch(self, user: User, batch_id: str) -> int:
        batch = self.get_batch_for_user(user, batch_id)
        rejected_count = 0
        for item in batch.items:
            if item.status != "pending":
                continue
            item.status = "discarded"
            rejected_count += 1
        self.db.commit()
        return rejected_count

    def confirm_item(self, user: User, item_id: str) -> tuple[ImportItem, str | None]:
        item = self.imports.get_item(item_id)
        if item is None:
            raise AppError("IMPORT_ITEM_NOT_FOUND", "导入项不存在", status_code=404)
        batch = self.get_batch_for_user(user, item.batch_id)
        if item.status != "pending":
            return item, item.confirmed_question_id
        question = self.questions.create_question(
            user,
            batch.bank_id,
            QuestionCreate(
                question=item.question,
                answer=item.answer,
                tags=item.tags,
                difficulty_score=item.difficulty_score,
                difficulty_label=item.difficulty_label,
                source_type=source_type_for_batch(batch),
                source_block_ids=item.source_block_ids,
            ),
        )
        question.source_id = batch.source_id
        item.status = "confirmed"
        item.confirmed_question_id = question.id
        self.db.commit()
        return item, question.id

    def confirm_batch(self, user: User, batch_id: str) -> tuple[int, list[str]]:
        batch = self.get_batch_for_user(user, batch_id)
        question_ids: list[str] = []
        for item in batch.items:
            if item.status != "pending":
                continue
            question = self.questions.create_question(
                user,
                batch.bank_id,
                QuestionCreate(
                    question=item.question,
                    answer=item.answer,
                    tags=item.tags,
                    difficulty_score=item.difficulty_score,
                    difficulty_label=item.difficulty_label,
                    source_type=source_type_for_batch(batch),
                    source_block_ids=item.source_block_ids,
                ),
            )
            question.source_id = batch.source_id
            item.status = "confirmed"
            item.confirmed_question_id = question.id
            question_ids.append(question.id)
        batch.status = "confirmed"
        self.db.commit()
        return len(question_ids), question_ids

    def queue_confirm_batch(self, user: User, batch_id: str) -> int:
        batch = self.get_batch_for_user(user, batch_id)
        pending_count = len([item for item in batch.items if item.status == "pending"])
        if pending_count:
            batch.status = "confirming"
            self.db.commit()
        return pending_count

    def process_queued_import_batch(self, batch_id: str) -> None:
        batch = self.imports.get_batch(batch_id)
        if batch is None:
            return
        raw_blocks = self.feishu.fetch_document_blocks(
            batch.source.document_id,
            batch.source.document_type,
        )
        normalized_text = normalize_feishu_blocks(raw_blocks)
        extracted = self.llm.extract_questions_from_text(normalized_text)
        self.db.execute(delete(ImportItem).where(ImportItem.batch_id == batch.id))
        batch.raw_blocks_json = raw_blocks
        batch.normalized_text = normalized_text
        batch.ai_result_json = extracted.model_dump()
        batch.status = "pending_confirmation"
        batch.error_message = None
        for item in extracted.items:
            self.imports.create_item(
                batch.id,
                item.question,
                item.answer,
                item.tags,
                item.difficulty_score,
                item.difficulty_label,
                item.source_block_ids,
                round(item.confidence * 100),
                item.notes,
            )
        self.db.commit()

    def _create_default_import_bank(self, user: User) -> QuestionBank:
        return self.banks.create_bank(
            user,
            QuestionBankCreate(
                name="飞书导入默认题库",
                description="未选择题库时自动创建",
                default_tags=["飞书导入"],
            ),
        )

    def _create_default_github_bank(self, user: User) -> QuestionBank:
        return self.banks.create_bank(
            user,
            QuestionBankCreate(
                name="GitHub 导入默认题库",
                description="未选择题库时自动创建",
                default_tags=["GitHub导入"],
            ),
        )


def process_feishu_import_batch(batch_id: str) -> None:
    with SessionLocal() as db:
        service = ImportService(db)
        batch = service.imports.get_batch(batch_id)
        if batch is None:
            return
        try:
            service.process_queued_import_batch(batch_id)
        except Exception as exc:
            batch.status = "failed"
            batch.error_message = _friendly_import_error(exc)
            db.commit()


def process_confirm_import_batch(batch_id: str, user_id: str) -> None:
    with SessionLocal() as db:
        service = ImportService(db)
        batch = service.imports.get_batch(batch_id)
        user = db.get(User, user_id)
        if batch is None or user is None:
            return
        try:
            service.confirm_batch(user, batch_id)
        except Exception as exc:
            batch.status = "pending_confirmation"
            batch.error_message = _friendly_import_error(exc)
            db.commit()


def _friendly_import_error(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return exc.message
    return "导入处理失败，请稍后重试"


def source_type_for_batch(batch: ImportBatch) -> str:
    source = getattr(batch, "source", None)
    if source and source.document_type == "github_markdown":
        return "github_import"
    return "feishu_import"


def github_document_id(repo_url: str, ref: str | None, include_paths: list[str]) -> str:
    repo_url, ref, include_paths = normalize_github_import_target(repo_url, ref, include_paths)
    digest = hashlib.sha1(
        f"{repo_url}@{ref or 'HEAD'}:{','.join(include_paths)}".encode(),
    ).hexdigest()[:16]
    return f"github:{digest}"


def normalize_github_import_target(
    repo_url: str,
    ref: str | None,
    include_paths: list[str],
) -> tuple[str, str | None, list[str]]:
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)(?:/(.*))?$", repo_url.rstrip("/"))
    if not match:
        return repo_url, ref, include_paths

    owner, repo, suffix = match.groups()
    normalized_repo_url = f"https://github.com/{owner}/{repo.removesuffix('.git')}.git"
    normalized_ref = ref
    normalized_paths = list(include_paths)
    if suffix:
        parts = suffix.split("/")
        if len(parts) >= 3 and parts[0] in {"tree", "blob"}:
            normalized_ref = normalized_ref or parts[1]
            path = "/".join(parts[2:]).strip("/")
            if path and not normalized_paths:
                normalized_paths = [path]
    return normalized_repo_url, normalized_ref, normalized_paths


def extract_github_markdown_questions(
    payload: GithubImportRequest,
) -> tuple[dict[str, Any], str, list[ExtractedQuestion]]:
    with tempfile.TemporaryDirectory(prefix="ohmyoffer_github_import_") as tmp_dir:
        repo_dir = Path(tmp_dir) / "repo"
        repo_url, ref, include_paths = normalize_github_import_target(
            payload.repo_url,
            payload.ref,
            payload.include_paths,
        )
        command = [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            repo_url,
            str(repo_dir),
        ]
        if ref:
            command[3:3] = ["--branch", ref]
        _run_git_command(command)
        return extract_markdown_questions_from_dir(
            repo_dir,
            include_paths=include_paths,
            max_files=payload.max_files,
        )


def extract_markdown_questions_from_dir(
    repo_dir: Path,
    *,
    include_paths: list[str],
    max_files: int,
) -> tuple[dict[str, Any], str, list[ExtractedQuestion]]:
    markdown_files = _select_markdown_files(repo_dir, include_paths, max_files)
    blocks: list[dict[str, Any]] = []
    normalized_parts: list[str] = []
    extracted_items: list[ExtractedQuestion] = []
    for file_path in markdown_files:
        relative_path = file_path.relative_to(repo_dir).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        file_blocks, file_items = _extract_markdown_file(relative_path, text)
        blocks.extend(file_blocks)
        if file_blocks:
            block_text = "\n".join(block["text"] for block in file_blocks)
            normalized_parts.append(f"# {relative_path}\n{block_text}")
        extracted_items.extend(file_items)
    return (
        {
            "files": [path.relative_to(repo_dir).as_posix() for path in markdown_files],
            "blocks": blocks,
        },
        "\n\n".join(normalized_parts),
        _dedupe_extracted_questions(extracted_items),
    )


def _run_git_command(command: list[str]) -> None:
    if not shutil.which("git"):
        raise AppError(
            "GIT_UNAVAILABLE",
            "当前环境未安装 git，无法导入 GitHub 仓库",
            status_code=503,
        )
    env = os.environ.copy()
    proxy_url = get_settings().github_proxy_url
    if proxy_url:
        env["ALL_PROXY"] = proxy_url
        env["HTTPS_PROXY"] = proxy_url
        env["HTTP_PROXY"] = proxy_url
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=90, env=env)
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "GitHub 仓库拉取失败"
        raise AppError("GITHUB_IMPORT_FAILED", message[:500], status_code=422) from exc
    except subprocess.TimeoutExpired as exc:
        raise AppError("GITHUB_IMPORT_TIMEOUT", "GitHub 仓库拉取超时", status_code=504) from exc


def _select_markdown_files(repo_dir: Path, include_paths: list[str], max_files: int) -> list[Path]:
    candidates = sorted(
        path
        for path in repo_dir.rglob("*.md")
        if (
            path.is_file()
            and ".git" not in path.parts
            and _is_included(repo_dir, path, include_paths)
        )
    )
    return candidates[:max_files]


def _is_included(repo_dir: Path, path: Path, include_paths: list[str]) -> bool:
    if not include_paths:
        return True
    relative = path.relative_to(repo_dir).as_posix()
    prefixes = [prefix.strip("/") for prefix in include_paths if prefix.strip("/")]
    return any(relative == prefix or relative.startswith(f"{prefix}/") for prefix in prefixes)


def _extract_markdown_file(
    relative_path: str,
    text: str,
) -> tuple[list[dict[str, Any]], list[ExtractedQuestion]]:
    blocks: list[dict[str, Any]] = []
    items: list[ExtractedQuestion] = []
    heading_stack: list[str] = []
    current_question: str | None = None
    current_answer: list[str] = []
    current_block_ids: list[str] = []

    def flush_question() -> None:
        nonlocal current_question, current_answer, current_block_ids
        if not current_question:
            return
        answer = _clean_answer("\n".join(current_answer))
        difficulty_score = _difficulty_for_question(current_question, answer)
        items.append(
            ExtractedQuestion(
                question=current_question,
                answer=answer or None,
                tags=_tags_for_markdown_question(relative_path, heading_stack, current_question),
                difficulty_score=difficulty_score,
                difficulty_label=difficulty_label_for_score(difficulty_score),
                source_block_ids=list(dict.fromkeys(current_block_ids)),
                confidence=0.72,
                notes=f"从 GitHub Markdown 导入：{relative_path}",
            ),
        )
        current_question = None
        current_answer = []
        current_block_ids = []

    for index, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            if current_question:
                current_answer.append("")
            continue
        block_id = f"{relative_path}:{index}"
        if line.startswith("#"):
            flush_question()
            heading = _strip_markdown(line.lstrip("#").strip())
            level = len(line) - len(line.lstrip("#"))
            heading_stack = heading_stack[: max(level - 1, 0)] + [heading]
            blocks.append({"block_id": block_id, "text": f"{'#' * min(level, 3)} {heading}"})
            if _looks_like_question(heading):
                current_question = _normalize_question(heading)
                current_block_ids = [block_id]
            continue
        blocks.append({"block_id": block_id, "text": f"[{block_id}] {line}"})
        parsed_question = _parse_question_line(line)
        if parsed_question:
            flush_question()
            current_question = parsed_question
            current_block_ids = [block_id]
            continue
        if current_question:
            current_answer.append(raw_line.rstrip())
            current_block_ids.append(block_id)
    flush_question()
    return blocks, items


def _parse_question_line(line: str) -> str | None:
    stripped = _strip_markdown(line).strip()
    stripped = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", stripped)
    stripped = re.sub(r"^(?:Q|Question|问|问题)\s*[:：]\s*", "", stripped, flags=re.I)
    if not _looks_like_question(stripped):
        return None
    return _normalize_question(stripped)


def _looks_like_question(text: str) -> bool:
    compact = text.strip()
    if len(compact) < 4 or len(compact) > 180:
        return False
    markers = ("?", "？", "什么", "如何", "怎么", "为什么", "区别", "原理", "介绍", "解释")
    return any(marker in compact for marker in markers)


def _normalize_question(text: str) -> str:
    question = _strip_markdown(text).strip(" #:：")
    return question if question.endswith(("?", "？")) else f"{question}？"


def _clean_answer(answer: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", answer).strip()


def _strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip("*_` ")


def _tags_for_markdown_question(
    relative_path: str,
    heading_stack: list[str],
    question: str,
) -> list[str]:
    raw_tags = ["GitHub导入", "JavaGuide"]
    path_parts = [part for part in Path(relative_path).parts[:-1] if part not in {"docs"}]
    raw_tags.extend(path_parts[-2:])
    raw_tags.extend(heading for heading in heading_stack[-2:] if heading and heading != question)
    return [tag[:30] for tag in dict.fromkeys(raw_tags) if tag][:12]


def _difficulty_for_question(question: str, answer: str) -> int:
    combined = f"{question}\n{answer}"
    hard_keywords = ("源码", "底层", "原理", "锁", "JVM")
    if len(combined) > 1200 or any(keyword in combined for keyword in hard_keywords):
        return 75
    if len(combined) < 240:
        return 35
    return 55


def _dedupe_extracted_questions(items: list[ExtractedQuestion]) -> list[ExtractedQuestion]:
    deduped: list[ExtractedQuestion] = []
    seen: set[str] = set()
    for item in items:
        key = re.sub(r"\s+", "", item.question.lower().strip(" ?？。"))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def normalize_feishu_blocks(raw_blocks: dict[str, Any]) -> str:
    lines: list[str] = []
    for block in raw_blocks.get("blocks", []):
        block_id = str(block.get("block_id", ""))
        block_type = str(block.get("block_type", "text"))
        text = extract_block_text(block)
        if not text:
            continue
        prefix = "#" if "heading1" in block_type else "##" if "heading2" in block_type else ""
        line = f"{prefix} {text}".strip() if prefix else text
        lines.append(f"[{block_id}] {line}" if block_id else line)
    return "\n".join(lines)


def extract_block_text(block: dict[str, Any]) -> str:
    if isinstance(block.get("text"), str):
        return block["text"]
    for key in (
        "text",
        "heading1",
        "heading2",
        "heading3",
        "heading4",
        "heading5",
        "heading6",
        "heading",
        "paragraph",
        "bullet",
        "ordered",
        "todo",
        "quote",
        "callout",
        "code",
    ):
        value = block.get(key)
        text = extract_feishu_text(value)
        if text:
            return text
    text = extract_feishu_text(block.get("elements"))
    if text:
        return text
    return ""
