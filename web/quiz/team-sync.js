"use strict";

// Loaded only by the team service. The original browser-local storage is never read or replaced.
(() => {
  const team = {};
  let auth;
  let identityOptions;
  let revision = 0;
  let queue = [];
  let running = null;
  let failure = null;
  let lastDraft = null;
  let carryover = null;
  const params = new URLSearchParams(window.location.search);
  const query = new URLSearchParams();
  if (params.get("group")) query.set("group", params.get("group"));
  query.set("mode", "exam");
  const progressUrl = "/api/progress?" + query;

  function element(tag, text, className) {
    const item = document.createElement(tag);
    if (text !== undefined) item.textContent = text;
    if (className) item.className = className;
    return item;
  }

  function action(text, handler) {
    const control = element("button", text, "button secondary");
    control.type = "button";
    control.addEventListener("click", handler);
    return control;
  }

  async function request(url, data, keepalive = false) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(url, data === undefined ? { signal: controller.signal } : {
        method: "POST", headers: { "Content-Type": "application/json", "X-Exam-Token": auth?.csrf || "" },
        body: JSON.stringify(data), signal: controller.signal, keepalive,
      });
      const result = await response.json();
      if (!response.ok) {
        const error = new Error(result.error || `请求失败 ${response.status}`);
        error.status = response.status;
        throw error;
      }
      return result;
    } finally { clearTimeout(timeout); }
  }

  function status(text, error = false) {
    let banner = document.getElementById("team-save-status");
    if (!banner) {
      banner = element("div", "", "team-save-status");
      banner.id = "team-save-status";
      banner.setAttribute("role", "status");
      document.getElementById("app").before(banner);
    }
    banner.replaceChildren(element("span", text));
    banner.classList.toggle("save-failed", error);
    const inline = document.getElementById("save-status");
    if (inline) inline.textContent = text;
    if (error) {
      banner.append(action("下载本页记录", () => {
        const link = element("a");
        const url = URL.createObjectURL(new Blob([JSON.stringify(lastDraft, null, 2)], { type: "application/json" }));
        link.href = url; link.download = "quiz-unsaved-progress.json";
        document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
      }));
      if (failure?.status !== 409 && failure?.status !== 401 && failure?.status !== 403) {
        banner.append(action("重试保存", () => { failure = null; drain(); }));
      }
      banner.append(action("重新加载服务器进度", () => {
        if (window.confirm("尚未确认保存的内容仍在本页，请先下载记录。确定重新加载服务器进度？")) window.location.reload();
      }));
      if (failure?.status === 409) {
        document.querySelectorAll(".options input").forEach(input => { input.disabled = true; });
        const clear = document.getElementById("clear-answer");
        if (clear) clear.disabled = true;
      }
    }
  }

  function compact(draft) {
    return JSON.parse(JSON.stringify({ version: draft.version, attemptId: draft.attemptId, answers: draft.answers,
      flagged: draft.flagged, index: draft.index, pending: draft.pending || null }));
  }

  function drain() {
    if (running || failure) return running;
    running = (async () => {
      while (queue.length) {
        const entry = queue[0];
        if (entry.revision === undefined) entry.revision = revision;
        status(`正在保存到 ${auth.user.display_name}…`);
        const result = await request(progressUrl, entry);
        revision = result.revision;
        if (lastDraft?.attemptId === entry.draft.attemptId) lastDraft.startedAt = result.startedAt;
        queue.shift();
      }
      status(`✓ 已保存到 ${auth.user.display_name}`);
    })().catch(error => {
      failure = error;
      status(`尚未确认保存：${error.name === "AbortError" ? "请求超时" : error.message}。本页内容保留。`, true);
    }).finally(() => { running = null; });
    return running;
  }

  team.save = draft => {
    lastDraft = draft;
    queue.push({ mutation_id: window.quizUUID(), draft: compact(draft) });
    drain();
  };

  team.flush = async () => {
    while (running || queue.length) {
      if (failure) throw failure;
      await (running || drain());
    }
    if (failure) throw failure;
  };

  team.load = async () => {
    const result = await request(progressUrl);
    revision = result.revision;
    lastDraft = result.draft;
    carryover = result.carryover || null;
    return result.draft;
  };

  team.savedText = () => failure ? "尚未确认保存，请看页面提示" : queue.length ? "正在保存到账号…" : "✓ 进度保存在服务器账号中";
  team.hasConflict = () => failure?.status === 409;
  team.request = request;
  team.heartbeat = payload => request("/api/timing" + (params.get("group") ? `?group=${encodeURIComponent(params.get("group"))}` : ""), payload, true);
  team.user = () => auth.user;
  team.carryover = () => carryover;
  team.rosterOnly = () => Boolean(identityOptions?.passwordless);

  function field(form, label, name, type = "text") {
    const wrapper = element("label", label);
    const input = element("input");
    input.name = name; input.type = type; input.required = true;
    input.autocomplete = name === "username" ? "username" : name === "new_password" ? "new-password" : type === "password" ? "current-password" : "off";
    if (type === "password") { input.minLength = name === "new_password" ? 12 : 1; input.maxLength = 128; }
    wrapper.append(input); form.append(wrapper);
    return input;
  }

  function gate(change = false) {
    return new Promise(resolve => {
      const container = element("section", "", "team-auth");
      container.append(element("h1", change ? "修改密码" : identityOptions?.passwordless ? "管理员登录" : "登录题库"), element("p", change
        ? "初始密码需先修改。新密码至少 12 个字符，修改后其他登录会失效。"
        : identityOptions?.passwordless ? "请输入管理员账号和密码。"
        : "使用管理员分配的账号。作答进度和成绩按账号保存在服务器，可换电脑继续。"));
      const form = element("form");
      const name = change ? null : field(form, "账号", "username");
      const secret = field(form, change ? "旧密码" : "密码", change ? "old_password" : "password", "password");
      const newSecret = change ? field(form, "新密码", "new_password", "password") : null;
      const error = element("p", "", "error-text"); error.setAttribute("role", "alert");
      const submit = element("button", change ? "保存新密码" : "登录", "button primary"); submit.type = "submit";
      form.append(error, submit);
      form.addEventListener("submit", async event => {
        event.preventDefault(); submit.disabled = true; error.textContent = "";
        try {
          auth = await request(change ? "/api/password" : "/api/login", change
            ? { old_password: secret.value, new_password: newSecret.value }
            : { username: name.value, password: secret.value });
          secret.value = ""; if (newSecret) newSecret.value = "";
          if (auth.user.must_change) await gate(true);
          resolve();
        } catch (exception) { error.textContent = exception.message; submit.disabled = false; }
      });
      container.append(form);
      if (!change && identityOptions?.passwordless) {
        container.append(action("返回免密学员入口", async () => { await identityGate(); resolve(); }));
      }
      document.getElementById("app").replaceChildren(container);
    });
  }

  function identityGate() {
    return new Promise(resolve => {
      const container = element("section", "", "team-auth");
      const domain = identityOptions.domain_account;
      container.append(element("h1", "进入题库（免密）"), element("p", domain
        ? `认证入口已验证域账号 ${domain}，将以该身份保存记录。`
        : "请输入名单中的本人完整姓名。名单外的姓名无法登录，进度和成绩按账号保存在服务器。"));
      if (!domain) container.append(element("p", "姓名属于自报身份，请填写自己的姓名。", "team-identity-note"));
      const form = element("form");
      const account = domain ? null : field(form, "姓名", "account");
      if (account) {
        account.maxLength = 128; account.placeholder = "输入姓名"; account.autocomplete = "off";
      }
      const error = element("p", "", "error-text"); error.setAttribute("role", "alert");
      const submit = element("button", "进入并继续考试", "button primary"); submit.type = "submit";
      form.append(error, submit);
      form.addEventListener("submit", async event => {
        event.preventDefault(); submit.disabled = true; error.textContent = "";
        try {
          auth = await request("/api/identify", { account: account?.value || "", computer_name: "" });
          resolve();
        } catch (exception) { error.textContent = exception.message; submit.disabled = false; }
      });
      container.append(form, action("管理员账号登录", async () => { await gate(); resolve(); }));
      document.getElementById("app").replaceChildren(container);
    });
  }

  function userBar() {
    const bar = element("div", "", "team-user-bar");
    const identity = auth.identity;
    bar.append(element("span", identity
      ? `${auth.user.display_name} · ${identity.source === "domain" ? "域认证" : "自报身份"} · ${identity.status === "matched" ? "已归属名单" : "未归属"}`
      : `${auth.user.display_name}（${auth.user.username}）`));
    for (const [text, href] of [["题库", "/"], ["我的记录", "/results"], ...(auth.user.role === "admin" ? [["成绩汇总 / 账号", "/admin"]] : [])]) {
      const link = element("a", text); link.href = href;
      link.addEventListener("click", async event => {
        if (queue.length || running || failure) {
          event.preventDefault();
          try { await team.flush(); window.location.assign(href); } catch { /* Banner already explains recovery. */ }
        }
      });
      bar.append(link);
    }
    if (!identity) bar.append(action("修改密码", async () => {
      try { await team.flush(); window.location.assign("/?password=1"); } catch { /* Keep unsaved work. */ }
    }));
    bar.append(action(identity ? "退出 / 换人" : "退出登录", async () => {
      try { await team.flush(); await request("/api/logout", {}); window.location.replace("/"); }
      catch (error) { status(error.message, true); }
    }));
    document.querySelector(".site-header").after(bar);
  }

  team.initialize = async () => {
    auth = await request("/api/session");
    identityOptions = auth.identity_options;
    if (!auth.user) await (identityOptions?.passwordless ? identityGate() : gate());
    else if (auth.user.must_change || params.get("password") === "1" && !auth.identity) await gate(true);
    userBar();
  };

  window.addEventListener("beforeunload", event => {
    if (queue.length || running || failure) { event.preventDefault(); event.returnValue = ""; }
  });
  document.addEventListener("click", async event => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented || event.ctrlKey || event.metaKey || link.target === "_blank") return;
    const url = new URL(link.href, window.location.href);
    if (url.origin !== window.location.origin || (!queue.length && !running && !failure)) return;
    event.preventDefault();
    try { await team.flush(); window.location.assign(url.href); } catch { /* Keep unsaved work visible. */ }
  }, true);
  window.quizTeam = team;
})();
