"use strict";

(() => {
  const app = document.getElementById("app");
  const notice = document.getElementById("notice");
  const dialog = document.getElementById("submit-dialog");
  const confirmButton = document.getElementById("confirm-submit");
  const cancelButton = document.getElementById("cancel-submit");
  const selectedGroup = new URLSearchParams(window.location.search).get("group");
  const paperQuery = selectedGroup === null ? "" : `?group=${encodeURIComponent(selectedGroup)}`;
  let storageKey = "csharp-course-exam-v1" +
    (selectedGroup === null ? "" : `-${selectedGroup}`);
  const team = window.quizTeam;
  const groupDescriptions = {
    types: "值与引用 · 可空 · 泛型与绑定",
    execution: "资源释放 · LINQ · 异步与取消",
    runtime: "装箱 · 内存视图 · 运行时与并发",
    foundations: "语法与运算 · 数组 · 文本与控制流",
    modeling: "成员与构造 · 接口 · 扩展与回调",
    queries: "查询操作 · 表达式树 · 反射与工具",
  };
  const statusNames = { correct: "正确", wrong: "错答", unanswered: "漏答" };
  let exam;
  let draft = null;
  let carryover = null;
  let view = "intro";
  let reviewFilter = "all";
  let submitting = false;
  let storageAvailable = true;
  let clockAnchor = null;
  let clockAttempt = null;
  let clockClient = null;
  let clockSequence = 0;
  let clientActiveMs = 0;
  let lastHeartbeat = 0;
  let timingQueue = Promise.resolve();
  let timingFailed = false;

  function prepareClock() {
    if (!draft || clockAttempt === draft.attemptId) return;
    clockAttempt = draft.attemptId;
    clockClient = window.quizUUID();
    clockSequence = 0; clientActiveMs = 0; clockAnchor = null;
    // Legacy drafts have no evidence of online time. Preserve answers, never infer it from startedAt.
    if (draft.timingMode !== "online-v1" || !Number.isFinite(draft.elapsedMs) || draft.elapsedMs < 0) draft.elapsedMs = 0;
    draft.timingMode = "online-v1";
    timingFailed = false;
  }

  function sampleClock() {
    prepareClock();
    if (clockAnchor === null || !draft || draft.pending || draft.report) return;
    const now = performance.now(), delta = now - clockAnchor;
    clockAnchor = now;
    // A long callback gap can be sleep or a frozen page, not evidence of online attendance.
    if (delta >= 0 && delta <= 5000) {
      draft.elapsedMs += delta;
      clientActiveMs += delta;
    }
  }

  function timingHint() {
    const hint = document.getElementById("timing-status");
    if (hint) hint.textContent = timingFailed ? "在线用时尚未确认保存，请保持页面联网；作答保存状态见下方。"
      : "仅累计考试页可见的在线时间；关闭或切到后台暂停。";
  }

  function sendTiming() {
    if (!draft || draft.report) return Promise.resolve();
    sampleClock();
    lastHeartbeat = performance.now();
    if (!team) { persist(); return Promise.resolve(); }
    const activeMs = Math.floor(clientActiveMs);
    const payload = { attempt_id: draft.attemptId, client_id: clockClient, sequence: ++clockSequence, active_ms: activeMs };
    const operation = timingQueue.catch(() => {}).then(async () => {
      await team.flush();
      const result = await team.heartbeat(payload);
      if (draft?.attemptId === payload.attempt_id && clockClient === payload.client_id) {
        sampleClock();
        draft.elapsedMs = result.elapsed_ms + Math.max(0, clientActiveMs - activeMs);
        timingFailed = false; timingHint();
      }
    }).catch(error => {
      if (draft?.attemptId === payload.attempt_id && clockClient === payload.client_id) {
        timingFailed = true; timingHint();
      }
      throw error;
    });
    timingQueue = operation;
    operation.catch(() => {}); // Periodic/lifecycle saves report failure in the page, submission awaits it.
    return operation;
  }

  function setView(next) {
    if (view === next) return;
    sampleClock();
    if (view === "exam") sendTiming();
    view = next;
    prepareClock();
    clockAnchor = next === "exam" && !document.hidden && !draft.pending && !draft.report ? performance.now() : null;
    if (clockAnchor !== null) sendTiming();
  }

  document.addEventListener("visibilitychange", () => {
    sampleClock();
    clockAnchor = view === "exam" && !document.hidden && !draft?.pending && !draft?.report ? performance.now() : null;
    if (view === "exam") sendTiming();
  });
  window.addEventListener("pagehide", () => {
    sampleClock(); clockAnchor = null;
    if (view === "exam") sendTiming();
  });
  window.addEventListener("pageshow", () => {
    if (view === "exam" && !document.hidden && !draft?.pending && !draft?.report) {
      clockAnchor = performance.now(); sendTiming();
    }
  });

  function pageUrl(group) {
    const params = new URLSearchParams();
    if (group !== null) params.set("group", group);
    return "/" + (params.size ? `?${params}` : "");
  }

  // Question text is always text, including C# generics and strings containing HTML.
  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
  }

  function rich(element, text) {
    String(text).split(/(`[^`]+`)/g).forEach(part => {
      element.append(part.startsWith("`") && part.endsWith("`")
        ? node("code", "inline-code", part.slice(1, -1)) : document.createTextNode(part));
    });
    return element;
  }

  function button(text, className, action) {
    const element = node("button", `button ${className}`, text);
    element.type = "button";
    element.addEventListener("click", action);
    return element;
  }

  function showNotice(text) {
    notice.textContent = text;
    notice.hidden = !text;
  }

  function persist() {
    sampleClock();
    if (team) { team.save(draft); return; }
    try {
      localStorage.setItem(storageKey, JSON.stringify(draft));
      storageAvailable = true;
    } catch {
      storageAvailable = false;
      showNotice("浏览器无法暂存作答，请保持此页面打开并完成交卷。报告仍可下载保存。");
    }
  }

  function readDraft(remoteDraft = null) {
    try {
      const raw = team ? (remoteDraft ? JSON.stringify(remoteDraft) : null) : localStorage.getItem(storageKey);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (!saved || typeof saved !== "object" || !saved.answers || typeof saved.answers !== "object" ||
          Array.isArray(saved.answers) || !Array.isArray(saved.flagged) ||
          !Number.isFinite(saved.startedAt) || typeof saved.attemptId !== "string") throw new Error("invalid draft");
      draft = saved;
      if (draft.version === exam.version) {
        const ids = new Set(exam.questions.map(q => q.id));
        if (Object.entries(draft.answers).some(([id, answer]) => !ids.has(id) || typeof answer !== "string" || !/^[ABCD]$/.test(answer))) throw new Error("invalid answers");
        draft.flagged = draft.flagged.filter(id => ids.has(id));
        draft.index = Number.isInteger(draft.index) ? Math.max(0, Math.min(exam.total - 1, draft.index)) : 0;
      }
    } catch {
      draft = null;
      showNotice("无法读取旧草稿。已交卷成绩仍保存在原报告或账号记录中。");
    }
  }

  function legacyPracticeRecords() {
    if (team) return null;
    const section = node("details", "practice-archives");
    const entries = [];
    try {
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        if (!key.startsWith("csharp-course-practice-v1")) continue;
        const raw = localStorage.getItem(key);
        const item = node("p", "archive-entry");
        item.append(node("span", "", key + " "), button("下载历史练习 JSON", "secondary", () =>
          download(raw, key + ".json", "application/json")));
        entries.push(item);
      }
    } catch { showNotice("无法读取历史练习列表；已经下载的文件仍可保留。"); }
    if (!entries.length) return null;
    section.append(node("summary", "", `历史练习记录（仅下载）· ${entries.length} 份`), ...entries);
    return section;
  }

  function legacyExamRecords() {
    if (team || exam.selected_group !== "combined") return null;
    const section = node("details", "exam-archives"), entries = [];
    try {
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        if (!key.startsWith("csharp-course-exam-v1") || key === storageKey) continue;
        const raw = localStorage.getItem(key), item = node("p", "archive-entry");
        item.append(node("span", "", key + " "), button("下载历史考试 JSON", "secondary", () => download(raw, key + ".json", "application/json")));
        try {
          const previous = JSON.parse(raw);
          if (previous.report?.questions?.length) item.append(button("查看历史报告", "secondary", () => reportView(previous.report)));
        } catch { /* Preserve malformed historical data as a raw download. */ }
        entries.push(item);
      }
    } catch { showNotice("无法读取历史考试列表，已下载的记录仍可保留。"); }
    if (!entries.length) return null;
    section.append(node("summary", "", `历史考试记录 · ${entries.length} 份`), ...entries);
    return section;
  }

  function localCarryover() {
    if (exam.selected_group !== "combined") return null;
    const answers = {}, flagged = new Set();
    for (const [name, version] of Object.entries(exam.previous_versions)) {
      try {
        const previous = JSON.parse(localStorage.getItem("csharp-course-exam-v1" + (name === "microsoft" ? "-microsoft" : "")));
        if (!previous || previous.report || previous.version !== version) continue;
        const ids = new Set(exam.questions.filter(q => q.group.startsWith("microsoft-") === (name === "microsoft")).map(q => q.id));
        Object.entries(previous.answers || {}).forEach(([id, answer]) => { if (ids.has(id) && typeof answer === "string" && /^[ABCD]$/.test(answer)) answers[id] = answer; });
        (previous.flagged || []).forEach(id => { if (ids.has(id)) flagged.add(id); });
      } catch { /* Historical data remains available for download. */ }
    }
    return Object.keys(answers).length || flagged.size ? { answers, flagged: [...flagged] } : null;
  }

  function elapsed() {
    sampleClock();
    return draft ? Math.floor(draft.elapsedMs / 1000) : 0;
  }

  function duration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const rest = seconds % 60;
    return (hours ? `${String(hours).padStart(2, "0")}:` : "") +
      `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
  }

  function formatScore(value) {
    return Number.isInteger(value) ? String(value) : Number(value).toFixed(1);
  }

  function download(text, filename, mime) {
    const url = URL.createObjectURL(new Blob([text], { type: mime }));
    const link = node("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  function intro() {
    setView("intro");
    const shell = node("section", "intro");
    const top = node("div", "intro-top");
    const copy = node("div");
    copy.append(node("p", "eyebrow", "ASSESSMENT / 01"), node("h1", "", exam.title),
      node("p", "intro-copy", exam.selected_group === "microsoft"
        ? "本课程自编的 Microsoft Learn C# 配套试卷。120 道单选覆盖 12 个学习单元；交卷后直接查看所有题目的答案、推导与逐项解析。"
        : exam.intro || "检查 C# 的语义差异与工程边界。交卷后直接查看所有题目的解析。"));
    const stats = node("div", "intro-stats");
    [[exam.total, "道", "全部单选"], [100, "分", "百分制成绩"], ["不限", "时", "记录答题用时"]].forEach(([value, unit, label]) => {
      const item = node("div"); const number = node("strong", "", value);
      number.append(node("small", "", unit)); item.append(number, node("span", "", label)); stats.append(item);
    });
    copy.append(stats);
    const actions = node("div", "actions");
    const compatible = draft?.version === exam.version;
    if (compatible && draft.report) {
      actions.append(button("查看上次报告", "primary large", () => reportView(draft.report)), button("再考一次", "secondary large", start));
    } else if (compatible) {
      actions.append(button(draft.pending ? "继续交卷" : `继续考试 · 已答 ${Object.keys(draft.answers).length} 题`, "primary large", () => {
        renderExam(); if (draft.pending) openSubmit();
      }), button("重新开始", "secondary", () => {
        if (window.confirm(team ? "服务器会保留本轮草稿，再建立新一轮。是否继续？" : "重新开始会替换当前未完成草稿。是否继续？")) start();
      }));
    } else {
      actions.append(button(carryover ? `开始考试 · 接续已答 ${Object.keys(carryover.answers).length} 题` : "开始考试  →", "primary large", start));
      if (draft) {
        showNotice("题库已更新，旧作答不会用于新试卷。可先下载旧草稿，再开始本次考试。");
        actions.append(button("下载旧作答", "secondary", () => download(JSON.stringify(draft, null, 2), "csharp-previous-attempt.json", "application/json")));
        if (draft.report) actions.append(button("查看旧报告", "secondary", () => reportView(draft.report)));
      }
    }
    copy.append(actions, node("p", "save-caption", team
      ? "进度按账号保存在服务器；请确认保存成功再关闭页面，可换电脑登录继续。"
      : "作答自动暂存在当前浏览器；交卷后可下载完整报告。"));
    copy.append(node("p", "save-caption", "在线用时只累计考试页可见的时间，关闭或切到后台暂停。"));
    const scope = node("aside", "scope-card"); const heading = node("div", "scope-heading");
    heading.append(node("h3", "", "本次试卷"), node("span", "pill", `${exam.total} 道单选`)); scope.append(heading);
    exam.groups.forEach((group, index) => {
      const item = node("div", "scope-item");
      const title = node("div"); title.append(node("span", "scope-number", String(index + 1).padStart(2, "0")), node("h3", "", group.label));
      item.append(title, node("p", "", groupDescriptions[group.id] || "每单元 10 题"), node("span", "scope-count", `${group.count} 题`)); scope.append(item);
    });
    top.append(copy, scope);
    const selection = node("section", "paper-selection"); selection.setAttribute("aria-label", "选择试卷");
    selection.append(node("h2", "", "选择试卷"), node("p", "muted", "历史独立试卷入口。"));
    const links = node("div", "paper-links");
    exam.papers.forEach(paper => {
      const label = paper.id === null ? "扩展题" : paper.id === "microsoft" ? "基础题" : paper.label;
      const link = node("a", "paper-link", `${label} · ${paper.count} 题`); link.href = pageUrl(paper.id);
      if (paper.id === exam.selected_group) link.setAttribute("aria-current", "page"); links.append(link);
    });
    selection.append(links);
    const rules = node("div", "rules");
    [["按工程场景判断", "可跳题、修改选择和标记稍后检查。交卷前隐藏答案与解析。"],
      ["统一交卷后计分", `每题 1 分，错答或漏答为 0 分；原始满分 ${exam.total} 分，按比例换算百分制。`],
      ["直接查看所有解析", "交卷后展示全部题目的答案、知识点规则、推导、适用边界和四项辨析，包括错答与漏答。"]].forEach(([title, text], index) => {
      const item = node("div"); item.append(node("span", "rule-index", `0${index + 1} /`), node("h3", "", title), node("p", "", text)); rules.append(item);
    });
    shell.append(top);
    if (exam.papers.length > 1) shell.append(selection);
    shell.append(rules);
    const old = legacyPracticeRecords(); if (old) shell.append(old);
    const previous = legacyExamRecords(); if (previous) shell.append(previous);
    app.replaceChildren(shell);
  }

  function start() {
    setView("intro");
    const restored = !draft && carryover;
    draft = { version: exam.version, attemptId: window.quizUUID(), startedAt: Date.now(), elapsedMs: 0, timingMode: "online-v1", answers: {}, flagged: [], index: 0, report: null, pending: null };
    if (restored) {
      draft.answers = { ...restored.answers }; draft.flagged = [...restored.flagged];
      const next = exam.questions.findIndex(q => !draft.answers[q.id]); draft.index = next < 0 ? 0 : next;
    }
    carryover = null;
    showNotice(""); persist(); renderExam();
  }

  function progress(percent) {
    const track = node("div", "progress-track");
    const fill = node("span");
    fill.style.width = `${percent}%`;
    track.append(fill);
    return track;
  }

  function navigate(index) {
    draft.index = index;
    persist();
    renderExam();
    document.getElementById("question-title").focus({ preventScroll: true });
    if (window.innerWidth <= 680) document.querySelector(".question-card").scrollIntoView({ behavior: "instant", block: "start" });
  }

  function questionContent(container, question) {
    if (question.scenario) container.append(rich(node("p", "scenario"), question.scenario));
    container.append(rich(node("p", "prompt"), question.prompt));
    if (question.compile_error) container.append(node("p", "compile-note", "编译判断题 · 以下代码为故意保留的负向样例。"));
    question.code.forEach(code => {
      const pre = node("pre", "code-block");
      pre.append(node("code", "", code));
      container.append(pre);
    });
  }

  function validExplanation(value) {
    return value && typeof value.principle === "string" && typeof value.boundary === "string" &&
      Array.isArray(value.steps) && value.steps.length >= 2 && value.steps.every(step => typeof step === "string");
  }

  function navigatorPanel() {
    const panel = node("aside", "navigator");
    panel.setAttribute("aria-label", "答题卡");
    const count = Object.keys(draft.answers).length;
    const label = node("div", "progress-label");
    label.append(node("span", "", "答题进度"), node("strong", "", `${count} / ${exam.total}`));
    panel.append(label, progress(count / exam.total * 100));
    const groups = node("div", "nav-groups");
    exam.groups.forEach(group => {
      const section = node("div", "nav-group");
      section.append(node("h3", "", group.label));
      const grid = node("div", "question-grid");
      exam.questions.forEach((question, index) => {
        if (question.group !== group.id) return;
        const displayId = question.display_id || question.id;
        const tile = node("button", "", displayId.slice(1));
        tile.dataset.questionId = question.id;
        const answered = Boolean(draft.answers[question.id]);
        const flagged = draft.flagged.includes(question.id);
        tile.classList.toggle("answered", answered);
        tile.classList.toggle("current", index === draft.index);
        tile.classList.toggle("flagged", flagged);
        const state = answered ? "已答" : "未答";
        tile.setAttribute("aria-label", `${displayId} ${state}${flagged ? " 待检查" : ""}`);
        if (index === draft.index) tile.setAttribute("aria-current", "step");
        tile.addEventListener("click", () => navigate(index));
        grid.append(tile);
      });
      section.append(grid);
      groups.append(section);
    });
    const legend = node("div", "nav-legend");
    legend.append(node("span", "done", "已答"));
    legend.append(node("span", "", "未答"), node("span", "flag", "待检查"));
    panel.append(groups, legend, button(draft.pending ? "重试交卷" : "检查并交卷",
      "primary", openSubmit));
    return panel;
  }

  function renderExam() {
    setView("exam");
    const question = exam.questions[draft.index];
    const shell = node("section", "exam-shell");
    const top = node("div", "exam-topline");
    const title = node("div");
    title.append(node("p", "eyebrow", "SINGLE CHOICE / 单选考试"), node("h1", "", exam.title));
    const timer = node("div", "time-box");
    const clock = node("strong", "", duration(elapsed()));
    clock.id = "clock";
    const hint = node("small", "", "仅累计考试页可见的在线时间；关闭或切到后台暂停。");
    hint.id = "timing-status";
    timer.append(node("span", "", "在线答题用时"), clock, hint);
    top.append(title, timer);
    const layout = node("div", "exam-layout");
    layout.append(navigatorPanel());
    const card = node("article", "question-card");
    const heading = node("div", "question-heading");
    const meta = node("div", "question-meta");
    meta.append(node("span", "question-id", question.display_id || question.id), node("span", "pill", `第 ${draft.index + 1} / ${exam.total} 题`), node("span", "pill", question.tier === "core" ? "核心" : "深入"));
    const flag = node("button", "flag-button", draft.flagged.includes(question.id) ? "● 已标记" : "○ 标记待检查");
    flag.setAttribute("aria-pressed", String(draft.flagged.includes(question.id)));
    flag.addEventListener("click", () => {
      draft.flagged = draft.flagged.includes(question.id) ? draft.flagged.filter(id => id !== question.id) : [...draft.flagged, question.id];
      persist();
      renderExam();
    });
    heading.append(meta, flag);
    const questionTitle = node("h2", "", question.title);
    questionTitle.id = "question-title";
    questionTitle.tabIndex = -1;
    card.append(heading, questionTitle);
    questionContent(card, question);
    const options = node("fieldset", "options");
    options.append(node("legend", "", "请选择一个答案"));
    const answersLocked = Boolean(draft.pending) || Boolean(team?.hasConflict());
    options.disabled = answersLocked;
    Object.entries(question.options).forEach(([letter, text]) => {
      const label = node("label", "option");
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "answer";
      input.value = letter;
      input.checked = draft.answers[question.id] === letter;
      input.disabled = answersLocked;
      input.addEventListener("change", () => {
        draft.answers[question.id] = letter;
        persist();
        // Keep the focused radio mounted so keyboard arrow navigation remains native.
        const previous = document.querySelector(".navigator");
        previous.replaceWith(navigatorPanel());
        document.getElementById("clear-answer").disabled = false;
        document.getElementById("save-status").textContent = team ? team.savedText() : storageAvailable ? "✓ 作答已暂存" : "本页暂存，关闭将丢失";
      });
      label.append(input, node("span", "option-letter", letter), rich(node("span", "option-text"), text));
      options.append(label);
    });
    const clear = button("清除本题选择", "text-button", () => {
      delete draft.answers[question.id];
      persist();
      renderExam();
    });
    clear.id = "clear-answer";
    clear.disabled = !draft.answers[question.id] || answersLocked;
    card.append(options, clear);
    const footer = node("div", "question-footer");
    const saved = node("span", "saved-status", team ? team.savedText() : draft.pending ? "交卷内容已固定，可重试提交" : storageAvailable ? "✓ 作答自动暂存" : "本页暂存，关闭将丢失");
    saved.id = "save-status";
    const controls = node("div", "actions");
    const prev = button("← 上一题", "secondary", () => navigate(draft.index - 1));
    prev.disabled = draft.index === 0;
    controls.append(prev, draft.index < exam.total - 1
      ? button("下一题 →", "primary", () => navigate(draft.index + 1))
      : button("检查并交卷", "primary", openSubmit));
    footer.append(saved, controls);
    card.append(footer);
    layout.append(card);
    shell.append(top, layout, button("← 返回考试首页", "text-button", intro));
    app.replaceChildren(shell);
  }

  function openSubmit() {
    const unanswered = exam.total - Object.keys(draft.answers).length;
    const flagged = draft.flagged.length;
    document.getElementById("submit-summary").textContent = draft.pending
      ? "上次交卷尚未收到确认。重试会恢复同一份报告，不会重复计分。"
      : `已作答 ${exam.total - unanswered} / ${exam.total} 题${unanswered ? `，还有 ${unanswered} 题未答（计 0 分）` : "，没有漏题"}${flagged ? `；${flagged} 题标记待检查` : ""}。`;
    document.getElementById("submit-error").hidden = true;
    confirmButton.textContent = draft.pending ? "重试交卷" : "确认交卷";
    confirmButton.disabled = false;
    cancelButton.hidden = Boolean(draft.pending);
    if (!dialog.open) dialog.showModal();
  }

  cancelButton.addEventListener("click", () => {
    dialog.close();
    const first = exam.questions.findIndex(q => !draft.answers[q.id]);
    if (first >= 0) navigate(first);
  });
  dialog.addEventListener("cancel", event => {
    if (submitting) event.preventDefault();
  });

  confirmButton.addEventListener("click", async () => {
    if (submitting) return;
    const clockFlush = sendTiming();
    if (!draft.pending) {
      draft.pending = { version: exam.version, attempt_id: draft.attemptId, answers: { ...draft.answers }, elapsed_seconds: elapsed() };
      persist();
    }
    clockAnchor = null;
    submitting = true;
    confirmButton.disabled = true;
    confirmButton.textContent = "正在生成报告…";
    cancelButton.hidden = true;
    const errorBox = document.getElementById("submit-error");
    errorBox.hidden = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      if (team) await team.flush();
      await clockFlush;
      const response = await fetch("/api/submit" + paperQuery, {
        method: "POST", headers: { "Content-Type": "application/json", "X-Exam-Token": exam.token },
        body: JSON.stringify(draft.pending), signal: controller.signal,
      });
      const report = await response.json();
      if (!response.ok) throw new Error(report.error || "交卷失败，请重试。");
      draft.report = report;
      persist();
      dialog.close();
      reportView(report);
      window.scrollTo(0, 0);
    } catch (error) {
      errorBox.textContent = `未能确认交卷：${error.name === "AbortError" ? "等待服务响应超时" : error.message}。作答已保留。请确认考试服务仍在运行；若服务重启，请刷新页面后继续交卷。`;
      errorBox.hidden = false;
      confirmButton.textContent = "重试交卷";
      confirmButton.disabled = false;
      renderExam();
    } finally {
      clearTimeout(timeout);
      submitting = false;
    }
  });

  function externalLink(title, url) {
    const link = node("a", "", title);
    // Stored reports are data, not trusted executable markup or arbitrary protocols.
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "https:") return node("span", "", title);
      // Private course references remain readable labels, including in historical reports.
      if (parsed.hostname === "github.com" && /^\/ximicpp\/csharp-for-cpp-python(?:\/|$)/i.test(parsed.pathname)) return node("span", "", title);
      link.href = parsed.href;
    } catch { return node("span", "", title); }
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  }

  function answerExplanation(body, question) {
    body.append(node("p", "review-answer", `你的答案：${question.selected || "未作答"}　 ·　 正确答案：${question.answer}`));
    if (validExplanation(question.explanation)) {
      const teaching = node("section", "answer-teaching");
      teaching.setAttribute("aria-label", "知识点与推导");
      teaching.append(node("h3", "", "知识点规则"), rich(node("p"), question.explanation.principle),
        node("h3", "", "本题推导"));
      const steps = node("ol", "reasoning-steps");
      question.explanation.steps.forEach(step => steps.append(rich(node("li"), step)));
      teaching.append(steps, node("h3", "", "适用边界"), rich(node("p"), question.explanation.boundary));
      body.append(teaching);
    }
    body.append(node("h3", "", "逐项辨析"));
    Object.entries(question.options).forEach(([letter, text]) => {
      const option = node("div", `review-option${letter === question.answer ? " correct" : letter === question.selected ? " wrong" : ""}`);
      option.append(rich(node("div"), `${letter}. ${text}${letter === question.answer ? "　✓ 正确项" : ""}`), rich(node("p"), question.rationale[letter]));
      body.append(option);
    });
    body.append(rich(node("div", "takeaway"), question.takeaway));
    const learn = node("div", "reference-links");
    learn.append(node("span", "muted", "相关学习内容"));
    question.learn.forEach(link => learn.append(externalLink(link.title, link.url)));
    const sources = node("div", "reference-links");
    sources.append(node("span", "muted", "官方依据"));
    question.sources.forEach(link => sources.append(externalLink(link.title, link.url)));
    body.append(learn, sources);
  }

  function reviewQuestion(question) {
    const item = node("details", "review-item");
    item.open = true;
    item.id = `review-${question.id}`;
    const summary = node("summary");
    summary.append(node("span", `status-badge status-${question.status}`, statusNames[question.status]), node("span", "question-id", question.display_id || question.id), node("span", "", question.title));
    const body = node("div", "review-body");
    questionContent(body, question);
    answerExplanation(body, question);
    item.append(summary, body);
    return item;
  }

  function lessonsView(lessons, report, openQuestion, supplementMarkdown) {
    const section = node("section", "report-section lessons");
    const heading = node("div", "section-heading");
    heading.append(node("h2", "", "每套题的讲解"));
    if (supplementMarkdown) heading.append(button("下载讲解 .md", "secondary", () =>
      download(supplementMarkdown, `csharp-lessons-${report.attempt_id}.md`, "text/markdown;charset=utf-8")));
    section.append(heading, node("p", "muted", "按主题理解这些判断，再点击相关题号回看自己的答案。"));
    const byId = new Map(report.questions.map(question => [question.id, question]));
    lessons.forEach(lesson => {
      const group = node("details", "review-item lesson-group");
      group.id = `lesson-${lesson.group}`;
      const summary = node("summary");
      summary.append(node("strong", "", lesson.title), node("span", "muted", `${lesson.sections.length} 个主题`));
      const body = node("div", "review-body lesson-body");
      body.append(rich(node("p", "lesson-intro"), lesson.intro));
      lesson.sections.forEach(topic => {
        const block = node("section", "lesson-topic");
        block.id = `lesson-${lesson.group}-${topic.questions[0]}`;
        block.tabIndex = -1;
        block.append(node("h3", "", topic.title));
        const questions = node("div", "lesson-questions");
        topic.questions.forEach(id => {
          const question = byId.get(id);
          if (!question) return;
          questions.append(button(`${question.display_id || id} · ${statusNames[question.status]}`, `lesson-question status-${question.status}`,
            () => openQuestion(id)));
        });
        block.append(questions);
        topic.code.forEach(code => {
          const pre = node("pre", "code-block");
          pre.append(node("code", "", code));
          block.append(pre);
        });
        block.append(rich(node("p", "lesson-result"), `观察与边界：${topic.result}`));
        topic.explanation.forEach(text => block.append(rich(node("p"), text)));
        block.append(rich(node("div", "takeaway"), `工程判断：${topic.takeaway}`));
        const sources = node("div", "reference-links");
        sources.append(node("span", "muted", "官方依据"));
        topic.sources.forEach(link => sources.append(externalLink(link.title, link.url)));
        block.append(sources);
        body.append(block);
      });
      group.append(summary, body);
      section.append(group);
    });
    return section;
  }

  function legacyLessons(report) {
    const section = node("section", "report-section");
    section.append(node("h2", "", "每套题的讲解"), node("p", "muted", "这份报告生成较早，可单独加载本卷讲解；原报告和分数保留。"));
    const message = node("p", "muted");
    message.setAttribute("role", "status");
    const load = button("加载本卷讲解", "secondary", async () => {
      load.disabled = true;
      message.textContent = "正在加载讲解…";
      try {
        const payload = { version: report.version, attempt_id: report.attempt_id,
          answers: Object.fromEntries(report.questions.filter(q => q.selected !== null).map(q => [q.id, q.selected])),
          elapsed_seconds: report.elapsed_seconds };
        const response = await fetch("/api/lessons" + paperQuery, { method: "POST",
          headers: { "Content-Type": "application/json", "X-Exam-Token": exam.token }, body: JSON.stringify(payload) });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "加载失败，请重试。");
        if (draft?.report?.attempt_id === report.attempt_id) {
          draft.lessonSupplement = { attemptId: report.attempt_id, ...result };
          persist();
        }
        if (section.isConnected) {
          reportView(report);
          document.querySelector(".lessons").scrollIntoView({ behavior: "smooth", block: "start" });
        }
      } catch (error) {
        message.textContent = `${error.message} 已有报告仍可查看和下载。`;
        load.disabled = false;
      }
    });
    section.append(load, message);
    return section;
  }

  function reportView(report) {
    setView("report");
    reviewFilter = "all";
    const supplement = draft?.lessonSupplement?.attemptId === report.attempt_id ? draft.lessonSupplement : null;
    const shell = node("section", "report-shell");
    const heading = node("div", "report-heading");
    const title = node("div");
    title.append(node("p", "eyebrow", "ASSESSMENT REPORT"), node("h1", "", "本次考试报告"), node("p", "", `${new Date(report.submitted_at).toLocaleString("zh-CN", { hour12: false })}　 ·　 ${report.timing_mode === "online-v1" ? "在线用时" : "用时（旧计时）"} ${duration(report.elapsed_seconds)}`));
    const actions = node("div", "actions");
    const filename = `csharp-exam-${report.attempt_id}`;
    actions.append(button("下载报告 .md", "primary", () => download(report.markdown, `${filename}.md`, "text/markdown;charset=utf-8")),
      button("下载数据 .json", "secondary", () => download(JSON.stringify(report, null, 2), `${filename}.json`, "application/json")),
      button("返回首页", "secondary", intro));
    heading.append(title, actions);
    const grid = node("div", "report-grid");
    const score = node("div", "score-card");
    score.append(node("p", "eyebrow", "YOUR SCORE / 百分制"));
    const value = node("div", "score-value", formatScore(report.percent));
    value.append(node("small", "", "/ 100"));
    const counts = node("div", "score-counts");
    [[report.correct, "答对"], [report.wrong, "错答"], [report.unanswered, "漏答"]].forEach(([number, label]) => {
      const cell = node("div");
      cell.append(node("strong", "", number), node("span", "", label));
      counts.append(cell);
    });
    score.append(value, node("div", "raw-score", `原始得分 ${report.score} / ${report.total} · 每题 1 分`), counts);
    const groups = node("div", "group-report");
    groups.append(node("h2", "", exam.selected_group === "combined" ? "本卷各章节的表现" : exam.selected_group === "microsoft" ? "本卷各单元的表现" : "本卷各方向的表现"));
    report.groups.forEach(group => {
      const row = node("div", "group-result");
      const label = node("div", "progress-label");
      label.append(node("span", "", group.label), node("strong", "", `${group.correct} / ${group.total} · ${formatScore(group.percent)}%`));
      row.append(label, progress(group.percent), node("div", "group-breakdown", `错答 ${group.wrong} 题 · 漏答 ${group.unanswered} 题`));
      if (report.lessons?.length || supplement) row.append(button(group.lesson_group ? "查看本单元讲解" : "查看本套讲解", "text-button", () => {
        const lesson = document.getElementById(`lesson-${group.lesson_group || group.id}`);
        if (!lesson) return;
        lesson.open = true;
        const firstQuestion = report.questions.find(question => question.group === group.id)?.id;
        const topic = group.lesson_group && document.getElementById(`lesson-${group.lesson_group}-${firstQuestion}`);
        const target = topic || lesson.querySelector("summary");
        target.focus({ preventScroll: true });
        (topic || lesson).scrollIntoView({ behavior: "smooth", block: "start" });
      }));
      groups.append(row);
    });
    grid.append(score, groups);
    shell.append(heading, grid);
    const weak = report.questions.filter(q => q.status !== "correct");
    const recommendations = new Map();
    weak.forEach(question => question.learn.forEach(link => {
      const current = recommendations.get(link.url) || { ...link, count: 0 };
      current.count += 1;
      recommendations.set(link.url, current);
    }));
    if (recommendations.size) {
      const section = node("section", "report-section");
      const header = node("div", "section-heading");
      header.append(node("h2", "", "接下来，优先复习这些内容"));
      const links = node("div", "review-links");
      [...recommendations.values()].sort((a, b) => b.count - a.count).forEach(link => {
        const element = externalLink(link.title, link.url);
        element.append(node("span", "", `${link.count} 道相关错题 / 漏题`));
        links.append(element);
      });
      section.append(header, links);
      shell.append(section);
    }
    const review = node("section", "report-section");
    const reviewHeader = node("div", "section-heading");
    reviewHeader.append(node("h2", "", "回看每一次判断"));
    const filters = node("div", "filters");
    const rows = node("div");
    rows.id = "review-questions";
    const renderRows = () => {
      const questions = report.questions.filter(q => reviewFilter === "all" ||
        (reviewFilter === "incorrect" ? q.status !== "correct" : q.status === "unanswered"));
      rows.replaceChildren(...questions.map(reviewQuestion));
      if (!questions.length) rows.append(node("div", "empty-state", reviewFilter === "incorrect" ? "本次没有错题或漏题。切换“全部”可查看完整解析。" : "本次没有漏答题。"));
    };
    [["incorrect", `错题与漏题 ${weak.length}`], ["unanswered", `漏题 ${report.unanswered}`], ["all", `全部 ${report.total}`]].forEach(([filter, label]) => {
      const control = node("button", "", label);
      control.setAttribute("aria-pressed", String(reviewFilter === filter));
      control.addEventListener("click", () => {
        reviewFilter = filter;
        [...filters.children].forEach(other => other.setAttribute("aria-pressed", String(other === control)));
        renderRows();
      });
      filters.append(control);
    });
    reviewHeader.append(filters);
    renderRows();
    review.append(reviewHeader, rows);
    const openQuestion = id => {
      reviewFilter = "all";
      [...filters.children].forEach(control => control.setAttribute("aria-pressed", String(control.textContent.startsWith("全部"))));
      renderRows();
      const item = document.getElementById(`review-${id}`);
      if (!item) return;
      item.open = true;
      item.querySelector("summary").focus({ preventScroll: true });
      item.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    shell.append(report.lessons?.length ? lessonsView(report.lessons, report, openQuestion)
      : supplement ? lessonsView(supplement.lessons, report, openQuestion, supplement.markdown)
      : legacyLessons(report));
    shell.append(review, node("p", "report-footnote", `报告已保存：${report.files.json} / ${report.files.markdown}。学习进度未自动更改。`));
    app.replaceChildren(shell);
  }

  setInterval(() => {
    sampleClock();
    const clock = document.getElementById("clock");
    if (clock && view === "exam") clock.textContent = duration(elapsed());
    timingHint();
    if (clockAnchor !== null && performance.now() - lastHeartbeat >= 15000) sendTiming();
  }, 1000);

  async function initialize() {
    try {
      if (team) await team.initialize();
      const response = await fetch("/api/exam" + paperQuery);
      if (!response.ok) throw new Error(`题库服务返回 ${response.status}`);
      exam = await response.json();
      storageKey = "csharp-course-exam-v1" + (exam.selected_group ? "-" + exam.selected_group : "");
      document.title = exam.title;
      const brand = document.querySelector(".brand");
      brand.href = pageUrl(null);
      brand.setAttribute("aria-label", "考试首页");
      readDraft(team ? await team.load() : null);
      carryover = !draft ? (team ? team.carryover() : localCarryover()) : null;
      if (draft?.version === exam.version && draft.report) reportView(draft.report);
      else intro();
    } catch (error) {
      const failure = node("div", "empty-state");
      failure.append(node("h2", "", "暂时无法加载试卷"), node("p", "", `${error.message}。${team ? "请重新加载或联系管理员检查服务。" : "请保持本地考试服务运行。"}`), button("重新加载", "primary", initialize));
      app.replaceChildren(failure);
    }
  }
  initialize();
})();
