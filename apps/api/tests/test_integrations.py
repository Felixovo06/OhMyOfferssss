import httpx
import pytest

from app.clients.feishu import FeishuClient
from app.clients.llm import LLMClient
from app.core.config import get_settings
from app.core.errors import AppError
from app.services.imports.service import extract_block_text


def test_llm_parses_json_wrapped_in_markdown(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_base_url", "https://llm.example/v1")

    def mock_post(*args, **kwargs) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": """```json
{"items":[{"question":"什么是事件循环？","answer":"调度任务","tags":["JS"],"difficulty_score":50,"difficulty_label":"medium","source_block_ids":["b1"],"confidence":0.9,"notes":null}]}
```""",
                        },
                    },
                ],
            },
            request=httpx.Request("POST", "https://llm.example/v1/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    result = LLMClient().extract_questions_from_text("[b1] Q: 什么是事件循环？")

    assert result.items[0].question == "什么是事件循环？"
    assert result.items[0].source_block_ids == ["b1"]


def test_llm_http_error_becomes_app_error(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_base_url", "https://llm.example/v1")

    def mock_post(*args, **kwargs) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": "bad key"}},
            request=httpx.Request("POST", "https://llm.example/v1/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    with pytest.raises(AppError) as exc:
        LLMClient().extract_questions_from_text("[b1] Q: 什么是事件循环？")

    assert exc.value.code == "LLM_REQUEST_FAILED"


def test_llm_extracts_long_text_in_chunks(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_base_url", "https://llm.example/v1")
    calls: list[str] = []

    def mock_post(*args, **kwargs) -> httpx.Response:
        calls.append(kwargs["json"]["messages"][1]["content"])
        index = len(calls)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"items":[{"question":"问题'
                                f'{index}'
                                '","answer":"答案","tags":["Java"],'
                                '"difficulty_score":50,"difficulty_label":"medium",'
                                '"source_block_ids":["b"],"confidence":0.9,"notes":null}]}'
                            ),
                        },
                    },
                ],
            },
            request=httpx.Request("POST", "https://llm.example/v1/chat/completions"),
        )

    monkeypatch.setattr(httpx, "post", mock_post)

    long_text = "\n".join(f"[b{i}] 知识点 {i} " + "x" * 120 for i in range(60))
    result = LLMClient().extract_questions_from_text(long_text)

    assert len(calls) > 1
    assert [item.question for item in result.items] == [
        f"问题{i}" for i in range(1, len(calls) + 1)
    ]


def test_feishu_docx_blocks_request_and_text_extraction(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "local")
    monkeypatch.setattr(settings, "feishu_app_id", "cli_test")
    monkeypatch.setattr(settings, "feishu_app_secret", "secret")
    requested_urls: list[str] = []

    class FakeRedis:
        def get(self, key: str) -> None:
            return None

        def setex(self, key: str, ttl: int, value: str) -> None:
            return None

    monkeypatch.setattr("app.clients.feishu.get_redis_client", lambda: FakeRedis())

    def mock_post(*args, **kwargs) -> httpx.Response:
        return httpx.Response(
            200,
            json={"code": 0, "tenant_access_token": "tenant-token"},
            request=httpx.Request("POST", args[0]),
        )

    def mock_get(*args, **kwargs) -> httpx.Response:
        requested_urls.append(args[0])
        return httpx.Response(
            200,
            json={
                "code": 0,
                "data": {
                    "items": [
                        {
                            "block_id": "b1",
                            "block_type": "text",
                            "text": {
                                "elements": [
                                    {"text_run": {"content": "Q: 什么是 Redis 缓存击穿？"}},
                                ],
                            },
                        },
                    ],
                    "has_more": False,
                },
            },
            request=httpx.Request("GET", args[0]),
        )

    monkeypatch.setattr(httpx, "post", mock_post)
    monkeypatch.setattr(httpx, "get", mock_get)

    blocks = FeishuClient().fetch_document_blocks("DOCX123", "docx")

    assert requested_urls == [
        "https://open.feishu.cn/open-apis/docx/v1/documents/DOCX123/blocks",
    ]
    assert extract_block_text(blocks["blocks"][0]) == "Q: 什么是 Redis 缓存击穿？"


def test_feishu_wiki_url_resolves_to_document(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "local")
    monkeypatch.setattr(settings, "feishu_app_id", "cli_test")
    monkeypatch.setattr(settings, "feishu_app_secret", "secret")
    requested_urls: list[str] = []

    class FakeRedis:
        def get(self, key: str) -> str:
            return "tenant-token"

        def setex(self, key: str, ttl: int, value: str) -> None:
            return None

    monkeypatch.setattr("app.clients.feishu.get_redis_client", lambda: FakeRedis())

    def mock_get(*args, **kwargs) -> httpx.Response:
        requested_urls.append(args[0])
        if args[0].endswith("/wiki/v2/spaces/get_node"):
            payload = {"code": 0, "data": {"node": {"obj_token": "DOCX456", "obj_type": "docx"}}}
        else:
            payload = {"code": 0, "data": {"items": [], "has_more": False}}
        return httpx.Response(200, json=payload, request=httpx.Request("GET", args[0]))

    monkeypatch.setattr(httpx, "get", mock_get)

    document_type, document_id = FeishuClient().parse_document_url(
        "https://example.feishu.cn/wiki/WIKI_TOKEN",
    )
    blocks = FeishuClient().fetch_document_blocks(document_id, document_type)

    assert blocks["document_id"] == "DOCX456"
    assert blocks["document_type"] == "docx"
    assert requested_urls[0].endswith("/wiki/v2/spaces/get_node")
    assert requested_urls[1].endswith("/docx/v1/documents/DOCX456/blocks")
