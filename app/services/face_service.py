"""Yüz tespiti, embedding çıkarma ve karşılaştırma.

Ağır bağımlılıklar (OpenCV, DeepFace/TensorFlow) ilk kullanımda yüklenir; böylece
uygulama hızlı açılır ve testler TensorFlow gerektirmez.
"""
import logging
import threading

import numpy as np

log = logging.getLogger(__name__)

MODEL_NAME = "Facenet"
DETECTOR_BACKEND = "opencv"

# TensorFlow modelleri iş parçacığı güvenli değildir; çıkarım tek seferde yapılır.
_inference_lock = threading.Lock()
_face_cascade = None


def _get_cascade():
    global _face_cascade
    if _face_cascade is None:
        import cv2

        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _face_cascade


class FaceError(Exception):
    """Gönderilen görüntüyle ilgili, kullanıcıya gösterilebilir hata."""


class FaceServiceError(Exception):
    """Yüz tanıma altyapısının çalışmamasından kaynaklanan sistem hatası."""


def _deepface():
    try:
        from deepface import DeepFace
    except Exception as exc:  # pragma: no cover - ortama bağlı
        log.exception("DeepFace yüklenemedi")
        raise FaceServiceError("Yüz tanıma modülü yüklenemedi.") from exc
    return DeepFace


def extract_face(image_bytes: bytes, min_size: int = 60) -> np.ndarray:
    """Görüntüdeki en büyük yüzü kırpıp (BGR) döndürür."""
    crop, _, _ = extract_face_detail(image_bytes, min_size=min_size)
    return crop


def extract_face_detail(
    image_bytes: bytes, min_size: int = 60
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """(yüz kırpması, ölçeklenmiş tam kare, (x, y, w, h)) döndürür.
    
    Önce hızlı ve hafif OpenCV kaskadı ile yüzü milisaniyeler içinde bulur;
    yalnızca bulunamazsa DeepFace yedek analizini çalıştırır.
    """
    import cv2

    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise FaceError("Görüntü okunamadı.")

    h, w = frame.shape[:2]
    cascade = _get_cascade()

    # Hızlı tespit için 400px genişliğe ölçekle
    scale = 1.0
    if max(h, w) > 400:
        scale = 400.0 / max(h, w)
        detect_frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    else:
        detect_frame = frame

    gray = cv2.cvtColor(detect_frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.18,
        minNeighbors=4,
        minSize=(max(int(min_size * scale), 28), max(int(min_size * scale), 28)),
    )

    if len(faces) > 0:
        largest = max(faces, key=lambda f: f[2] * f[3])
        fx, fy, fw, fh = largest
        x = max(0, int(fx / scale))
        y = max(0, int(fy / scale))
        bw = min(w - x, int(fw / scale))
        bh = min(h - y, int(fh / scale))

        pad_x = int(bw * 0.08)
        pad_y = int(bh * 0.08)
        crop_x = max(0, x - pad_x)
        crop_y = max(0, y - pad_y)
        crop_w = min(w - crop_x, bw + 2 * pad_x)
        crop_h = min(h - crop_y, bh + 2 * pad_y)

        crop = frame[crop_y : crop_y + crop_h, crop_x : crop_x + crop_w]
        if crop.size > 0:
            return crop, frame, (x, y, bw, bh)

    # Kaskad bulamazsa DeepFace yedek kontrolü
    DeepFace = _deepface()
    try:
        with _inference_lock:
            faces = DeepFace.extract_faces(
                img_path=frame, detector_backend=DETECTOR_BACKEND, enforce_detection=True
            )
    except Exception as exc:
        raise FaceError("Yüz algılanamadı. Kameraya doğrudan bakın ve ortamı aydınlatın.") from exc

    if not faces:
        raise FaceError("Yüz algılanamadı. Lütfen kameraya doğrudan bakın.")

    area = max((f["facial_area"] for f in faces), key=lambda a: a["w"] * a["h"])
    x, y, bw, bh = max(area["x"], 0), max(area["y"], 0), area["w"], area["h"]
    if min(bw, bh) < min_size:
        raise FaceError("Yüz çok küçük görünüyor. Kameraya biraz yaklaşın.")

    crop = frame[y : y + bh, x : x + bw]
    if crop.size == 0:
        raise FaceError("Yüz bölgesi kırpılamadı.")
    return crop, frame, (x, y, bw, bh)


def compute_embedding(face_crop: np.ndarray) -> np.ndarray:
    """Kırpılmış yüzden embedding vektörü üretir."""
    DeepFace = _deepface()
    try:
        with _inference_lock:
            result = DeepFace.represent(
                img_path=face_crop,
                model_name=MODEL_NAME,
                detector_backend="skip",
                enforce_detection=False,
            )
        return np.asarray(result[0]["embedding"], dtype=np.float32)
    except Exception as exc:
        log.exception("Embedding oluşturulamadı")
        raise FaceServiceError("Yüz özellikleri çıkarılamadı.") from exc


def find_best_match(
    vector: np.ndarray, candidates: list[tuple[int, np.ndarray]], threshold: float
) -> tuple[int | None, float | None]:
    """Adaylar arasında kosinüs mesafesi en küçük olanı bulur.

    Dönüş: (eşleşen_öğrenci_id | None, en_yakın_mesafe | None)
    """
    if not candidates:
        return None, None

    ids = [student_id for student_id, _ in candidates]
    matrix = np.vstack([vec for _, vec in candidates]).astype(np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    unit = vector / np.linalg.norm(vector)

    distances = 1.0 - matrix @ unit
    best = int(np.argmin(distances))
    distance = float(distances[best])
    return (ids[best] if distance <= threshold else None), distance


def is_live(*args, **kwargs) -> tuple[bool, str]:
    """Canlılık kontrolü kaldırıldı; anlık ve kesintisiz akış sağlanır."""
    return True, "Canlı"


def warmup() -> None:
    """Uygulama açılırken kaskad ve modeli arka planda RAM'e yükler; ilk istekteki gecikmeyi önler."""
    try:
        log.info("Yüz tespit ve tanıma modelleri arka planda belleğe yükleniyor (warm-up)...")
        # 1. Hızlı kaskadı belleğe al
        cascade = _get_cascade()
        cascade.detectMultiScale(np.ones((100, 100), dtype=np.uint8), 1.2, 2)

        # 2. Facenet modelini RAM'e yükle
        DeepFace = _deepface()
        with _inference_lock:
            dummy = np.zeros((160, 160, 3), dtype=np.uint8)
            DeepFace.represent(
                img_path=dummy,
                model_name=MODEL_NAME,
                detector_backend="skip",
                enforce_detection=False,
            )
        log.info("Yüz modelleri hazır ve bellekte.")
    except Exception as exc:
        log.warning("Model ön yükleme atlandı: %s", exc)
