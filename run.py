"""Geliştirme sunucusu giriş noktası. Üretimde: gunicorn -w 1 --threads 4 run:app"""
import os
import socket
from pathlib import Path

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    base_dir = Path(__file__).resolve().parent
    cert_file = base_dir / "cert.pem"
    key_file = base_dir / "key.pem"

    use_ssl = os.environ.get("USE_SSL", "1") == "1" and cert_file.exists() and key_file.exists()
    ssl_ctx = (str(cert_file), str(key_file)) if use_ssl else None
    proto = "https" if ssl_ctx else "http"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "127.0.0.1"

    print("\n" + "=" * 60)
    print(f" Sunucu başlatılıyor ({proto.upper()})")
    print(f"  > Bilgisayardan: {proto}://localhost:{port}")
    print(f"  > Telefondan:    {proto}://{local_ip}:{port}")
    if proto == "https":
        print("  * Not: Tarayıcı 'Güvenli Değil / Gelişmiş' uyarısı verirse")
        print("    'Gelişmiş -> Siteye devam et' seçeneğine tıklayın.")
        print("    Bu sertifika kamera erişiminin (WebRTC) çalışması içindir.")
    print("=" * 60 + "\n")

    import threading
    from app.services.face_service import warmup

    # Yüz tanıma modelini arka planda önceden belleğe yükle (warm-up)
    threading.Thread(target=warmup, daemon=True).start()

    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True,
        ssl_context=ssl_ctx,
    )
