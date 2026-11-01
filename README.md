# 🎓 Yüz Tanıma Destekli Akıllı Yoklama Sistemi

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![DeepFace](https://img.shields.io/badge/DeepFace-Facenet-orange.svg)](https://github.com/serengil/deepface)
[![SQLite / MySQL](https://img.shields.io/badge/Database-SQLite%20%7C%20MySQL-informational.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Öğretmenlerin derslerini yönetip, öğrencilerin yüzlerini web kamerası veya telefon kamerası üzerinden **milisaniyeler içinde** tanıyarak anlık yoklama aldığı modern, güvenli ve hafif bir web uygulaması.

---

## 🌟 Öne Çıkan Özellikler

- ⚡ **Yüksek Hızlı Yüz Tanıma & Analiz**:
  - Hızlı yüz algılama: Ölçeklendirilmiş OpenCV Haar Cascade mimarisi (~15ms).
  - Doğru yüz öznitelik çıkarımı: DeepFace Facenet 128/512-boyutlu gömme (embedding) vektörleri.
  - Kosinüs benzerliği optimizasyonu ile adaylar arasında anlık eşleştirme (<300ms).
  - Sunucu açılışında arka plan model ısınması (warm-up) sayesinde ilk istek gecikmelerinin önlenmesi.
- 📱 **Çoklu Cihaz & Mobil Kamera Desteği (HTTPS / WebRTC)**:
  - Bilgisayar kamerasının yanı sıra, yerel ağdaki akıllı telefonlardan (`https://<yerel-ip>:5000`) bağlanarak telefonun ön/arka kamerasıyla yoklama alma desteği.
- 👥 **Mükerrer Yüz Koruması**:
  - Sistemde zaten kayıtlı olan bir yüzle farklı bir öğrenci numarası adına mükerrer hesap açılmasını engeller.
- 📚 **Gelişmiş Ders & Toplu Öğrenci Yönetimi**:
  - Tek tıkla tüm öğrencileri derse ekleme ("Hepsini Ekle").
  - Çoklu seçim kutuları ("Tümünü Seç / Kaldır") ve anlık filtreleme / arama çubuğu.
  - Derse sonradan katılan öğrenciler için doğrudan ilgili ders seçili öğrenci kayıt akışı.
- 📊 **Detaylı Devam Raporları & Excel / CSV Dışa Aktarımı**:
  - Günlük katılım tablosu (Var / Yok / Katılım Saati).
  - Dönemlik devam yüzdesi hesaplama çubukları.
  - Türkçe karakter uyumlu (UTF-8 with BOM) CSV indirme özelliği.
- 🛡️ **Kurumsal Güvenlik & Mimari**:
  - PBKDF2/SHA256 ile parola hash'leme.
  - CSRF koruması, güvenli yönlendirme (Open Redirect koruması), SQL Injection korumalı SQLAlchemy ORM.
  - Temiz ve harici ağır CDN bağımlılığı olmayan modern, duyarlı (responsive) CSS arayüzü.

---

## 🛠️ Teknolojiler ve Kütüphaneler

| Kategori | Teknoloji | Açıklama |
|---|---|---|
| **Backend** | Python 3.10+, Flask 3.1, Werkzeug | Web çekirdeği ve güvenli API servisleri |
| **Veritabanı** | SQLAlchemy 2.0, Flask-SQLAlchemy | SQLite (sıfır kurulum) veya MySQL desteği |
| **Yapay Zekâ & Görüntü İşleme** | OpenCV 4.x, DeepFace, TensorFlow, Keras | Yüz algılama, hizalama ve Facenet vektör çıkarımı |
| **Kimlik & Güvenlik** | Flask-Login, Flask-WTF (CSRF) | Oturum yönetimi ve form koruması |
| **Frontend** | Modern Semantik HTML5, CSS3, ES6 JavaScript | Framework bağımsız, ultra hızlı ve duyarlı kullanıcı arayüzü |

---

## 📁 Proje Dizin Yapısı

```
yuz-tanima-destekli-akilli-yoklama-sistemi/
├── app/
│   ├── __init__.py          # Uygulama fabrikası (create_app) & hata yakalayıcılar
│   ├── config.py            # Ortam değişkenleri ve yapılandırma sınıfları
│   ├── extensions.py        # SQLAlchemy db, LoginManager, CSRFProtect
│   ├── models.py            # Teacher, Student, Course, FaceEmbedding, Attendance
│   ├── cli.py               # CLI komutları (init-db, create-teacher)
│   ├── utils.py             # Yetkilendirme ve güvenli URL yardımcıları
│   ├── blueprints/
│   │   ├── auth.py          # Öğretmen giriş, çıkış ve kayıt işlemleri
│   │   ├── courses.py       # Ders CRUD, toplu ve tekli öğrenci kaydı
│   │   ├── students.py      # Öğrenci listeleme, arama ve silme
│   │   ├── attendance.py    # Canlı yoklama ekranı, günlük raporlar ve CSV export
│   │   └── api.py           # Kamera karesi tabanlı JSON API (/api/students, /api/recognize)
│   ├── services/
│   │   └── face_service.py  # OpenCV kaskadı + Facenet embedding ve kosinüs eşleştirme
│   ├── templates/           # Jinja2 şablonları (courses, students, attendance, auth)
│   └── static/              # CSS ve JavaScript (camera.js, register.js, attendance.js)
├── tests/                   # Pytest test paketi ve test fikstürleri
├── run.py                   # HTTPS & WebRTC destekli başlatıcı
├── requirements.txt         # Temel bağımlılıklar
├── requirements-dev.txt     # Test ve geliştirme araçları
└── .env.example             # Örnek yapılandırma şablonu
```

---

## 🚀 Hızlı Başlangıç & Kurulum

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/<kullanici-adiniz>/yuz-tanima-destekli-akilli-yoklama-sistemi.git
cd yuz-tanima-destekli-akilli-yoklama-sistemi
```

### 2. Sanal Ortamı Oluşturun ve Aktif Edin
```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Yapılandırma Dosyasını Hazırlayın
`.env.example` dosyasını `.env` olarak kopyalayın:
```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

`.env` dosyanızda güçlü bir `SECRET_KEY` belirleyin:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Sunucuyu Başlatın
```bash
python run.py
```

Başlatıldığında terminalde aşağıdaki bağlantılar görüntülenir:
- **Bilgisayardan erişim:** `https://localhost:5000`
- **Telefondan erişim:** `https://192.168.1.xxx:5000`

> 💡 **Kamera (WebRTC) Notu:** Tarayıcılar güvenlik standardı gereği kamera erişimine yalnızca `localhost` veya `HTTPS` üzerinden izin verir. `run.py` yerel sertifika (`cert.pem` / `key.pem`) ile çalışır. Telefonunuzdan açarken tarayıcının sunduğu *"Gelişmiş -> Siteye devam et"* seçeneğine tıklayarak kamera iznini onaylayabilirsiniz.

---

## ⚙️ Yapılandırma Seçenekleri (`.env`)

| Değişken | Açıklama | Önerilen / Varsayılan |
|---|---|---|
| `SECRET_KEY` | Flask oturum imzalama anahtarı | Güçlü rastgele 64 hex karakter |
| `DATABASE_URL` | Veritabanı bağlantı URI'si | Boşsa `instance/yoklama.db` (SQLite) |
| `FACE_MATCH_THRESHOLD` | Facenet kosinüs benzerlik eşiği | `0.40` (Düşük = daha katı) |
| `ALLOW_TEACHER_REGISTRATION` | Açık öğretmen kayıt sayfasını aktif/pasif yapar | `true` |
| `HOST` | Sunucu dinleme adresi | `0.0.0.0` |
| `PORT` | Sunucu portu | `5000` |
| `USE_SSL` | Yerel HTTPS sertifikasını etkinleştirir | `1` |

> **MySQL Kullanımı:** MySQL kullanmak isterseniz `.env` dosyasına şu satırı eklemeniz yeterlidir:
> `DATABASE_URL=mysql+pymysql://kullanici:parola@localhost:3306/yoklama_db?charset=utf8mb4`

---

## 🧪 Testlerin Çalıştırılması

Geliştirme bağımlılıklarını kurup test paketini çalıştırabilirsiniz:

```bash
pip install -r requirements-dev.txt
pytest
```

> Testler, gerçek donanım veya TensorFlow gerektirmeyen izole fikstürler (`fake_face`) ile çalışır; böylece CI/CD ortamlarında saniyeler içinde tamamlanır.

---

## 🔒 Gizlilik & Biyometrik Veri Uyarısı (KVKK / GDPR)

Yüz verileri, kişisel veri koruma mevzuatları (KVKK / GDPR) kapsamında **özel nitelikli biyometrik veri** statüsündedir.
- Sistem orijinal yüz fotoğraflarını diskte saklamaz; yalnızca matematiksel vektörleri (embedding) şifreli biçimde depolar.
- Öğrenci kaydı silindiğinde ilişkili tüm yüz embedding vektörleri ve verileri anında kalıcı olarak silinir (cascade delete).

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
