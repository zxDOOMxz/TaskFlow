def test_register(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login(client):
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    })

    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_me(auth_client):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
