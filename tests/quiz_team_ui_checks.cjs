"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");
const root = path.resolve(__dirname, "..");
const { JSDOM } = require(require.resolve("jsdom", { paths: [path.join(root, ".tools/ui-tests")] }));
const html = fs.readFileSync(path.join(root, "web/quiz/index.html"), "utf8");
const syncScript = fs.readFileSync(path.join(root, "web/quiz/team-sync.js"), "utf8");
const appScript = fs.readFileSync(path.join(root, "web/quiz/app.js"), "utf8");
const idScript = fs.readFileSync(path.join(root, "web/quiz/id.js"), "utf8");
const resultsScript = fs.readFileSync(path.join(root, "web/quiz/team-results.js"), "utf8");
const resultsHtml = fs.readFileSync(path.join(root, "web/quiz/team-results.html"), "utf8");
const rosterNames = JSON.parse(fs.readFileSync(path.join(root, "data/quiz-team-roster.example.json"), "utf8")).members.map(member => member.name);
const fixture = spawnSync(process.env.PYTHON || "python", ["-c", `
import json,sys
sys.path.insert(0,'scripts')
from quiz_exam import Exam
p=Exam()
print(json.dumps(p.public(),ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 4 * 1024 * 1024 });
assert.equal(fixture.status, 0, fixture.stderr);
const exam = JSON.parse(fixture.stdout);
const combinedProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json,sys
sys.path.insert(0,'scripts')
from quiz_exam import Exam
print(json.dumps(Exam(selected_group='combined').public(),ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
assert.equal(combinedProcess.status, 0, combinedProcess.stderr);
const combined = JSON.parse(combinedProcess.stdout);
const clone = value => JSON.parse(JSON.stringify(value));
const auth = { user: { id: 1, username: "alice", display_name: "甲", role: "student", must_change: 0 }, csrf: "csrf-account-specific" };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => clone(data) });
async function until(condition) {
  for (let i = 0; i < 100; i++) { if (condition()) return; await new Promise(resolve => setTimeout(resolve, 10)); }
  assert.fail("Expected UI state did not appear");
}
async function page(t, { remote = null, revision = 0, save, insecureHttp = false, paper = exam, carryover = null, timing, controlledClock = false } = {}) {
  const dom = new JSDOM(html, { url: insecureHttp ? "http://192.168.1.2:8080/" : "https://quiz.test/", runScripts: "outside-only", pretendToBeVisual: true });
  t.after(() => dom.window.close());
  const { window } = dom;
  const document = window.document;
  let onlineNow = 0, hidden = false;
  const ticks = [], timingCalls = [];
  if (controlledClock) {
    window.performance.now = () => onlineNow;
    window.setInterval = callback => { ticks.push(callback); return ticks.length; };
    Object.defineProperty(document, "hidden", { get: () => hidden });
  }
  if (insecureHttp) Object.defineProperty(window.crypto, "randomUUID", { value: undefined });
  window.localStorage.setItem("csharp-course-practice-v1", "preserved original practice");
  window.localStorage.setItem("csharp-course-exam-v1", "preserved original local exam");
  window.scrollTo = () => {};
  window.HTMLElement.prototype.scrollIntoView = () => {};
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement.prototype.close = function () { this.open = false; };
  window.confirm = () => true;
  const calls = [];
  let savedRevision = revision;
  window.fetch = async (url, options = {}) => {
    if (url === "/api/session") return response(auth);
    if (url === "/api/exam") return response({ ...paper, token: auth.csrf });
    if (url === "/api/progress?mode=exam" && !options.method) return response({ draft: remote, revision, carryover });
    const body = JSON.parse(options.body);
    if (url === "/api/timing") {
      assert.equal(options.headers["X-Exam-Token"], auth.csrf);
      assert.equal(options.keepalive, true);
      timingCalls.push(body);
      return timing ? timing(body) : response({ elapsed_ms: body.active_ms });
    }
    calls.push({ url, body });
    if (url === "/api/progress?mode=exam") {
      assert.equal(options.headers["X-Exam-Token"], auth.csrf);
      return save ? save(body, calls.length) : response({ revision: ++savedRevision, startedAt: Date.now() });
    }
    if (url === "/api/submit") return response({ error: "Injected submit failure" }, 503);
    assert.fail("Unexpected endpoint " + url);
  };
  window.eval(idScript); window.eval(syncScript); window.eval(appScript);
  await until(() => document.querySelector(".intro"));
  return { window, document, calls, timingCalls,
    advance(ms, step = 1000) {
      for (let left = ms; left > 0; left -= step) { onlineNow += Math.min(left, step); ticks.forEach(callback => callback()); }
    },
    visible(value) { hidden = !value; document.dispatchEvent(new window.Event("visibilitychange")); },
    click(text) {
    const control = [...document.querySelectorAll("button")].find(button => text instanceof RegExp ? text.test(button.textContent) : button.textContent === text);
    assert.ok(control, "Button exists: " + text); control.click();
  }, choose(letter) { document.querySelector(`input[value="${letter}"]`).click(); } };
}

test("team timing persists independently, pauses in background, and submission waits for its acknowledgment", async t => {
  let release, block = false;
  const current = await page(t, { controlledClock: true, timing: async body => {
    if (block) await new Promise(resolve => { release = resolve; });
    return response({ elapsed_ms: body.active_ms });
  } });
  current.click(/开始考试/);
  await until(() => current.timingCalls.length === 1);
  current.advance(15000);
  await until(() => current.timingCalls.length === 2);
  current.visible(false); current.advance(3600000);
  await until(() => current.timingCalls.length === 3);
  assert.equal(current.timingCalls[2].active_ms, 15000);
  assert.equal(current.calls.length, 1);
  current.visible(true);
  await until(() => current.timingCalls.length === 4);
  current.advance(5000);
  block = true;
  current.click("检查并交卷"); current.click("确认交卷");
  await until(() => release);
  assert.ok(!current.calls.some(call => call.url === "/api/submit"));
  release();
  await until(() => current.calls.some(call => call.url === "/api/submit"));
  assert.equal(current.timingCalls.at(-1).active_ms, 20000);
  assert.equal(current.timingCalls.at(-1).client_id, current.timingCalls[0].client_id);
});

test("failed online-time acknowledgment prevents submission and has a visible separate status", async t => {
  const current = await page(t, { timing: () => response({ error: "计时服务离线" }, 503) });
  current.click(/开始考试/);
  await until(() => current.document.getElementById("timing-status").textContent.includes("尚未确认保存"));
  current.choose("B"); await current.window.quizTeam.flush();
  current.click("检查并交卷"); current.click("确认交卷");
  await until(() => !current.document.getElementById("submit-error").hidden);
  assert.ok(!current.calls.some(call => call.url === "/api/submit"));
  assert.equal(current.calls.at(-1).body.draft.answers.Q01, "B");
});

test("combined team exam saves carried answers as a new attempt and restores the same account draft", async t => {
  const current = await page(t, { paper: combined, carryover: { answers: { Q121: "A", Q01: "B" }, flagged: ["Q01"] } });
  assert.equal(current.calls.length, 0);
  current.click(/接续已答 2 题/);
  await current.window.quizTeam.flush();
  const draft = current.calls[0].body.draft;
  assert.equal(draft.version, combined.version);
  assert.deepEqual(draft.answers, { Q121: "A", Q01: "B" });
  assert.deepEqual(draft.flagged, ["Q01"]);
  assert.equal(draft.index, 1);
  const restored = await page(t, { paper: combined, remote: { ...draft, startedAt: Date.now(), report: null }, revision: 1 });
  restored.click("继续考试 · 已答 2 题");
  assert.equal(restored.document.querySelector(".question-id").textContent, "Q02");
  assert.equal(restored.document.querySelectorAll(".question-grid button").length, 160);
  assert.equal(current.window.localStorage.getItem("csharp-course-exam-v1"), "preserved original local exam");
});

test("team exam saves serialized choices without reading or replacing local records", async t => {
  const current = await page(t);
  current.click(/开始考试/); current.choose("A"); current.choose("B");
  await current.window.quizTeam.flush();
  assert.equal(current.calls.length, 3);
  assert.deepEqual(current.calls.map(call => call.body.revision), [0, 1, 2]);
  assert.equal(current.calls[1].body.draft.answers.Q01, "A");
  assert.equal(current.calls[2].body.draft.answers.Q01, "B");
  assert.equal(current.window.localStorage.getItem("csharp-course-practice-v1"), "preserved original practice");
  assert.equal(current.window.localStorage.getItem("csharp-course-exam-v1"), "preserved original local exam");
  assert.equal(current.document.querySelector(".practice-feedback"), null);
});

test("LAN HTTP without randomUUID saves unique mutations and submits the same attempt", async t => {
  const current = await page(t, { insecureHttp: true });
  current.click(/开始考试/); current.choose("B");
  await current.window.quizTeam.flush();
  const attempt = current.calls[0].body.draft.attemptId;
  const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
  assert.match(attempt, uuid);
  assert.notEqual(current.calls[0].body.mutation_id, current.calls[1].body.mutation_id);
  assert.ok(current.calls.every(call => uuid.test(call.body.mutation_id)));
  current.click("检查并交卷"); current.click("确认交卷");
  await until(() => current.calls.some(call => call.url === "/api/submit"));
  const submitted = current.calls.at(-1).body;
  assert.equal(submitted.attempt_id, attempt);
  assert.equal(submitted.answers.Q01, "B");
});

test("another browser restores the account draft and resumes at its saved question", async t => {
  const remote = { version: exam.version, attemptId: "11111111-1111-4111-8111-111111111111", startedAt: Date.now(),
    answers: { Q01: "B" }, flagged: ["Q01"], index: 1, report: null, pending: null };
  const current = await page(t, { remote, revision: 7 });
  current.click(/继续考试/);
  assert.equal(current.document.getElementById("question-title").textContent, exam.questions[1].title);
  current.choose("A"); await current.window.quizTeam.flush();
  assert.equal(current.calls[0].body.revision, 7);
  assert.equal(current.calls[0].body.draft.answers.Q01, "B");
  assert.deepEqual(current.calls[0].body.draft.flagged, ["Q01"]);
});

test("an ambiguous network failure retries the identical mutation before later choices", async t => {
  let failed = false;
  const current = await page(t, { save: body => {
    if (!failed) { failed = true; throw new Error("Lost response after server commit"); }
    return response({ revision: body.revision + 1, startedAt: Date.now() });
  } });
  current.click(/开始考试/);
  await until(() => current.document.querySelector(".save-failed"));
  const original = clone(current.calls[0].body);
  current.choose("B");
  current.click("重试保存"); await current.window.quizTeam.flush();
  assert.deepEqual(current.calls[1].body, original);
  assert.equal(current.calls[2].body.revision, 1);
  assert.equal(current.calls[2].body.draft.answers.Q01, "B");
});

test("a revision conflict stops saving and submission rather than overwriting server work", async t => {
  const current = await page(t, { save: () => response({ error: "另一页面已更新" }, 409) });
  current.click(/开始考试/);
  await until(() => current.document.querySelector(".save-failed"));
  assert.ok([...current.document.querySelectorAll(".options input")].every(input => input.disabled));
  current.click("下一题 →");
  assert.ok([...current.document.querySelectorAll(".options input")].every(input => input.disabled));
  assert.ok(current.document.getElementById("clear-answer").disabled);
  current.click("检查并交卷"); current.click("确认交卷");
  await until(() => !current.document.getElementById("submit-error").hidden);
  assert.ok(!current.calls.some(call => call.url === "/api/submit"));
  assert.match(current.document.querySelector(".save-failed").textContent, /下载本页记录/);
});

test("submission waits for all saved answers and the fixed pending snapshot", async t => {
  let release;
  let first = true;
  const current = await page(t, { save: async body => {
    if (first) { first = false; await new Promise(resolve => { release = resolve; }); }
    return response({ revision: body.revision + 1, startedAt: Date.now() });
  } });
  current.click(/开始考试/); current.choose("B"); current.click("检查并交卷"); current.click("确认交卷");
  assert.equal(current.calls.length, 1);
  release();
  await until(() => current.calls.some(call => call.url === "/api/submit"));
  const saves = current.calls.filter(call => call.url.startsWith("/api/progress"));
  assert.equal(saves.length, 3);
  assert.equal(saves[2].body.draft.pending.answers.Q01, "B");
  assert.equal(current.calls.at(-1).url, "/api/submit");
});

test("anonymous users sign in before any question data is requested", async t => {
  const dom = new JSDOM(html, { url: "https://quiz.test/", runScripts: "outside-only" });
  t.after(() => dom.window.close());
  const { window } = dom; const calls = [];
  window.fetch = async (url, options) => {
    calls.push(url);
    if (url === "/api/session") return response({ user: null });
    if (url === "/api/login") { assert.equal(JSON.parse(options.body).username, "alice"); return response(auth); }
    if (url === "/api/exam") return response(exam);
    if (url.startsWith("/api/progress")) return response({ revision: 0, draft: null });
    assert.fail(url);
  };
  window.eval(idScript); window.eval(syncScript); window.eval(appScript);
  await until(() => window.document.querySelector(".team-auth"));
  assert.deepEqual(calls, ["/api/session"]);
  window.document.querySelector('input[name="username"]').value = "alice";
  window.document.querySelector('input[name="password"]').value = "Fake-Test-Password-12";
  window.document.querySelector("form").dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await until(() => window.document.querySelector(".intro"));
  assert.deepEqual(calls.slice(0, 3), ["/api/session", "/api/login", "/api/exam"]);
});

async function identityEntry(t, { domain = null } = {}) {
  const dom = new JSDOM(html, { url: "http://192.168.1.2:8080/", runScripts: "outside-only" });
  t.after(() => dom.window.close());
  const { window } = dom, document = window.document, calls = [];
  window.scrollTo = () => {};
  window.HTMLElement.prototype.scrollIntoView = () => {};
  let session;
  window.fetch = async (url, options = {}) => {
    calls.push({ url, body: options.body ? JSON.parse(options.body) : null });
    if (url === "/api/session") return response({ user: null, identity_options: { passwordless: true, names: rosterNames, domain_account: domain } });
    if (url === "/api/identify") {
      const input = JSON.parse(options.body);
      const name = domain ? "示例学员01" : input.account;
      const matched = rosterNames.includes(name);
      if (!matched) return response({ error: "姓名不在允许登录的名单中，请输入名单中的本人完整姓名。" }, 403);
      session = { ...auth, user: { ...auth.user, display_name: name },
        identity: { status: "matched", source: domain ? "domain" : "self_reported", account: name, computer_name: input.computer_name } };
      return response(session);
    }
    if (url === "/api/exam") return response({ ...exam, token: auth.csrf });
    if (url.startsWith("/api/progress")) return response({ draft: null, revision: 0 });
    assert.fail("Unexpected identity endpoint " + url);
  };
  window.eval(idScript); window.eval(syncScript); window.eval(appScript);
  await until(() => document.querySelector(".team-auth"));
  return { window, document, calls,
    click(text) {
      const button = [...document.querySelectorAll("button")].find(item => item.textContent === text);
      assert.ok(button, "Button exists: " + text); button.click();
    },
    enter(account) {
      if (document.querySelector('input[name="account"]')) document.querySelector('input[name="account"]').value = account;
      document.querySelector("form").dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
    } };
}

test("passwordless student manually types a roster name without selection or autocomplete suggestions", async t => {
  const current = await identityEntry(t);
  assert.equal(current.document.querySelector('input[type="password"]'), null);
  assert.equal(current.document.querySelector("datalist, select, input[list]"), null);
  assert.match(current.document.querySelector(".team-auth").textContent, /自报身份/);
  assert.equal(current.document.querySelectorAll(".team-auth input").length, 1);
  assert.equal(current.document.querySelector('input[name="computer_name"]'), null);
  assert.equal(current.document.querySelector('input[name="account"]').placeholder, "输入姓名");
  assert.equal(current.document.querySelector('input[name="account"]').autocomplete, "off");
  assert.ok([...current.document.querySelectorAll("button")].some(item => item.textContent === "管理员账号登录"));
  current.enter("示例学员䶮");
  await until(() => current.document.querySelector(".intro"));
  assert.deepEqual(current.calls.find(call => call.url === "/api/identify").body, { account: "示例学员䶮", computer_name: "" });
  assert.match(current.document.querySelector(".team-user-bar").textContent, /示例学员䶮 · 自报身份 · 已归属名单/);
  assert.equal([...current.document.querySelectorAll("button")].some(item => item.textContent === "修改密码"), false);
  assert.ok(!current.calls.some(call => call.url === "/api/login"));
});

test("unknown name stays on login page and a listed name can be entered after rejection", async t => {
  const current = await identityEntry(t);
  current.enter("未列名学员");
  await until(() => current.document.querySelector(".error-text").textContent);
  assert.equal(current.document.querySelector('input[name="account"]').value, "未列名学员");
  assert.match(current.document.querySelector(".error-text").textContent, /名单/);
  assert.ok(!current.calls.some(call => call.url === "/api/exam"));
  current.enter("示例学员01");
  await until(() => current.document.querySelector(".intro"));
  assert.match(current.document.querySelector(".team-user-bar").textContent, /示例学员01 · 自报身份 · 已归属名单/);
});

test("verified gateway domain takes the primary entry and administrator entry remains available", async t => {
  const domain = await identityEntry(t, { domain: "GAME\\ex1" });
  assert.equal(domain.document.querySelector('input[name="account"]'), null);
  assert.match(domain.document.querySelector(".team-auth").textContent, /GAME\\ex1/);
  domain.enter("");
  await until(() => domain.document.querySelector(".intro"));
  assert.match(domain.document.querySelector(".team-user-bar").textContent, /域认证/);
  const current = await identityEntry(t);
  current.click("管理员账号登录");
  assert.ok(current.document.querySelector('input[name="password"]'));
  assert.equal(current.document.querySelector("h1").textContent, "管理员登录");
  current.click("返回免密学员入口");
  assert.ok(current.document.querySelector('input[name="account"]'));
  current.enter("示例学员01");
  await until(() => current.document.querySelector(".intro"));
});

test("administrator separates roster and unattributed summaries and shows auxiliary evidence", async t => {
  const dom = new JSDOM(resultsHtml, { url: "http://192.168.1.2:8080/admin", runScripts: "outside-only" });
  t.after(() => dom.window.close());
  const { window } = dom, document = window.document, calls = [];
  const summaries = ["matched", "unmatched"].map(identity_status => ({ identity_status, paper: "extension", version: exam.version,
    people: 1, attempts: 1, average_percent: 0, groups: [], questions: [] }));
  const records = ["matched", "unmatched"].map((identity_status, index) => ({ identity_status, username: "student" + index,
    input_account: index ? "unknown-account" : "示例学员01", display_name: index ? "未归属：unknown-account" : "示例学员01",
    identity_source: "self_reported", client_ip: "10.1.2.3", computer_name: "SHARED-PC", paper: "extension",
    time: "2026-10-10T00:00:00Z", correct: 0, total: 40, percent: 0, wrong: 0, unanswered: 40, version: exam.version, attempt_id: "id" + index }));
  const users = rosterNames.map((display_name, i) => ({ display_name, username: "person-" + i, role: "student", disabled: 0, attribution: "matched" }));
  users.push({ display_name: "未归属：unknown-account", username: "unmatched-one", role: "student", disabled: 0, attribution: "unmatched",
    last_identity: { account: "unknown-account", source: "self_reported", client_ip: "10.1.2.3", computer_name: "SHARED-PC" } });
  window.fetch = async url => {
    calls.push(url);
    if (url === "/api/session") return response({ ...auth, user: { ...auth.user, role: "admin" },
      identity_options: { passwordless: true, names: rosterNames, domain_account: null } });
    if (url === "/api/admin/users") return response({ users });
    if (url.startsWith("/api/results?")) {
      const kind = new URL(url, window.location.href).searchParams.get("attribution");
      return response({ summaries: summaries.filter(row => kind === "all" || row.identity_status === kind),
        records: records.filter(row => kind === "all" || row.identity_status === kind) });
    }
    assert.fail(url);
  };
  window.eval(syncScript); window.eval(resultsScript);
  await until(() => document.querySelector("h3")?.textContent.includes(`已归属名单 · ${rosterNames.length} 人`));
  assert.equal(document.querySelectorAll(".team-summary").length, 2);
  assert.ok(document.querySelector(".team-dashboard").textContent.includes(`已归属名单 · ${rosterNames.length} 人`));
  assert.match(document.querySelector(".team-dashboard").textContent, /未归属 · 1 人/);
  assert.match(document.querySelector(".team-dashboard").textContent, /示例学员䶮/);
  assert.match(document.querySelector(".team-dashboard").textContent, /10\.1\.2\.3/);
  assert.match(document.querySelector(".team-dashboard").textContent, /SHARED-PC/);
  assert.equal(document.querySelector(".team-account-form"), null);
  document.querySelector('select[name="attribution"]').value = "unmatched";
  document.querySelector(".team-filters").dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await until(() => document.querySelectorAll(".team-summary").length === 1);
  assert.match(document.querySelector(".team-summary h2").textContent, /未归属/);
  assert.match(document.querySelector('.team-filters a').href, /attribution=unmatched/);
});

test("personal results show account and exam fields while preserving scores, history and downloads", async t => {
  const dom = new JSDOM(resultsHtml, { url: "http://192.168.1.2:8080/results", runScripts: "outside-only" });
  t.after(() => dom.window.close());
  const { window } = dom, document = window.document, calls = [];
  const record = { identity_status: "matched", username: "person-internal-id", input_account: "示例学员䶮", display_name: "示例学员䶮",
    identity_source: "self_reported", client_ip: "10.1.2.3", computer_name: "HISTORICAL-PC", paper: "extension",
    time: "2026-10-10T00:00:00Z", correct: 1, total: 40, percent: 2.5, wrong: 1, unanswered: 38, version: exam.version, attempt_id: "old-report" };
  window.fetch = async url => {
    calls.push(url);
    if (url === "/api/session") return response({ ...auth, user: { ...auth.user, display_name: "示例学员䶮" },
      identity_options: { passwordless: true, names: rosterNames, domain_account: null } });
    if (url.startsWith("/api/results?")) return response({ records: [record], summaries: [{ paper: "extension", version: exam.version,
      identity_status: "matched", people: 1, attempts: 1, average_percent: 2.5, groups: [], questions: [] }] });
    if (url === "/api/history") return response({ attempts: [
      { ...record, answered: 2, submitted: true }, { ...record, attempt_id: "old-draft", answered: 1, submitted: false }] });
    assert.fail(url);
  };
  window.eval(syncScript); window.eval(resultsScript);
  await until(() => document.querySelector("h2")?.textContent === "扩展题（旧卷） · 考试" && document.querySelectorAll('.team-table').length === 4);
  assert.equal(document.querySelector('select[name="attribution"]'), null);
  const results = document.querySelectorAll('.team-table')[2];
  assert.deepEqual([...results.querySelectorAll("th")].map(th => th.textContent),
    ["账号", "题库", "时间", "正确 / 题数", "正确率", "错答", "漏答", "版本", "记录"]);
  const cells = [...results.querySelectorAll("tbody td")].map(td => td.textContent);
  assert.equal(cells[0], "示例学员䶮");
  assert.equal(cells[3], "1/40"); assert.equal(cells[4], "2.5%");
  assert.equal(cells[5], "1"); assert.equal(cells[6], "38");
  assert.equal(results.querySelector("a").pathname, "/api/attempts/old-report");
  const history = document.querySelectorAll('.team-table')[3];
  assert.equal(history.querySelectorAll("tbody tr").length, 2);
  assert.match(history.textContent, /已交卷/); assert.match(history.textContent, /草稿/);
  assert.equal(history.querySelectorAll("a")[1].pathname, "/api/attempts/old-draft");
  assert.ok(!document.querySelector('.team-dashboard').textContent.includes("10.1.2.3"));
  assert.ok(!document.querySelector('.team-dashboard').textContent.includes("HISTORICAL-PC"));
  assert.match(document.querySelector('.team-filters a').href, /scope=self/);
  document.querySelector('select[name="policy"]').value = "all";
  document.querySelector('.team-filters').dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await until(() => calls.some(url => url.includes("policy=all")));
  assert.ok(calls.filter(url => url.startsWith("/api/results?")).every(url => new URL(url, window.location.href).searchParams.get("scope") === "self"));
});
