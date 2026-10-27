"use strict";

// Optional DOM checks. No browser automation, server, network, or learner report writes.
// Install jsdom into .tools/ui-tests; the normal exam has no Node.js dependency.
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const root = path.resolve(__dirname, "..");
const { JSDOM } = require(require.resolve("jsdom", { paths: [path.join(root, ".tools/ui-tests"), __dirname] }));
const html = fs.readFileSync(path.join(root, "web/quiz/index.html"), "utf8");
const script = fs.readFileSync(path.join(root, "web/quiz/app.js"), "utf8");
const idScript = fs.readFileSync(path.join(root, "web/quiz/id.js"), "utf8");
const storageKey = "csharp-course-exam-v1";
const fixtureProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
sys.path.insert(0, "scripts")
from quiz_exam import Exam
exam = Exam()
first, second = exam.questions[:2]
answers = {first["id"]: first["answers"][0],
           second["id"]: next(x for x in "ABCD" if x != second["answers"][0])}
payload = {"version": exam.version, "attempt_id": "11111111-1111-4111-8111-111111111111",
           "answers": answers, "elapsed_seconds": 135}
last = exam.questions[-1]
print(json.dumps({"exam": exam.public(), "answers": answers, "report": exam.grade(payload),
                  "last_report": exam.grade(payload | {"answers": {last["id"]: last["answers"][0]}})}, ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
assert.equal(fixtureProcess.status, 0, `Load repository Python environment first.\n${fixtureProcess.stderr}`);
const fixtures = JSON.parse(fixtureProcess.stdout);
assert.equal(fixtures.exam.total, 40);
assert.deepEqual([fixtures.report.correct, fixtures.report.wrong, fixtures.report.unanswered], [1, 1, 38]);

const paperProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
sys.path.insert(0, "scripts")
from quiz_exam import Exam
exam = Exam(selected_group="queries")
payload = {"version": exam.version, "attempt_id": "22222222-2222-4222-8222-222222222222",
           "answers": {q["id"]: q["answers"][0] for q in exam.questions}, "elapsed_seconds": 5}
print(json.dumps({"exam": exam.public(), "report": exam.grade(payload)}, ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 4 * 1024 * 1024 });
assert.equal(paperProcess.status, 0, paperProcess.stderr);
const paperFixture = JSON.parse(paperProcess.stdout);
const companionProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
sys.path.insert(0, "scripts")
from quiz_exam import Exam
exam = Exam(selected_group="microsoft")
answers = {q["id"]: q["answers"][0] for q in exam.questions}
payload = {"version": exam.version, "attempt_id": "33333333-3333-4333-8333-333333333333",
           "answers": answers, "elapsed_seconds": 5}
print(json.dumps({"exam": exam.public(), "answers": answers, "report": exam.grade(payload)}, ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
assert.equal(companionProcess.status, 0, companionProcess.stderr);
const companionFixture = JSON.parse(companionProcess.stdout);
const combinedProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
sys.path.insert(0, "scripts")
from quiz_exam import Exam
p = Exam(selected_group="combined")
payload = {"version": p.version, "attempt_id": "77777777-7777-4777-8777-777777777777", "answers": {}, "elapsed_seconds": 0}
print(json.dumps({"exam": p.public(), "report": p.grade(payload)}, ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 12 * 1024 * 1024 });
assert.equal(combinedProcess.status, 0, combinedProcess.stderr);
const combinedFixture = JSON.parse(combinedProcess.stdout);
const legacyProcess = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
from unittest.mock import patch
sys.path.insert(0, "scripts")
import quiz
from quiz_exam import Exam
bank = {g: qs for g, qs in quiz.load_bank().items() if g in quiz.COMBINED_GROUPS}
manifest = {"title": "旧迁移综合卷", "intro": "历史报告",
            "groups": [{"id": g, "focus": "旧题库", "questions": [q["id"] for q in qs]} for g, qs in bank.items()]}
lessons = quiz.resolved_lessons(bank)
with patch.object(quiz, "load_migration_exam", return_value=manifest), patch.object(quiz, "resolved_lessons", return_value=lessons):
    old = Exam()
payload = {"version": old.version, "attempt_id": "55555555-5555-4555-8555-555555555555",
           "answers": {}, "elapsed_seconds": 135}
print(json.dumps({"exam": old.public(), "report": old.grade(payload)}, ensure_ascii=True))
`], { cwd: root, encoding: "utf8", maxBuffer: 8 * 1024 * 1024 });
assert.equal(legacyProcess.status, 0, legacyProcess.stderr);
const legacyFixture = JSON.parse(legacyProcess.stdout);
assert.equal(legacyFixture.exam.total, 120);
const runtimeQuestion = fixtures.exam.questions.find(question => question.group === "runtime").id;
const clone = value => JSON.parse(JSON.stringify(value));

async function waitFor(condition, label) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (condition()) return;
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.fail(`UI did not settle: ${label}`);
}

function reportFor(payload, source = fixtures.report) {
  const report = clone(source);
  report.attempt_id = payload.attempt_id;
  report.elapsed_seconds = payload.elapsed_seconds;
  report.files = {
    json: `artifacts/quiz-reports/${payload.attempt_id}.json`,
    markdown: `artifacts/quiz-reports/${payload.attempt_id}.md`,
  };
  report.markdown = report.markdown.replaceAll(source.attempt_id, payload.attempt_id)
    .replace(`用时：${source.elapsed_seconds} 秒`, `用时：${payload.elapsed_seconds} 秒`);
  return report;
}

async function makePage(t, { exam = fixtures.exam, storage = {}, submit, practiceResponse, report = fixtures.report, lessonResponse, url = "https://exam.test/", insecureHttp = false, controlledClock = false } = {}) {
  // No resource loader is configured: external scripts, CSS, and links never load.
  const dom = new JSDOM(html, { url, runScripts: "outside-only", pretendToBeVisual: true });
  t.after(() => dom.window.close());
  const { window } = dom;
  const { document } = window;
  let onlineNow = 0, hidden = false;
  const ticks = [];
  if (controlledClock) {
    window.performance.now = () => onlineNow;
    window.setInterval = callback => { ticks.push(callback); return ticks.length; };
    Object.defineProperty(document, "hidden", { get: () => hidden });
  }
  if (insecureHttp) Object.defineProperty(window.crypto, "randomUUID", { value: undefined });
  const requests = [];
  const lessonRequests = [];
  const practiceRequests = [];
  const downloads = [];
  const blobs = new Map();
  for (const [key, value] of Object.entries(storage)) window.localStorage.setItem(key, value);
  window.scrollTo = () => {};
  window.HTMLElement.prototype.scrollIntoView = () => {};
  window.HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  window.HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  window.confirm = () => true;
  window.URL.createObjectURL = blob => {
    const url = `blob:https://exam.test/${blobs.size + 1}`;
    blobs.set(url, blob);
    return url;
  };
  window.URL.revokeObjectURL = () => {};
  window.HTMLAnchorElement.prototype.click = function () {
    downloads.push({ filename: this.download, blob: blobs.get(this.href) });
  };
  const pageParams = new window.URL(url).searchParams;
  const endpointQuery = pageParams.has("group") ? `?group=${encodeURIComponent(pageParams.get("group"))}` : "";
  const pageStorageKey = (pageParams.get("mode") === "practice" ? "csharp-course-practice-v1" : storageKey) +
    (exam.selected_group ? `-${exam.selected_group}` : "");
  window.fetch = async (url, options = {}) => {
    if (url === "/api/exam" + endpointQuery) return { ok: true, status: 200, json: async () => clone(exam) };
    if (url === "/api/practice" + endpointQuery) {
      const payload = JSON.parse(options.body);
      assert.equal(options.headers["X-Exam-Token"], exam.token);
      practiceRequests.push(payload);
      const source = report.questions.find(question => question.id === payload.question_id);
      const result = { version: exam.version, question: { ...clone(source), selected: payload.answer,
        status: source.answer === payload.answer ? "correct" : "wrong" } };
      if (practiceResponse) return practiceResponse(payload, practiceRequests.length, result);
      return { ok: true, status: 200, json: async () => result };
    }
    if (url === "/api/lessons" + endpointQuery) {
      const payload = JSON.parse(options.body);
      lessonRequests.push(payload);
      if (lessonResponse) return lessonResponse(payload, lessonRequests.length);
      return { ok: true, status: 200, json: async () => ({ lessons: clone(fixtures.report.lessons), markdown: fixtures.report.markdown }) };
    }
    assert.equal(url, "/api/submit" + endpointQuery, "Only in-memory exam endpoints may be requested");
    const payload = JSON.parse(options.body);
    requests.push({ payload, body: options.body, headers: clone(options.headers) });
    if (submit) return submit(payload, requests.length);
    return { ok: true, status: 200, json: async () => reportFor(payload, report) };
  };
  window.eval(idScript); window.eval(script);
  await waitFor(() => document.querySelector(".intro, .report-shell, .empty-state"), "initial page");
  const page = {
    dom, window, document, requests, lessonRequests, practiceRequests, downloads,
    advance(ms, step = 1000) {
      for (let left = ms; left > 0; left -= step) { onlineNow += Math.min(left, step); ticks.forEach(callback => callback()); }
    },
    visible(value) { hidden = !value; document.dispatchEvent(new window.Event("visibilitychange")); },
    button(label) {
      const matches = [...document.querySelectorAll("button")].filter(element =>
        label instanceof RegExp ? label.test(element.textContent) : element.textContent === label);
      assert.equal(matches.length, 1, `Expected one button: ${String(label)}`);
      return matches[0];
    },
    click(label) { this.button(label).click(); },
    start() { this.click(/开始考试/); },
    select(letter) {
      const radio = document.querySelector(`input[type=radio][value="${letter}"]`);
      assert.ok(radio, `Option ${letter} exists`);
      radio.click();
    },
    jump(id) {
      const tile = document.querySelector(`.question-grid button[data-question-id="${id}"]`);
      assert.ok(tile, `Question ${id} is on the answer sheet`);
      tile.click();
    },
    saved() { return JSON.parse(window.localStorage.getItem(pageStorageKey)); },
    storage() {
      return Object.fromEntries(Array.from({ length: window.localStorage.length }, (_, i) => {
        const key = window.localStorage.key(i);
        return [key, window.localStorage.getItem(key)];
      }));
    },
    fillSampleAnswers() {
      for (const [id, letter] of Object.entries(fixtures.answers)) {
        this.jump(id);
        this.select(letter);
      }
    },
    async finish() {
      document.querySelector(".navigator > .button.primary").click();
      document.getElementById("confirm-submit").click();
      await waitFor(() => document.querySelector(".report-shell"), "completed report");
    },
    async downloadText(download) {
      return new Promise((resolve, reject) => {
        const reader = new window.FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsText(download.blob);
      });
    },
  };
  return page;
}

test("start presents 40 single-choice questions without exposing explanations", async t => {
  const page = await makePage(t);
  assert.match(page.document.querySelector(".intro").textContent, /40.*道.*全部单选/s);
  assert.deepEqual([...page.document.querySelectorAll(".scope-count")].map(x => x.textContent), ["10 题", "14 题", "8 题", "8 题"]);
  page.start();
  assert.equal(page.document.querySelectorAll(".question-grid button").length, 40);
  assert.equal(page.document.querySelectorAll("input[type=radio]").length, 4);
  assert.equal(page.document.querySelectorAll("input[type=checkbox]").length, 0);
  assert.equal(page.document.querySelector("#question-title").textContent, fixtures.exam.questions[0].title);
  assert.equal(page.document.querySelectorAll("input:checked").length, 0);
  assert.equal(page.document.querySelector(".review-answer"), null);
  assert.ok(!page.document.body.textContent.includes(fixtures.report.questions[0].rationale.A));
  assert.equal(page.saved().version, fixtures.exam.version);
  assert.deepEqual(page.saved().answers, {});
});

test("combined exam shows one paper, 16 prefixed chapters and all 160 explanations", async t => {
  const page = await makePage(t, { exam: combinedFixture.exam, report: combinedFixture.report });
  assert.equal(page.document.querySelector(".paper-selection"), null);
  const labels = [...page.document.querySelectorAll(".scope-item h3")].map(el => el.textContent);
  assert.equal(labels.length, 16);
  assert.ok(labels.slice(0, 12).every(label => label.startsWith("基础 · ")));
  assert.ok(labels.slice(12).every(label => label.startsWith("扩展 · ")));
  page.start();
  assert.equal(page.document.querySelectorAll(".question-grid button").length, 160);
  assert.equal(page.document.querySelector(".question-id").textContent, "Q01");
  page.select("B"); assert.equal(page.saved().answers.Q121, "B");
  page.jump("Q01"); assert.equal(page.document.querySelector(".question-id").textContent, "Q121");
  await page.finish();
  assert.equal(page.document.querySelectorAll("#review-questions details").length, 160);
  assert.ok([...page.document.querySelectorAll("#review-questions details")].every(el => el.open));
  assert.equal(page.document.querySelectorAll(".group-result").length, 16);
  assert.equal(page.saved().report.total, 160);
  assert.match(page.document.querySelector(".raw-score").textContent, /\/ 160/);
});

test("combined local draft carries both old drafts, resumes separately and preserves raw records", async t => {
  const previous = { version: fixtures.exam.version, attemptId: "88888888-8888-4888-8888-888888888888", startedAt: Date.now(),
    answers: { Q01: "B", Q03: ["A"] }, flagged: ["Q01"], index: 0, report: null, pending: null };
  const basic = { ...previous, version: companionFixture.exam.version, answers: { Q121: "A" }, flagged: ["Q122"] };
  const storage = { [storageKey]: JSON.stringify(previous), [storageKey + "-microsoft"]: JSON.stringify(basic) };
  const page = await makePage(t, { exam: combinedFixture.exam, report: combinedFixture.report, storage });
  assert.equal(page.button(/接续已答/).textContent, "开始考试 · 接续已答 2 题");
  assert.equal(page.document.querySelector(".exam-archives summary").textContent, "历史考试记录 · 2 份");
  page.start();
  assert.deepEqual(page.saved().answers, { Q121: "A", Q01: "B" });
  assert.deepEqual(page.saved().flagged.sort(), ["Q01", "Q122"]);
  assert.notEqual(page.saved().attemptId, previous.attemptId);
  assert.equal(page.storage()[storageKey], storage[storageKey]);
  assert.equal(page.storage()[storageKey + "-microsoft"], storage[storageKey + "-microsoft"]);
  const restored = await makePage(t, { exam: combinedFixture.exam, report: combinedFixture.report, storage: page.storage() });
  restored.click("继续考试 · 已答 2 题");
  assert.deepEqual(restored.saved().answers, page.saved().answers);
  const excluded = await makePage(t, { exam: combinedFixture.exam, storage: {
    [storageKey]: JSON.stringify({ ...previous, report: fixtures.report }),
    [storageKey + "-microsoft"]: JSON.stringify({ ...basic, version: "stale" }) } });
  assert.equal(excluded.document.querySelector(".exam-archives summary").textContent, "历史考试记录 · 2 份");
  excluded.start(); assert.deepEqual(excluded.saved().answers, {});
  const history = await makePage(t, { exam: combinedFixture.exam, storage: {
    [storageKey]: JSON.stringify({ ...previous, report: fixtures.report }) } });
  history.click("查看历史报告");
  assert.equal(history.document.querySelectorAll("#review-questions details").length, 40);
  assert.match(history.document.querySelector(".raw-score").textContent, /\/ 40/);
  assert.equal(JSON.parse(history.storage()[storageKey]).report.version, fixtures.report.version);
});

test("extension numbering stays consecutive on cards, lessons and reports while preserving answer keys", async t => {
  const page = await makePage(t, { report: fixtures.last_report });
  page.start();
  const tiles = [...page.document.querySelectorAll(".question-grid button")];
  assert.deepEqual(tiles.map(tile => tile.textContent), Array.from({ length: 40 }, (_, i) => String(i + 1).padStart(2, "0")));
  assert.equal(tiles[39].getAttribute("aria-label"), "Q40 未答");
  page.jump("Q38");
  assert.equal(page.document.querySelector(".question-id").textContent, "Q40");
  page.select(fixtures.report.questions.at(-1).answer);
  assert.ok(Object.hasOwn(page.saved().answers, "Q38"));
  assert.ok(!Object.hasOwn(page.saved().answers, "Q40"));
  const resumed = await makePage(t, { storage: page.storage(), report: fixtures.last_report });
  resumed.click("继续考试 · 已答 1 题");
  assert.equal(resumed.document.querySelector(".question-id").textContent, "Q40");
  assert.equal(resumed.document.querySelector("input:checked").value, fixtures.report.questions.at(-1).answer);
  await resumed.finish();
  assert.ok(resumed.button("Q40 · 正确"));
  resumed.click("Q40 · 正确");
  assert.equal(resumed.document.querySelector("#review-Q38 .question-id").textContent, "Q40");
  assert.equal(resumed.saved().report.questions.at(-1).id, "Q38");
  assert.equal(resumed.saved().report.questions.at(-1).display_id, "Q40");
  assert.ok(resumed.saved().report.markdown.includes(`### Q40 · ${fixtures.report.questions.at(-1).title}`));
});

test("questions omit empty scenarios and retain required constraints", async t => {
  for (const practice of [false]) {
    const page = await makePage(t, { url: practice ? "https://exam.test/?mode=practice" : "https://exam.test/" });
    page.click(practice ? /开始练习/ : /开始考试/);
    page.jump("Q03");
    assert.equal(page.document.querySelector(".scenario"), null);
    assert.equal(page.document.querySelector(".prompt").textContent,
      fixtures.exam.questions.find(q => q.id === "Q03").prompt);
    page.jump("Q46");
    assert.equal(page.document.querySelector(".scenario").textContent,
      fixtures.exam.questions.find(q => q.id === "Q46").scenario);
    assert.equal(page.document.querySelectorAll("input[type=radio]").length, 4);
  }
});

test("space-sensitive output keeps visible spacing in the choices", async t => {
  const page = await makePage(t, { exam: companionFixture.exam, report: companionFixture.report,
    url: "https://exam.test/?group=microsoft" });
  const style = page.document.createElement("style");
  style.textContent = fs.readFileSync(path.join(root, "web/quiz/styles.css"), "utf8");
  page.document.head.append(style);
  page.start();
  page.jump("Q132");
  const output = page.document.querySelectorAll(".option-text code")[3];
  assert.equal(output.textContent, "[  007]/2.5");
  assert.equal(page.window.getComputedStyle(output).whiteSpace, "pre-wrap");
});

test("paper selection exposes exactly two choices and preserves hidden legacy topic drafts", async t => {
  const combined = await makePage(t);
  const links = [...combined.document.querySelectorAll(".paper-links .paper-link")];
  assert.equal(combined.document.querySelectorAll(".mode-selection a").length, 0);
  assert.equal(links.length, 2);
  assert.deepEqual(links.map(link => link.textContent), ["基础题 · 120 题", "扩展题 · 40 题"]);
  assert.equal(links.find(link => link.textContent === "基础题 · 120 题").getAttribute("href"), "/?group=microsoft");
  assert.equal(links[1].getAttribute("aria-current"), "page");
  assert.ok(links.every(link => ["/", "/?group=microsoft"].includes(link.getAttribute("href"))));
  assert.ok(!combined.document.querySelector(".paper-selection").textContent.includes("专题"));
  assert.equal(combined.document.querySelector('a[href="/question-bank.md"]'), null);
  combined.start();
  combined.select("B");
  const savedCombined = combined.storage()[storageKey];
  const page = await makePage(t, { exam: paperFixture.exam, report: paperFixture.report,
    url: "https://exam.test/?group=queries", storage: combined.storage() });
  assert.match(page.document.querySelector("h1").textContent, /查询与元数据/);
  page.start();
  assert.equal(page.document.querySelectorAll(".question-grid button").length, 20);
  assert.equal(page.document.getElementById("question-title").textContent, paperFixture.exam.questions[0].title);
  for (const question of paperFixture.report.questions) {
    page.jump(question.id);
    page.select(question.answer);
  }
  await page.finish();
  assert.equal(page.document.querySelector(".raw-score").textContent, "原始得分 20 / 20 · 每题 1 分");
  assert.equal(page.document.querySelectorAll(".lesson-group").length, 1);
  assert.equal(page.document.querySelectorAll(".lesson-question").length, 20);
  assert.equal(page.storage()[storageKey], savedCombined);
  assert.equal(page.saved().report.total, 20);
  const restored = await makePage(t, { exam: paperFixture.exam, report: paperFixture.report,
    url: "https://exam.test/?group=queries", storage: page.storage() });
  assert.equal(restored.saved().report.score, 20);
  assert.equal(restored.requests.length, 0);
});


test("independent official companion covers twelve units and preserves its report and draft", async t => {
  const combined = await makePage(t);
  combined.start();
  combined.select("B");
  const migrationDraft = combined.storage()[storageKey];
  const page = await makePage(t, { exam: companionFixture.exam, report: companionFixture.report,
    url: "https://exam.test/?group=microsoft", storage: combined.storage() });
  assert.equal(page.document.querySelector("h1").textContent, "Microsoft Learn C# 配套自测");
  assert.equal(page.document.querySelectorAll(".scope-item").length, 12);
  assert.ok(page.document.querySelector(".intro-copy").textContent.includes("本课程自编"));
  assert.equal(page.document.querySelector('a[href$="microsoft-map.md"]'), null);
  assert.deepEqual([...page.document.querySelectorAll('.paper-link')].map(link => link.textContent), ["基础题 · 120 题", "扩展题 · 40 题"]);
  assert.equal(page.document.querySelector('.paper-link').getAttribute("aria-current"), "page");
  assert.ok(!page.document.body.textContent.includes(companionFixture.report.lessons[0].intro));
  page.start();
  assert.equal(page.document.querySelectorAll(".question-grid button").length, 120);
  for (const [id, letter] of Object.entries(companionFixture.answers)) {
    page.jump(id);
    page.select(letter);
  }
  assert.equal(page.storage()[storageKey], migrationDraft);
  await page.finish();
  assert.equal(page.requests[0].payload.answers.Q240, companionFixture.answers.Q240);
  assert.equal(page.saved().report.score, 120);
  assert.equal(page.saved().report.percent, 100);
  assert.equal(page.saved().report.groups.length, 12);
  assert.ok(page.saved().report.groups.every(group => group.total === 10 && group.correct === 10));
  assert.equal(page.document.querySelectorAll(".lesson-topic").length, 12);
  const lessonButtons = [...page.document.querySelectorAll("button")].filter(button => button.textContent === "查看本单元讲解");
  assert.equal(lessonButtons.length, 12);
  lessonButtons.forEach((button, index) => {
    button.click();
    assert.ok(page.document.getElementById("lesson-microsoft").open);
    assert.equal(page.document.activeElement.id, `lesson-microsoft-Q${121 + index * 10}`);
  });
  page.click("下载数据 .json");
  const report = JSON.parse(await page.downloadText(page.downloads[0]));
  assert.equal(report.questions.length, 120);
  assert.equal(report.questions[0].id, "Q121");
  assert.equal(report.questions.at(-1).id, "Q240");
  const reloaded = await makePage(t, { exam: companionFixture.exam, report: companionFixture.report,
    url: "https://exam.test/?group=microsoft", storage: page.storage() });
  assert.ok(reloaded.document.querySelector(".report-shell"));
  assert.equal(reloaded.saved().report.percent, 100);
});


test("new report review teaches each question while old snapshots still open unchanged", async t => {
  const page = await makePage(t);
  page.start();
  page.fillSampleAnswers();
  await page.finish();
  page.click("全部 40");
  assert.equal(page.document.querySelectorAll(".answer-teaching").length, 40);
  assert.ok(page.document.querySelector("#review-Q01").textContent.includes(fixtures.report.questions[0].explanation.principle));
  const draft = page.saved();
  draft.report.questions.forEach(q => { delete q.explanation; delete q.explanation_version; });
  const old = clone(draft.report);
  const resumed = await makePage(t, { storage: { [storageKey]: JSON.stringify(draft) } });
  resumed.click("全部 40");
  assert.equal(resumed.document.querySelectorAll(".answer-teaching").length, 0);
  assert.equal(resumed.document.querySelectorAll(".review-option").length, 160);
  assert.equal(resumed.document.querySelector('a[href^="https://github.com/ximicpp/csharp-for-cpp-python"]'), null);
  assert.ok(resumed.document.querySelector('.reference-links a[href^="https://learn.microsoft.com/"]'));
  assert.deepEqual(resumed.saved().report, old);
});

test("radio selection replaces the prior answer and clearing restores unanswered state", async t => {
  const page = await makePage(t);
  page.start();
  assert.equal(page.document.getElementById("clear-answer").disabled, true);
  page.select("A");
  page.select("C");
  assert.deepEqual(page.saved().answers, { Q01: "C" });
  assert.deepEqual([...page.document.querySelectorAll("input:checked")].map(x => x.value), ["C"]);
  assert.equal(page.document.querySelector(".navigator .progress-label strong").textContent, "1 / 40");
  page.click("清除本题选择");
  assert.deepEqual(page.saved().answers, {});
  assert.equal(page.document.querySelectorAll("input:checked").length, 0);
  assert.equal(page.document.querySelector(".navigator .progress-label strong").textContent, "0 / 40");
  assert.equal(page.document.getElementById("clear-answer").disabled, true);
});

test("flagging and answer-sheet navigation preserve question state", async t => {
  const page = await makePage(t);
  page.start();
  page.select("B");
  page.click("○ 标记待检查");
  assert.deepEqual(page.saved().flagged, ["Q01"]);
  assert.equal(page.document.querySelector(".flag-button").getAttribute("aria-pressed"), "true");
  page.jump(runtimeQuestion);
  assert.equal(page.document.querySelector(".question-id").textContent, fixtures.exam.questions.find(q => q.id === runtimeQuestion).display_id);
  assert.equal(page.document.querySelector("#question-title"), page.document.activeElement);
  page.jump("Q01");
  assert.equal(page.document.querySelector("input:checked").value, "B");
  assert.match(page.document.querySelector('.question-grid button[aria-label^="Q01 "]').getAttribute("aria-label"), /已答 待检查/);
  page.click("● 已标记");
  assert.deepEqual(page.saved().flagged, []);
});

test("a new DOM restores answers, flags, current question, and elapsed start time", async t => {
  const page = await makePage(t);
  page.start();
  page.select("D");
  page.click("○ 标记待检查");
  page.jump(runtimeQuestion);
  page.select("A");
  const original = page.saved();
  const resumed = await makePage(t, { storage: page.storage() });
  resumed.click("继续考试 · 已答 2 题");
  assert.equal(resumed.document.querySelector(".question-id").textContent, fixtures.exam.questions.find(q => q.id === runtimeQuestion).display_id);
  assert.equal(resumed.document.querySelector("input:checked").value, "A");
  assert.deepEqual(resumed.saved().answers, original.answers);
  assert.deepEqual(resumed.saved().flagged, ["Q01"]);
  assert.equal(resumed.saved().attemptId, original.attemptId);
  assert.equal(resumed.saved().startedAt, original.startedAt);
});

test("submission warns about missing and flagged questions; return checks the first unanswered", async t => {
  const page = await makePage(t);
  page.start();
  page.select("A");
  page.click("○ 标记待检查");
  page.jump(runtimeQuestion);
  page.click("检查并交卷");
  const dialog = page.document.getElementById("submit-dialog");
  assert.equal(dialog.open, true);
  assert.match(page.document.getElementById("submit-summary").textContent, /39 题未答.*1 题标记待检查/);
  page.click("返回检查");
  assert.equal(dialog.open, false);
  assert.equal(page.document.querySelector(".question-id").textContent, "Q02");
  assert.deepEqual(page.saved().answers, { Q01: "A" });
  assert.equal(page.requests.length, 0);
});

test("a failed submission freezes answers and retries the identical payload after reload", async t => {
  const page = await makePage(t, { submit: async () => { throw new Error("response lost"); } });
  page.start();
  page.fillSampleAnswers();
  page.click("检查并交卷");
  page.document.getElementById("confirm-submit").click();
  await waitFor(() => !page.document.getElementById("submit-error").hidden, "submission error");
  assert.equal(page.requests.length, 1);
  assert.equal(page.document.querySelector("fieldset.options").disabled, true);
  assert.equal(page.document.getElementById("clear-answer").disabled, true);
  assert.equal(page.document.getElementById("cancel-submit").hidden, true);
  assert.deepEqual(page.saved().pending, page.requests[0].payload);
  const frozen = clone(page.saved().answers);
  page.select("D");
  assert.deepEqual(page.saved().answers, frozen, "disabled options cannot modify submitted answers");
  page.document.getElementById("confirm-submit").click();
  await waitFor(() => page.requests.length === 2 && !page.document.getElementById("confirm-submit").disabled, "identical retry");
  assert.equal(page.requests[0].body, page.requests[1].body);
  const replacementExam = clone(fixtures.exam);
  replacementExam.token = "new-process-token";
  const resumed = await makePage(t, { storage: page.storage(), exam: replacementExam });
  resumed.click("继续交卷");
  assert.equal(resumed.document.getElementById("submit-dialog").open, true);
  resumed.document.getElementById("confirm-submit").click();
  await waitFor(() => resumed.document.querySelector(".report-shell"), "report after service restart");
  assert.equal(resumed.requests[0].body, page.requests[0].body);
  assert.equal(resumed.requests[0].headers["X-Exam-Token"], "new-process-token");
});

test("LAN HTTP without randomUUID can save, resume and submit a local exam", async t => {
  const page = await makePage(t, { url: "http://192.168.1.2:8080/", insecureHttp: true });
  page.start(); page.select("B");
  const attempt = page.saved().attemptId;
  assert.match(attempt, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  const resumed = await makePage(t, { storage: page.storage(), url: "http://192.168.1.2:8080/", insecureHttp: true });
  resumed.click(/继续考试/); await resumed.finish();
  assert.equal(resumed.requests[0].payload.attempt_id, attempt);
  assert.equal(resumed.requests[0].payload.answers.Q01, "B");
  assert.equal(resumed.document.querySelectorAll("#review-questions details").length, 40);
});

test("successful report shows Python-scored totals, groups, explanations, and review filters", async t => {
  const page = await makePage(t);
  page.start();
  page.fillSampleAnswers();
  await page.finish();
  assert.deepEqual(page.requests[0].payload.answers, fixtures.answers);
  assert.match(page.document.querySelector(".score-value").textContent, /^2\.5\/ 100$/);
  assert.equal(page.document.querySelector(".raw-score").textContent, "原始得分 1 / 40 · 每题 1 分");
  assert.deepEqual([...page.document.querySelectorAll(".score-counts strong")].map(x => x.textContent), ["1", "1", "38"]);
  assert.equal(page.document.querySelectorAll(".group-result").length, 4);
  assert.match(page.document.querySelector(".group-result").textContent, /1 \/ 10 · 10%/);
  assert.equal(page.document.querySelectorAll("#review-questions details").length, 40);
  page.click("漏题 38");
  assert.equal(page.document.querySelectorAll("#review-questions details").length, 38);
  assert.ok([...page.document.querySelectorAll("#review-questions .status-badge")].every(x => x.textContent === "漏答"));
  page.click("全部 40");
  assert.equal(page.document.querySelectorAll("#review-questions details").length, 40);
  const first = page.document.querySelector("#review-questions details");
  assert.match(first.querySelector(".review-answer").textContent, /正确答案：/);
  assert.ok(first.textContent.includes(fixtures.report.questions[0].rationale.A));
  assert.equal(first.querySelectorAll(".review-option").length, 4);
  assert.ok(first.querySelector(".reference-links a").href.startsWith("https://learn.microsoft.com/"));
  assert.ok(page.document.querySelector(".review-links > span"));
  assert.equal(page.document.querySelector('a[href^="https://github.com/ximicpp/csharp-for-cpp-python"]'), null);
});

test("lessons are available after submission and link back to answered questions", async t => {
  const page = await makePage(t);
  assert.equal(page.document.querySelector(".lessons"), null);
  page.start();
  assert.ok(!page.document.body.textContent.includes(fixtures.report.lessons[0].intro));
  page.fillSampleAnswers();
  await page.finish();
  assert.equal(page.document.querySelectorAll(".lesson-group").length, 4);
  assert.equal(page.document.querySelectorAll(".lesson-question").length, 40);
  assert.ok(page.document.querySelector(".lessons").textContent.includes(fixtures.report.lessons[0].intro));
  assert.ok(page.document.querySelector(".lesson-topic .code-block"));
  const open = [...page.document.querySelectorAll(".group-result button")][0];
  open.click();
  assert.equal(page.document.getElementById("lesson-types").open, true);
  assert.ok(page.document.getElementById("review-Q01").open, "all answers are directly expanded");
  page.click("Q01 · 正确");
  assert.equal(page.document.getElementById("review-Q01").open, true);
  assert.equal(page.button("全部 40").getAttribute("aria-pressed"), "true");
  assert.equal(page.saved().report.score, 1);
});

test("old reports load supplemental lessons with retry and preserve the original report", async t => {
  const old = clone(fixtures.report);
  delete old.lessons;
  const page = await makePage(t, { report: old, lessonResponse: async (_, count) => count === 1
    ? { ok: false, status: 500, json: async () => ({ error: "temporary lesson failure" }) }
    : { ok: true, status: 200, json: async () => ({ lessons: clone(fixtures.report.lessons), markdown: fixtures.report.markdown }) } });
  page.start();
  page.fillSampleAnswers();
  await page.finish();
  const original = clone(page.saved().report);
  page.click("加载本卷讲解");
  await waitFor(() => !page.button("加载本卷讲解").disabled, "lesson retry");
  assert.match(page.document.querySelector(".report-shell").textContent, /temporary lesson failure/);
  page.click("加载本卷讲解");
  await waitFor(() => page.document.querySelectorAll(".lesson-group").length === 4, "supplemental lessons");
  assert.equal(page.requests.length, 1, "loading lessons must not resubmit the exam");
  assert.equal(page.lessonRequests.length, 2);
  assert.deepEqual(page.lessonRequests[0].answers, fixtures.answers);
  assert.deepEqual(page.saved().report, original);
  assert.equal(page.document.querySelectorAll(".group-result button").length, 4);
  page.click("下载讲解 .md");
  assert.ok((await page.downloadText(page.downloads[0])).includes(fixtures.report.lessons[0].intro));
  const resumed = await makePage(t, { storage: page.storage() });
  assert.equal(resumed.document.querySelectorAll(".lesson-group").length, 4);
  assert.equal(resumed.document.querySelectorAll(".group-result button").length, 4);
  assert.equal(resumed.lessonRequests.length, 0);
  assert.deepEqual(resumed.saved().report, original);
});

test("Markdown and JSON downloads preserve the complete report, which reload restores", async t => {
  const page = await makePage(t);
  page.start();
  page.fillSampleAnswers();
  await page.finish();
  page.click("下载报告 .md");
  page.click("下载数据 .json");
  assert.equal(page.downloads.length, 2);
  assert.match(page.downloads[0].filename, /^csharp-exam-.*\.md$/);
  assert.match(page.downloads[1].filename, /^csharp-exam-.*\.json$/);
  const saved = page.saved().report;
  assert.equal(await page.downloadText(page.downloads[0]), saved.markdown);
  assert.deepEqual(JSON.parse(await page.downloadText(page.downloads[1])), saved);
  assert.equal(saved.questions.length, 40);
  assert.equal(saved.lessons.length, 4);
  assert.ok(saved.markdown.includes(saved.lessons[0].intro));
  const resumed = await makePage(t, { storage: page.storage() });
  assert.ok(resumed.document.querySelector(".report-shell"));
  assert.equal(resumed.requests.length, 0, "report reload does not submit again");
  assert.equal(resumed.saved().report.attempt_id, saved.attempt_id);
  resumed.click("返回首页");
  assert.ok(resumed.button("查看上次报告"));
  assert.ok(resumed.button("再考一次"));
});

test("a changed bank offers old-draft export but starts a clean attempt for the new version", async t => {
  const page = await makePage(t);
  page.start();
  page.select("A");
  const oldId = page.saved().attemptId;
  const changed = clone(fixtures.exam);
  changed.version = "updated-question-bank";
  const resumed = await makePage(t, { storage: page.storage(), exam: changed });
  assert.match(resumed.document.getElementById("notice").textContent, /题库已更新/);
  assert.equal([...resumed.document.querySelectorAll("button")].some(x => /继续考试/.test(x.textContent)), false);
  resumed.click("下载旧作答");
  assert.equal(JSON.parse(await resumed.downloadText(resumed.downloads[0])).attemptId, oldId);
  resumed.start();
  assert.equal(resumed.saved().version, changed.version);
  assert.notEqual(resumed.saved().attemptId, oldId);
  assert.deepEqual(resumed.saved().answers, {});
});

test("the old 120-question report is viewable and downloadable without rescoring", async t => {
  const record = { version: legacyFixture.exam.version, attemptId: legacyFixture.report.attempt_id,
    startedAt: 1770000000000, answers: {}, flagged: [], index: 119,
    report: clone(legacyFixture.report), pending: null };
  const raw = JSON.stringify(record);
  const page = await makePage(t, { storage: { [storageKey]: raw } });
  assert.ok(page.document.querySelector(".intro"));
  assert.ok(page.document.querySelector(".intro-copy").textContent.includes("40 题"));
  page.click("查看旧报告");
  assert.equal(page.document.querySelector(".raw-score").textContent, "原始得分 0 / 120 · 每题 1 分");
  page.click("全部 120");
  assert.equal(page.document.querySelectorAll("#review-questions details").length, 120);
  assert.equal(page.document.querySelectorAll(".lesson-group").length, 6);
  page.click("下载数据 .json");
  assert.deepEqual(JSON.parse(await page.downloadText(page.downloads[0])), legacyFixture.report);
  assert.equal(page.storage()[storageKey], raw);
  assert.equal(page.requests.length, 0);
  assert.equal(page.lessonRequests.length, 0);
});

test("question and report content renders as text and rejects executable link protocols", async t => {
  const malicious = '<img src="x" onerror="window.injected=true">';
  const exam = clone(fixtures.exam);
  exam.questions[0].title = malicious;
  exam.questions[0].scenario = `场景 ${malicious}`;
  exam.questions[0].prompt = `查看 \`${malicious}\` 后判断。`;
  exam.questions[0].code = [`var text = "${malicious}";`];
  exam.questions[0].options.A = malicious;
  const report = clone(fixtures.report);
  report.questions[0].title = malicious;
  report.questions[0].rationale.A = malicious;
  report.questions[0].takeaway = malicious;
  report.questions[0].explanation = { principle: malicious, steps: [malicious, malicious], boundary: malicious };
  report.questions[0].sources = [{ title: malicious, url: "javascript:window.injected=true" }];
  report.lessons[0].intro = malicious;
  report.lessons[0].sections[0].explanation = [malicious];
  report.lessons[0].sections[0].code = [malicious];
  report.lessons[0].sections[0].sources = [{ title: malicious, url: "javascript:window.injected=true" }];
  const page = await makePage(t, { exam, report });
  page.start();
  assert.equal(page.document.querySelector("#question-title").textContent, malicious);
  assert.ok(page.document.querySelector(".prompt code").textContent.includes(malicious));
  assert.equal(page.document.querySelectorAll("img, [onerror]").length, 0);
  assert.equal(page.window.injected, undefined);
  page.fillSampleAnswers();
  await page.finish();
  page.click("全部 40");
  assert.ok(page.document.querySelector("#review-questions").textContent.includes(malicious));
  assert.ok(page.document.querySelector(".lessons").textContent.includes(malicious));
  assert.equal(page.document.querySelector(".lessons img"), null);
  assert.equal(page.document.querySelectorAll("img, [onerror], a[href^='javascript:']").length, 0);
  assert.equal(page.window.injected, undefined);
});

test("resuming after nine offline days preserves online time without counting the closed gap", async t => {
  const page = await makePage(t, { controlledClock: true });
  page.start();
  page.advance(15000);
  const saved = page.saved();
  const elapsedSeconds = 9 * 24 * 60 * 60 + 23;
  saved.startedAt = Date.now() - elapsedSeconds * 1000;
  const resumed = await makePage(t, { storage: { [storageKey]: JSON.stringify(saved) }, controlledClock: true });
  resumed.click("继续考试 · 已答 0 题");
  resumed.fillSampleAnswers();
  await resumed.finish();
  const actual = resumed.requests[0].payload.elapsed_seconds;
  assert.equal(actual, 15);
  assert.equal(resumed.saved().report.elapsed_seconds, actual);
});

test("online timer pauses while hidden and after pagehide, resumes after pageshow, and skips sleep", async t => {
  const page = await makePage(t, { controlledClock: true });
  page.start(); page.advance(10000);
  page.visible(false); page.advance(3600000);
  assert.equal(page.document.getElementById("clock").textContent, "00:10");
  page.visible(true); page.advance(5000);
  page.advance(3600000, 3600000);
  assert.equal(page.document.getElementById("clock").textContent, "00:15");
  page.window.dispatchEvent(new page.window.Event("pagehide")); page.advance(10000);
  assert.equal(page.saved().elapsedMs, 15000);
  page.window.dispatchEvent(new page.window.Event("pageshow")); page.advance(5000);
  await page.finish();
  assert.equal(page.requests[0].payload.elapsed_seconds, 20);
});

test("legacy drafts retain choices but never reinterpret wall time as online time", async t => {
  const page = await makePage(t);
  page.start(); page.select("B");
  const saved = page.saved();
  delete saved.elapsedMs; delete saved.timingMode;
  saved.startedAt = 1;
  const resumed = await makePage(t, { storage: { [storageKey]: JSON.stringify(saved) }, controlledClock: true });
  resumed.click("继续考试 · 已答 1 题"); resumed.advance(5000);
  await resumed.finish();
  assert.equal(resumed.requests[0].payload.elapsed_seconds, 5);
  assert.equal(resumed.requests[0].payload.answers.Q01, "B");
});

test("removed practice URLs present only the exam and keep every old local record downloadable", async t => {
  const firstKey = "csharp-course-practice-v1";
  const archivedKey = firstKey + "-archive-old";
  const old = JSON.stringify({ attemptId: "old", firstAnswers: { Q01: "B" }, answers: { Q01: "A" } });
  const storage = { [firstKey]: old, [archivedKey]: "original raw backup", "csharp-course-practice-v1-microsoft": "microsoft backup" };
  const page = await makePage(t, { storage, url: "https://exam.test/?mode=practice" });
  assert.equal(page.document.querySelector(".mode-selection"), null);
  assert.ok(page.button(/开始考试/));
  assert.equal(page.document.querySelectorAll(".practice-archives button").length, 3);
  page.document.querySelector(".practice-archives button").click();
  assert.equal(await page.downloadText(page.downloads[0]), old);
  page.start(); page.select("A");
  assert.equal(page.practiceRequests.length, 0);
  for (const [key, value] of Object.entries(storage)) assert.equal(page.storage()[key], value);
  await page.finish();
  const reviews = [...page.document.querySelectorAll("#review-questions details")];
  assert.equal(reviews.length, 40);
  assert.ok(reviews.every(item => item.open));
  assert.equal(page.document.querySelectorAll(".answer-teaching").length, 40);
});
