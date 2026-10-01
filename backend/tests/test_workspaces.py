def test_list_workspaces(auth_client):
    response = auth_client.get("/api/v1/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_create_project(auth_client):
    response = auth_client.post("/api/v1/workspaces/test-user/projects", json={
        "key": "TF",
        "name": "TaskFlow",
        "description": "Test project",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "TF"
    assert data["name"] == "TaskFlow"


def test_list_projects(auth_client):
    auth_client.post("/api/v1/workspaces/test-user/projects", json={
        "key": "TF",
        "name": "TaskFlow",
    })
    response = auth_client.get("/api/v1/workspaces/test-user/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_create_project_duplicate_key(auth_client):
    auth_client.post("/api/v1/workspaces/test-user/projects", json={
        "key": "TF",
        "name": "TaskFlow",
    })
    response = auth_client.post("/api/v1/workspaces/test-user/projects", json={
        "key": "TF",
        "name": "Another",
    })
    assert response.status_code == 400
