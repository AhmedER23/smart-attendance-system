/* Ortak kamera ve ağ yardımcıları. window.Cam olarak dışa açılır. */
(function () {
  "use strict";

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let stream = null;
  let currentFacingMode = "user";

  function describeCameraError(err) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return "Bu tarayıcıda kamera kullanılamıyor. Sayfayı HTTPS veya localhost üzerinden açın.";
    }
    switch (err && err.name) {
      case "NotAllowedError":
        return "Kamera izni verilmedi. Tarayıcı adres çubuğundan izin verip tekrar deneyin.";
      case "NotFoundError":
        return "Bağlı bir kamera bulunamadı.";
      case "NotReadableError":
        return "Kamera başka bir uygulama tarafından kullanılıyor.";
      default:
        return "Kamera açılamadı.";
    }
  }

  async function start(video, facingMode) {
    if (facingMode) currentFacingMode = facingMode;
    stop(video);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error(describeCameraError());
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: currentFacingMode },
        audio: false,
      });
    } catch (_) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: currentFacingMode },
          audio: false,
        });
      } catch (err) {
        throw new Error(describeCameraError(err));
      }
    }
    video.srcObject = stream;
    await video.play().catch(() => {});
    video.closest(".viewport")?.classList.add("live");
  }

  function flip(video) {
    currentFacingMode = currentFacingMode === "user" ? "environment" : "user";
    return start(video, currentFacingMode);
  }

  function stop(video) {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }
    if (video) {
      video.srcObject = null;
      video.closest(".viewport")?.classList.remove("live");
    }
  }

  function isActive() {
    return stream !== null;
  }

  /** Videonun anlık görüntüsünü, genişliği `width` olacak şekilde JPEG Blob olarak döndürür. */
  function capture(video, width = 640, quality = 0.85) {
    const ratio = video.videoHeight && video.videoWidth ? video.videoHeight / video.videoWidth : 0.75;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = Math.round(width * ratio);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
  }

  /** CSRF başlığı ekleyerek POST gönderir; { ok, status, data } döndürür. */
  async function post(url, formData) {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      headers: { "X-CSRFToken": csrfToken },
      credentials: "same-origin",
    });
    let data = null;
    try {
      data = await response.json();
    } catch (_) {
      /* JSON olmayan yanıt */
    }
    return { ok: response.ok, status: response.status, data };
  }

  /** Durum çubuğunu günceller. kind: success | error | info */
  function setStatus(el, kind, text) {
    el.className = "statusbar is-" + kind;
    el.textContent = text;
  }

  window.Cam = { start, stop, flip, isActive, capture, post, setStatus };
})();
