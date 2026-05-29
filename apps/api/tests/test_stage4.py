from fastapi.testclient import TestClient

from tests.test_stage1 import login


def test_resume_upload_and_customized_interview_flow(client: TestClient) -> None:
    token = login(client, "resume-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resume_text = """
张三
zhangsan@example.com
13800000000
技能：Python FastAPI PostgreSQL Redis Docker
某科技公司 后端工程师 负责推荐系统缓存优化项目
浙江大学 计算机科学与技术
项目：高并发缓存平台，使用 Redis 和 Python 完成核心链路
"""
    upload_response = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.txt", resume_text.encode(), "text/plain")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    resume = upload_response.json()["data"]
    assert resume["status"] == "completed"
    assert resume["is_scanned"] is False
    assert "Python" in resume["summary"]["skills"]
    assert resume["summary"]["follow_up_directions"]

    list_response = client.get("/api/v1/resumes", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["id"] == resume["id"]

    detail_response = client.get(f"/api/v1/resumes/{resume['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["summary"]["email"] == "zhangsan@example.com"

    bank_response = client.post(
        "/api/v1/banks",
        json={"name": "客制化面试题库"},
        headers=headers,
    )
    bank_id = bank_response.json()["data"]["id"]
    for index in range(2):
        response = client.post(
            f"/api/v1/banks/{bank_id}/questions",
            json={
                "content": f"请说明 Redis 缓存击穿治理方案 {index}",
                "answer": "可使用互斥锁、逻辑过期、热点预热和降级保护。",
                "tags": ["Redis", "后端"],
                "difficulty": 60,
            },
            headers=headers,
        )
        assert response.status_code == 200

    interview_response = client.post(
        "/api/v1/interviews",
        json={
            "bank_ids": [bank_id],
            "tags": ["Redis"],
            "question_count": 1,
            "goal": "后端工程师",
            "mode": "custom",
            "resume_id": resume["id"],
        },
        headers=headers,
    )
    assert interview_response.status_code == 200
    interview = interview_response.json()["data"]
    assert interview["mode"] == "custom"
    assert interview["resume_id"] == resume["id"]
    assert "候选人技能" in interview["strategy"] or "客制化" in interview["title"]


def test_scanned_pdf_gets_clear_resume_error(client: TestClient) -> None:
    token = login(client, "scan-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/resumes",
        files={"file": ("scan.pdf", b"%PDF-1.4\n/Images only\n%%EOF", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 200
    resume = response.json()["data"]
    assert resume["status"] == "failed"
    assert resume["is_scanned"] is True
    assert "扫描件" in resume["error_message"]
