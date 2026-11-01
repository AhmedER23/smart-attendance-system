import numpy as np

from app.extensions import db
from app.models import Attendance, Student

from .conftest import frame


def register(client, number, name, course_ids=()):
    return client.post(
        "/api/students",
        data={
            "school_number": number,
            "name": name,
            "surname": "Test",
            "course_ids": [str(c) for c in course_ids],
            "frame": frame(),
        },
    )


def test_register_student_with_face(auth_client, course, fake_face):
    response = register(auth_client, "100", "Ayşe", [course.id])
    assert response.status_code == 201
    student = db.session.scalar(db.select(Student).filter_by(school_number="100"))
    assert student.face_embedding is not None
    assert course in student.courses


def test_duplicate_face_is_rejected_without_creating_student(auth_client, fake_face):
    assert register(auth_client, "100", "Ayşe").status_code == 201
    response = register(auth_client, "101", "Mehmet")  # aynı vektör = aynı yüz
    assert response.status_code == 409
    assert db.session.scalar(db.select(Student).filter_by(school_number="101")) is None


def test_duplicate_school_number_is_rejected(auth_client, fake_face):
    register(auth_client, "100", "Ayşe")
    fake_face["vector"] = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert register(auth_client, "100", "Başka").status_code == 409


def test_register_without_face_returns_error_and_saves_nothing(auth_client, fake_face):
    fake_face["error"] = "Yüz algılanamadı."
    response = register(auth_client, "100", "Ayşe")
    assert response.status_code == 422
    assert db.session.scalar(db.select(Student)) is None


def test_recognize_marks_once_per_day(auth_client, course, fake_face):
    register(auth_client, "100", "Ayşe", [course.id])

    first = auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})
    assert first.get_json()["status"] == "marked"

    second = auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})
    assert second.get_json()["status"] == "already"
    assert db.session.query(Attendance).count() == 1


def test_recognize_ignores_students_not_enrolled_in_course(auth_client, course, fake_face):
    register(auth_client, "100", "Ayşe")  # derse kayıtlı değil
    response = auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})
    assert response.get_json()["status"] == "no_enrollment"


def test_recognize_unknown_face_and_no_face(auth_client, course, fake_face):
    register(auth_client, "100", "Ayşe", [course.id])

    fake_face["vector"] = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    unknown = auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})
    assert unknown.get_json()["status"] == "no_match"

    fake_face["error"] = "Yüz algılanamadı."
    missing = auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})
    assert missing.get_json()["status"] == "no_face"


def test_same_student_can_attend_two_courses_on_same_day(auth_client, course, fake_face, teacher):
    from app.models import Course

    other = Course(name="Veritabanı", teacher_id=teacher.id)
    db.session.add(other)
    db.session.commit()
    register(auth_client, "100", "Ayşe", [course.id, other.id])

    for c in (course, other):
        result = auth_client.post("/api/recognize", data={"course_id": c.id, "frame": frame()})
        assert result.get_json()["status"] == "marked"


def test_report_lists_absent_students_and_csv_export(auth_client, course, fake_face):
    register(auth_client, "100", "Ayşe", [course.id])
    fake_face["vector"] = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    register(auth_client, "101", "Mehmet", [course.id])

    fake_face["vector"] = np.array([1.0, 0.0, 0.0], dtype=np.float32)  # yalnızca Ayşe gelir
    auth_client.post("/api/recognize", data={"course_id": course.id, "frame": frame()})

    page = auth_client.get(f"/reports?course_id={course.id}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Var" in html and "Yok" in html

    export = auth_client.get(f"/reports/export.csv?course_id={course.id}")
    assert export.mimetype == "text/csv"
    text = export.get_data(as_text=True)
    assert "Ayşe" in text and "Mehmet" in text and ",Yok," in text
