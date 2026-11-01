"""Öğrenci listesi ve yüz kaydı ekranı."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Student

bp = Blueprint("students", __name__, url_prefix="/students")


@bp.get("/")
@login_required
def list_students():
    query = request.args.get("q", "").strip()
    stmt = db.select(Student).order_by(Student.name, Student.surname)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            db.or_(Student.name.ilike(like), Student.surname.ilike(like), Student.school_number.ilike(like))
        )
    students = db.session.scalars(stmt).all()
    return render_template("students/list.html", students=students, query=query)


@bp.get("/new")
@login_required
def new():
    preselected_course_id = request.args.get("course_id", type=int)
    return render_template(
        "students/new.html",
        courses=current_user.courses,
        preselected_course_id=preselected_course_id,
    )


@bp.post("/<int:student_id>/delete")
@login_required
def delete(student_id: int):
    student = db.session.get(Student, student_id)
    if student is None:
        flash("Öğrenci bulunamadı.", "error")
    else:
        name = student.full_name
        db.session.delete(student)
        db.session.commit()
        flash(f"{name} ve yüz verisi silindi.", "success")
    return redirect(url_for("students.list_students"))
