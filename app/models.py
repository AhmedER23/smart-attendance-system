"""Veritabanı modelleri."""
import json
from datetime import date, datetime

import numpy as np
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

# Öğrenci <-> Ders çoklu ilişkisi. Raporlarda "YOK" durumunu hesaplayabilmek için gerekli.
enrollments = db.Table(
    "enrollments",
    db.Column("student_id", db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)


class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    courses = db.relationship(
        "Course", back_populates="teacher", cascade="all, delete-orphan", order_by="Course.name"
    )

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    school_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    face_embedding = db.relationship(
        "FaceEmbedding", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    courses = db.relationship("Course", secondary=enrollments, back_populates="students")
    attendance_records = db.relationship(
        "Attendance", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)

    teacher = db.relationship("Teacher", back_populates="courses")
    students = db.relationship("Student", secondary=enrollments, back_populates="courses")
    attendance_records = db.relationship(
        "Attendance", back_populates="course", cascade="all, delete-orphan"
    )


class FaceEmbedding(db.Model):
    __tablename__ = "face_embeddings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    embedding = db.Column(db.Text, nullable=False)  # JSON olarak saklanan vektör
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", back_populates="face_embedding")

    @property
    def vector(self) -> np.ndarray:
        return np.asarray(json.loads(self.embedding), dtype=np.float32)


class Attendance(db.Model):
    """Yalnızca derse katıldığı doğrulanan öğrenciler için kayıt tutulur."""

    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint("course_id", "student_id", "date", name="uq_attendance_course_student_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    distance = db.Column(db.Float, nullable=True)  # eşleşme mesafesi (denetim için)

    course = db.relationship("Course", back_populates="attendance_records")
    student = db.relationship("Student", back_populates="attendance_records")
