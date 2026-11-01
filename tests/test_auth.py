from app.extensions import db
from app.models import Teacher

from .conftest import PASSWORD, login


def test_protected_pages_redirect_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_returns_json_401_when_logged_out(client):
    response = client.post("/api/recognize")
    assert response.status_code == 401
    assert response.get_json()["status"] == "error"


def test_login_success_and_failure(client, teacher):
    assert client.post("/login", data={"email": "teacher1@example.com", "password": "yanlis"}).status_code == 200
    response = login(client)
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 200


def test_login_does_not_redirect_to_external_site(client, teacher):
    response = client.post(
        "/login?next=https://evil.example.com/",
        data={"email": "teacher1@example.com", "password": PASSWORD},
    )
    assert response.status_code == 302
    assert "evil.example.com" not in response.headers["Location"]


def test_register_validates_input(client):
    weak = client.post(
        "/register",
        data={"name": "Ayşe", "surname": "Yılmaz", "email": "ayse@example.com", "password": "kisa", "confirm": "kisa"},
    )
    assert weak.status_code == 200
    assert db.session.scalar(db.select(Teacher).filter_by(email="ayse@example.com")) is None

    ok = client.post(
        "/register",
        data={"name": "Ayşe", "surname": "Yılmaz", "email": "ayse@example.com", "password": "uzunparola1", "confirm": "uzunparola1"},
    )
    assert ok.status_code == 302
    assert db.session.scalar(db.select(Teacher).filter_by(email="ayse@example.com")) is not None


def test_register_can_be_disabled(app, client):
    app.config["ALLOW_TEACHER_REGISTRATION"] = False
    assert client.get("/register").status_code == 404
