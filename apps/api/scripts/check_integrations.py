import argparse
import json

from app.clients.feishu import FeishuClient
from app.clients.llm import LLMClient
from app.core.errors import AppError


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Feishu and LLM integrations.")
    parser.add_argument("--feishu-url", help="Feishu doc/docx/wiki URL to fetch and normalize.")
    parser.add_argument("--llm", action="store_true", help="Call the configured LLM once.")
    args = parser.parse_args()

    if args.feishu_url:
        _check_feishu(args.feishu_url)
    if args.llm:
        _check_llm()
    if not args.feishu_url and not args.llm:
        parser.error("pass --feishu-url, --llm, or both")


def _check_feishu(url: str) -> None:
    client = FeishuClient()
    document_type, document_id = client.parse_document_url(url)
    blocks = client.fetch_document_blocks(document_id, document_type)
    print(
        json.dumps(
            {
                "feishu": "ok",
                "document_type": blocks["document_type"],
                "document_id": blocks["document_id"],
                "block_count": len(blocks.get("blocks", [])),
            },
            ensure_ascii=False,
        ),
    )


def _check_llm() -> None:
    result = LLMClient().extract_questions_from_text(
        "[b1] Q: 什么是事件循环？\n[b2] A: 事件循环负责调度宏任务和微任务。",
    )
    print(
        json.dumps(
            {
                "llm": "ok",
                "item_count": len(result.items),
                "first_question": result.items[0].question if result.items else None,
            },
            ensure_ascii=False,
        ),
    )


if __name__ == "__main__":
    try:
        main()
    except AppError as exc:
        print(
            json.dumps(
                {"success": False, "code": exc.code, "message": exc.message},
                ensure_ascii=False,
            ),
        )
        raise SystemExit(1) from exc
