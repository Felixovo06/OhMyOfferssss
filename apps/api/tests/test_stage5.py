from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.core.middleware import RequestIdMiddleware
from app.main import create_app
from tests.test_stage1 import login


def test_success_and_error_responses_include_request_id(client: TestClient) -> None:
    request_id = "req_stage5_contract"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "stage5@example.com", "password": "secret123", "name": "Stage 5"},
        headers={"x-request-id": request_id},
    )
    assert login_response.status_code == 200
    assert login_response.headers["x-request-id"] == request_id
    assert login_response.json()["request_id"] == request_id

    client.post("/api/v1/auth/logout")
    error_response = client.get(
        "/api/v1/auth/me",
        headers={"x-request-id": request_id},
    )
    assert error_response.status_code == 401
    assert error_response.headers["x-request-id"] == request_id
    assert error_response.json()["request_id"] == request_id
    assert error_response.json()["error"]["code"] == "UNAUTHORIZED"


def test_validation_errors_keep_request_id(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "short"},
        headers={"x-request-id": "req_validation"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["request_id"] == "req_validation"
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_unexpected_errors_are_logged_with_request_id(caplog) -> None:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    router = APIRouter()

    @router.get("/boom")
    def boom() -> None:
        raise RuntimeError("private failure details")

    app.include_router(router)

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/boom", headers={"x-request-id": "req_unexpected"})

    assert response.status_code == 500
    body = response.json()
    assert body["request_id"] == "req_unexpected"
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "private failure details" not in body["error"]["message"]
    assert "request_id=req_unexpected" in caplog.text


def test_settings_defaults_do_not_point_at_shared_infrastructure() -> None:
    settings = Settings(_env_file=None)

    assert "39.104" not in settings.database_url
    assert "39.104" not in settings.redis_url
    assert "localhost" in settings.database_url
    assert "localhost" in settings.redis_url


def test_openapi_contract_contains_stage5_error_and_core_paths(client: TestClient) -> None:
    token = login(client, "openapi@example.com")

    schema = create_app().openapi()
    assert schema["openapi"].startswith("3.")
    assert "/api/v1/auth/me" in schema["paths"]
    assert "/api/v1/groups" in schema["paths"]
    assert "/api/v1/banks" in schema["paths"]
    assert "/api/v1/imports/feishu" in schema["paths"]
    assert "/api/v1/interviews" in schema["paths"]
    assert "/api/v1/resumes" in schema["paths"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "x-request-id": "req_openapi"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["request_id"] == "req_openapi"
