from fastapi.testclient import TestClient

from tests.test_stage1 import login


def test_normal_interview_flow(client: TestClient) -> None:
    token = login(client, "interview-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    bank_response = client.post(
        "/api/v1/banks",
        json={"name": "普通面试题库"},
        headers=headers,
    )
    assert bank_response.status_code == 200
    bank_id = bank_response.json()["data"]["id"]

    for index in range(3):
        response = client.post(
            f"/api/v1/banks/{bank_id}/questions",
            json={
                "content": f"请解释 Python 协程调度机制 {index}",
                "answer": "协程通过事件循环调度，遇到 await 让出控制权，适合 IO 密集任务。",
                "tags": ["Python", "异步"],
                "difficulty": 40 + index * 10,
            },
            headers=headers,
        )
        assert response.status_code == 200

    create_response = client.post(
        "/api/v1/interviews",
        json={
            "bank_ids": [bank_id],
            "tags": ["Python"],
            "difficulty_min": 30,
            "difficulty_max": 80,
            "question_count": 2,
            "target": "后端工程师",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    session = create_response.json()["data"]
    assert session["status"] == "ready"
    assert session["strategy"]
    assert session["selection_reason"]
    assert len(session["items"]) == 2
    assert session["items"][0]["question"]["content"].startswith("请解释 Python")

    item_id = session["items"][0]["id"]
    answer_response = client.post(
        f"/api/v1/interviews/items/{item_id}/answer",
        json={"answer": "协程由事件循环调度，await 时释放执行权，适合高并发 IO。"},
        headers=headers,
    )
    assert answer_response.status_code == 200
    item = answer_response.json()["data"]
    assert item["status"] == "answered"
    assert item["feedback"]["score"] >= 0
    assert item["feedback"]["reference_answer"]
    assert item["feedback"]["follow_up"]

    detail_response = client.get(f"/api/v1/interviews/{session['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["items"][0]["feedback"]["comment"]

    complete_response = client.post(
        f"/api/v1/interviews/{session['id']}/complete",
        headers=headers,
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()["data"]
    assert completed["status"] == "completed"
    assert completed["summary"]["score"] >= 0
    assert completed["completed_at"]

    list_response = client.get("/api/v1/interviews", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["id"] == session["id"]


def test_interview_requires_enough_candidates(client: TestClient) -> None:
    token = login(client, "interview-empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    bank_response = client.post(
        "/api/v1/banks",
        json={"name": "空题库"},
        headers=headers,
    )
    bank_id = bank_response.json()["data"]["id"]

    response = client.post(
        "/api/v1/interviews",
        json={"bank_ids": [bank_id], "question_count": 1},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NOT_ENOUGH_QUESTIONS"

