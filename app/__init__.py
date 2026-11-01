"""Yüz tanıma ile ders yoklama sistemi - uygulama fabrikası."""
import logging

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["INSTANCE_DIR"].mkdir(parents=True, exist_ok=True)

    if not app.config["SECRET_KEY"]:
        if not (app.testing or app.debug):
            logging.getLogger(__name__).warning(
                "SECRET_KEY tanımlı değil; geçici bir anahtar kullanılıyor. "
                "Oturumlar yeniden başlatmada sıfırlanır. .env dosyasına SECRET_KEY ekleyin."
            )
        import secrets

        app.config["SECRET_KEY"] = secrets.token_hex(32)

    db.init_app(app)
    csrf.init_app(app)
    _setup_login(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_helpers(app)

    from .cli import register_cli

    register_cli(app)

    if app.config["AUTO_CREATE_TABLES"]:
        with app.app_context():
            db.create_all()

    return app


def _setup_login(app: Flask) -> None:
    from .models import Teacher

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(Teacher, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(status="error", message="Oturum süresi doldu. Tekrar giriş yapın."), 401
        flash("Bu sayfa için giriş yapmanız gerekiyor.", "info")
        return redirect(url_for("auth.login", next=request.path))


def _register_blueprints(app: Flask) -> None:
    from .blueprints import api, attendance, auth, courses, students

    for module in (auth, courses, students, attendance, api):
        app.register_blueprint(module.bp)


def _register_error_handlers(app: Flask) -> None:
    messages = {
        400: ("Geçersiz istek", "İstek doğrulanamadı. Sayfayı yenileyip tekrar deneyin."),
        403: ("Erişim yok", "Bu içeriğe erişme yetkiniz bulunmuyor."),
        404: ("Sayfa bulunamadı", "Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir."),
        413: ("Dosya çok büyük", "Gönderilen görüntü izin verilen boyutu aşıyor."),
        500: ("Sunucu hatası", "Beklenmeyen bir sorun oluştu. Biraz sonra tekrar deneyin."),
    }

    def handle(code: int):
        title, text = messages[code]
        if request.path.startswith("/api/"):
            return jsonify(status="error", message=text), code
        return render_template("errors/error.html", code=code, title=title, text=text), code

    for code in messages:
        app.register_error_handler(code, lambda e, c=code: handle(c))
    app.register_error_handler(CSRFError, lambda e: handle(400))


def _register_template_helpers(app: Flask) -> None:
    @app.template_filter("tr_date")
    def tr_date(value):
        return value.strftime("%d.%m.%Y") if value else ""
