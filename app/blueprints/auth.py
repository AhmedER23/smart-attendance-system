"""Giriş, çıkış ve öğretmen kaydı."""
import re

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Teacher
from ..utils import is_safe_redirect

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("courses.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        teacher = db.session.scalar(db.select(Teacher).filter_by(email=email))

        if teacher and teacher.check_password(password):
            login_user(teacher, remember=request.form.get("remember") == "on")
            target = request.args.get("next")
            return redirect(target if is_safe_redirect(target) else url_for("courses.dashboard"))
        flash("E-posta adresi veya parola hatalı.", "error")

    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if not current_app.config["ALLOW_TEACHER_REGISTRATION"]:
        abort(404)
    if current_user.is_authenticated:
        return redirect(url_for("courses.dashboard"))

    form = {"name": "", "surname": "", "email": ""}
    if request.method == "POST":
        form["name"] = request.form.get("name", "").strip()
        form["surname"] = request.form.get("surname", "").strip()
        form["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if not form["name"] or len(form["name"]) > 100:
            error = "Ad 1-100 karakter arasında olmalıdır."
        elif not form["surname"] or len(form["surname"]) > 100:
            error = "Soyad 1-100 karakter arasında olmalıdır."
        elif not EMAIL_RE.match(form["email"]) or len(form["email"]) > 120:
            error = "Lütfen geçerli bir e-posta adresi girin (örn. hoca@okul.edu.tr)."
        elif len(password) < 8:
            error = "Parola en az 8 karakter olmalıdır."
        elif password != confirm:
            error = "Parolalar eşleşmiyor."
        elif db.session.scalar(db.select(Teacher).filter_by(email=form["email"])):
            error = "Bu e-posta adresiyle zaten bir hesap açılmış."

        if error:
            flash(error, "error")
        else:
            teacher = Teacher(email=form["email"], name=form["name"], surname=form["surname"])
            teacher.set_password(password)
            db.session.add(teacher)
            db.session.commit()
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Oturum kapatıldı.", "info")
    return redirect(url_for("auth.login"))
