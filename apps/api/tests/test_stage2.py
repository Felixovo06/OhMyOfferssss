from fastapi.testclient import TestClient

from app.clients.feishu import FeishuClient
from tests.test_stage1 import login


def test_question_bank_and_question_crud(client: TestClient) -> None:
    token = login(client, "bank-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_bank = client.post(
        "/api/v1/question-banks",
        json={"name": "前端八股", "description": "基础题库", "default_tags": ["前端"]},
        headers=headers,
    )
    assert create_bank.status_code == 200
    bank = create_bank.json()["data"]
    assert bank["scope"] == "personal"
    assert bank["question_count"] == 0

    create_question = client.post(
        f"/api/v1/question-banks/{bank['id']}/questions",
        json={
            "question": "React key 的作用是什么？",
            "answer": "帮助 React 识别列表项的稳定身份。",
            "tags": ["React", "前端"],
            "difficulty_score": 45,
        },
        headers=headers,
    )
    assert create_question.status_code == 200
    question = create_question.json()["data"]
    assert question["difficulty_label"] == "medium"
    assert set(question["tags"]) == {"React", "前端"}

    list_questions = client.get(
        f"/api/v1/question-banks/{bank['id']}/questions",
        params={"tag": "React", "keyword": "key"},
        headers=headers,
    )
    assert list_questions.status_code == 200
    assert len(list_questions.json()["data"]) == 1

    update_question = client.patch(
        f"/api/v1/questions/{question['id']}",
        json={"enabled": False, "difficulty_score": 85},
        headers=headers,
    )
    assert update_question.status_code == 200
    assert update_question.json()["data"]["enabled"] is False
    assert update_question.json()["data"]["difficulty_label"] == "hard"


def test_frontend_bank_alias_contract(client: TestClient) -> None:
    token = login(client, "frontend-contract@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    bank_response = client.post(
        "/api/v1/banks",
        json={"name": "前端契约题库", "description": "alias"},
        headers=headers,
    )
    assert bank_response.status_code == 200
    bank_id = bank_response.json()["data"]["id"]

    question_response = client.post(
        f"/api/v1/banks/{bank_id}/questions",
        json={
            "content": "什么是浏览器事件循环？",
            "answer": "事件循环负责调度任务。",
            "tags": ["JavaScript"],
            "difficulty": 60,
        },
        headers=headers,
    )
    assert question_response.status_code == 200
    question = question_response.json()["data"]
    assert question["content"] == "什么是浏览器事件循环？"
    assert question["difficulty"] == 60
    assert question["status"] == "active"

    disabled = client.patch(
        f"/api/v1/questions/{question['id']}",
        json={"status": "disabled"},
        headers=headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["enabled"] is False

    filtered = client.get(
        f"/api/v1/banks/{bank_id}/questions",
        params={"keyword": "事件循环", "difficulty": "60", "status": "disabled"},
        headers=headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()["data"]) == 1


def test_group_bank_requires_membership(client: TestClient) -> None:
    owner_token = login(client, "group-bank-owner@example.com")
    outsider_token = login(client, "group-bank-outsider@example.com")

    group_response = client.post(
        "/api/v1/groups",
        json={"name": "Group Bank", "description": None},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    group_id = group_response.json()["data"]["id"]

    forbidden = client.post(
        "/api/v1/question-banks",
        json={"name": "非法小组题库", "group_id": group_id},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert forbidden.status_code == 403

    created = client.post(
        "/api/v1/question-banks",
        json={"name": "小组题库", "group_id": group_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert created.status_code == 200
    assert created.json()["data"]["scope"] == "group"


def test_feishu_import_confirm_flow(client: TestClient, monkeypatch) -> None:
    def mock_blocks(self, document_id: str, document_type: str) -> dict:
        return self._mock_blocks(document_id, document_type)

    monkeypatch.setattr(FeishuClient, "fetch_document_blocks", mock_blocks)
    token = login(client, "import-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    bank_response = client.post(
        "/api/v1/question-banks",
        json={"name": "飞书导入题库"},
        headers=headers,
    )
    bank_id = bank_response.json()["data"]["id"]

    import_response = client.post(
        "/api/v1/imports/feishu",
        json={"bank_id": bank_id, "url": "https://example.feishu.cn/docx/ABC123"},
        headers=headers,
    )
    assert import_response.status_code == 200
    batch = import_response.json()["data"]
    assert batch["status"] == "completed"
    assert "事件循环" in batch["normalized_text"]
    assert batch["total_count"] == 1

    items_response = client.get(f"/api/v1/imports/{batch['id']}/items", headers=headers)
    assert items_response.status_code == 200
    items = items_response.json()["data"]
    assert len(items) == 1
    assert items[0]["status"] == "pending"
    assert items[0]["question_content"]

    detail_response = client.get(f"/api/v1/imports/{batch['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["batch"]["id"] == batch["id"]
    assert len(detail_response.json()["data"]["items"]) == 1

    confirm_response = client.post(f"/api/v1/imports/{batch['id']}/confirm", headers=headers)
    assert confirm_response.status_code == 200
    assert confirm_response.json()["data"]["confirmed_count"] == 1

    questions = client.get(f"/api/v1/question-banks/{bank_id}/questions", headers=headers)
    assert questions.status_code == 200
    assert questions.json()["data"][0]["source_type"] == "feishu_import"
