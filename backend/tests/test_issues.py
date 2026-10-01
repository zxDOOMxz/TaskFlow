import pytest


@pytest.fixture
def project_client(auth_client):
    auth_client.post("/api/v1/workspaces/test-user/projects", json={
        "key": "TF",
        "name": "TaskFlow",
    })
    return auth_client


def test_create_issue(project_client):
    response = project_client.post("/api/v1/projects/TF/issues", json={
        "title": "Test issue",
        "description": "Description",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test issue"
    assert data["key"] == "TF-1"


def test_list_issues(project_client):
    project_client.post("/api/v1/projects/TF/issues", json={
        "title": "Test issue",
    })
    response = project_client.get("/api/v1/projects/TF/issues")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_add_comment(project_client):
    project_client.post("/api/v1/projects/TF/issues", json={
        "title": "Test issue",
    })
    response = project_client.post("/api/v1/projects/TF/issues/TF-1/comments", json={
        "content": "Great work!",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Great work!"


def test_list_boards(project_client):
    response = project_client.get("/api/v1/projects/TF/boards")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Board"
