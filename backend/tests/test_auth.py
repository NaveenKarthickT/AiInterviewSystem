import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

# Ensure tables exist
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api_version" in data


def test_register_and_login():
    email = "candidate_test_1@example.com"
    password = "StrongPassword123!"
    full_name = "Alex Engineer"

    # 1. Register candidate
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )
    # Could be 201 or 400 if already exists in persistent dev db
    assert reg_response.status_code in (201, 400)
    
    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["email"] == email
    assert login_data["user"]["full_name"] == full_name

    token = login_data["access_token"]

    # 3. Authenticated /me endpoint
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == full_name
    print("Authentication test passed successfully!")


if __name__ == "__main__":
    test_health_check()
    test_register_and_login()
