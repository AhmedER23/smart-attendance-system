import io

import numpy as np
import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Course, Teacher
from app.services import face_service
from app.services.face_service import FaceError

PASSWORD = "password123"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_teacher(email="teacher1@example.com", name="Ali", surname="Yılmaz"):
    teacher = Teacher(email=email, name=name, surname=surname)
    teacher.set_password(PASSWORD)
    db.session.add(teacher)
    db.session.commit()
    return teacher


@pytest.fixture()
def teacher(app):
    return make_teacher()


@pytest.fixture()
def course(teacher):
    course = Course(name="Yapay Zeka", teacher_id=teacher.id)
    db.session.add(course)
    db.session.commit()
    return course


def login(client, email="teacher1@example.com"):
    return client.post("/login", data={"email": email, "password": PASSWORD})


@pytest.fixture()
def auth_client(client, teacher):
    login(client)
    return client


@pytest.fixture()
def fake_face(monkeypatch):
    """Gerçek model yerine kontrol edilebilir yüz servisi kullanır (TensorFlow gerekmez)."""
    state = {"vector": np.array([1.0, 0.0, 0.0], dtype=np.float32), "error": None}

    def extract(data, min_size=60):
        if state["error"]:
            raise FaceError(state["error"])
        return np.zeros((80, 80, 3), dtype=np.uint8)

    def extract_detail(data, min_size=60):
        if state["error"]:
            raise FaceError(state["error"])
        crop = np.zeros((80, 80, 3), dtype=np.uint8)
        return crop, np.zeros((240, 320, 3), dtype=np.uint8), (10, 10, 80, 80)

    monkeypatch.setattr(face_service, "extract_face", extract)
    monkeypatch.setattr(face_service, "extract_face_detail", extract_detail)
    monkeypatch.setattr(face_service, "compute_embedding", lambda crop: state["vector"])
    monkeypatch.setattr(face_service, "is_live", lambda *args, **kwargs: (True, "Canlı"))
    return state


def frame():
    return (io.BytesIO(b"fake-jpeg"), "frame.jpg")
