from app.extensions import db
from app.models import Course, Student

from .conftest import login, make_teacher


def test_create_course(auth_client, teacher):
    response = auth_client.post("/dashboard", data={"course_name": "Veri Yapıları"})
    assert response.status_code == 302
    assert db.session.scalar(db.select(Course).filter_by(name="Veri Yapıları")) is not None


def test_course_name_is_validated(auth_client):
    auth_client.post("/dashboard", data={"course_name": "x"})
    assert db.session.scalar(db.select(Course)) is None


def test_other_teachers_course_is_forbidden(client, course):
    make_teacher(email="teacher2@example.com", name="Başka", surname="Hoca")
    login(client, "teacher2@example.com")
    assert client.get(f"/courses/{course.id}").status_code == 403
    assert client.get(f"/attendance/{course.id}").status_code == 403
    assert client.post(f"/courses/{course.id}/delete").status_code == 403


def test_enroll_and_unenroll(auth_client, course):
    student = Student(school_number="1", name="Ayşe", surname="Demir")
    db.session.add(student)
    db.session.commit()

    auth_client.post(f"/courses/{course.id}/enroll", data={"student_id": student.id})
    assert student in db.session.get(Course, course.id).students

    auth_client.post(f"/courses/{course.id}/unenroll/{student.id}")
    assert student not in db.session.get(Course, course.id).students


def test_enroll_all_students(auth_client, course):
    s1 = Student(school_number="1", name="Ayşe", surname="Demir")
    s2 = Student(school_number="2", name="Mehmet", surname="Kaya")
    db.session.add_all([s1, s2])
    db.session.commit()

    auth_client.post(f"/courses/{course.id}/enroll", data={"enroll_all": "1"})
    students = db.session.get(Course, course.id).students
    assert s1 in students and s2 in students


def test_unknown_course_returns_404(auth_client):
    assert auth_client.get("/courses/999").status_code == 404
