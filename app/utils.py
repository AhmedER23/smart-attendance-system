"""Küçük yardımcı fonksiyonlar."""
from urllib.parse import urljoin, urlparse

from flask import abort, request
from flask_login import current_user

from .extensions import db
from .models import Course


def get_owned_course(course_id: int) -> Course:
    """Dersi getirir; yoksa 404, giriş yapan öğretmene ait değilse 403 döner."""
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    if course.teacher_id != current_user.id:
        abort(403)
    return course


def is_safe_redirect(target: str | None) -> bool:
    """Giriş sonrası yönlendirmede dış sitelere (open redirect) izin vermez."""
    if not target:
        return False
    host = urlparse(request.host_url)
    dest = urlparse(urljoin(request.host_url, target))
    return dest.scheme in {"http", "https"} and host.netloc == dest.netloc
