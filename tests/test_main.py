from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.models import Base
from datetime import datetime
import time
import pytest

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def clean_database():
    """Fixture para limpar o banco de dados antes de cada teste."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def get_auth_token(client):
    username = f"admin_{int(time.time())}"

    client.post(
        "/auth/register",
        json={"username": username, "password": "testpass"}
    )
    response = client.post(
        "/auth/login",
        json={"username": username, "password": "testpass"}
    )
    return response.json()["access_token"]

def test_create_sensor_data(client):    
    headers={"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.post(
        "/data",
        json={
            "server_ulid": "server_1",
            "timestamp": "2023-10-01T12:00:00",
            "temperature": 25.5,
            "humidity": 60.0
        },
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["server_ulid"] == "server_1"
    assert response.json()["temperature"] == 25.5

def test_get_sensor_data(client):
    headers={"Authorization": f"Bearer {get_auth_token(client)}"}
    client.post(
        "/data",
        json={
            "server_ulid": "server_1",
            "timestamp": "2024-02-19T12:00:00Z",
            "temperature": {"value": 25.5},
            "humidity": {"value": 60.0}
        },
        headers=headers
    )

    response = client.get("/data", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    response = client.get("/data?aggregation=minute", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    response = client.get("/data?server_ulid=server_1&start_time=2024-02-19T12:00:00Z&end_time=2024-02-19T13:00:00Z", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_login_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass"}
    )

    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_register_server(client):
    headers = {"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.post(
        "/servers",
        json={"server_name": "Dolly #1"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["server_name"] == "Dolly #1"
    assert "server_ulid" in response.json()

def test_get_server_health(client):
    headers = {"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.post(
        "/servers",
        json={"server_name": "Dolly #1"},
        headers=headers
    )
    server_ulid = response.json()["server_ulid"]
    client.post(
        "/data",
        json={
            "server_ulid": server_ulid,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature": {"value": 25.5}
        },
        headers=headers
    )
    response = client.get(f"/health/{server_ulid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_all_servers_health(client):
    headers = {"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.post(
        "/servers",
        json={"server_name": "Dolly #1"},
        headers=headers
    )
    server_ulid = response.json()["server_ulid"]

    response = client.post(
        "/servers",
        json={"server_name": "Dolly #2"},
        headers=headers
    )
    server_ulid_2 = response.json()["server_ulid"]

    client.post(
        "/data",
        json={
            "server_ulid": server_ulid,
            "server_name": "Dolly #1",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature": {"value": 25.5}
        },
        headers=headers
    )
    client.post(
        "/data",
        json={
            "server_ulid": server_ulid_2,
            "server_name": "Dolly #2",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature": {"value": 30.0}
        },
        headers=headers
    )
    response = client.get("/healths/all", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["servers"]) == 2

def test_create_sensor_data_invalid(client):
    headers = {"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.post(
        "/data",
        json={
            "server_ulid": "server_1",
            "timestamp": "2024-02-19T12:00:00Z"
        },
        headers=headers
    )
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("Pelo menos um valor de sensor deve ser enviado." in error["msg"] for error in error_detail)

def test_get_server_health_invalid(client):
    headers = {"Authorization": f"Bearer {get_auth_token(client)}"}
    response = client.get("/health/invalid_server", headers=headers)
    assert response.status_code == 404
    assert "Servidor não encontrado." in response.json()["detail"]