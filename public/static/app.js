(() => {
"use strict";

const state = {
  lastPlan: null,
  selectedUnitIndex: 0,
  viewMode: "user",
  inputLanguage: "ru",
  submittedFeedbackType: null,
  playbackSpeed: 0.75,
  playbackTimer: null,
  playbackDurationMs: 6000,
  playbackProgressMs: 0,
  playbackStartedAt: 0,
  uploadDirty: false,
  lastRenderPlan: null,
  lastAIBrief: null,
  aiBriefMode: "universal_prompt",
  aiBriefRequestId: 0,
  generationRequestId: 0,
  videoPreviewReady: false,
  previewVideoRequestId: 0,
  renderPlanRequestId: 0,
  healthFailures: 0,
  healthRetryTimer: null,
  route: "app",
  reviewToken: "",
  reviewJobs: [],
  reviewFeedback: [],
  reviewSessions: [],
  reviewAuditEvents: [],
  selectedReviewJobId: "",
  reviewFilter: "",
};

const defaultUploadCopy = {
  title: "Перетащите аудио сюда",
  status: "WAV, MP3, M4A до 50 MB",
};

const sampleSources = [
  { name: "Slovo", task: "rsl_dataset_models", languages: ["ru", "rsl"], status: "needs_license_check" },
  { name: "Easy Sign", task: "rsl_isolated_recognition", languages: ["ru", "rsl"], status: "verified" },
  { name: "KRSL20", task: "krsl_dataset_nonmanual", languages: ["krsl"], status: "needs_license_check" },
];

const steps = [
  { title: "Текст", description: "Берем введенную фразу или расшифровку аудио." },
  { title: "Язык", description: "Проверяем выбранный язык и готовим текст к разбору." },
  { title: "Жесты", description: "Подбираем известные жесты и отмечаем спорные места." },
  { title: "Показ", description: "Собираем прозрачный черновик для проверки человеком." },
];

const inputText = document.querySelector("#inputText");
const inputHint = document.querySelector("#inputHint");
const charCount = document.querySelector("#charCount");
const generateButton = document.querySelector("#generateButton");
const clearButton = document.querySelector("#clearButton");
const uploadBox = document.querySelector("#uploadBox");
const audioInput = document.querySelector("#audioInput");
const uploadTitle = document.querySelector("#uploadTitle");
const uploadStatus = document.querySelector("#uploadStatus");
const timeline = document.querySelector("#timeline");
const stepper = document.querySelector("#stepper");
const confidenceBar = document.querySelector("#confidenceBar");
const confidenceValue = document.querySelector("#confidenceValue");
const warningText = document.querySelector("#warningText");
const warningCount = document.querySelector("#warningCount");
const feedbackStatus = document.querySelector("#feedbackStatus");
const feedbackButtons = Array.from(document.querySelectorAll("[data-feedback]"));
const renderPlanSummary = document.querySelector("#renderPlanSummary");
const renderPlanList = document.querySelector("#renderPlanList");
const aiBriefSummary = document.querySelector("#aiBriefSummary");
const aiBriefOutput = document.querySelector("#aiBriefOutput");
const copyAIBriefButton = document.querySelector("#copyAIBriefButton");
const aiBriefModeButtons = Array.from(document.querySelectorAll("[data-brief-mode]"));
const riskCard = document.querySelector("#riskCard");
const riskText = document.querySelector("#riskText");
const subtitleBox = document.querySelector("#subtitleBox");
const trustTitle = document.querySelector("#trustTitle");
const trustText = document.querySelector("#trustText");
const resultTranscript = document.querySelector("#resultTranscript");
const transcriptMeta = document.querySelector("#transcriptMeta");
const applyTranscriptButton = document.querySelector("#applyTranscriptButton");
const resultPanel = document.querySelector(".result-panel");
const fallbackSummary = document.querySelector("#fallbackSummary");
const jobMeta = document.querySelector("#jobMeta");
const coverageStrip = document.querySelector("#coverageStrip");
const traceGate = document.querySelector("#traceGate");
const traceSummary = document.querySelector("#traceSummary");
const traceList = document.querySelector("#traceList");
const unitInspector = document.querySelector("#unitInspector");
const sourceRows = document.querySelector("#sourceRows");
const serviceStatus = document.querySelector("#serviceStatus");
const readyStatus = document.querySelector("#readyStatus");
const apiBadge = document.querySelector("#apiBadge");
const footerStamp = document.querySelector("#footerStamp");
const serviceStatusLabel = document.querySelector("#serviceStatusLabel");
const settingsButton = document.querySelector("#settingsButton");
const reviewButton = document.querySelector("#reviewButton");
const fullscreenButton = document.querySelector("#fullscreenButton");
const fullscreenButtonLabel = document.querySelector("#fullscreenButtonLabel");
const videoFrame = document.querySelector("#videoFrame");
const previewVideo = document.querySelector("#previewVideo");
const videoState = document.querySelector("#videoState");
const playButton = document.querySelector("#playButton");
const videoTime = document.querySelector("#videoTime");
const soundButton = document.querySelector("#soundButton");
const subtitleToggle = document.querySelector("#subtitleToggle");
const planViewButton = document.querySelector("#planViewButton");
const scrubberFill = document.querySelector(".scrubber span");
const speedButtons = Array.from(document.querySelectorAll(".speed-button"));
const appView = document.querySelector("#appView");
const reviewView = document.querySelector("#reviewView");
const reviewBackButton = document.querySelector("#reviewBackButton");
const reviewTokenInput = document.querySelector("#reviewTokenInput");
const reviewStatusFilter = document.querySelector("#reviewStatusFilter");
const reviewLoadButton = document.querySelector("#reviewLoadButton");
const reviewStatusBanner = document.querySelector("#reviewStatusBanner");
const reviewSummary = document.querySelector("#reviewSummary");
const reviewJobs = document.querySelector("#reviewJobs");
const reviewQueueStatus = document.querySelector("#reviewQueueStatus");
const reviewDetailSummary = document.querySelector("#reviewDetailSummary");
const reviewUnitList = document.querySelector("#reviewUnitList");
const reviewUnitsMeta = document.querySelector("#reviewUnitsMeta");
const reviewSessionList = document.querySelector("#reviewSessionList");
const reviewSessionsMeta = document.querySelector("#reviewSessionsMeta");
const reviewFeedbackList = document.querySelector("#reviewFeedbackList");
const reviewFeedbackMeta = document.querySelector("#reviewFeedbackMeta");
const reviewAuditList = document.querySelector("#reviewAuditList");
const reviewAuditMeta = document.querySelector("#reviewAuditMeta");
const reviewStatusActionButtons = Array.from(document.querySelectorAll("[data-review-status-action]"));
const reviewSessionForm = document.querySelector("#reviewSessionForm");
const reviewerRoleInput = document.querySelector("#reviewerRoleInput");
const reviewerLanguageInput = document.querySelector("#reviewerLanguageInput");
const reviewSessionStatusInput = document.querySelector("#reviewSessionStatusInput");
const reviewMeaningScoreInput = document.querySelector("#reviewMeaningScoreInput");
const reviewUnderstandabilityScoreInput = document.querySelector("#reviewUnderstandabilityScoreInput");
const reviewBlockingIssueInput = document.querySelector("#reviewBlockingIssueInput");
const reviewSessionNotesInput = document.querySelector("#reviewSessionNotesInput");
const reviewSessionStatus = document.querySelector("#reviewSessionStatus");
const reviewSessionSubmitButton = document.querySelector("#reviewSessionSubmitButton");
const reviewUploadForm = document.querySelector("#reviewUploadForm");
const reviewRenderedVideoInput = document.querySelector("#reviewRenderedVideoInput");
const reviewUploadStatus = document.querySelector("#reviewUploadStatus");
const reviewUploadSubmitButton = document.querySelector("#reviewUploadSubmitButton");
const reviewPublishForm = document.querySelector("#reviewPublishForm");
const reviewPublishStatusInput = document.querySelector("#reviewPublishStatusInput");
const reviewPublishNoteInput = document.querySelector("#reviewPublishNoteInput");
const reviewPublishStatus = document.querySelector("#reviewPublishStatus");
const reviewPublishSubmitButton = document.querySelector("#reviewPublishSubmitButton");

const warningLabels = {
  prototype_sign_plan_not_professional_interpretation: "Черновик не заменяет профессиональный перевод.",
  native_signer_validation_required: "Нужна проверка носителем жестового языка.",
  high_risk_domain_requires_human_interpreter: "Высокорисковый сценарий: нужен человек-переводчик.",
  api_unavailable: "Сервис временно недоступен.",
};

const riskLabels = {
  emergency: "экстренная помощь",
  medical: "медицина",
  legal: "юридические вопросы",
  finance: "финансы",
};

const reviewStatusOptions = [
  { value: "pending_signer_review", label: "Ожидает проверки", tone: "warn" },
  { value: "needs_edit", label: "Нужна правка", tone: "bad" },
  { value: "approved", label: "Одобрено", tone: "ok" },
  { value: "rejected", label: "Отклонено", tone: "bad" },
];

const supportedAudioTypes = new Set([
  "audio/aac",
  "audio/mp4",
  "audio/mpeg",
  "audio/mp3",
  "audio/wav",
  "audio/webm",
  "audio/x-m4a",
  "audio/x-wav",
]);
const maxAudioBytes = 50 * 1024 * 1024;

function setService(status, label) {
  serviceStatus.classList.remove("ok", "bad", "pending");
  if (status) serviceStatus.classList.add(status);
  serviceStatusLabel.textContent = label;
  apiBadge.textContent = `Сервис: ${label}`;
}

function loadReviewToken() {
  try {
    const saved = window.localStorage.getItem("qsignReviewToken");
    state.reviewToken = String(saved || "");
  } catch {
    state.reviewToken = "";
  }
  reviewTokenInput.value = state.reviewToken;
}

function saveReviewToken(value) {
  state.reviewToken = String(value || "").trim();
  try {
    if (state.reviewToken) {
      window.localStorage.setItem("qsignReviewToken", state.reviewToken);
    } else {
      window.localStorage.removeItem("qsignReviewToken");
    }
  } catch {}
}

function reviewHeaders() {
  if (!state.reviewToken) return {};
  return { "x-qsign-review-token": state.reviewToken };
}

function setRoute(route) {
  state.route = route === "review" ? "review" : "app";
  const reviewMode = state.route === "review";
  appView.hidden = reviewMode;
  reviewView.hidden = !reviewMode;
  reviewButton.classList.toggle("active-route", reviewMode);
  if (reviewMode) {
    window.location.hash = "#/review";
    if (!state.reviewJobs.length) {
      loadReviewDashboard();
    }
  } else if (window.location.hash === "#/review") {
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
  }
}

function syncRouteFromLocation() {
  setRoute(window.location.hash.startsWith("#/review") ? "review" : "app");
}

function scheduleHealthRetry() {
  if (state.healthRetryTimer) return;
  state.healthRetryTimer = window.setTimeout(() => {
    state.healthRetryTimer = null;
    loadHealthAndSources();
  }, 2500);
}

function updateCharCount() {
  charCount.textContent = `${inputText.value.length} / 5000`;
}

function syncClearButton() {
  const hasInputText = String(inputText.value || "").trim().length > 0;
  const hasTranscriptText = String(resultTranscript.value || "").trim().length > 0;
  clearButton.disabled = !hasInputText && !hasTranscriptText && !state.lastPlan && !state.uploadDirty;
}

function setInputLanguage(language) {
  const normalized = String(language || "ru").toLowerCase();
  state.inputLanguage = normalized === "kk" || normalized === "en" ? normalized : "ru";
  const isKazakh = state.inputLanguage === "kk";
  const isEnglish = state.inputLanguage === "en";
  inputText.lang = state.inputLanguage;
  resultTranscript.lang = state.inputLanguage;
  inputText.placeholder = isKazakh
    ? "Қысқа қазақша мәтінді енгізіңіз"
    : isEnglish
      ? "Enter short English phrase"
      : "Введите короткий русский текст";
}

function setUploadState(nextState, title, status) {
  uploadBox.classList.remove("error", "success", "loading");
  if (nextState) uploadBox.classList.add(nextState);
  uploadTitle.textContent = title;
  uploadStatus.textContent = status;
  state.uploadDirty = Boolean(nextState);
  syncClearButton();
}

function resetUploadState() {
  setUploadState("", defaultUploadCopy.title, defaultUploadCopy.status);
}

function renderMetricGrid(parent, items, className = "") {
  clearNode(parent);
  items.forEach(([value, label]) => {
    const item = document.createElement("div");
    if (className) item.className = className;
    appendTextElement(item, "strong", "", String(value));
    appendTextElement(item, "span", "", label);
    parent.append(item);
  });
}

function clearNode(node) {
  node.replaceChildren();
}

function appendTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderRenderPlanSummary(summary, items) {
  renderPlanSummary.textContent = summary;
  clearNode(renderPlanList);
  items.forEach((item) => {
    appendTextElement(renderPlanList, "span", "", item);
  });
}

function resetRenderPlanSummary() {
  state.lastRenderPlan = null;
  renderRenderPlanSummary(
    "Видео еще не готовится. После сохранения записи здесь появится готовность к сборке.",
    ["готовность: ожидание", "есть фрагментов: 0", "нужно добавить: 0", "выпуск: нет"]
  );
}

function renderAIBriefSummary(summary, text, enabled) {
  aiBriefSummary.textContent = summary;
  aiBriefOutput.value = text;
  aiBriefOutput.textContent = text;
  aiBriefOutput.scrollTop = 0;
  aiBriefOutput.scrollLeft = 0;
  copyAIBriefButton.disabled = !enabled;
}

function syncAIBriefModeButtons() {
  aiBriefModeButtons.forEach((button) => {
    const active = button.dataset.briefMode === state.aiBriefMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function renderAIBriefData() {
  const data = state.lastAIBrief;
  if (!data) {
    resetAIBrief();
    return;
  }
  const exports = data.exports || {};
  const selected = exports[state.aiBriefMode];
  const fallback = exports.universal_prompt;
  const activeExport = selected || fallback;
  if (!activeExport) {
    renderAIBriefSummary(
      "Пакет для AI-видео пока не получен.",
      "Не удалось собрать экспортный пакет. Попробуйте позже.",
      false
    );
    return;
  }
  renderAIBriefSummary(
    `Готов формат: ${activeExport.label || "brief"} · запись ${(data.job_id || "").slice(0, 8) || "—"}.`,
    String(activeExport.text || ""),
    true
  );
  syncAIBriefModeButtons();
}

function resetAIBrief() {
  state.lastAIBrief = null;
  renderAIBriefSummary(
    "Пакет для AI-видео появится после сохранения черновика.",
    "Пока пусто.",
    false
  );
  syncAIBriefModeButtons();
}

function appendSvg(parent, className) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  if (className) svg.setAttribute("class", className);
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "m8 5 11 7-11 7V5Z");
  svg.append(path);
  parent.append(svg);
  return svg;
}

function setGenerateButtonIdle() {
  clearNode(generateButton);
  generateButton.append(document.createTextNode("Собрать перевод"));
  appendSvg(generateButton);
}

function renderFooterStamp() {
  if (!footerStamp) return;
  const formatter = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  footerStamp.textContent = formatter.format(new Date());
}

function formatTime(totalSeconds) {
  const safeValue = Math.max(0, Math.round(totalSeconds));
  const minutes = String(Math.floor(safeValue / 60)).padStart(2, "0");
  const seconds = String(safeValue % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function getPreviewDurationMs(plan = state.lastPlan) {
  if (previewVideo && Number.isFinite(previewVideo.duration) && previewVideo.duration > 0) {
    return previewVideo.duration * 1000;
  }
  const units = plan?.units || [];
  if (!units.length) return 0;
  return Math.max(3000, units.length * 1400);
}

function setPlaybackControlsEnabled(enabled) {
  const isEnabled = Boolean(enabled);
  playButton.disabled = !isEnabled;
  fullscreenButton.disabled = !isEnabled;
  speedButtons.forEach((button) => {
    button.disabled = !isEnabled;
  });
}

function setVideoPreviewState(ready, label) {
  state.videoPreviewReady = Boolean(ready);
  videoFrame.classList.toggle("ready", state.videoPreviewReady);
  videoFrame.classList.toggle("no-video", !state.videoPreviewReady);
  videoState.textContent = label;
  setPlaybackControlsEnabled(state.videoPreviewReady);
  if (!state.videoPreviewReady) stopPlayback(true);
}

function syncFeedbackButtons() {
  feedbackButtons.forEach((button) => {
    const active = button.dataset.feedback === state.submittedFeedbackType;
    button.classList.toggle("selected", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function refreshPlaybackUi() {
  const totalMs = state.videoPreviewReady ? (state.playbackDurationMs || getPreviewDurationMs()) : 0;
  const progressMs = Math.max(0, Math.min(totalMs, state.playbackProgressMs));
  const ratio = totalMs > 0 ? progressMs / totalMs : 0;
  scrubberFill.style.width = `${ratio * 100}%`;
  videoTime.textContent = `${formatTime(progressMs / 1000)} / ${formatTime(totalMs / 1000)}`;
}

function stopPlayback(resetProgress = false) {
  if (previewVideo && !previewVideo.paused) {
    previewVideo.pause();
  }
  state.playbackTimer = null;
  if (resetProgress && previewVideo) {
    previewVideo.currentTime = 0;
  }
  state.playbackProgressMs = previewVideo ? previewVideo.currentTime * 1000 : 0;
  videoFrame.classList.remove("playing");
  playButton.setAttribute("aria-pressed", "false");
  playButton.setAttribute("aria-label", "Воспроизвести");
  refreshPlaybackUi();
}

function setPlaybackSpeed(speed) {
  const nextSpeed = Number(speed);
  if (!Number.isFinite(nextSpeed) || nextSpeed <= 0) return;
  state.playbackSpeed = nextSpeed;
  speedButtons.forEach((button) => {
    const active = Number(button.dataset.speed) === nextSpeed;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  if (previewVideo) previewVideo.playbackRate = nextSpeed;
  state.playbackDurationMs = getPreviewDurationMs();
  refreshPlaybackUi();
}

function startPlayback() {
  if (!state.videoPreviewReady || !previewVideo?.src) return;
  previewVideo.playbackRate = state.playbackSpeed;
  const playPromise = previewVideo.play();
  if (playPromise && typeof playPromise.catch === "function") {
    playPromise.catch(() => {
      stopPlayback(false);
    });
  }
}

function resetPlayback() {
  state.playbackDurationMs = getPreviewDurationMs();
  state.playbackProgressMs = 0;
  stopPlayback(true);
}

function clearPreviewVideo() {
  if (previewVideo) {
    previewVideo.pause();
    previewVideo.removeAttribute("src");
    previewVideo.load();
    previewVideo.hidden = true;
  }
  videoFrame.classList.remove("has-video");
  state.playbackProgressMs = 0;
  state.playbackDurationMs = 0;
  refreshPlaybackUi();
}

function applyLoadedVideoState(label) {
  if (!previewVideo) return;
  previewVideo.hidden = false;
  previewVideo.muted = true;
  previewVideo.loop = true;
  previewVideo.playbackRate = state.playbackSpeed;
  videoFrame.classList.add("has-video");
  state.playbackDurationMs = getPreviewDurationMs();
  state.playbackProgressMs = previewVideo.currentTime * 1000;
  setVideoPreviewState(true, label);
  refreshPlaybackUi();
  const playPromise = previewVideo.play();
  if (playPromise && typeof playPromise.catch === "function") {
    playPromise.catch(() => {});
  }
}

async function loadReviewVideo(jobId, generationRequestId = 0) {
  const requestId = ++state.previewVideoRequestId;
  clearPreviewVideo();
  if (!jobId) {
    setVideoPreviewState(false, "Без сохраненной записи обзорное видео не собирается.");
    return;
  }
  if (generationRequestId && generationRequestId !== state.generationRequestId) {
    return;
  }
  setVideoPreviewState(false, "Собираем обзорное видео черновика.");
  const url = `/v1/jobs/${jobId}/review-video?ts=${Date.now()}`;
  const previewAvailability = await preflightReviewVideo(url, requestId, generationRequestId);
  if (requestId !== state.previewVideoRequestId) {
    return;
  }
  if (generationRequestId && generationRequestId !== state.generationRequestId) {
    return;
  }
  if (!previewAvailability.ok) {
    clearPreviewVideo();
    setVideoPreviewState(false, previewAvailability.message);
    return;
  }
  await new Promise((resolve) => {
    let timeoutId = 0;
    const handleReady = () => {
      cleanup();
      if (requestId !== state.previewVideoRequestId) {
        resolve();
        return;
      }
      if (generationRequestId && generationRequestId !== state.generationRequestId) {
        resolve();
        return;
      }
      applyLoadedVideoState("Доступно обзорное видео черновика.");
      resolve();
    };
    const handleError = () => {
      cleanup();
      if (requestId !== state.previewVideoRequestId) {
        resolve();
        return;
      }
      if (generationRequestId && generationRequestId !== state.generationRequestId) {
        resolve();
        return;
      }
      clearPreviewVideo();
      setVideoPreviewState(false, "Обзорное видео пока не собрано.");
      resolve();
    };
    const cleanup = () => {
      window.clearTimeout(timeoutId);
      previewVideo.removeEventListener("loadedmetadata", handleReady);
      previewVideo.removeEventListener("error", handleError);
    };
    previewVideo.addEventListener("loadedmetadata", handleReady, { once: true });
    previewVideo.addEventListener("error", handleError, { once: true });
    timeoutId = window.setTimeout(handleError, 3500);
    previewVideo.src = url;
    previewVideo.load();
  });
}

async function preflightReviewVideo(url, requestId, generationRequestId) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 2500);
  try {
    const response = await fetch(url, {
      method: "HEAD",
      cache: "no-store",
      signal: controller.signal,
    });
    if (requestId !== state.previewVideoRequestId) {
      return { ok: false, message: "Обзорное видео пока не собрано." };
    }
    if (generationRequestId && generationRequestId !== state.generationRequestId) {
      return { ok: false, message: "Обзорное видео пока не собрано." };
    }
    if (response.ok) {
      return { ok: true, message: "" };
    }
    if (response.status === 404 || response.status === 503) {
      return { ok: false, message: "Обзорное видео пока не собрано." };
    }
    return { ok: false, message: "Не удалось загрузить обзорное видео." };
  } catch {
    return { ok: false, message: "Обзорное видео пока не собрано." };
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function loadAIVideoBrief(jobId, generationRequestId = 0) {
  const requestId = ++state.aiBriefRequestId;
  if (generationRequestId && generationRequestId !== state.generationRequestId) {
    return;
  }
  if (!jobId) {
    renderAIBriefSummary(
      "Экспорт для AI-видео доступен только после сохранения записи.",
      "Сейчас доступен только локальный черновик плана без экспортного пакета.",
      false
    );
    return;
  }
  renderAIBriefSummary(
    "Собираем пакет для AI-видео генератора.",
    "Подождите, идет подготовка экспортного пакета.",
    false
  );
  try {
    const response = await fetch(`/v1/jobs/${jobId}/ai-video-brief`);
    if (requestId !== state.aiBriefRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    if (!response.ok) throw new Error(`Сервис вернул ошибку ${response.status}`);
    const data = await response.json();
    if (requestId !== state.aiBriefRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    state.lastAIBrief = data;
    renderAIBriefData();
  } catch {
    if (requestId !== state.aiBriefRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    state.lastAIBrief = null;
    renderAIBriefSummary(
      "Пакет для AI-видео пока не получен.",
      "Не удалось собрать экспортный пакет. Попробуйте позже.",
      false
    );
  }
}

function showUnsavedDependentState() {
  state.lastAIBrief = null;
  setVideoPreviewState(false, "Сохранение записи недоступно: обзорное видео не собирается.");
  resetAIBrief();
  renderRenderPlanSummary(
    "Без сохраненной записи нельзя проверить готовность к сборке видео.",
    ["готовность: нужна запись", "есть фрагментов: —", "нужно добавить: —", "выпуск: нет"]
  );
  renderAIBriefSummary(
    "Экспорт для AI-видео доступен только после сохранения записи.",
    "Сейчас доступен только локальный черновик плана без экспортного пакета.",
    false
  );
}

function renderSteps(activeIndex = 0) {
  clearNode(stepper);
  const completed = activeIndex >= steps.length;
  steps.forEach((step, index) => {
    const item = document.createElement("li");
    item.className = "step";
    if (completed || index < activeIndex) item.classList.add("done");
    if (!completed && index === activeIndex) item.classList.add("active");

    appendTextElement(item, "span", "step-index", String(index + 1));
    const content = document.createElement("div");
    appendTextElement(content, "h3", "", step.title);
    appendTextElement(content, "p", "", step.description);
    item.append(content);
    stepper.append(item);
  });
}

function renderPlan(plan) {
  state.lastPlan = plan;
  state.submittedFeedbackType = null;
  resultPanel.classList.remove("is-empty", "is-stale");
  clearPreviewVideo();
  setVideoPreviewState(false, "Проверяем, можно ли собрать обзорное видео.");
  resetPlayback();
  const units = plan.units || [];
  if (state.selectedUnitIndex >= units.length) state.selectedUnitIndex = Math.max(0, units.length - 1);
  const confidence = Number(plan.confidence || 0);
  confidenceValue.textContent = confidence.toFixed(2);
  confidenceBar.style.width = `${Math.max(0, Math.min(1, confidence)) * 100}%`;
  subtitleBox.textContent = plan.input_text || "Нет текста";
  const fallbackCount = Number(plan?.metadata?.fallback_count ?? plan?.coverage?.fallback ?? 0);
  if (trustTitle) {
    trustTitle.textContent = fallbackCount
      ? "Нужна проверка черновика"
      : "Черновик собран";
  }
  if (trustText) {
    trustText.textContent = fallbackCount
      ? "Словарная база покрыла только часть фразы или оставила подсказки. Носителю жестового языка нужно подтвердить результат."
      : "План собран без буквенного фолбэка, но перед выпуском все равно нужна контрольная проверка носителем.";
  }
  resultTranscript.value = plan.input_text || "";
  syncClearButton();
  syncTranscriptState();
  renderTranscriptMeta(plan);
  warningCount.textContent = String((plan.warnings || []).length);
  warningText.textContent = formatWarnings(plan.warnings);
  renderJobMeta(plan.metadata);
  renderRisk(plan.risk);
  renderSteps(4);
  renderCoverage(units, plan.coverage);
  renderFallbackSummary(units, plan.coverage);
  renderTrace(plan.trace, plan);

  clearNode(timeline);
  units.forEach((unit, index) => {
    const fallback = unit.kind !== "gloss" || String(unit.source || "").startsWith("fallback");
    const gloss = formatGloss(unit);
    const card = document.createElement("article");
    card.className = "unit-card";
    if (fallback) card.classList.add("fallback");
    if (index === state.selectedUnitIndex) card.classList.add("selected");
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-pressed", String(index === state.selectedUnitIndex));
    card.setAttribute("aria-label", `Единица ${index + 1}: ${gloss}`);
    card.addEventListener("click", () => selectUnit(index));
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      selectUnit(index);
    });

    appendTextElement(card, "span", "unit-kind", formatUnitKind(unit.kind));
    const glossElement = appendTextElement(card, "strong", "unit-gloss", `${index + 1}. ${gloss}`);
    glossElement.title = String(unit.gloss || "");
    appendTextElement(card, "span", "unit-source", `${unit.source_token || ""} · ${formatUnitSource(unit.source)}`);
    appendTextElement(card, "span", "unit-source", `оценка ${Number(unit.confidence || 0).toFixed(2)}`);
    appendTextElement(card, "span", "unit-decision", formatUnitDecision(unit));
    appendTextElement(card, "span", "unit-review", formatReviewerHint(unit));
    timeline.append(card);
  });
  renderUnitInspector(units);
}

function renderEmptyState() {
  state.generationRequestId += 1;
  state.renderPlanRequestId += 1;
  state.previewVideoRequestId += 1;
  state.aiBriefRequestId += 1;
  state.lastPlan = null;
  state.lastRenderPlan = null;
  state.videoPreviewReady = false;
  state.selectedUnitIndex = 0;
  state.submittedFeedbackType = null;
  resultPanel.classList.add("is-empty");
  resultPanel.classList.remove("is-stale");
  jobMeta.classList.remove("stale");
  clearPreviewVideo();
  setVideoPreviewState(false, "Сначала соберите черновик перевода.");
  resetPlayback();
  setFullscreen(false);
  resetUploadState();
  subtitleBox.hidden = false;
  subtitleToggle.checked = true;
  subtitleBox.textContent = "Черновик появится после генерации.";
  if (trustTitle) trustTitle.textContent = "Пока нет черновика";
  if (trustText) {
    trustText.textContent = "Введите короткую фразу. Система покажет, что найдено в словарях, а что нужно проверить человеком.";
  }
  resultTranscript.value = inputText.value.trim();
  syncClearButton();
  transcriptMeta.textContent = "После первой сборки здесь можно будет быстро поправить текст и пересобрать черновик.";
  syncTranscriptState();
  confidenceValue.textContent = "0.00";
  confidenceBar.style.width = "0%";
  warningText.textContent = "Пока предупреждений нет.";
  warningCount.textContent = "0";
  jobMeta.textContent = "Введите фразу или загрузите аудио, затем нажмите «Собрать перевод».";
  jobMeta.classList.add("muted");
  jobMeta.classList.remove("stale");
  renderRisk(null);
  renderSteps(0);
  renderCoverage([], { gloss: 0, dactyl: 0, fallback: 0, total: 0 });
  renderFallbackSummary([], { gloss: 0, dactyl: 0, fallback: 0, total: 0 });
  traceGate.textContent = "ожидание";
  traceGate.classList.remove("bad");
  renderMetricGrid(traceSummary, [
    ["0", "токенов"],
    ["0", "найдено"],
    ["0", "замен"],
    ["старт", "режим проверки"],
  ]);
  clearNode(traceList);
  const pendingItem = document.createElement("li");
  pendingItem.className = "trace-step";
  appendTextElement(pendingItem, "span", "trace-step-status", "старт");
  const pendingContent = document.createElement("div");
  appendTextElement(pendingContent, "strong", "", "Ждет запуска");
  appendTextElement(pendingContent, "span", "", "Сначала соберите перевод, затем здесь появится прозрачная трасса.");
  pendingItem.append(pendingContent);
  traceList.append(pendingItem);
  clearNode(timeline);
  clearNode(unitInspector);
  appendTextElement(unitInspector, "p", "unit-inspector-note", "План жестов появится после генерации.");
  setFeedbackEnabled(false);
  resetRenderPlanSummary();
  resetAIBrief();
}

function markPlanStale() {
  if (!state.lastPlan) return;
  state.generationRequestId += 1;
  state.renderPlanRequestId += 1;
  state.previewVideoRequestId += 1;
  state.aiBriefRequestId += 1;
  resultPanel.classList.add("is-stale");
  state.submittedFeedbackType = null;
  clearPreviewVideo();
  resetPlayback();
  setVideoPreviewState(false, "Черновик изменился. Пересоберите результат.");
  jobMeta.textContent = "Текст изменен. Пересоберите черновик, чтобы обновить план, оценку и проверку.";
  jobMeta.classList.remove("muted");
  jobMeta.classList.add("stale");
  setFeedbackEnabled(false);
  renderRenderPlanSummary(
    "Готовность видео устарела вместе с черновиком. Пересоберите результат.",
    ["готовность: устарела", "есть фрагментов: -", "нужно добавить: -", "выпуск: нет"]
  );
  renderAIBriefSummary(
    "Пакет для AI-видео устарел вместе с черновиком.",
    "Пересоберите результат, чтобы обновить экспортный пакет.",
    false
  );
  syncAIBriefModeButtons();
}

function syncDirtyState() {
  const currentText = String(inputText.value || "").trim();
  const sourceText = String(state.lastPlan?.input_text || "").trim();
  syncClearButton();
  if (!state.lastPlan) {
    resultPanel.classList.remove("is-stale");
    jobMeta.classList.remove("stale");
    return;
  }
  if (!currentText) {
    renderEmptyState();
    return;
  }
  if (currentText !== sourceText) {
    markPlanStale();
    return;
  }
  resultPanel.classList.remove("is-stale");
  jobMeta.classList.remove("stale");
  renderJobMeta(state.lastPlan.metadata);
}

function selectUnit(index) {
  state.selectedUnitIndex = index;
  if (state.lastPlan) renderPlan(state.lastPlan);
}

function renderUnitInspector(units) {
  clearNode(unitInspector);
  const unit = units[state.selectedUnitIndex];
  if (!unit) {
    appendTextElement(unitInspector, "p", "unit-inspector-note", "План появится после генерации перевода.");
    return;
  }

  appendTextElement(unitInspector, "h3", "", `Выбрана единица ${state.selectedUnitIndex + 1}`);
  const grid = document.createElement("div");
  grid.className = "unit-inspector-grid";
  [
    ["Текст", unit.source_token || "—"],
    ["Глосса", formatInspectorGloss(unit)],
    ["Источник", formatUnitSource(unit.source)],
    ["Оценка", Number(unit.confidence || 0).toFixed(2)],
  ].forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "unit-inspector-item";
    appendTextElement(item, "span", "", label);
    appendTextElement(item, "strong", "", String(value));
    grid.append(item);
  });
  unitInspector.append(grid);
  appendTextElement(unitInspector, "p", "unit-inspector-note", formatUnitDecision(unit));
  appendTextElement(unitInspector, "p", "unit-inspector-note", formatReviewerHint(unit));
}

function renderTrace(trace, plan) {
  const fallbackTrace = buildFallbackTrace(plan);
  const nextTrace = trace || fallbackTrace;
  const summary = nextTrace.summary || fallbackTrace.summary;
  const gate = formatReviewGate(summary.review_gate);
  traceGate.textContent = gate.label;
  traceGate.classList.toggle("bad", gate.critical);

  clearNode(traceSummary);
  [
    [summary.token_count ?? 0, pluralRu(Number(summary.token_count ?? 0), "токен", "токена", "токенов")],
    [summary.matched_units ?? 0, "найдено"],
    [summary.fallback_units ?? 0, pluralRu(Number(summary.fallback_units ?? 0), "замена", "замены", "замен")],
    [gate.shortLabel, "режим проверки"],
  ].forEach(([value, label]) => {
    const item = document.createElement("div");
    appendTextElement(item, "strong", "", String(value));
    appendTextElement(item, "span", "", label);
    traceSummary.append(item);
  });

  clearNode(traceList);
  (nextTrace.stages || []).forEach((stage) => {
    const item = document.createElement("li");
    item.className = `trace-step ${stage.status || "pending"}`;
    appendTextElement(item, "span", "trace-step-status", formatStageStatus(stage.status));
    const content = document.createElement("div");
    appendTextElement(content, "strong", "", stage.title || "Этап");
    appendTextElement(content, "span", "", stage.summary || "");
    item.append(content);
    traceList.append(item);
  });
}

function renderTranscriptMeta(plan) {
  const language = formatPlanLanguage(plan.language);
  const text = String(plan.input_text || "").trim();
  const tokenCount = text ? text.split(/\s+/).filter(Boolean).length : 0;
  const outputStatus = formatOutputStatus(plan?.metadata?.output_status);
  transcriptMeta.textContent = `${language} · ${tokenCount} ${pluralRu(tokenCount, "токен", "токена", "токенов")} · ${outputStatus}.`;
}

function buildFallbackTrace(plan) {
  const units = plan?.units || [];
  const matched = units.filter((unit) => unit.kind === "gloss").length;
  const fallback = units.filter((unit) => unit.kind !== "gloss" || String(unit.source || "").startsWith("fallback")).length;
  const tokens = String(plan?.input_text || "").trim().split(/\s+/).filter(Boolean);
  const reviewGate = plan?.risk?.needs_human_interpreter
    ? "human_interpreter_required"
    : fallback
      ? "native_signer_review_required"
      : "native_signer_review_recommended";
  return {
    summary: {
      token_count: tokens.length,
      matched_units: matched,
      fallback_units: fallback,
      review_gate: reviewGate,
    },
    stages: [
      { id: "input", status: "complete", title: "Фраза принята", summary: `${tokens.length} токенов.` },
      { id: "language", status: "complete", title: "Язык определен", summary: `Маршрут перевода: ${plan?.language || "не задан"}.` },
      { id: "planning", status: "complete", title: "План жестов собран", summary: `Найдено ${matched}, требует замены ${fallback}.` },
      { id: "review", status: plan?.risk?.needs_human_interpreter ? "blocked" : "required", title: "Проверка человеком", summary: "Черновик нужно проверить перед применением." },
      { id: "output", status: "pending", title: "Видео", summary: "Видео пока не собрано. Доступен только черновик плана." },
    ],
  };
}

function renderJobMeta(metadata = {}) {
  const fallbackCount = Number(metadata?.fallback_count ?? 0);
  const unknownCount = Number(metadata?.unknown_token_count ?? 0);
  const reviewStatus = formatReviewStatus(metadata?.review_status);
  const jobStatus = formatJobStatus(metadata?.job_status);
  const outputKind = formatOutputKind(metadata?.output_kind);
  const outputStatus = formatOutputStatus(metadata?.output_status);
  const outputSentence = capitalizeFirst(outputStatus);
  jobMeta.classList.remove("stale");
  if (metadata?.persisted && metadata?.job_id) {
    jobMeta.textContent = `Черновик сохранен для проверки. ${outputSentence}. Обзорное видео собирается отдельно. Проверка: ${reviewStatus}. Требует замены: ${fallbackCount}, неизвестно: ${unknownCount}.`;
    jobMeta.classList.remove("muted");
    setFeedbackEnabled(true);
    return;
  }
  if (metadata?.persisted === false) {
    jobMeta.textContent = `Черновик показан локально без сохранения. Зависимые функции ревью и AI-видео сейчас недоступны. ${outputSentence}. Проверка: ${reviewStatus}. Требует замены: ${fallbackCount}, неизвестно: ${unknownCount}.`;
    jobMeta.classList.add("muted");
    setFeedbackEnabled(false);
    return;
  }
  jobMeta.textContent = `Статус: ${jobStatus}. Вывод: ${outputKind}, ${outputSentence}. Проверка: ${reviewStatus}. Требует замены: ${fallbackCount}, неизвестно: ${unknownCount}.`;
  jobMeta.classList.add("muted");
  setFeedbackEnabled(false);
}

function setFullscreen(active) {
  videoFrame.classList.toggle("fullscreen", active);
  fullscreenButton.setAttribute("aria-pressed", String(active));
  fullscreenButtonLabel.textContent = active ? "Свернуть" : "Полный экран";
}

function setFeedbackEnabled(enabled) {
  feedbackButtons.forEach((button) => {
    button.disabled = !enabled;
  });
  syncFeedbackButtons();
  if (!enabled) {
    feedbackStatus.textContent = "Оценка доступна после сохранения записи.";
  } else {
    feedbackStatus.textContent = "Помогите проверить качество результата.";
  }
}

function formatAdapterStatus(status) {
  if (status === "ready_for_render") return "готов к сборке";
  if (status === "partial_assets") return "часть фрагментов есть";
  if (status === "awaiting_assets") return "нужны фрагменты";
  return String(status || "не задан");
}

async function loadRenderPlan(jobId, generationRequestId = 0) {
  const requestId = ++state.renderPlanRequestId;
  if (!jobId) {
    resetRenderPlanSummary();
    return;
  }
  if (generationRequestId && generationRequestId !== state.generationRequestId) {
    return;
  }
  renderRenderPlanSummary(
    "Проверяем, хватает ли фрагментов для сборки видео.",
    ["готовность: проверка", "есть фрагментов: ...", "нужно добавить: ...", "выпуск: ..."]
  );
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(`/v1/jobs/${jobId}/render-plan`, { signal: controller.signal });
    window.clearTimeout(timeoutId);
    if (requestId !== state.renderPlanRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    if (!response.ok) throw new Error(`Сервис вернул ошибку ${response.status}`);
    const data = await response.json();
    if (requestId !== state.renderPlanRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    state.lastRenderPlan = data;
    const adapterStatus = formatAdapterStatus(data?.adapter?.adapter_status);
    const resolved = Number(data?.summary?.resolved_segments ?? 0);
    const missing = Number(data?.summary?.missing_segments ?? 0);
    const missingBindings = Number(data?.summary?.missing_clip_bindings ?? 0);
    const missingFiles = Number(data?.summary?.missing_clip_files ?? 0);
    const publishReady = Boolean(data?.adapter?.publish_ready);
    const outputKind = formatOutputKind(data?.target_output_kind);
    const blockers = Array.isArray(data?.publish_gate?.blockers)
      ? data.publish_gate.blockers.map(formatPipelineBlocker)
      : [];
    const nextStep = String(data?.publish_gate?.next_step || "").trim();
    renderRenderPlanSummary(
      `${outputKind}. ${publishReady ? "Можно выпускать после проверки." : "К выпуску пока не готово: нужен следующий операционный шаг."}`,
      [
        `пайплайн: ${formatPipelineStatus(data?.pipeline_status)}`,
        `готовность: ${adapterStatus}`,
        `есть фрагментов: ${resolved}`,
        `нужно добавить: ${missing}`,
        `без clip binding: ${missingBindings}`,
        `нет файла клипа: ${missingFiles}`,
        `выпуск: ${publishReady ? "да" : "нет"}`,
        blockers.length ? `блокеры: ${blockers.join(", ")}` : "блокеры: нет",
        nextStep ? `следующий шаг: ${formatPipelineNextStep(nextStep)}` : "следующий шаг: ожидание",
      ]
    );
  } catch {
    window.clearTimeout(timeoutId);
    if (requestId !== state.renderPlanRequestId) return;
    if (generationRequestId && generationRequestId !== state.generationRequestId) return;
    renderRenderPlanSummary(
      "Готовность видео пока не получена. Черновик сохранен, проверьте позже.",
      ["готовность: ошибка", "есть фрагментов: ?", "нужно добавить: ?", "выпуск: нет"]
    );
  }
}

function renderRisk(risk) {
  const domains = risk?.domains || [];
  const needsHuman = Boolean(risk?.needs_human_interpreter);
  riskCard.hidden = !needsHuman;
  const domainText = domains.map((domain) => riskLabels[domain] || domain).join(", ");
  riskText.textContent = needsHuman
    ? `Сценарий: ${domainText}. Используйте только как черновик до проверки человеком.`
    : "";
}

function formatWarnings(warnings = []) {
  return warnings.map((warning) => warningLabels[warning] || warning).join(" ") || "Нет предупреждений";
}

function renderCoverage(units, coverage) {
  const covered = Number(coverage?.gloss ?? units.filter((unit) => unit.kind === "gloss").length);
  const dactyl = Number(coverage?.dactyl ?? units.filter((unit) => unit.kind === "dactyl").length);
  const fallback = Number(
    coverage?.fallback ?? units.filter((unit) => String(unit.source || "").startsWith("fallback")).length
  );
  const total = Number(coverage?.total ?? units.length);
  renderMetricGrid(coverageStrip, [
    [covered, "найдено жестов"],
    [dactyl, "по буквам"],
    [fallback, "требует замены"],
    [total, "единиц плана"],
  ]);
}

function renderFallbackSummary(units, coverage) {
  const covered = Number(coverage?.gloss ?? units.filter((unit) => unit.kind === "gloss").length);
  const dactyl = Number(coverage?.dactyl ?? units.filter((unit) => unit.kind === "dactyl").length);
  const fallback = Number(
    coverage?.fallback ?? units.filter((unit) => String(unit.source || "").startsWith("fallback")).length
  );
  const total = Number(coverage?.total ?? units.length);
  renderMetricGrid(fallbackSummary, [
    [covered, "словарных жестов"],
    [dactyl, "по буквам"],
    [fallback, "требуют замены"],
    [total, "единиц всего"],
  ], "fallback-summary-item");
}

function formatGloss(unit) {
  const value = unit?.gloss;
  const kind = unit?.kind;
  const parts = String(value || "").split(/\s+/).filter(Boolean);
  if (kind === "dactyl") {
    const preview = formatDactylPreview(unit?.source_token);
    if (preview) return preview;
    if (parts.length > 6) {
      return `${parts.slice(0, 4).map(formatDactylPart).join(" ")} +${parts.length - 4}`;
    }
    return parts.map(formatDactylPart).join(" ");
  }
  if (parts.length > 10) {
    return `${parts.slice(0, 10).join(" ")} +${parts.length - 10}`;
  }
  return value;
}

function formatDactylPart(part) {
  return String(part || "").replace(/^DACTYL_/, "").replaceAll("_", "-");
}

function formatInspectorGloss(unit) {
  if (!unit?.gloss) return "—";
  if (unit.kind !== "dactyl") return String(unit.gloss);
  return formatDactylPreview(unit.source_token) || String(unit.gloss);
}

function formatDactylPreview(sourceToken) {
  const letters = Array.from(String(sourceToken || "").trim().toLowerCase())
    .filter((char) => /[a-zA-Zа-яА-Яәіңғүұқөһё]/.test(char))
    .map((char) => char.toUpperCase());
  if (!letters.length) return "";
  if (letters.length > 8) {
    return `${letters.slice(0, 8).join(" ")} +${letters.length - 8}`;
  }
  return letters.join(" ");
}

async function generatePlan() {
  const text = inputText.value.trim();
  if (!text) {
    inputText.focus();
    return;
  }
  const generationId = ++state.generationRequestId;
  state.renderPlanRequestId += 1;
  state.previewVideoRequestId += 1;
  state.aiBriefRequestId += 1;
  state.lastRenderPlan = null;
  state.lastAIBrief = null;
  state.aiBriefMode = "universal_prompt";
  syncAIBriefModeButtons();
  resetRenderPlanSummary();
  renderAIBriefSummary(
    "Готовим пакет для AI-видео...",
    "Сохраните черновик, затем здесь появится свежий экспортный пакет.",
    false
  );
  generateButton.disabled = true;
  generateButton.textContent = "Собираем...";
  renderSteps(2);
  try {
    const response = await fetch("/v1/translate/text", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, language: state.inputLanguage }),
    });
    if (generationId !== state.generationRequestId) return;
    if (!response.ok) throw new Error(`Сервис вернул ошибку ${response.status}`);
    const plan = await response.json();
    if (generationId !== state.generationRequestId) return;
    renderPlan(plan);
    state.lastAIBrief = null;
    const jobId = plan?.metadata?.job_id;
    if (jobId) {
      void Promise.allSettled([
        loadReviewVideo(jobId, generationId),
        loadRenderPlan(jobId, generationId),
        loadAIVideoBrief(jobId, generationId),
      ]);
    } else {
      if (generationId !== state.generationRequestId) return;
      showUnsavedDependentState();
    }
    if (generationId === state.generationRequestId) {
      setService("ok", "работает");
    }
  } catch (error) {
    if (generationId !== state.generationRequestId) return;
    renderPlan({
      input_text: text,
      language: "unknown",
      confidence: 0,
      units: [
        {
          kind: "subtitle",
          source_token: "error",
          gloss: "СЕРВИС НЕДОСТУПЕН",
          confidence: 0,
          source: "service:error",
        },
      ],
      warnings: ["api_unavailable"],
    });
    resetAIBrief();
    resetRenderPlanSummary();
    setService("bad", "ошибка сервиса");
  } finally {
    if (generationId !== state.generationRequestId) return;
    generateButton.disabled = false;
    setGenerateButtonIdle();
  }
}

async function uploadAudio(file) {
  if (!file) return;
  if (file.size > maxAudioBytes) {
    setUploadState("error", "Файл слишком большой", "Максимальный размер аудио — 50 MB");
    return;
  }
  if (!supportedAudioTypes.has(file.type)) {
    setUploadState("error", "Неподдерживаемый формат", "Загрузите WAV, MP3, M4A, AAC или WEBM");
    return;
  }

  setUploadState("loading", "Распознаем аудио...", file.name);
  try {
    const response = await fetch("/v1/transcribe/audio", {
      method: "POST",
      headers: { "content-type": file.type },
      body: file,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || `Сервис вернул ошибку ${response.status}`);
    }
    if (data.status === "asr_unavailable") {
      setUploadState("error", "Распознавание пока не подключено", "Проверьте перевод через текстовое поле");
      return;
    }
    inputText.value = data.text || "";
    if (data.language) {
      setInputLanguage(data.language);
      document.querySelectorAll("[data-language]").forEach((item) => {
        const isCurrent = item.dataset.language === state.inputLanguage;
        item.classList.toggle("active", isCurrent);
        item.setAttribute("aria-pressed", String(isCurrent));
      });
    }
    updateCharCount();
    setUploadState("success", "Текст получен", data.language ? `Язык: ${data.language}` : file.name);
    if (inputText.value.trim()) await generatePlan();
  } catch (error) {
    setUploadState("error", "Аудио не обработано", String(error.message || error));
    setService("pending", "аудио недоступно");
  } finally {
    audioInput.value = "";
  }
}

async function sendFeedback(feedbackType) {
  const jobId = state.lastPlan?.metadata?.job_id;
  if (!jobId) return;
  state.submittedFeedbackType = null;
  syncFeedbackButtons();
  feedbackButtons.forEach((button) => {
    button.disabled = true;
  });
  feedbackStatus.textContent = "Сохраняем оценку...";
  try {
    const response = await fetch("/v1/feedback", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ job_id: jobId, feedback_type: feedbackType }),
    });
    if (!response.ok) throw new Error(`Сервис вернул ошибку ${response.status}`);
    state.submittedFeedbackType = feedbackType;
    syncFeedbackButtons();
    const selectedButton = feedbackButtons.find((button) => button.dataset.feedback === feedbackType);
    feedbackStatus.textContent = `Спасибо, оценка «${selectedButton?.textContent?.trim() || feedbackType}» сохранена.`;
  } catch {
    feedbackStatus.textContent = "Оценку не удалось сохранить. Попробуйте позже.";
    setFeedbackEnabled(Boolean(state.lastPlan?.metadata?.job_id));
  }
}

function renderSources(items) {
  clearNode(sourceRows);
  const visibleItems = Array.isArray(items) ? items.slice(0, 8) : [];
  if (!visibleItems.length) {
    const row = document.createElement("tr");
    const emptyCell = appendTextElement(row, "td", "source-empty", "Источники пока не загружены.");
    emptyCell.colSpan = 4;
    sourceRows.append(row);
    return;
  }
  visibleItems.forEach((source) => {
    const languages = formatSourceLanguages(source.languages);
    const statusLabel = formatStatus(source.status);
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    nameCell.dataset.label = "Источник";
    const nameWrap = document.createElement("div");
    nameWrap.className = "source-name";
    if (source.url) {
      const sourceLink = document.createElement("a");
      sourceLink.className = "source-link";
      sourceLink.href = String(source.url);
      sourceLink.target = "_blank";
      sourceLink.rel = "noopener noreferrer";
      sourceLink.textContent = String(source.name || source.id || "");
      nameWrap.append(sourceLink);
    } else {
      appendTextElement(nameWrap, "span", "source-link", source.name || source.id || "");
    }
    if (source.license_note) {
      appendTextElement(nameWrap, "span", "source-note", formatSourceNote(source.license_note));
    }
    nameCell.append(nameWrap);
    row.append(nameCell);
    const taskCell = appendTextElement(row, "td", "", formatTask(source.task));
    taskCell.dataset.label = "Тип";
    taskCell.title = String(source.task || "");
    const languageCell = appendTextElement(row, "td", "", languages || "");
    languageCell.dataset.label = "Языки";
    const statusCell = document.createElement("td");
    statusCell.dataset.label = "Статус";
    const badge = appendTextElement(statusCell, "span", "status-badge", statusLabel);
    badge.title = statusLabel;
    if (source.status === "verified") badge.classList.add("verified");
    if (source.status === "needs_license_check") badge.classList.add("needs-license");
    if (source.status === "needs_access_check") badge.classList.add("needs-access");
    row.append(statusCell);
    sourceRows.append(row);
  });
}

function formatStatus(status) {
  if (status === "verified") return "проверено";
  if (status === "needs_access_check") return "нужен доступ";
  if (status === "needs_license_check") return "нужна лицензия";
  return String(status || "неизвестно").replace(/^needs_/, "").replace(/_check$/, "").replaceAll("_", " ");
}

function formatUnitKind(kind) {
  if (kind === "gloss") return "жест";
  if (kind === "dactyl") return "по буквам";
  if (kind === "subtitle") return "текст";
  return String(kind || "элемент");
}

function formatUnitSource(source) {
  if (!source) return "источник не указан";
  if (String(source).startsWith("seed:manual_phrase")) return "фраза из словаря";
  if (String(source).startsWith("seed:manual_nonmanual")) return "грамматическая пометка";
  if (String(source).startsWith("seed:manual")) return "словарь";
  if (String(source).startsWith("fallback:dactyl")) return "написание по буквам";
  if (String(source).startsWith("fallback:subtitle")) return "текстовая подсказка";
  if (String(source).startsWith("service:error")) return "ошибка сервиса";
  return String(source).replaceAll("_", " ");
}

function formatUnitDecision(unit) {
  if (unit?.decision?.reason) return unit.decision.reason;
  if (unit?.kind === "gloss") return "Единица найдена в словаре.";
  if (unit?.kind === "dactyl") return "Слово показано по буквам, потому что словарного жеста пока нет.";
  return "Нужна ручная проверка и замена.";
}

function formatReviewerHint(unit) {
  if (unit?.decision?.review_hint) return unit.decision.review_hint;
  if (unit?.kind === "gloss") return "Ревьюеру: сверить движение, мимику и порядок в фразе.";
  if (unit?.kind === "dactyl") return "Ревьюеру: заменить дактиль словарным жестом, если он есть в локальной практике.";
  return "Ревьюеру: подобрать жест или оставить понятную текстовую подсказку.";
}

function formatStageStatus(status) {
  if (status === "complete") return "готово";
  if (status === "blocked") return "стоп";
  if (status === "required") return "проверка";
  if (status === "empty") return "пусто";
  return "ожидает";
}

function formatJobStatus(status) {
  if (status === "review_required") return "нужно ревью";
  if (status === "draft_plan") return "черновик плана";
  if (status === "reviewed") return "проверено";
  if (status === "rejected") return "отклонено";
  return String(status || "не задан");
}

function formatOutputKind(kind) {
  if (kind === "sign_plan_preview") return "Черновик плана";
  if (kind === "avatar_video") return "Видео-аватар";
  return String(kind || "вывод не задан");
}

function formatOutputStatus(status) {
  if (status === "not_rendered") return "видео еще не собрано";
  if (status === "queued") return "видео поставлено в очередь";
  if (status === "rendering") return "видео собирается";
  if (status === "ready") return "видео готово";
  if (status === "failed") return "сборка видео не удалась";
  return String(status || "статус вывода не задан");
}

function formatReviewGate(gate) {
  if (gate === "human_interpreter_required") {
    return { label: "нужен человек-переводчик", shortLabel: "человек", critical: true };
  }
  if (gate === "native_signer_review_required") {
    return { label: "нужна проверка носителем", shortLabel: "носитель", critical: false };
  }
  return { label: "контрольная проверка", shortLabel: "контроль", critical: false };
}

function capitalizeFirst(value) {
  const text = String(value || "");
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : "";
}

function pluralRu(value, one, few, many) {
  const normalized = Math.abs(value);
  if (normalized % 100 >= 11 && normalized % 100 <= 14) return many;
  if (normalized % 10 === 1) return one;
  if (normalized % 10 >= 2 && normalized % 10 <= 4) return few;
  return many;
}

function formatReviewStatus(status) {
  if (status === "pending_signer_review") return "ожидает проверки";
  if (status === "approved") return "одобрено";
  if (status === "rejected") return "отклонено";
  if (status === "needs_edit") return "нужна правка";
  return String(status || "не задан");
}

function formatPipelineStatus(status) {
  if (status === "ready_for_external_render") return "можно готовить внешний рендер";
  if (status === "approved_but_asset_incomplete") return "одобрено, но не хватает материалов";
  if (status === "approved_pending_render") return "одобрено, можно запускать сборку";
  if (status === "awaiting_signer_review") return "ждет проверки носителем";
  if (status === "render_uploaded_pending_review") return "видео загружено, ждет финальной проверки";
  if (status === "ready_for_publish") return "готово к публикации";
  if (status === "uploaded_video_needs_fix") return "загруженное видео требует правки";
  return String(status || "не задан");
}

function formatPipelineBlocker(blocker) {
  if (blocker === "needs_signer_approval") return "нужна проверка носителем";
  if (blocker === "missing_render_assets") return "не хватает видеофрагментов";
  if (blocker === "render_output_missing") return "финальное видео еще не загружено";
  if (blocker === "empty_sign_plan") return "план жестов пуст";
  return String(blocker || "не задан");
}

function formatPipelineNextStep(step) {
  if (step === "publishable_now") return "можно публиковать";
  if (step === "replace_or_reupload_final_video") return "заменить или заново загрузить финальное видео";
  if (step === "complete_final_video_review") return "завершить финальную проверку видео";
  if (step === "prepare_external_render") return "подготовить внешний рендер";
  if (step === "attach_or_generate_missing_assets") return "добавить недостающие клипы";
  if (step === "start_render_or_brief_export") return "запустить сборку или отдать пакет в работу";
  if (step === "complete_signer_review") return "завершить проверку носителем";
  return String(step || "ожидание");
}

function formatReviewerRole(role) {
  if (role === "native_signer") return "носитель";
  if (role === "linguist") return "лингвист";
  if (role === "operator") return "оператор";
  return String(role || "ревьюер");
}

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatPublishStatus(status) {
  if (status === "draft") return "черновик";
  if (status === "final_review_pending") return "ждет финальной проверки";
  if (status === "publishable") return "можно публиковать";
  if (status === "needs_video_fix") return "нужна правка видео";
  if (status === "rejected") return "отклонено";
  return String(status || "не задан");
}

function formatAuditEventType(type) {
  if (type === "job_created") return "создана запись";
  if (type === "review_status_updated") return "обновлен статус проверки";
  if (type === "review_session_created") return "сохранена сессия ревью";
  if (type === "feedback_recorded") return "получен отзыв пользователя";
  if (type === "rendered_video_attached") return "прикреплено финальное видео";
  if (type === "publish_status_updated") return "обновлен статус публикации";
  return String(type || "событие");
}

function formatAuditDetailKey(key) {
  const labels = {
    input_type: "вход",
    language: "язык",
    reviewer_language: "язык ревью",
    blocking_issue: "блокирующая проблема",
    meaning_score: "смысл",
    understandability_score: "понятность",
    output_uri: "ссылка",
    render_adapter: "рендер",
    review_status: "статус проверки",
    publish_status: "статус публикации",
    feedback_type: "тип отзыва",
    has_note: "есть заметка",
    note: "комментарий",
  };
  return labels[key] || String(key || "поле");
}

function formatAuditDetailValue(value) {
  if (typeof value === "boolean") return value ? "да" : "нет";
  if (value == null || value === "") return "—";
  return String(value);
}

function formatFeedbackType(type) {
  if (type === "good") return "Хорошо";
  if (type === "wrong_sign") return "Неверный жест";
  if (type === "unclear_sign") return "Непонятно";
  if (type === "missing_sign") return "Нет жеста";
  if (type === "offensive") return "Неприемлемо";
  return String(type || "отзыв");
}

function formatAuditDetailEntry(key, value) {
  const label = formatAuditDetailKey(key);
  if (key === "feedback_type") return `${label}: ${formatFeedbackType(value)}`;
  if (key === "review_status") return `${label}: ${formatReviewStatus(value)}`;
  if (key === "publish_status") return `${label}: ${formatPublishStatus(value)}`;
  if (key === "language" || key === "reviewer_language") return `${label}: ${formatPlanLanguage(value)}`;
  if (key === "render_adapter" && value === "external_ai_video") return `${label}: внешний AI-видео рендер`;
  return `${label}: ${formatAuditDetailValue(value)}`;
}

function formatPlanLanguage(language) {
  if (language === "ru") return "Русский";
  if (language === "kk") return "Казахский";
  if (language === "en") return "Английский";
  return "Язык не определен";
}

function syncTranscriptState() {
  const currentText = String(resultTranscript.value || "").trim();
  const sourceText = String(state.lastPlan?.input_text || "").trim();
  const changed = currentText !== sourceText && currentText.length > 0;
  applyTranscriptButton.disabled = !changed;
}

function formatTask(task) {
  const labels = {
    rsl_dataset_models: "лексическая база",
    rsl_isolated_recognition: "распознавание",
    rsl_dactyl: "дактиль",
    rsl_encoder_pretrain: "модель жестов",
    text_to_rsl_video: "сборка видео",
    framework: "открытый код",
    asl_lexical_database: "лексическая база",
    asl_dataset: "датасет ASL",
    krsl_dataset_nonmanual: "маркеры KRSL",
    krsl_large_corpus: "корпус KRSL",
  };
  return labels[task] || String(task || "").replaceAll("_", " ");
}

function formatSourceLanguages(languages) {
  const values = Array.isArray(languages) ? languages : [languages];
  const labels = {
    ru: "RU",
    kk: "KZ",
    kz: "KZ",
    en: "EN",
    rsl: "RSL",
    asl: "ASL",
    krsl: "KRSL",
    multi: "несколько",
  };
  return values
    .map((value) => labels[String(value || "").toLowerCase()] || String(value || "").toUpperCase())
    .filter(Boolean)
    .join(", ");
}

function formatSourceNote(note) {
  const value = String(note || "").trim();
  const exact = {
    "Public pages state a CC BY-SA 4.0 variant; exact data/model terms require file-level review.":
      "На публичных страницах указан вариант CC BY-SA 4.0; точные условия для данных и моделей нужно проверить по файлам.",
    "Repository LICENSE is Creative Commons Attribution-ShareAlike 4.0.":
      "В репозитории указана лицензия Creative Commons Attribution-ShareAlike 4.0.",
    "Repository code is Apache 2.0; dataset and weights require separate review.":
      "Код репозитория под Apache 2.0; датасет и веса нужно проверить отдельно.",
    "Code follows MimicMotion Apache 2.0; third-party weights and Slovo-derived assets require separate review.":
      "Код опирается на MimicMotion Apache 2.0; сторонние веса и материалы на базе Slovo нужно проверить отдельно.",
    "Apache 2.0.":
      "Лицензия Apache 2.0.",
    "Academic lexical database; use as metadata/research candidate only until terms are reviewed.":
      "Академическая лексическая база; использовать только как исследовательский источник, пока условия не проверены.",
    "Research dataset candidate for ASL translation experiments; exact reuse terms require review.":
      "Исследовательский датасет для экспериментов с ASL; точные условия повторного использования нужно проверить.",
    "Academic dataset terms require review before reuse.":
      "Условия академического датасета нужно проверить до повторного использования.",
    "Paper reports large corpus; downloadable data and terms require author/project confirmation.":
      "В статье описан большой корпус; доступные данные и условия использования нужно подтвердить у авторов проекта.",
  };
  return exact[value] || value;
}

async function loadHealthAndSources() {
  try {
    const health = await fetch("/health/ready");
    const data = await health.json();
    state.healthFailures = 0;
    if (state.healthRetryTimer) {
      window.clearTimeout(state.healthRetryTimer);
      state.healthRetryTimer = null;
    }
    readyStatus.textContent = data.status === "ok" ? "готов" : "проверка";
    setService(health.ok ? "ok" : "bad", health.ok ? "работает" : "требует проверки");
  } catch {
    state.healthFailures += 1;
    if (state.healthFailures < 2) {
      readyStatus.textContent = "повтор";
      setService("pending", "проверяем");
      scheduleHealthRetry();
    } else {
      readyStatus.textContent = "нет связи";
      setService("bad", "нет связи");
    }
  }

  try {
    const response = await fetch("/v1/sources");
    if (!response.ok) throw new Error("sources unavailable");
    const data = await response.json();
    renderSources(data.items || []);
  } catch {
    renderSources(sampleSources);
  }
}

function formatReviewPill(status) {
  const match = reviewStatusOptions.find((item) => item.value === status);
  return {
    label: match?.label || formatReviewStatus(status),
    tone: match?.tone || "warn",
  };
}

function renderReviewSummary(items) {
  const counts = {
    total: items.length,
    pending_signer_review: items.filter((item) => item.review_status === "pending_signer_review").length,
    needs_edit: items.filter((item) => item.review_status === "needs_edit").length,
    approved: items.filter((item) => item.review_status === "approved").length,
  };
  renderMetricGrid(
    reviewSummary,
    [
      [counts.total, "записей в выборке"],
      [counts.pending_signer_review, "ждут проверки"],
      [counts.needs_edit, "нуждаются в правке"],
      [counts.approved, "уже одобрены"],
    ],
    "review-summary-item"
  );
}

function syncReviewActionButtons() {
  const disabled = !state.reviewToken || !state.selectedReviewJobId;
  reviewStatusActionButtons.forEach((button) => {
    button.disabled = disabled;
  });
  reviewSessionSubmitButton.disabled = disabled;
  reviewerRoleInput.disabled = disabled;
  reviewerLanguageInput.disabled = disabled;
  reviewSessionStatusInput.disabled = disabled;
  reviewMeaningScoreInput.disabled = disabled;
  reviewUnderstandabilityScoreInput.disabled = disabled;
  reviewBlockingIssueInput.disabled = disabled;
  reviewSessionNotesInput.disabled = disabled;
  reviewRenderedVideoInput.disabled = disabled;
  reviewUploadSubmitButton.disabled = disabled;
  reviewPublishStatusInput.disabled = disabled;
  reviewPublishNoteInput.disabled = disabled;
  reviewPublishSubmitButton.disabled = disabled;
}

function renderReviewJobs(items) {
  clearNode(reviewJobs);
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "review-empty-state";
    appendTextElement(empty, "strong", "", state.reviewToken ? "Очередь пуста" : "Очередь закрыта");
    appendTextElement(
      empty,
      "p",
      "",
      state.reviewToken
        ? "Для выбранного фильтра пока нет сохраненных записей."
        : "Чтобы увидеть сохраненные записи, введите review token и обновите очередь."
    );
    reviewJobs.append(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "review-job-card";
    if (item.id === state.selectedReviewJobId) card.classList.add("selected");
    card.tabIndex = 0;
    const pill = formatReviewPill(item.review_status);
    const head = document.createElement("div");
    head.className = "review-job-head";
    appendTextElement(head, "strong", "", String(item.input_text || "Без текста"));
    const status = appendTextElement(head, "span", `review-pill ${pill.tone}`, pill.label);
    status.title = String(item.review_status || "");
    card.append(head);
    appendTextElement(
      card,
      "p",
      "",
      `${formatPlanLanguage(item.detected_language)} · ${formatOutputStatus(item.output_status)} · ${formatPublishStatus(item.publish_status)}.`
    );
    appendTextElement(card, "p", "", `Замены: ${Number(item.fallback_count || 0)} · неизвестно: ${Number(item.unknown_token_count || 0)}.`);
    card.addEventListener("click", () => selectReviewJob(item.id));
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      selectReviewJob(item.id);
    });
    reviewJobs.append(card);
  });
}

function renderReviewDetail(job, feedbackItems = []) {
  clearNode(reviewDetailSummary);
  clearNode(reviewUnitList);
  clearNode(reviewSessionList);
  clearNode(reviewFeedbackList);
  clearNode(reviewAuditList);
  syncReviewActionButtons();
  if (!job) {
    appendTextElement(reviewDetailSummary, "strong", "", "Выберите запись");
    appendTextElement(
      reviewDetailSummary,
      "p",
      "",
      state.reviewToken
        ? "После выбора записи здесь появятся детали, единицы плана и отзывы."
        : "После ввода токена ревью здесь откроются защищенные детали сохраненной записи."
    );
    reviewSessionStatus.textContent = state.reviewToken
      ? "Сессию можно сохранить после выбора записи."
      : "Сессии ревью доступны после ввода токена.";
    reviewUploadStatus.textContent = state.reviewToken
      ? "Видео можно прикрепить после выбора записи."
      : "Загрузка видео доступна после ввода токена.";
    reviewPublishStatus.textContent = state.reviewToken
      ? "Финальное решение можно сохранить после выбора записи."
      : "Финальное решение доступно после ввода токена.";
    reviewUnitsMeta.textContent = "0 единиц";
    reviewSessionsMeta.textContent = "0 сессий";
    reviewFeedbackMeta.textContent = "0 отзывов";
    reviewAuditMeta.textContent = "0 событий";
    return;
  }
  appendTextElement(reviewDetailSummary, "strong", "", String(job.input_text || "Без текста"));
  const summaryGrid = document.createElement("div");
  summaryGrid.className = "review-detail-grid";
  [
    ["Язык", formatPlanLanguage(job.detected_language)],
    ["Статус ревью", formatReviewStatus(job.review_status)],
    ["Публикация", formatPublishStatus(job.publish_status)],
    ["Вывод", formatOutputStatus(job.output_status)],
    ["Замены", `${Number(job.fallback_count || 0)} / неизвестно ${Number(job.unknown_token_count || 0)}`],
  ].forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "review-detail-grid-item";
    appendTextElement(item, "span", "", label);
    appendTextElement(item, "strong", "", String(value));
    summaryGrid.append(item);
  });
  reviewDetailSummary.append(summaryGrid);
  appendTextElement(reviewDetailSummary, "p", "", formatWarnings(job.warnings || []));
  if (state.lastRenderPlan) {
    const blockers = Array.isArray(state.lastRenderPlan?.publish_gate?.blockers)
      ? state.lastRenderPlan.publish_gate.blockers.map(formatPipelineBlocker).join(", ")
      : "";
    const nextStep = formatPipelineNextStep(state.lastRenderPlan?.publish_gate?.next_step);
    appendTextElement(
      reviewDetailSummary,
      "p",
      "",
      `Пайплайн: ${formatPipelineStatus(state.lastRenderPlan.pipeline_status)}.${blockers ? ` Блокеры: ${blockers}.` : ""}${nextStep ? ` Следующий шаг: ${nextStep}.` : ""}`
    );
    if (job.output_status === "ready" && job.output_uri) {
      const outputLink = document.createElement("a");
      outputLink.href = String(job.output_uri);
      outputLink.target = "_blank";
      outputLink.rel = "noopener noreferrer";
      outputLink.className = "inline-link";
      outputLink.textContent = "Открыть загруженное видео";
      reviewDetailSummary.append(outputLink);
      reviewUploadStatus.textContent = "У записи уже есть прикрепленное видео. Можно заменить новой версией.";
    } else {
      reviewUploadStatus.textContent = "Загрузите внешний mp4 после рендера.";
    }
  }
  const latestPublishNote = (state.reviewAuditEvents || []).find((item) => item.event_type === "publish_status_updated")?.detail?.note;
  reviewPublishStatusInput.value = String(job.publish_status || "draft");
  reviewPublishNoteInput.value = typeof latestPublishNote === "string" ? latestPublishNote : "";
  reviewPublishStatus.textContent = latestPublishNote
    ? "Последний комментарий к публикации подставлен в форму."
    : "Финальное решение сохраняется отдельно от статуса проверки.";
  syncReviewActionButtons();
  reviewSessionStatus.textContent = "Сохраните решение носителя или оператора по этой записи.";

  const units = job.units || [];
  reviewUnitsMeta.textContent = `${units.length} ${units.length === 1 ? "единица" : "единиц"}`;
  if (!units.length) {
    const emptyUnits = document.createElement("div");
    emptyUnits.className = "review-empty-state";
    appendTextElement(emptyUnits, "strong", "", "Единиц плана нет");
    appendTextElement(emptyUnits, "p", "", "У записи пока нет загруженных единиц плана.");
    reviewUnitList.append(emptyUnits);
  } else {
    units.forEach((unit, index) => {
      const card = document.createElement("article");
      card.className = "review-unit-card";
      appendTextElement(card, "strong", "", `${index + 1}. ${formatGloss(unit)}`);
      appendTextElement(card, "p", "", `${unit.source_token || "—"} · ${formatUnitSource(unit.source)}`);
      appendTextElement(card, "p", "", `${formatUnitDecision(unit)} ${formatReviewerHint(unit)}`);
      reviewUnitList.append(card);
    });
  }

  renderReviewSessions(state.reviewSessions);
  renderReviewAudit(state.reviewAuditEvents);
  reviewSessionsMeta.textContent = `${state.reviewSessions.length} ${state.reviewSessions.length === 1 ? "сессия" : "сессий"}`;
  reviewAuditMeta.textContent = `${state.reviewAuditEvents.length} ${state.reviewAuditEvents.length === 1 ? "событие" : "событий"}`;

  reviewFeedbackMeta.textContent = `${feedbackItems.length} ${feedbackItems.length === 1 ? "отзыв" : "отзывов"}`;
  if (!feedbackItems.length) {
    const emptyFeedback = document.createElement("div");
    emptyFeedback.className = "review-empty-state";
    appendTextElement(emptyFeedback, "strong", "", "Отзывов пока нет");
    appendTextElement(emptyFeedback, "p", "", "Когда пользователи оставят оценку, она появится здесь.");
    reviewFeedbackList.append(emptyFeedback);
  } else {
    feedbackItems.forEach((item) => {
      const card = document.createElement("article");
      card.className = "review-feedback-card";
      appendTextElement(card, "strong", "", formatFeedbackType(item.feedback_type));
      const meta = document.createElement("div");
      meta.className = "review-card-meta";
      appendTextElement(meta, "span", "", formatDateTime(item.created_at) || "время не указано");
      card.append(meta);
      appendTextElement(card, "p", "", item.note || "Без дополнительной заметки.");
      reviewFeedbackList.append(card);
    });
  }
}

function renderReviewAudit(items) {
  clearNode(reviewAuditList);
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "review-empty-state";
    appendTextElement(empty, "strong", "", "История пока пуста");
    appendTextElement(empty, "p", "", "После действий по записи здесь появится понятный журнал событий.");
    reviewAuditList.append(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "review-feedback-card review-session-card";
    appendTextElement(card, "strong", "", `${formatAuditEventType(item.event_type)} · ${formatReviewerRole(item.actor_role)}`);
    const meta = document.createElement("div");
    meta.className = "review-card-meta";
    appendTextElement(meta, "span", "", formatDateTime(item.created_at) || "время не указано");
    card.append(meta);
    const detail = item.detail && typeof item.detail === "object" ? Object.entries(item.detail).slice(0, 5) : [];
    appendTextElement(
      card,
      "p",
      "",
      detail.length
        ? detail.map(([key, value]) => formatAuditDetailEntry(key, value)).join(" · ")
        : "Без деталей."
    );
    reviewAuditList.append(card);
  });
}

function renderReviewSessions(items) {
  clearNode(reviewSessionList);
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "review-empty-state";
    appendTextElement(empty, "strong", "", "Сессий ревью пока нет");
    appendTextElement(empty, "p", "", "Сохраните первую проверку носителя, лингвиста или оператора по этой записи.");
    reviewSessionList.append(empty);
    return;
  }
  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "review-feedback-card review-session-card";
    appendTextElement(
      card,
      "strong",
      "",
      `${formatReviewerRole(item.reviewer_role)} · ${formatPlanLanguage(item.reviewer_language)}`
    );
    const details = [];
    if (Number.isFinite(Number(item.meaning_score))) details.push(`смысл ${item.meaning_score}/5`);
    if (Number.isFinite(Number(item.understandability_score))) details.push(`понятность ${item.understandability_score}/5`);
    if (item.blocking_issue) details.push("есть блокирующая проблема");
    const meta = document.createElement("div");
    meta.className = "review-card-meta";
    appendTextElement(meta, "span", "", formatDateTime(item.created_at) || "время не указано");
    card.append(meta);
    appendTextElement(card, "p", "", details.join(" · ") || "Без оценок.");
    appendTextElement(card, "p", "", item.notes || "Без заметки.");
    reviewSessionList.append(card);
  });
}

async function loadReviewDashboard() {
  saveReviewToken(reviewTokenInput.value);
  state.reviewFilter = reviewStatusFilter.value || "";
  syncReviewActionButtons();
  reviewStatusBanner.textContent = state.reviewToken
    ? "Загружаем очередь ревью и последние отзывы."
    : "Введите токен ревью, чтобы открыть защищенную очередь.";
  reviewQueueStatus.textContent = "проверка";
  if (!state.reviewToken) {
    state.reviewJobs = [];
    state.reviewSessions = [];
    state.reviewAuditEvents = [];
    state.selectedReviewJobId = "";
    renderReviewSummary([]);
    renderReviewJobs([]);
    renderReviewDetail(null);
    reviewQueueStatus.textContent = "нужен токен";
    return;
  }
  try {
    const params = new URLSearchParams();
    if (state.reviewFilter) params.set("review_status", state.reviewFilter);
    const response = await fetch(`/v1/review/jobs?${params.toString()}`, { headers: reviewHeaders() });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${response.status}`);
    }
    const data = await response.json();
    state.reviewJobs = data.items || [];
    reviewQueueStatus.textContent = data.count ? "активно" : "пусто";
    reviewStatusBanner.textContent = data.count
      ? `Загружено ${data.count} записей для ревью.`
      : "Очередь ревью сейчас пуста.";
    renderReviewSummary(state.reviewJobs);
    renderReviewJobs(state.reviewJobs);
    if (!state.reviewJobs.some((item) => item.id === state.selectedReviewJobId)) {
      state.selectedReviewJobId = state.reviewJobs[0]?.id || "";
    }
    await selectReviewJob(state.selectedReviewJobId, false);
  } catch (error) {
    state.reviewJobs = [];
    state.reviewSessions = [];
    state.reviewAuditEvents = [];
    state.selectedReviewJobId = "";
    renderReviewSummary([]);
    renderReviewJobs([]);
    renderReviewDetail(null);
    reviewQueueStatus.textContent = "ошибка";
    reviewStatusBanner.textContent = `Ревью не загрузилось: ${String(error.message || error)}`;
  }
}

async function selectReviewJob(jobId, refreshList = true) {
  state.selectedReviewJobId = String(jobId || "");
  syncReviewActionButtons();
  reviewerLanguageInput.value = reviewerLanguageInput.value || "ru";
  reviewSessionStatus.textContent = state.selectedReviewJobId
    ? "Сохраните решение носителя или оператора по этой записи."
    : "Сессию можно сохранить после выбора записи.";
  reviewUploadStatus.textContent = state.selectedReviewJobId
    ? "Загрузите внешний mp4 после рендера."
    : "Видео можно прикрепить после выбора записи.";
  reviewPublishStatus.textContent = state.selectedReviewJobId
    ? "Сохраните финальное решение по видео."
    : "Финальное решение можно сохранить после выбора записи.";
  if (refreshList) renderReviewJobs(state.reviewJobs);
  if (!state.selectedReviewJobId) {
    renderReviewDetail(null);
    return;
  }
  try {
    const [jobResponse, feedbackResponse, sessionsResponse, auditResponse, renderPlanResponse] = await Promise.all([
      fetch(`/v1/jobs/${state.selectedReviewJobId}`, { headers: reviewHeaders() }),
      fetch(`/v1/review/feedback?job_id=${encodeURIComponent(state.selectedReviewJobId)}`, { headers: reviewHeaders() }),
      fetch(`/v1/review/sessions?job_id=${encodeURIComponent(state.selectedReviewJobId)}`, { headers: reviewHeaders() }),
      fetch(`/v1/review/audit?job_id=${encodeURIComponent(state.selectedReviewJobId)}`, { headers: reviewHeaders() }),
      fetch(`/v1/jobs/${state.selectedReviewJobId}/render-plan`, { headers: reviewHeaders() }),
    ]);
    if (!jobResponse.ok) {
      const detail = await jobResponse.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${jobResponse.status}`);
    }
    const job = await jobResponse.json();
    const feedbackData = feedbackResponse.ok ? await feedbackResponse.json() : { items: [] };
    const sessionsData = sessionsResponse.ok ? await sessionsResponse.json() : { items: [] };
    const auditData = auditResponse.ok ? await auditResponse.json() : { items: [] };
    state.lastRenderPlan = renderPlanResponse.ok ? await renderPlanResponse.json() : null;
    state.reviewFeedback = feedbackData.items || [];
    state.reviewSessions = sessionsData.items || [];
    state.reviewAuditEvents = auditData.items || [];
    renderReviewJobs(state.reviewJobs);
    renderReviewDetail(job, state.reviewFeedback);
  } catch (error) {
    state.reviewSessions = [];
    state.reviewAuditEvents = [];
    state.lastRenderPlan = null;
    renderReviewDetail(null);
    reviewStatusBanner.textContent = `Не удалось открыть запись: ${String(error.message || error)}`;
  }
}

async function updateReviewStatus(status) {
  if (!state.selectedReviewJobId || !state.reviewToken) return;
  reviewStatusBanner.textContent = "Сохраняем статус ревью...";
  try {
    const response = await fetch(`/v1/review/jobs/${state.selectedReviewJobId}`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        ...reviewHeaders(),
      },
      body: JSON.stringify({ review_status: status }),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${response.status}`);
    }
    reviewStatusBanner.textContent = `Статус обновлен: ${formatReviewStatus(status)}.`;
    await loadReviewDashboard();
  } catch (error) {
    reviewStatusBanner.textContent = `Статус не обновлен: ${String(error.message || error)}`;
  }
}

function parseOptionalScore(value) {
  const normalized = String(value || "").trim();
  if (!normalized) return null;
  const numeric = Number(normalized);
  return Number.isFinite(numeric) ? numeric : null;
}

async function saveReviewSession() {
  if (!state.selectedReviewJobId || !state.reviewToken) return;
  const reviewerRole = String(reviewerRoleInput.value || "").trim();
  const reviewerLanguage = String(reviewerLanguageInput.value || "").trim();
  if (!reviewerRole || !reviewerLanguage) {
    reviewSessionStatus.textContent = "Укажите роль и язык ревьюера.";
    return;
  }
  reviewSessionStatus.textContent = "Сохраняем сессию ревью...";
  reviewSessionSubmitButton.disabled = true;
  try {
    const response = await fetch("/v1/review/sessions", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...reviewHeaders(),
      },
      body: JSON.stringify({
        job_id: state.selectedReviewJobId,
        reviewer_role: reviewerRole,
        reviewer_language: reviewerLanguage,
        review_status: String(reviewSessionStatusInput.value || "").trim() || null,
        meaning_score: parseOptionalScore(reviewMeaningScoreInput.value),
        understandability_score: parseOptionalScore(reviewUnderstandabilityScoreInput.value),
        blocking_issue: Boolean(reviewBlockingIssueInput.checked),
        notes: String(reviewSessionNotesInput.value || "").trim() || null,
      }),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${response.status}`);
    }
    reviewSessionStatus.textContent = "Сессия ревью сохранена.";
    reviewSessionNotesInput.value = "";
    reviewBlockingIssueInput.checked = false;
    reviewSessionStatusInput.value = "";
    await loadReviewDashboard();
  } catch (error) {
    reviewSessionStatus.textContent = `Сессия не сохранена: ${String(error.message || error)}`;
  } finally {
    syncReviewActionButtons();
  }
}

async function uploadRenderedVideo() {
  if (!state.selectedReviewJobId || !state.reviewToken) return;
  const file = reviewRenderedVideoInput.files?.[0];
  if (!file) {
    reviewUploadStatus.textContent = "Выберите mp4-файл для загрузки.";
    return;
  }
  if (file.type !== "video/mp4") {
    reviewUploadStatus.textContent = "Поддерживается только mp4.";
    return;
  }
  reviewUploadStatus.textContent = "Загружаем финальный mp4...";
  reviewUploadSubmitButton.disabled = true;
  try {
    const response = await fetch(`/v1/review/jobs/${state.selectedReviewJobId}/rendered-video`, {
      method: "POST",
      headers: {
        "content-type": "video/mp4",
        ...reviewHeaders(),
      },
      body: file,
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${response.status}`);
    }
    reviewRenderedVideoInput.value = "";
    reviewUploadStatus.textContent = "Финальный mp4 прикреплен к записи.";
    await loadReviewDashboard();
  } catch (error) {
    reviewUploadStatus.textContent = `Видео не прикреплено: ${String(error.message || error)}`;
  } finally {
    syncReviewActionButtons();
  }
}

async function savePublishDecision() {
  if (!state.selectedReviewJobId || !state.reviewToken) return;
  reviewPublishStatus.textContent = "Сохраняем финальное решение...";
  reviewPublishSubmitButton.disabled = true;
  try {
    const response = await fetch(`/v1/review/jobs/${state.selectedReviewJobId}/publish-status`, {
      method: "PATCH",
      headers: {
        "content-type": "application/json",
        ...reviewHeaders(),
      },
      body: JSON.stringify({
        publish_status: String(reviewPublishStatusInput.value || "").trim(),
        note: String(reviewPublishNoteInput.value || "").trim() || null,
      }),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Сервис вернул ошибку ${response.status}`);
    }
    reviewPublishStatus.textContent = "Финальное решение сохранено.";
    await loadReviewDashboard();
  } catch (error) {
    reviewPublishStatus.textContent = `Финальное решение не сохранено: ${String(error.message || error)}`;
  } finally {
    syncReviewActionButtons();
  }
}

inputText.addEventListener("input", () => {
  updateCharCount();
  syncDirtyState();
});
resultTranscript.addEventListener("input", syncTranscriptState);
generateButton.addEventListener("click", generatePlan);
clearButton.addEventListener("click", () => {
  inputText.value = "";
  updateCharCount();
  renderEmptyState();
  inputText.focus();
});

document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-language]").forEach((item) => {
      item.classList.toggle("active", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
    setInputLanguage(button.dataset.language);
  });
});

document.querySelectorAll("[data-view-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    state.viewMode = button.dataset.viewMode || "user";
    document.body.classList.toggle("review-mode", state.viewMode === "reviewer");
    document.querySelectorAll("[data-view-mode]").forEach((item) => {
      item.classList.toggle("active", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
    if (state.lastPlan) renderPlan(state.lastPlan);
  });
});

document.querySelectorAll("[data-input-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-input-mode]").forEach((item) => {
      item.classList.toggle("active", item === button);
      item.setAttribute("aria-pressed", String(item === button));
    });
    const audioMode = button.dataset.inputMode === "audio";
    uploadBox.classList.toggle("active", audioMode);
    inputHint.textContent = audioMode
      ? "Выберите аудиофайл. Если распознавание еще не включено, сервис покажет это честно."
      : "Короткие фразы легче проверить и показать по шагам.";
    if (audioMode) uploadBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
});

uploadBox.addEventListener("click", () => audioInput.click());
uploadBox.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  audioInput.click();
});

uploadBox.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadBox.classList.add("active");
});

uploadBox.addEventListener("dragleave", () => {
  if (!document.querySelector("#audioTab").classList.contains("active")) {
    uploadBox.classList.remove("active");
  }
});

uploadBox.addEventListener("drop", (event) => {
  event.preventDefault();
  const [file] = event.dataTransfer.files;
  uploadAudio(file);
});

audioInput.addEventListener("change", () => {
  uploadAudio(audioInput.files[0]);
});

feedbackButtons.forEach((button) => {
  button.addEventListener("click", () => {
    sendFeedback(button.dataset.feedback);
  });
});

settingsButton.addEventListener("click", () => {
  document.querySelector(".sources-panel").scrollIntoView({ behavior: "smooth", block: "start" });
});

reviewButton.addEventListener("click", () => {
  setRoute("review");
});

reviewBackButton.addEventListener("click", () => {
  setRoute("app");
});

reviewLoadButton.addEventListener("click", () => {
  loadReviewDashboard();
});

reviewStatusFilter.addEventListener("change", () => {
  loadReviewDashboard();
});

reviewTokenInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  loadReviewDashboard();
});

reviewStatusActionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    updateReviewStatus(button.dataset.reviewStatusAction);
  });
});

reviewSessionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  saveReviewSession();
});

reviewUploadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  uploadRenderedVideo();
});

reviewPublishForm.addEventListener("submit", (event) => {
  event.preventDefault();
  savePublishDecision();
});

copyAIBriefButton.addEventListener("click", async () => {
  const text = String(aiBriefOutput.value || "").trim();
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    aiBriefSummary.textContent = "Экспортный пакет скопирован в буфер обмена.";
  } catch {
    aiBriefSummary.textContent = "Не удалось скопировать экспортный пакет автоматически.";
  }
});

aiBriefModeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const nextMode = String(button.dataset.briefMode || "");
    if (!nextMode || nextMode === state.aiBriefMode) return;
    state.aiBriefMode = nextMode;
    renderAIBriefData();
  });
});

applyTranscriptButton.addEventListener("click", async () => {
  const nextText = String(resultTranscript.value || "").trim();
  if (!nextText) {
    resultTranscript.focus();
    return;
  }
  inputText.value = nextText;
  updateCharCount();
  syncTranscriptState();
  await generatePlan();
});

fullscreenButton.addEventListener("click", () => {
  setFullscreen(!videoFrame.classList.contains("fullscreen"));
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (!videoFrame.classList.contains("fullscreen")) return;
  setFullscreen(false);
});

playButton.addEventListener("click", () => {
  if (playButton.disabled) return;
  if (previewVideo && !previewVideo.paused) {
    stopPlayback(false);
    return;
  }
  if (previewVideo && previewVideo.ended) {
    previewVideo.currentTime = 0;
    state.playbackProgressMs = 0;
  }
  startPlayback();
});

subtitleToggle.addEventListener("change", () => {
  subtitleBox.hidden = !subtitleToggle.checked;
});

planViewButton.addEventListener("click", () => {
  const compact = timeline.classList.toggle("compact");
  planViewButton.setAttribute("aria-pressed", String(compact));
  planViewButton.textContent = compact ? "Карточки" : "Компактно";
});

speedButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (button.disabled) return;
    const wasPlaying = previewVideo ? !previewVideo.paused : false;
    const progressRatio =
      state.playbackDurationMs > 0 ? state.playbackProgressMs / state.playbackDurationMs : 0;
    setPlaybackSpeed(button.dataset.speed);
    state.playbackProgressMs = progressRatio * state.playbackDurationMs;
    refreshPlaybackUi();
    if (wasPlaying) startPlayback();
  });
});

previewVideo.addEventListener("play", () => {
  videoFrame.classList.add("playing");
  playButton.setAttribute("aria-pressed", "true");
  playButton.setAttribute("aria-label", "Пауза");
});

previewVideo.addEventListener("pause", () => {
  if (!previewVideo.ended) {
    videoFrame.classList.remove("playing");
  }
  playButton.setAttribute("aria-pressed", "false");
  playButton.setAttribute("aria-label", "Воспроизвести");
  state.playbackProgressMs = previewVideo.currentTime * 1000;
  refreshPlaybackUi();
});

previewVideo.addEventListener("timeupdate", () => {
  state.playbackProgressMs = previewVideo.currentTime * 1000;
  state.playbackDurationMs = getPreviewDurationMs();
  refreshPlaybackUi();
});

previewVideo.addEventListener("ended", () => {
  videoFrame.classList.remove("playing");
  playButton.setAttribute("aria-pressed", "false");
  playButton.setAttribute("aria-label", "Воспроизвести");
  state.playbackProgressMs = state.playbackDurationMs;
  refreshPlaybackUi();
});

updateCharCount();
setInputLanguage(state.inputLanguage);
setPlaybackSpeed(state.playbackSpeed);
loadReviewToken();
syncReviewActionButtons();
renderEmptyState();
renderFooterStamp();
renderSources(sampleSources);
loadHealthAndSources();
syncRouteFromLocation();
window.addEventListener("hashchange", syncRouteFromLocation);
})();
