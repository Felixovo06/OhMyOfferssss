from fastapi.testclient import TestClient


def login(client: TestClient, email: str = "owner@example.com") -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "secret123", "name": "Owner"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_auth_me_requires_login(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_and_me(client: TestClient) -> None:
    token = login(client)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "owner@example.com"


def test_group_invitation_flow(client: TestClient) -> None:
    owner_token = login(client, "owner@example.com")
    member_token = login(client, "member@example.com")

    group_response = client.post(
        "/api/v1/groups",
        json={"name": "Frontend Prep", "description": "Practice group"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert group_response.status_code == 200
    group_id = group_response.json()["data"]["id"]

    invitation_response = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        json={"email": "member@example.com"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert invitation_response.status_code == 200
    token = invitation_response.json()["data"]["token"]

    accept_response = client.post(
        f"/api/v1/invitations/{token}/accept",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["data"]["group"]["id"] == group_id

    members_response = client.get(
        f"/api/v1/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert members_response.status_code == 200
    members = members_response.json()["data"]
    assert {member["role"] for member in members} == {"owner", "member"}

