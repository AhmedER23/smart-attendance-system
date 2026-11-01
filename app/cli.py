"""Yönetim komutları: `flask --app run <komut>`."""
import click

from .extensions import db
from .models import Teacher


def register_cli(app) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Eksik tabloları oluşturur."""
        db.create_all()
        click.echo("Veritabanı tabloları hazır.")

    @app.cli.command("create-teacher")
    @click.option("--email", prompt="E-posta", help="Öğretmen e-posta adresi")
    @click.option("--name", prompt="Ad", help="Öğretmen adı")
    @click.option("--surname", prompt="Soyad", help="Öğretmen soyadı")
    @click.password_option(prompt="Parola")
    def create_teacher(email: str, name: str, surname: str, password: str):
        """Yeni öğretmen hesabı oluşturur."""
        email = email.strip().lower()
        if db.session.scalar(db.select(Teacher).filter_by(email=email)):
            raise click.ClickException(f"'{email}' e-posta adresi zaten alınmış.")
        teacher = Teacher(email=email, name=name.strip(), surname=surname.strip())
        teacher.set_password(password)
        db.session.add(teacher)
        db.session.commit()
        click.echo(f"Öğretmen oluşturuldu: {teacher.full_name} ({email})")
