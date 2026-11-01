/* Öğrenci kaydı: form bilgileri ve kamera karesi tek istekte gönderilir. */
(function () {
  "use strict";

  const root = document.getElementById("register");
  const form = document.getElementById("student-form");
  const video = document.getElementById("video");
  const statusEl = document.getElementById("status");
  const cameraBtn = document.getElementById("camera-btn");
  const saveBtn = document.getElementById("save-btn");
  const flipBtn = document.getElementById("flip-btn");

  const say = (kind, text) => Cam.setStatus(statusEl, kind, text);

  if (flipBtn) {
    flipBtn.addEventListener("click", async () => {
      try {
        await Cam.flip(video);
      } catch (err) {
        say("error", err.message);
      }
    });
  }

  cameraBtn.addEventListener("click", async () => {
    if (Cam.isActive()) {
      Cam.stop(video);
      cameraBtn.textContent = "Kamerayı aç";
      if (flipBtn) flipBtn.style.display = "none";
      saveBtn.disabled = true;
      say("info", "Kamera kapatıldı.");
      return;
    }
    try {
      await Cam.start(video);
      cameraBtn.textContent = "Kamerayı kapat";
      if (flipBtn) flipBtn.style.display = "inline-flex";
      saveBtn.disabled = false;
      say("info", "Kamera açık. Yüzünüzü çerçevenin ortasına alın.");
    } catch (err) {
      say("error", err.message);
    }
  });

  saveBtn.addEventListener("click", async () => {
    const values = {
      school_number: form.school_number.value.trim(),
      name: form.name.value.trim(),
      surname: form.surname.value.trim(),
    };
    if (!values.school_number || !values.name || !values.surname) {
      say("error", "Okul numarası, ad ve soyad zorunludur.");
      return;
    }

    saveBtn.disabled = true;
    say("info", "Yüz analiz ediliyor ve kaydediliyor…");

    const frame = await Cam.capture(video, 540, 0.85);

    const body = new FormData();
    Object.entries(values).forEach(([key, value]) => body.append(key, value));
    form.querySelectorAll('input[name="course_ids"]:checked').forEach((box) => body.append("course_ids", box.value));
    body.append("frame", frame, "face.jpg");

    try {
      const { data } = await Cam.post(root.dataset.url, body);
      if (data && data.status === "success") {
        say("success", data.message + " Yeni bir öğrenci kaydedebilirsiniz.");
        form.reset();
        form.school_number.focus();
      } else {
        say("error", (data && data.message) || "Kayıt tamamlanamadı.");
      }
    } catch (err) {
      say("error", "Sunucuya ulaşılamıyor. Bağlantınızı kontrol edin.");
    } finally {
      saveBtn.disabled = !Cam.isActive();
    }
  });

  window.addEventListener("pagehide", () => Cam.stop(video));
})();
