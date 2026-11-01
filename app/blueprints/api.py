"""Kamera tabanlı JSON uç noktaları: öğrenci yüz kaydı ve yoklama tanıma."""
import json
from datetime import date, datetime

import numpy as np
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Attendance, Course, FaceEmbedding, Student
from ..services import face_service
from ..services.face_service import FaceError, FaceServiceError
from ..utils import get_owned_course

bp = Blueprint("api", __name__, url_prefix="/api")


def _load_candidates(student_ids=None) -> list[tuple[int, np.ndarray]]:
    stmt = db.select(FaceEmbedding.student_id, FaceEmbedding.embedding)
    if student_ids is not None:
        stmt = stmt.where(FaceEmbedding.student_id.in_(student_ids))
    return [(sid, np.asarray(json.loads(raw), dtype=np.float32)) for sid, raw in db.session.execute(stmt)]


def _face_vector(frame_bytes: bytes) -> tuple[np.ndarray, np.ndarray]:
    """(yüz kırpması, embedding) çifti döndürür."""
    face = face_service.extract_face(frame_bytes, min_size=current_app.config["MIN_FACE_SIZE"])
    return face, face_service.compute_embedding(face)


def _error(message: str, code: int, status: str = "error"):
    return jsonify(status=status, message=message), code


@bp.post("/students")
@login_required
def create_student():
    """Öğrenciyi ve yüz verisini tek işlemde kaydeder (yarım kayıt oluşmaz)."""
    school_number = request.form.get("school_number", "").strip()
    name = request.form.get("name", "").strip()
    surname = request.form.get("surname", "").strip()
    frame = request.files.get("frame")

    if not (school_number and name and surname):
        return _error("Okul numarası, ad ve soyad zorunludur.", 400)
    if len(school_number) > 50 or len(name) > 100 or len(surname) > 100:
        return _error("Girilen alanlardan biri izin verilen uzunluğu aşıyor.", 400)
    if frame is None:
        return _error("Kamera görüntüsü eksik. Lütfen kameraya bakın.", 400)
    if db.session.scalar(db.select(Student).filter_by(school_number=school_number)):
        return _error(f"{school_number} numaralı öğrenci zaten kayıtlı.", 409)

    try:
        face, vector = _face_vector(frame.read())
    except FaceError as exc:
        return _error(str(exc), 422, status="fail")
    except FaceServiceError as exc:
        return _error(str(exc), 503)

    owner_id, distance = face_service.find_best_match(
        vector, _load_candidates(), current_app.config["FACE_MATCH_THRESHOLD"]
    )
    if owner_id is not None:
        owner = db.session.get(Student, owner_id)
        return _error(
            f"Bu yüz zaten {owner.full_name} ({owner.school_number}) adına kayıtlı.",
            409,
            status="duplicate",
        )

    course_ids = request.form.getlist("course_ids", type=int)
    courses = (
        db.session.scalars(
            db.select(Course).where(Course.id.in_(course_ids), Course.teacher_id == current_user.id)
        ).all()
        if course_ids
        else []
    )

    student = Student(school_number=school_number, name=name, surname=surname)
    student.face_embedding = FaceEmbedding(embedding=json.dumps(vector.tolist()))
    student.courses = courses
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error(f"{school_number} numaralı öğrenci zaten kayıtlı.", 409)

    return (
        jsonify(
            status="success",
            message=f"{student.full_name} kaydedildi.",
            student={"id": student.id, "name": student.full_name, "school_number": student.school_number},
            enrolled_courses=len(courses),
        ),
        201,
    )


@bp.post("/recognize")
@login_required
def recognize():
    """Kare içindeki yüzü derse kayıtlı öğrencilerle eşleştirir ve yoklamaya işler."""
    course_id = request.form.get("course_id", type=int)
    frame = request.files.get("frame")
    if not course_id or frame is None:
        return _error("Ders veya görüntü eksik.", 400)

    course = get_owned_course(course_id)
    candidates = _load_candidates([s.id for s in course.students])
    if not candidates:
        return jsonify(status="no_enrollment", message="Bu derse yüzü kayıtlı öğrenci yok.")

    try:
        face, vector = _face_vector(frame.read())
    except FaceError as exc:
        return jsonify(status="no_face", message=str(exc))
    except FaceServiceError as exc:
        return _error(str(exc), 503)

    student_id, distance = face_service.find_best_match(
        vector, candidates, current_app.config["FACE_MATCH_THRESHOLD"]
    )
    if student_id is None:
        return jsonify(status="no_match", message="Yüz derse kayıtlı bir öğrenciyle eşleşmedi.")

    student = db.session.get(Student, student_id)
    payload = {"id": student.id, "name": student.full_name, "school_number": student.school_number}
    today = date.today()

    existing = db.session.scalar(
        db.select(Attendance).filter_by(course_id=course.id, student_id=student.id, date=today)
    )
    if existing:
        return jsonify(
            status="already",
            message=f"{student.full_name} bugün zaten yoklamada.",
            student=payload,
            marked_at=existing.marked_at.strftime("%H:%M"),
        )

    record = Attendance(
        course_id=course.id,
        student_id=student.id,
        date=today,
        marked_at=datetime.now(),
        distance=round(distance, 4) if distance is not None else None,
    )
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:  # aynı anda gelen ikinci istek
        db.session.rollback()
        return jsonify(status="already", message=f"{student.full_name} bugün zaten yoklamada.", student=payload)

    return jsonify(
        status="marked",
        message=f"{student.full_name} yoklamaya eklendi.",
        student=payload,
        marked_at=record.marked_at.strftime("%H:%M"),
    )
