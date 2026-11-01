"""Yoklama ekranı ve raporlar."""
import csv
import io
from collections import defaultdict
from datetime import date, datetime

from flask import Blueprint, Response, render_template, request
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Attendance
from ..utils import get_owned_course

bp = Blueprint("attendance", __name__)


def _sorted_students(course):
    return sorted(course.students, key=lambda s: (s.name.lower(), s.surname.lower()))


@bp.get("/attendance/<int:course_id>")
@login_required
def take(course_id: int):
    course = get_owned_course(course_id)
    students = _sorted_students(course)
    marked = {
        a.student_id: a.marked_at
        for a in db.session.scalars(db.select(Attendance).filter_by(course_id=course.id, date=date.today()))
    }
    return render_template(
        "attendance/take.html", course=course, students=students, marked=marked, today=date.today()
    )


def _collect(course):
    """Ders için {tarih: {öğrenci_id: kayıt}} sözlüğünü döndürür."""
    by_date = defaultdict(dict)
    for record in db.session.scalars(db.select(Attendance).filter_by(course_id=course.id)):
        by_date[record.date][record.student_id] = record
    return by_date


@bp.get("/reports")
@login_required
def reports():
    courses = current_user.courses
    course_id = request.args.get("course_id", type=int)
    course = next((c for c in courses if c.id == course_id), None)

    context = {"courses": courses, "course": course}
    if course:
        students = _sorted_students(course)
        by_date = _collect(course)
        dates = sorted(by_date, reverse=True)

        selected = None
        raw_date = request.args.get("date", "")
        if raw_date:
            try:
                selected = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                selected = None
        if selected not in by_date:
            selected = dates[0] if dates else None

        day_rows = []
        if selected:
            for s in students:
                rec = by_date[selected].get(s.id)
                day_rows.append({"student": s, "present": rec is not None, "time": rec.marked_at if rec else None})

        summary = []
        for s in students:
            attended = sum(1 for d in dates if s.id in by_date[d])
            rate = round(100 * attended / len(dates)) if dates else 0
            summary.append({"student": s, "attended": attended, "total": len(dates), "rate": rate})

        context.update(
            dates=dates,
            selected=selected,
            day_rows=day_rows,
            present_count=sum(1 for r in day_rows if r["present"]),
            summary=summary,
        )
    return render_template("attendance/reports.html", **context)


def _csv_safe(value: str) -> str:
    """Excel'de formül olarak çalışmasını önlemek için tehlikeli başlangıçları etkisizleştirir."""
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


@bp.get("/reports/export.csv")
@login_required
def export_csv():
    course = get_owned_course(request.args.get("course_id", type=int) or 0)
    by_date = _collect(course)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Tarih", "Okul No", "Ad", "Soyad", "Durum", "Saat"])
    for day in sorted(by_date):
        for s in _sorted_students(course):
            rec = by_date[day].get(s.id)
            writer.writerow(
                [
                    day.strftime("%d.%m.%Y"),
                    _csv_safe(s.school_number),
                    _csv_safe(s.name),
                    _csv_safe(s.surname),
                    "Var" if rec else "Yok",
                    rec.marked_at.strftime("%H:%M") if rec else "",
                ]
            )

    # utf-8-sig: Excel'in Türkçe karakterleri doğru açması için
    body = buffer.getvalue().encode("utf-8-sig")
    filename = f"yoklama_{course.id}_{date.today().isoformat()}.csv"
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
