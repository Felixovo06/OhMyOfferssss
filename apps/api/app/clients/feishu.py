import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.clients.redis import get_redis_client
from app.core.config import get_settings
from app.core.errors import AppError


class FeishuClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def parse_document_url(self, url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        match = re.search(r"/(docx|doc|wiki)/([A-Za-z0-9]+)", parsed.path)
        if not match:
            raise AppError("INVALID_FEISHU_URL", "无法解析飞书文档链接", status_code=422)
        return match.group(1), match.group(2)

    def get_tenant_access_token(self) -> str:
        cache_key = "feishu:tenant_access_token"
        redis_client = get_redis_client()
        cached = redis_client.get(cache_key)
        if cached:
            return str(cached)

        if not self.settings.feishu_app_id or not self.settings.feishu_app_secret:
            raise AppError("FEISHU_NOT_CONFIGURED", "飞书应用未配置", status_code=503)

        response = httpx.post(
            f"{self.settings.feishu_api_base_url}/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.settings.feishu_app_id,
                "app_secret": self.settings.feishu_app_secret,
            },
            timeout=15,
        )
        payload = response.json()
        if response.status_code >= 400 or payload.get("code") not in {0, None}:
            raise AppError("FEISHU_TOKEN_FAILED", "飞书 token 获取失败", status_code=502)
        token = payload.get("tenant_access_token")
        if not token:
            raise AppError("FEISHU_TOKEN_FAILED", "飞书 token 响应无效", status_code=502)
        redis_client.setex(cache_key, self.settings.feishu_token_cache_ttl_seconds, token)
        return str(token)

    def fetch_document_blocks(self, document_id: str, document_type: str) -> dict[str, Any]:
        if self.settings.environment == "test":
            return self._mock_blocks(document_id, document_type)

        token = self.get_tenant_access_token()
        blocks: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            response = httpx.get(
                f"{self.settings.feishu_api_base_url}/docx/v1/documents/{document_id}/blocks",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=20,
            )
            payload = response.json()
            if response.status_code >= 400 or payload.get("code") not in {0, None}:
                raise AppError("FEISHU_BLOCKS_FAILED", "飞书文档读取失败", status_code=502)
            data = payload.get("data", {})
            blocks.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")
        return {"document_id": document_id, "document_type": document_type, "blocks": blocks}

    def _mock_blocks(self, document_id: str, document_type: str) -> dict[str, Any]:
        return {
            "document_id": document_id,
            "document_type": document_type,
            "blocks": [
                {"block_id": "b1", "block_type": "heading1", "text": "前端基础"},
                {"block_id": "b2", "block_type": "text", "text": "Q: 什么是事件循环？"},
                {"block_id": "b3", "block_type": "text", "text": "A: 事件循环协调宏任务和微任务。"},
            ],
        }

