from fastapi.testclient import TestClient

from tests.test_stage1 import login


def test_question_bank_semantic_metadata(client: TestClient) -> None:
    token = login(client, "phase6-bank-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/banks",
        json={
            "name": "后端项目题库",
            "description": "覆盖 FastAPI、Redis、PostgreSQL 的项目追问题",
            "default_tags": ["后端"],
            "target_positions": ["后端工程师"],
            "skill_keywords": ["FastAPI", "Redis"],
            "domain_tags": ["Web 后端", "缓存"],
            "semantic_profile": {"depth": "project"},
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    bank = create_response.json()["data"]
    assert bank["target_roles"] == ["后端工程师"]
    assert bank["target_positions"] == ["后端工程师"]
    assert bank["skill_keywords"] == ["FastAPI", "Redis"]
    assert bank["domains"] == ["Web 后端", "缓存"]
    assert bank["domain_tags"] == ["Web 后端", "缓存"]
    assert bank["semantic_profile"]["depth"] == "project"

    update_response = client.patch(
        f"/api/v1/banks/{bank['id']}",
        json={"skill_keywords": ["Redis", "PostgreSQL"], "domain_tags": ["数据库"]},
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["skill_keywords"] == ["Redis", "PostgreSQL"]
    assert updated["domains"] == ["数据库"]


def test_smart_interview_plan_recommends_resume_related_bank(client: TestClient) -> None:
    token = login(client, "phase6-plan-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    resume = upload_phase6_resume(client, headers)
    redis_bank_id = create_phase6_bank(
        client,
        headers,
        name="Redis 后端项目题库",
        skill_keywords=["Redis", "FastAPI"],
        domains=["缓存", "后端"],
    )
    create_phase6_question(client, headers, redis_bank_id, "请说明 Redis 缓存击穿治理方案")
    frontend_bank_id = create_phase6_bank(
        client,
        headers,
        name="React 前端题库",
        skill_keywords=["React", "CSS"],
        domains=["前端"],
    )
    create_phase6_question(client, headers, frontend_bank_id, "请说明 React 渲染优化方案")

    response = client.post(
        "/api/v1/interviews/plan",
        json={
            "resume_id": resume["id"],
            "target": "后端工程师",
            "flow_mode": "project_first",
            "question_count": 2,
        },
        headers=headers,
    )
    assert response.status_code == 200
    plan = response.json()["data"]
    assert plan["flow_mode"] == "project_first"
    assert plan["recommended_banks"][0]["bank_id"] == redis_bank_id
    assert plan["recommended_banks"][0]["score"] >= plan["recommended_banks"][1]["score"]
    assert frontend_bank_id in [item["bank_id"] for item in plan["recommended_banks"]]
    assert plan["stages"][0]["stage"] == "project_deep_dive"
    assert plan["selected_bank_ids"][0] == redis_bank_id


def test_project_first_interview_stores_stage_metadata(client: TestClient) -> None:
    token = login(client, "phase6-create-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    resume = upload_phase6_resume(client, headers)
    bank_id = create_phase6_bank(
        client,
        headers,
        name="Redis 项目深挖题库",
        skill_keywords=["Redis", "FastAPI"],
        domains=["缓存", "后端"],
    )
    create_phase6_question(client, headers, bank_id, "请结合项目说明 Redis 缓存击穿如何处理")

    response = client.post(
        "/api/v1/interviews",
        json={
            "resume_id": resume["id"],
            "target": "后端工程师",
            "flow_mode": "project",
            "question_count": 1,
        },
        headers=headers,
    )
    assert response.status_code == 200
    session = response.json()["data"]
    assert session["flow_mode"] == "project"
    assert session["current_stage"] == "准备第一题"
    assert session["config"]["bank_ids"] == []
    assert session["stage_plan"] == []
    assert session["items"] == []

    start_response = client.post(
        f"/api/v1/interviews/{session['id']}/start",
        headers=headers,
    )
    assert start_response.status_code == 200
    session = start_response.json()["data"]
    assert session["current_stage"] == "项目追问"
    assert session["config"]["bank_ids"] == [bank_id]
    assert session["stage_plan"][0]["stage"] == "project_deep_dive"
    assert session["items"][0]["stage"] == "项目追问"
    assert session["items"][0]["intent"]
    assert session["items"][0]["intention"] == session["items"][0]["intent"]
    assert session["items"][0]["related_project"]
    assert session["items"][0]["related_skill"] in {"Redis", "后端"}
    assert session["items"][0]["related_skills"]

    item_id = session["items"][0]["id"]
    answer_response = client.post(
        f"/api/v1/interviews/items/{item_id}/answer",
        json={"answer": "我会使用互斥锁、逻辑过期和热点预热，结合监控做降级保护。"},
        headers=headers,
    )
    assert answer_response.status_code == 200
    feedback = answer_response.json()["data"]["feedback"]
    assert feedback["next_action"] in {"continue_project", "next_question"}
    assert feedback["decision_reason"]
    complete_response = client.post(
        f"/api/v1/interviews/{session['id']}/complete",
        headers=headers,
    )
    assert complete_response.status_code == 200

    summary_response = client.get(
        f"/api/v1/interviews/{session['id']}/summary",
        headers=headers,
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()["data"]
    assert summary["project_performance"][0]["project_name"]
    assert summary["knowledge_performance"]
    assert summary["review_plan"]


def test_interview_candidate_retrieval_prefers_goal_topics(client: TestClient) -> None:
    token = login(client, "phase6-retrieval-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    bank_id = create_phase6_bank(
        client,
        headers,
        name="混合后端题库",
        skill_keywords=["Java", "Redis", "React"],
        domains=["后端", "前端"],
    )
    create_phase6_question(
        client,
        headers,
        bank_id,
        "volatile 的作用是什么？",
        tags=["Java并发"],
        difficulty=60,
    )
    create_phase6_question(
        client,
        headers,
        bank_id,
        "什么是缓存穿透、击穿、雪崩？",
        tags=["Redis"],
        difficulty=65,
    )
    create_phase6_question(
        client,
        headers,
        bank_id,
        "React key 的作用是什么？",
        tags=["React"],
        difficulty=50,
    )

    response = client.post(
        "/api/v1/interviews",
        json={
            "bank_ids": [bank_id],
            "target": "我要面试 3 年 Java 后端，重点考并发、Redis、MySQL，时长 30 分钟",
            "question_count": 1,
            "duration_minutes": 30,
        },
        headers=headers,
    )
    assert response.status_code == 200
    session = response.json()["data"]

    start_response = client.post(
        f"/api/v1/interviews/{session['id']}/start",
        headers=headers,
    )
    assert start_response.status_code == 200
    first_question = start_response.json()["data"]["items"][0]["question"]
    assert "React" not in first_question["content"]
    assert set(first_question["tags"]) & {"Java并发", "Redis"}


def test_smart_interview_rejects_unready_resume(client: TestClient) -> None:
    token = login(client, "phase6-unready-resume@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/resumes",
        files={"file": ("scan.pdf", b"%PDF-1.4\n/Images only\n%%EOF", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    resume = response.json()["data"]
    assert resume["status"] == "failed"

    plan_response = client.post(
        "/api/v1/interviews/plan",
        json={"resume_id": resume["id"], "flow_mode": "project", "question_count": 1},
        headers=headers,
    )
    assert plan_response.status_code == 422
    assert plan_response.json()["error"]["code"] == "RESUME_NOT_READY"


def upload_phase6_resume(client: TestClient, headers: dict[str, str]) -> dict:
    resume_text = """
李四
技能：Python FastAPI Redis PostgreSQL Docker
项目：高并发缓存平台，使用 FastAPI 和 Redis 治理缓存击穿和热点 key
"""
    response = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.txt", resume_text.encode(), "text/plain")},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


def create_phase6_bank(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    skill_keywords: list[str],
    domains: list[str],
) -> str:
    response = client.post(
        "/api/v1/banks",
        json={
            "name": name,
            "description": f"{name}，用于项目追问和知识点联动",
            "target_positions": ["后端工程师"],
            "skill_keywords": skill_keywords,
            "domain_tags": domains,
            "default_tags": skill_keywords,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def create_phase6_question(
    client: TestClient,
    headers: dict[str, str],
    bank_id: str,
    content: str,
    *,
    tags: list[str] | None = None,
    difficulty: int = 70,
) -> None:
    response = client.post(
        f"/api/v1/banks/{bank_id}/questions",
        json={
            "content": content,
            "answer": "需要结合项目背景、核心方案、边界问题和取舍说明。",
            "tags": tags or ["Redis", "后端"],
            "difficulty": difficulty,
        },
        headers=headers,
    )
    assert response.status_code == 200
