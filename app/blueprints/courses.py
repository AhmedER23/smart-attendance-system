"""Ders yönetimi ve derse öğrenci kaydı."""
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Attendance, Course, Student
from ..utils import get_owned_course

bp = Blueprint("courses", __name__)


@bp.route("/")
def index():
    return redirect(url_for("courses.dashboard"))


@bp.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        name = request.form.get("course_name", "").strip()
        if not 2 <= len(name) <= 100:
            flash("Ders adı 2-100 karakter arasında olmalıdır.", "error")
        else:
            db.session.add(Course(name=name, teacher_id=current_user.id))
            db.session.commit()
            flash(f"“{name}” dersi eklendi. Şimdi öğrencileri derse kaydedin.", "success")
        return redirect(url_for("courses.dashboard"))

    courses = current_user.courses
    present_today = {}
    if courses:
        rows = db.session.execute(
            db.select(Attendance.course_id, func.count())
            .where(Attendance.date == date.today(), Attendance.course_id.in_([c.id for c in courses]))
            .group_by(Attendance.course_id)
        ).all()
        present_today = dict(rows)

    return render_template("courses/dashboard.html", courses=courses, present_today=present_today)


@bp.get("/courses/<int:course_id>")
@login_required
def detail(course_id: int):
    course = get_owned_course(course_id)
    enrolled = sorted(course.students, key=lambda s: (s.name.lower(), s.surname.lower()))
    enrolled_ids = {s.id for s in enrolled}
    available = [
        s
        for s in db.session.scalars(db.select(Student).order_by(Student.name, Student.surname))
        if s.id not in enrolled_ids
    ]
    return render_template("courses/detail.html", course=course, enrolled=enrolled, available=available)


@bp.post("/courses/<int:course_id>/enroll")
@login_required
def enroll(course_id: int):
    course = get_owned_course(course_id)

    # 1. Hepsini tek tıkla ekle
    if request.form.get("enroll_all") == "1":
        enrolled_ids = {s.id for s in course.students}
        to_add = [
            s for s in db.session.scalars(db.select(Student)).all()
            if s.id not in enrolled_ids
        ]
        if not to_add:
            flash("Eklenebilecek başka öğrenci yok.", "info")
        else:
            for s in to_add:
                course.students.append(s)
            db.session.commit()
            flash(f"{len(to_add)} öğrencinin tümü derse eklendi.", "success")
        return redirect(url_for("courses.detail", course_id=course.id))

    # 2. Seçilen öğrencileri toplu veya tekli ekle
    student_ids = request.form.getlist("student_ids", type=int)
    single_id = request.form.get("student_id", type=int)
    if single_id and single_id not in student_ids:
        student_ids.append(single_id)

    if not student_ids:
        flash("Lütfen derse eklenecek en az bir öğrenci seçin.", "error")
        return redirect(url_for("courses.detail", course_id=course.id))

    added_count = 0
    for sid in student_ids:
        student = db.session.get(Student, sid)
        if student and student not in course.students:
            course.students.append(student)
            added_count += 1

    db.session.commit()
    if added_count > 0:
        flash(f"{added_count} öğrenci derse başarıyla eklendi.", "success")
    else:
        flash("Seçilen öğrenciler zaten bu derse kayıtlı.", "info")

    return redirect(url_for("courses.detail", course_id=course.id))


@bp.post("/courses/<int:course_id>/unenroll/<int:student_id>")
@login_required
def unenroll(course_id: int, student_id: int):
    course = get_owned_course(course_id)
    student = db.session.get(Student, student_id)
    if student and student in course.students:
        course.students.remove(student)
        db.session.commit()
        flash(f"{student.full_name} dersten çıkarıldı.", "success")
    return redirect(url_for("courses.detail", course_id=course.id))


@bp.post("/courses/<int:course_id>/delete")
@login_required
def delete(course_id: int):
    course = get_owned_course(course_id)
    name = course.name
    db.session.delete(course)
    db.session.commit()
    flash(f"“{name}” dersi ve yoklama kayıtları silindi.", "success")
    return redirect(url_for("courses.dashboard"))
