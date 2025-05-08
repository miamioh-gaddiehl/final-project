import pytest

from app import Note, create_app, db


@pytest.fixture
def client():
    app = create_app(database=":memory:", testing=True, debug=True)

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def test_get_notes_empty(client):
    response = client.get("/api/notes")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_note(client):
    data = {"x": 100, "y": 150, "content": "Hello!"}
    response = client.post("/api/notes", json=data)
    assert response.status_code == 200
    note = response.get_json()
    assert note["x"] == 100
    assert note["y"] == 150
    assert note["content"] == "Hello!"
    assert note["color"] is not None

def test_fail_creating_note(client):
    data = {"x": "Invalid", "y": 150, "content": "Hello!"}
    response = client.post("/api/notes", json=data)
    assert response.status_code == 400

    data["x"] = 150
    data["y"] = "Invalid"
    response = client.post("/api/notes", json=data)
    assert response.status_code == 400

def test_reflected_xss(client):
    data = {"x": 150, "y": 150, "content": "< >"}
    response = client.post("/api/notes", json=data)
    note = response.get_json()
    assert response.status_code == 200
    assert "<" not in note["content"]
    assert ">" not in note["content"]

def test_get_note_by_id(client):
    data = {"x": 10, "y": 20, "content": "Check me"}
    response = client.post("/api/notes", json=data)
    assert response.status_code == 200

    note_id = response.get_json()["id"]

    get_response = client.get(f"/api/notes/{note_id}")
    assert get_response.status_code == 200
    note = get_response.get_json()
    assert note["id"] == note_id
    assert note["content"] == "Check me"
    assert note["x"] == 10
    assert note["y"] == 20
    assert note["color"] is not None


def test_update_note(client):
    data = {"x": 10, "y": 10, "content": "Initial"}
    response = client.post("/api/notes", json=data)
    note_id = response.get_json()["id"]

    update_data = {"x": 200, "y": 250, "content": "Updated"}
    response = client.put(f"/api/notes/{note_id}", json=update_data)
    assert response.status_code == 200
    note = response.get_json()
    assert note["x"] == 200
    assert note["y"] == 250
    assert note["content"] == "Updated"

    update_data = {"content": "Updated Again"}
    response = client.put(f"/api/notes/{note_id}", json=update_data)
    note = response.get_json()
    assert note["x"] == 200
    assert note["y"] == 250
    assert note["content"] == "Updated Again"
    assert response.status_code == 200

    update_data = {"x": 300}
    response = client.put(f"/api/notes/{note_id}", json=update_data)
    note = response.get_json()
    assert note["x"] == 300
    assert note["y"] == 250
    assert note["content"] == "Updated Again"
    assert response.status_code == 200

    update_data = {"y": 300}
    response = client.put(f"/api/notes/{note_id}", json=update_data)
    note = response.get_json()
    assert note["x"] == 300
    assert note["y"] == 300
    assert note["content"] == "Updated Again"
    assert response.status_code == 200

def test_delete_note(client):
    data = {"x": 10, "y": 10, "content": "To Delete"}
    response = client.post("/api/notes", json=data)
    note_id = response.get_json()["id"]

    delete_response = client.delete(f"/api/notes/{note_id}")
    assert delete_response.status_code == 200

    get_response = client.get("/api/notes")
    assert all(n["id"] != note_id for n in get_response.get_json())
