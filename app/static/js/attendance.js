/* Yoklama ekranı: kareleri sırayla sunucuya gönderir, tanınanları listede işaretler. */
(function () {
  "use strict";

  const root = document.getElementById("scanner");
  const video = document.getElementById("video");
  const statusEl = document.getElementById("status");
  const startBtn = document.getElementById("start-btn");
  const stopBtn = document.getElementById("stop-btn");
  const flipBtn = document.getElementById("flip-btn");
  const countEl = document.getElementById("present-count");
  const rosterItems = document.querySelectorAll("#roster li");

  const courseId = root.dataset.courseId;
  const url = root.dataset.url;
  const INTERVAL_MS = 800;

  let running = false;
  let timer = null;

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

  function presentCount() {
    return document.querySelectorAll("#roster li.present").length;
  }

  function markInRoster(studentId, time) {
    const item = document.querySelector('#roster li[data-student-id="' + studentId + '"]');
    if (!item || item.classList.contains("present")) return;
    item.classList.add("present", "just-marked");
    item.querySelector(".when").textContent = time || "";
    item.scrollIntoView({ block: "nearest" });
    countEl.textContent = presentCount();
  }

  function handle(result) {
    const { ok, status, data } = result;
    if (status === 401) {
      say("error", "Oturum süresi doldu. Sayfayı yenileyip tekrar giriş yapın.");
      stopScanning(false);
      return;
    }
    if (!data) {
      say("error", "Sunucudan beklenmeyen bir yanıt geldi.");
      return;
    }
    switch (data.status) {
      case "marked":
        markInRoster(data.student.id, data.marked_at);
        say("success", data.student.name + " yoklamaya eklendi.");
        break;
      case "already":
        markInRoster(data.student.id, data.marked_at);
        say("info", data.message);
        break;
      case "no_face":
        say("info", "Yüz aranıyor… Kameraya doğrudan bakın.");
        break;
      case "no_match":
        say("error", "Tanınmadı. Bu derse kayıtlı değilsiniz ya da görüntü net değil.");
        break;
      case "no_enrollment":
        say("error", data.message);
        break;
      default:
        say("error", data.message || "Beklenmeyen bir hata oluştu.");
        if (!ok && status >= 500) stopScanning(false);
    }

    if (presentCount() === rosterItems.length) {
      stopScanning(false);
      say("success", "Tüm öğrenciler yoklamada. Yoklama tamamlandı.");
    }
  }

  async function tick() {
    if (!running) return;
    try {
      const frame = await Cam.capture(video, 480, 0.8);
      const form = new FormData();
      form.append("frame", frame, "frame.jpg");
      form.append("course_id", courseId);
      handle(await Cam.post(url, form));
    } catch (err) {
      say("error", "Sunucuya ulaşılamıyor. Bağlantınızı kontrol edin.");
    } finally {
      // Bir önceki istek bitmeden yenisi gönderilmez; sunucu yavaşlasa bile istekler yığılmaz.
      if (running) timer = setTimeout(tick, INTERVAL_MS);
    }
  }

  async function startScanning() {
    startBtn.disabled = true;
    try {
      await Cam.start(video);
    } catch (err) {
      say("error", err.message);
      startBtn.disabled = false;
      return;
    }
    running = true;
    stopBtn.disabled = false;
    if (flipBtn) flipBtn.style.display = "inline-flex";
    say("info", "Yoklama başladı. Öğrenciler sırayla kameraya baksın.");
    tick();
  }

  function stopScanning(announce = true) {
    running = false;
    clearTimeout(timer);
    Cam.stop(video);
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (flipBtn) flipBtn.style.display = "none";
    if (announce) say("info", "Yoklama durduruldu.");
  }

  startBtn.addEventListener("click", startScanning);
  stopBtn.addEventListener("click", () => stopScanning(true));
  window.addEventListener("pagehide", () => Cam.stop(video));
})();
