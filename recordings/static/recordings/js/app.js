(function () {
  "use strict";

  const SPEAKER_STORAGE_KEY = "collecte_speaker_id";

  let speakerId = "";

  async function ensureSpeakerId() {
    try {
      var stored = localStorage.getItem(SPEAKER_STORAGE_KEY);
      if (stored && /^spk_\d+$/.test(stored)) {
        return stored;
      }
    } catch (e) {
      /* ignore */
    }
    const res = await fetch("/next-speaker-id/", { credentials: "same-origin" });
    if (!res.ok) {
      throw new Error("Impossible d’obtenir un identifiant.");
    }
    const data = await res.json();
    var id = data.speaker_id;
    try {
      localStorage.setItem(SPEAKER_STORAGE_KEY, id);
    } catch (e) {
      /* ignore */
    }
    return id;
  }

  const sentences = JSON.parse(
    document.getElementById("sentences-data").textContent
  );

  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");
  const step3 = document.getElementById("step3");
  const step4 = document.getElementById("step4");
  const step5 = document.getElementById("step5");
  const stepDots = document.getElementById("stepDots");
  const stepLabel = document.getElementById("stepLabel");

  const el = {
    language: document.getElementById("language"),
    age: document.getElementById("age"),
    gender: document.getElementById("gender"),
    textLocal: document.getElementById("textLocal"),
    translation: document.getElementById("translation"),
    progressLine: document.getElementById("progressLine"),
    btnStart: document.getElementById("btnStart"),
    btnStop: document.getElementById("btnStop"),
    btnReplay: document.getElementById("btnReplay"),
    btnRerecord: document.getElementById("btnRerecord"),
    btnUpload: document.getElementById("btnUpload"),
    btnPrev: document.getElementById("btnPrev"),
    btnNext: document.getElementById("btnNext"),
    statusMsg: document.getElementById("statusMsg"),
    audioPlayer: document.getElementById("audioPlayer"),
    csrf: document.querySelector("[name=csrfmiddlewaretoken]"),
    doneMessage: document.getElementById("doneMessage"),
    speakerIdDisplay: document.getElementById("speakerIdDisplay"),
  };

  let sentenceIndex = 0;
  let mediaRecorder = null;
  let recordedChunks = [];
  let audioBlob = null;
  let lastMimeType = "";

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return decodeURIComponent(parts.pop().split(";").shift());
    }
    return null;
  }

  function getCsrfToken() {
    if (el.csrf && el.csrf.value) return el.csrf.value;
    return getCookie("csrftoken");
  }

  function pickMimeType() {
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg;codecs=opus",
    ];
    for (let i = 0; i < candidates.length; i += 1) {
      if (MediaRecorder.isTypeSupported(candidates[i])) {
        return candidates[i];
      }
    }
    return "";
  }

  function extensionForMime(mime) {
    if (!mime) return "webm";
    if (mime.indexOf("webm") !== -1) return "webm";
    if (mime.indexOf("ogg") !== -1) return "ogg";
    if (mime.indexOf("mp4") !== -1) return "m4a";
    if (mime.indexOf("wav") !== -1) return "wav";
    return "webm";
  }

  function currentLang() {
    return el.language.value;
  }

  function listForLang() {
    return sentences[currentLang()] || [];
  }

  function currentSentence() {
    const list = listForLang();
    return list[sentenceIndex] || { text_local: "—", translation: "—" };
  }

  function setStatus(msg, isError) {
    el.statusMsg.textContent = msg || "";
    el.statusMsg.classList.toggle("is-error", Boolean(isError));
  }

  function stopRecordingIfNeeded() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      try {
        mediaRecorder.stop();
      } catch (e) {
        /* ignore */
      }
    }
    el.btnStart.disabled = false;
    el.btnStop.disabled = true;
  }

  function resetRecordingState() {
    stopRecordingIfNeeded();
    mediaRecorder = null;
    recordedChunks = [];
    audioBlob = null;
    lastMimeType = "";
    if (el.audioPlayer.src && el.audioPlayer.src.indexOf("blob:") === 0) {
      URL.revokeObjectURL(el.audioPlayer.src);
    }
    el.audioPlayer.removeAttribute("src");
    el.audioPlayer.hidden = true;
    el.btnReplay.disabled = true;
    el.btnRerecord.disabled = true;
    el.btnUpload.disabled = true;
  }

  function updateSentenceUI() {
    const list = listForLang();
    const total = list.length;
    const s = currentSentence();
    el.textLocal.textContent = s.text_local;
    el.translation.textContent = s.translation;
    el.btnPrev.disabled = sentenceIndex <= 0;
    el.btnNext.disabled = sentenceIndex >= total - 1;
  }

  function updateProgressLine(recordedInDb, totalSentences) {
    const list = listForLang();
    const total = list.length;
    const phraseNum = total ? sentenceIndex + 1 : 0;
    el.progressLine.textContent = "Phrase " + phraseNum + " / " + total;
  }

  async function refreshStats() {
    const lang = currentLang();
    try {
      const res = await fetch(
        "/stats/?language=" + encodeURIComponent(lang)
      );
      if (!res.ok) throw new Error("stats");
      const data = await res.json();
      updateProgressLine(data.recorded_count, data.total_sentences);
    } catch (e) {
      const list = listForLang();
      updateProgressLine("?", list.length);
    }
  }

  function attachBlobToPlayer(blob) {
    if (el.audioPlayer.src && el.audioPlayer.src.indexOf("blob:") === 0) {
      URL.revokeObjectURL(el.audioPlayer.src);
    }
    const url = URL.createObjectURL(blob);
    el.audioPlayer.src = url;
    el.audioPlayer.hidden = false;
    el.btnReplay.disabled = false;
    el.btnRerecord.disabled = false;
    el.btnUpload.disabled = false;
  }

  function updateStepChrome(step) {
    const dots = stepDots.querySelectorAll(".dot");
    if (step <= 4) {
      stepDots.hidden = false;
      stepLabel.hidden = false;
      stepLabel.textContent = "Étape " + step + " sur 4";
      for (let i = 0; i < dots.length; i += 1) {
        dots[i].classList.toggle("is-active", i < step);
      }
    } else {
      stepDots.hidden = true;
      stepLabel.textContent = "Enregistrement envoyé";
      stepLabel.hidden = false;
    }
  }

  function showStep(step) {
    step1.hidden = step !== 1;
    step2.hidden = step !== 2;
    step3.hidden = step !== 3;
    step4.hidden = step !== 4;
    step5.hidden = step !== 5;
    updateStepChrome(step);
  }

  async function startRecording() {
    setStatus("");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Microphone non disponible dans ce navigateur.", true);
      return;
    }
    const mime = pickMimeType();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      recordedChunks = [];
      const options = mime ? { mimeType: mime } : undefined;
      mediaRecorder = new MediaRecorder(stream, options);
      lastMimeType = mediaRecorder.mimeType || mime || "audio/webm";
      mediaRecorder.ondataavailable = function (e) {
        if (e.data && e.data.size > 0) recordedChunks.push(e.data);
      };
      mediaRecorder.onstop = function () {
        stream.getTracks().forEach(function (t) {
          t.stop();
        });
        if (!recordedChunks.length) {
          setStatus("Aucun son capturé. Réessayez.", true);
          resetRecordingState();
          return;
        }
        audioBlob = new Blob(recordedChunks, { type: lastMimeType });
        attachBlobToPlayer(audioBlob);
        setStatus("Enregistrement prêt. Réécoutez ou envoyez.");
      };
      mediaRecorder.start();
      el.btnStart.disabled = true;
      el.btnStop.disabled = false;
      setStatus("Enregistrement… Parlez maintenant.");
    } catch (err) {
      setStatus(
        "Impossible d’accéder au micro. Vérifiez les permissions.",
        true
      );
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    el.btnStart.disabled = false;
    el.btnStop.disabled = true;
  }

  function replay() {
    if (!audioBlob) {
      setStatus("Aucun audio à réécouter.", true);
      return;
    }
    el.audioPlayer.currentTime = 0;
    el.audioPlayer.play().catch(function () {
      setStatus("Lecture audio impossible.", true);
    });
  }

  function rerecord() {
    resetRecordingState();
    setStatus("Vous pouvez enregistrer à nouveau.");
  }

  async function upload() {
    if (!audioBlob) {
      setStatus(
        "Aucun enregistrement. Démarrez puis arrêtez avant d’envoyer.",
        true
      );
      return;
    }
    if (!speakerId) {
      setStatus("Identifiant indisponible. Rechargez la page.", true);
      return;
    }
    const s = currentSentence();
    const lang = currentLang();
    const ext = extensionForMime(audioBlob.type || lastMimeType);
    const form = new FormData();
    form.append("audio", audioBlob, "recording." + ext);
    form.append("text_local", s.text_local);
    form.append("translation", s.translation);
    form.append("language", lang);
    form.append("speaker_id", speakerId);
    form.append("age", String(parseInt(el.age.value, 10) || 30));
    form.append("gender", el.gender.value);

    setStatus("Envoi en cours…");
    el.btnUpload.disabled = true;

    try {
      const res = await fetch("/upload/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken() || "",
        },
        body: form,
        credentials: "same-origin",
      });
      const body = await res.json().catch(function () {
        return {};
      });
      if (!res.ok) {
        const msg =
          (body && (body.detail || body.message)) ||
          JSON.stringify(body) ||
          res.statusText;
        throw new Error(msg);
      }
      resetRecordingState();
      await refreshStats();
      const list = listForLang();
      const hasMore = sentenceIndex < list.length - 1;
      if (hasMore) {
        sentenceIndex += 1;
        updateSentenceUI();
        setStatus("Enregistrement enregistré · phrase suivante.");
        showStep(4);
        window.setTimeout(function () {
          if (el.statusMsg && !el.statusMsg.classList.contains("is-error")) {
            el.statusMsg.textContent = "";
          }
        }, 4500);
      } else {
        el.doneMessage.textContent =
          "Vous avez enregistré toutes les phrases prévues pour cette langue. Merci pour votre contribution.";
        setStatus("");
        showStep(5);
      }
    } catch (e) {
      setStatus("Erreur : " + (e.message || "échec de l’envoi"), true);
      el.btnUpload.disabled = false;
    }
  }

  document.getElementById("btnGoStep2").addEventListener("click", function () {
    showStep(2);
  });

  document.getElementById("btnBackTo1").addEventListener("click", function () {
    showStep(1);
  });

  document.getElementById("btnGoToInstructions").addEventListener(
    "click",
    function () {
      showStep(3);
    }
  );

  document
    .getElementById("btnBackFromInstructions")
    .addEventListener("click", function () {
      showStep(2);
    });

  document.getElementById("btnGoToRecord").addEventListener("click", function () {
    updateSentenceUI();
    refreshStats();
    showStep(4);
  });

  document
    .getElementById("btnBackToInstructions")
    .addEventListener("click", function () {
      resetRecordingState();
      setStatus("");
      showStep(3);
    });

  document
    .getElementById("btnNewSession")
    .addEventListener("click", async function () {
      try {
        localStorage.removeItem(SPEAKER_STORAGE_KEY);
      } catch (e) {
        /* ignore */
      }
      try {
        speakerId = await ensureSpeakerId();
        if (el.speakerIdDisplay) {
          el.speakerIdDisplay.textContent = speakerId;
        }
      } catch (e) {
        if (el.speakerIdDisplay) {
          el.speakerIdDisplay.textContent = "—";
        }
      }
      sentenceIndex = 0;
      resetRecordingState();
      setStatus("");
      updateSentenceUI();
      refreshStats();
      showStep(1);
    });

  el.language.addEventListener("change", function () {
    sentenceIndex = 0;
    resetRecordingState();
    updateSentenceUI();
    refreshStats();
  });

  el.btnPrev.addEventListener("click", function () {
    if (sentenceIndex > 0) {
      sentenceIndex -= 1;
      resetRecordingState();
      setStatus("");
      updateSentenceUI();
      refreshStats();
    }
  });

  el.btnNext.addEventListener("click", function () {
    const list = listForLang();
    if (sentenceIndex < list.length - 1) {
      sentenceIndex += 1;
      resetRecordingState();
      setStatus("");
      updateSentenceUI();
      refreshStats();
    }
  });

  el.btnStart.addEventListener("click", startRecording);
  el.btnStop.addEventListener("click", stopRecording);
  el.btnReplay.addEventListener("click", replay);
  el.btnRerecord.addEventListener("click", rerecord);
  el.btnUpload.addEventListener("click", upload);

  async function init() {
    try {
      speakerId = await ensureSpeakerId();
      if (el.speakerIdDisplay) {
        el.speakerIdDisplay.textContent = speakerId;
      }
    } catch (e) {
      if (el.speakerIdDisplay) {
        el.speakerIdDisplay.textContent = "—";
      }
    }
    updateSentenceUI();
    refreshStats();
    showStep(1);
  }

  init();
})();
