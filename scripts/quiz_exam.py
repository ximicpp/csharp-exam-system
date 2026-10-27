"""Local, single-choice exam and reports; the browser never receives answers before submission."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import threading
from urllib.parse import parse_qs, quote, urlsplit
from uuid import UUID, uuid4
import webbrowser

import quiz

ROOT = quiz.ROOT
TITLE = "C# 迁移能力自测"
REPORTS = ROOT / "artifacts/quiz-reports"
STATIC = ROOT / "web/quiz"
MAX_BODY = 16_384
# Match JavaScript's exact integer range without imposing an exam time limit.
MAX_ELAPSED = 9_007_199_254_740_991
GITHUB = "https://github.com/ximicpp/csharp-for-cpp-python/blob/master/"
PUBLIC_FIELDS = ("id", "title", "kind", "tier", "topics", "scenario", "prompt", "options")


def compatible_practice_versions(group: str | None, version: str) -> list[str]:
    path = quiz.BANK / "practice-compatibility.json"
    if not path.exists():
        return []
    manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=quiz.unique_object)
    quiz.require(isinstance(manifest, dict)
                 and set(manifest) == {"source_revision", "reviewed_revision", "note", "papers"},
                 "Invalid practice compatibility manifest")
    quiz.require(all(quiz.nonempty(manifest[key]) for key in ("source_revision", "reviewed_revision", "note"))
                 and isinstance(manifest["papers"], list), "Invalid practice compatibility metadata")
    seen = set()
    result = []
    for paper in manifest["papers"]:
        quiz.require(isinstance(paper, dict) and set(paper) == {"group", "from", "to"},
                     "Invalid practice compatibility paper")
        name = paper["group"]
        quiz.require(name is None or isinstance(name, str) and name in quiz.GROUPS,
                     "Unknown practice compatibility group")
        quiz.require(name not in seen, "Duplicate practice compatibility group")
        seen.add(name)
        quiz.require(all(isinstance(paper[key], str) and re.fullmatch(r"[0-9a-f]{64}", paper[key])
                         for key in ("from", "to")) and paper["from"] != paper["to"],
                     "Invalid practice compatibility versions")
        if name == group and paper["to"] == version:
            result.append(paper["from"])
    return result


class ExamError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def encode_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def parse_submission(body: bytes) -> dict:
    def reject_constant(value: str) -> None:
        raise ValueError(f"Invalid JSON constant: {value}")

    try:
        value = json.loads(body.decode("utf-8"), object_pairs_hook=quiz.unique_object,
                           parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ExamError(400, "提交内容必须是有效 JSON，且不能有重复字段。") from exc
    if not isinstance(value, dict):
        raise ExamError(400, "提交内容必须是 JSON 对象。")
    return value


def chapter_link(relative: str) -> dict:
    path = quiz.local_path(relative)
    heading = next((line[2:].strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
                    if line.startswith("# ")), path.stem)
    return {"title": heading, "url": GITHUB + quote(relative, safe="/")}


def percentage(correct: int, total: int) -> float:
    return round(correct / total * 100, 1) if total else 0.0


def markdown_report(report: dict) -> str:
    display_ids = {q["id"]: q.get("display_id", q["id"]) for q in report["questions"]}
    lines = [f"# {report['title']} · 考试报告", "",
             f"- 提交时间：{report['submitted_at']}",
             f"- 作答编号：{report['attempt_id']}",
             f"- 题库版本：{report['version']}",
             f"- 用时：{report['elapsed_seconds']} 秒",
             f"- 得分：**{report['score']} / {report['total']}**（{report['percent']:.1f}%）",
             f"- 答对 {report['correct']} 题，答错 {report['wrong']} 题，漏答 {report['unanswered']} 题。", "",
             "每题 1 分，答错或漏答 0 分。成绩用于定位复习方向，不代表已掌握，也不修改学习进度。", "",
             "## 分组表现", "", "| 分组 | 答对 | 答错 | 漏答 | 正确率 |",
             "| --- | --- | --- | --- | --- |"]
    if report.get("timing_mode") == "online-v1":
        lines.insert(9, "计时口径：累计考试页可见的在线用时；关闭、后台和无心跳间隔不计入。")
    for group in report["groups"]:
        lines.append(f"| {group['label']} | {group['correct']}/{group['total']} | "
                     f"{group['wrong']} | {group['unanswered']} | {group['percent']:.1f}% |")
    if report.get("lessons"):
        lines += ["", "## 套题讲解", ""]
        for lesson in report["lessons"]:
            lines += quiz.lesson_lines(lesson, level=3, display_ids=display_ids)
    lines += ["", "## 逐题复盘", ""]
    status_labels = {"correct": "答对", "wrong": "答错", "unanswered": "漏答"}
    for q in report["questions"]:
        selected = q["selected"] or "未作答"
        lines += [f"### {display_ids[q['id']]} · {q['title']}", "",
                  f"**{status_labels[q['status']]}** · 你的答案：{selected} · 正确答案：{q['answer']}", ""]
        if q["scenario"]:
            lines += [q["scenario"], ""]
        lines += [q["prompt"], ""]
        if q["compile_error"]:
            lines += ["**编译判断题：以下为故意不能编译的负向样例。**", ""]
        for code in q["code"]:
            fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", code)), default=3))
            lines += [fence + "csharp", code, fence, ""]
        if q.get("explanation"):
            lines += quiz.explanation_lines(q["explanation"])
        lines += ["**逐项辨析**", ""]
        for letter in "ABCD":
            lines += [f"- **{letter}. {q['options'][letter]}**：{q['rationale'][letter]}"]
        lines += ["", f"**学习方向：** {q['takeaway']}", "",
                  "**继续阅读：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in q["learn"]), "",
                  "**官方依据：** " + " · ".join(f"[{s['title']}]({s['url']})" for s in q["sources"]), ""]
    return "\n".join(lines)


def publish_once(path: Path, content: bytes) -> bool:
    """Publish a complete file atomically, without replacing an existing report."""
    temporary = path.with_name(f".{path.name}.{uuid4()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
            return True
        except FileExistsError:
            return False
    finally:
        temporary.unlink(missing_ok=True)


class Exam:
    def __init__(self, report_dir: Path = REPORTS, selected_group: str | None = None):
        if selected_group == "combined":
            self._combined(report_dir)
            return
        bank = quiz.load_bank()
        self.bank_total = sum(len(questions) for questions in bank.values())
        migration = quiz.load_migration_exam(bank)
        selected = quiz.migration_questions(bank, migration)
        self.combined_total = sum(len(questions) for questions in selected.values())
        self.papers = []
        if "microsoft" in bank:
            self.papers.append({"id": "microsoft", "label": quiz.GROUPS["microsoft"], "count": len(bank["microsoft"])})
        self.papers.append({"id": None, "label": "迁移工程扩展卷", "count": self.combined_total})
        # Display numbering is presentation metadata, never part of the answer/version identity.
        display_ids = quiz.migration_numbering(selected) if selected_group is None else {}
        if selected_group is not None:
            if selected_group not in bank:
                raise ExamError(404, "试卷不存在。")
            bank = {selected_group: bank[selected_group]}
        else:
            bank = selected
        self.selected_group = selected_group
        self.title = migration["title"] if selected_group is None else f"{TITLE} · {quiz.GROUPS[selected_group]}"
        self.intro = migration["intro"] if selected_group is None else ""
        if selected_group == "microsoft":
            self.title = "Microsoft Learn C# 配套自测"
        # Explanatory text does not enter the question version hash.
        self.lessons = list(quiz.resolved_lessons(
            bank, quiz.BANK / "lessons/migration" if selected_group is None else None).values())
        units = self.lessons[0]["sections"] if selected_group == "microsoft" else []
        self.questions = []
        self.public_questions = []
        self.groups = []
        for group, questions in bank.items():
            if group == "microsoft":
                self.groups.extend({"id": f"microsoft-{index:02}", "label": section["title"], "count": 10,
                                    "lesson_group": "microsoft"} for index, section in enumerate(units, 1))
            else:
                self.groups.append({"id": group, "label": quiz.GROUPS[group], "count": len(questions)})
            for question in questions:
                display = (self.groups[(int(question["id"][1:]) - 121) // 10] if group == "microsoft"
                           else self.groups[-1])
                private = deepcopy(question)
                private["code"] = [quiz.excerpt(block) for block in question["code"]]
                private["group"] = display["id"]
                self.questions.append(private)
                public = {field: deepcopy(private[field]) for field in PUBLIC_FIELDS}
                public.update(group=display["id"], group_label=display["label"], code=private["code"],
                              compile_error=private["verification"]["kind"] == "compile-error",
                              display_id=display_ids.get(private["id"], private["id"]))
                self.public_questions.append(public)
        # Adding or revising teaching must preserve in-progress answers and scoring versions.
        versioned_questions = [{key: value for key, value in question.items() if key != "explanation"}
                               for question in self.questions]
        self.version = hashlib.sha256(encode_json(versioned_questions)).hexdigest()
        self.practice_compatible_versions = compatible_practice_versions(selected_group, self.version)
        self.explanation_version = hashlib.sha256(encode_json(
            {q["id"]: q["explanation"] for q in self.questions})).hexdigest()
        self.token = secrets.token_urlsafe(32)
        self.report_dir = Path(report_dir)
        self.lock = threading.Lock()
        self.question_ids = {q["id"] for q in self.questions}

    def _combined(self, report_dir: Path) -> None:
        self.parts = {"microsoft": Exam(report_dir, "microsoft"), "extension": Exam(report_dir)}
        self.selected_group, self.title = "combined", "C# 基础与扩展自测"
        self.intro = "基础 120 题、扩展 40 题合为一套考试，按 12 个基础章节、4 个扩展章节排列。可保存后继续，交卷后查看全部题目的解析。"
        self.questions, self.public_questions, self.groups, self.lessons = [], [], [], []
        for name, part in self.parts.items():
            prefix = "基础" if name == "microsoft" else "扩展"
            self.questions.extend(deepcopy(part.questions))
            for question in deepcopy(part.public_questions):
                question["group_label"] = prefix + " · " + question["group_label"]
                question["display_id"] = f"Q{len(self.public_questions) + 1:02}"
                self.public_questions.append(question)
            for group in deepcopy(part.groups):
                group["label"] = prefix + " · " + group["label"]
                self.groups.append(group)
            for lesson in deepcopy(part.lessons):
                lesson["title"] = prefix + " · " + lesson["title"]
                for section in lesson["sections"]:
                    section["title"] = prefix + " · " + section["title"]
                self.lessons.append(lesson)
        self.bank_total = self.parts["extension"].bank_total
        self.combined_total = len(self.questions)
        self.papers = [{"id": "combined", "label": self.title, "count": self.combined_total}]
        self.version = hashlib.sha256(encode_json([{key: value for key, value in q.items() if key != "explanation"}
                                                  for q in self.questions])).hexdigest()
        self.explanation_version = hashlib.sha256(encode_json({q["id"]: q["explanation"] for q in self.questions})).hexdigest()
        self.practice_compatible_versions = []
        self.token, self.report_dir, self.lock = secrets.token_urlsafe(32), Path(report_dir), threading.Lock()
        self.question_ids = {q["id"] for q in self.questions}

    def public(self) -> dict:
        return deepcopy({"version": self.version, "title": self.title, "groups": self.groups,
                         "intro": self.intro,
                         "practice_compatible_versions": self.practice_compatible_versions,
                         "explanation_version": self.explanation_version,
                         "papers": self.papers, "bank_total": self.bank_total, "combined_total": self.combined_total,
                         "selected_group": self.selected_group,
                         **({"previous_versions": {name: part.version for name, part in self.parts.items()}}
                            if self.selected_group == "combined" else {}),
                         "questions": self.public_questions, "total": len(self.questions), "token": self.token})

    def validate(self, payload: dict) -> None:
        if not isinstance(payload, dict) or set(payload) != {"version", "attempt_id", "answers", "elapsed_seconds"}:
            raise ExamError(400, "提交字段应为 version、attempt_id、answers、elapsed_seconds。")
        if payload["version"] != self.version:
            raise ExamError(409, "题库版本已变化，请刷新页面后重新作答。")
        attempt = payload["attempt_id"]
        try:
            valid_id = isinstance(attempt, str) and str(UUID(attempt)) == attempt
        except ValueError:
            valid_id = False
        if not valid_id:
            raise ExamError(400, "attempt_id 必须是标准小写 UUID。")
        elapsed = payload["elapsed_seconds"]
        if type(elapsed) is not int or not 0 <= elapsed <= MAX_ELAPSED:
            raise ExamError(400, "作答用时必须是非负安全整数秒。")
        answers = payload["answers"]
        if (not isinstance(answers, dict) or not set(answers) <= self.question_ids
                or any(not isinstance(value, str) or value not in ("A", "B", "C", "D")
                       for value in answers.values())):
            raise ExamError(400, "只能提交本卷题号及 A、B、C、D 中的一个选项。")

    def grade(self, payload: dict) -> dict:
        self.validate(payload)
        questions = []
        for private, public in zip(self.questions, self.public_questions, strict=True):
            selected = payload["answers"].get(private["id"])
            questions.append(self.answer_result(private, public, selected))
        groups = []
        for group in self.groups:
            subset = [q for q in questions if q["group"] == group["id"]]
            counts = {status: sum(q["status"] == status for q in subset)
                      for status in ("correct", "wrong", "unanswered")}
            groups.append({"id": group["id"], "label": group["label"], "total": len(subset),
                           **({"lesson_group": group["lesson_group"]} if "lesson_group" in group else {}),
                           **counts, "percent": percentage(counts["correct"], len(subset))})
        counts = {status: sum(g[status] for g in groups) for status in ("correct", "wrong", "unanswered")}
        report = {"attempt_id": payload["attempt_id"], "version": self.version, "title": self.title,
                  "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "elapsed_seconds": payload["elapsed_seconds"], "timing_mode": "online-v1", "total": len(questions), **counts,
                  "score": counts["correct"], "percent": percentage(counts["correct"], len(questions)),
                  "groups": groups, "questions": questions, "lessons": deepcopy(self.lessons),
                  "files": {extension: f"artifacts/quiz-reports/{payload['attempt_id']}.{suffix}"
                            for extension, suffix in (("json", "json"), ("markdown", "md"))}}
        report["markdown"] = markdown_report(report)
        return report

    def answer_result(self, private: dict, public: dict, selected: str | None) -> dict:
        result = deepcopy(public)
        answer = private["answers"][0]
        result.update(selected=selected, answer=answer,
                      status="unanswered" if selected is None else "correct" if selected == answer else "wrong",
                      rationale=deepcopy(private["rationale"]), takeaway=private["takeaway"],
                      explanation=deepcopy(private["explanation"]), explanation_version=self.explanation_version,
                      learn=[chapter_link(p) for p in private["learn"]], sources=deepcopy(private["sources"]))
        return result

    def practice(self, payload: dict) -> dict:
        """Check one selected answer without submitting an exam or saving a report."""
        if not isinstance(payload, dict) or set(payload) != {"version", "question_id", "answer"}:
            raise ExamError(400, "练习提交字段应为 version、question_id、answer。")
        if payload["version"] != self.version:
            raise ExamError(409, "题库版本已变化，请刷新页面后重新练习。")
        qid, selected = payload["question_id"], payload["answer"]
        if (not isinstance(qid, str) or qid not in self.question_ids
                or not isinstance(selected, str) or selected not in ("A", "B", "C", "D")):
            raise ExamError(400, "只能检查本卷题号及 A、B、C、D 中的一个选项。")
        index = next(index for index, question in enumerate(self.questions) if question["id"] == qid)
        return {"version": self.version,
                "question": self.answer_result(self.questions[index], self.public_questions[index], selected)}

    def _existing(self, path: Path, payload: dict) -> dict:
        report = json.loads(path.read_text(encoding="utf-8"))
        original_answers = {q["id"]: q["selected"] for q in report["questions"] if q["selected"] is not None}
        if (report["version"] != payload["version"] or original_answers != payload["answers"]
                or report["elapsed_seconds"] != payload["elapsed_seconds"]):
            raise ExamError(409, "此作答编号已有不同内容的报告，请开始一次新考试。")
        return report

    def lesson_supplement(self, payload: dict) -> dict:
        """Read lessons for an already submitted exam without rewriting its report."""
        self.validate(payload)
        path = self.report_dir / f"{payload['attempt_id']}.json"
        if not path.is_file():
            raise ExamError(404, "交卷后才能查看本卷讲解。")
        self._existing(path, payload)
        lessons = deepcopy(self.lessons)
        lines = [f"# {self.title} · 套题讲解", "", f"题库版本：{self.version}", ""]
        for lesson in lessons:
            lines += quiz.lesson_lines(lesson, display_ids={q["id"]: q["display_id"] for q in self.public_questions})
        return {"lessons": lessons, "markdown": "\n".join(lines)}

    def submit(self, payload: dict) -> dict:
        self.validate(payload)
        with self.lock:
            self.report_dir.mkdir(parents=True, exist_ok=True)
            path = self.report_dir / f"{payload['attempt_id']}.json"
            if path.exists():
                report = self._existing(path, payload)
            else:
                report = self.grade(payload)
                if not publish_once(path, encode_json(report) + b"\n"):
                    report = self._existing(path, payload)
            markdown = report["markdown"].encode("utf-8")
            markdown_path = path.with_suffix(".md")
            if not publish_once(markdown_path, markdown) and markdown_path.read_bytes() != markdown:
                raise OSError("Existing Markdown report differs from saved JSON")
            return report


class ExamServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, exam: Exam, static_dir: Path = STATIC):
        self.exam = exam
        self.papers = {None: exam}
        self.paper_lock = threading.Lock()
        self.static_dir = Path(static_dir)
        super().__init__(("127.0.0.1", port), ExamHandler)
        self.origin = f"http://127.0.0.1:{self.server_port}"

    def paper(self, query: str) -> Exam:
        params = parse_qs(query, keep_blank_values=True)
        if not params:
            return self.exam
        if set(params) != {"group"} or len(params["group"]) != 1 or params["group"][0] not in (*quiz.GROUPS, "combined", "extension"):
            raise ExamError(404, "试卷不存在。")
        group = params["group"][0]
        with self.paper_lock:
            if group not in self.papers:
                self.papers[group] = Exam(self.exam.report_dir, selected_group=None if group == "extension" else group)
            return self.papers[group]

    def handle_error(self, request, client_address) -> None:
        # Broken local connections should not expose a traceback or stop the server.
        pass


class ExamHandler(BaseHTTPRequestHandler):
    server: ExamServer
    server_version = "QuizExam"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format: str, *args) -> None:
        pass

    def respond(self, status: int, body: bytes, content_type: str, *, location: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if location:
            self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                         "frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def json_response(self, status: int, payload: dict) -> None:
        self.respond(status, encode_json(payload), "application/json; charset=utf-8")

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self.json_response(code, {"error": "请求未被接受。"})

    def local_request(self) -> None:
        hosts = self.headers.get_all("Host", [])
        if hosts != [self.server.origin.removeprefix("http://")]:
            raise ExamError(403, "只允许通过本机考试地址访问。")
        origins = self.headers.get_all("Origin", [])
        if origins and origins != [self.server.origin]:
            raise ExamError(403, "不允许其他页面来源访问考试。")
        fetch_site = self.headers.get("Sec-Fetch-Site")
        if fetch_site and fetch_site not in ("same-origin", "none"):
            raise ExamError(403, "不允许跨来源访问考试。")

    def do_GET(self) -> None:
        try:
            self.local_request()
            target = urlsplit(self.path)
            if target.scheme or target.netloc or target.fragment:
                raise ExamError(404, "页面不存在。")
            if target.path == "/api/exam":
                self.json_response(200, self.server.paper(target.query).public())
                return
            if (target.path in ("/", "/index.html") and self.server.exam.selected_group == "combined"
                    and parse_qs(target.query).get("group", [None])[0] in ("microsoft", "extension")):
                self.respond(302, b"", "text/html", location="/")
                return
            if target.path == "/question-bank.md":
                path = quiz.DOCS / "question-bank.md"
                if not path.is_file():
                    raise ExamError(404, "题库归档尚未生成，请运行题库生成命令。")
                self.respond(200, path.read_bytes(), "text/markdown; charset=utf-8")
                return
            routes = {"/": ("index.html", "text/html"), "/index.html": ("index.html", "text/html"),
                      "/id.js": ("id.js", "text/javascript"), "/app.js": ("app.js", "text/javascript"), "/styles.css": ("styles.css", "text/css")}
            if target.path not in routes:
                raise ExamError(404, "页面不存在。")
            name, content_type = routes[target.path]
            path = self.server.static_dir / name
            if not path.is_file():
                raise ExamError(404, "考试页面文件不存在。")
            self.respond(200, path.read_bytes(), content_type + "; charset=utf-8")
        except ExamError as exc:
            self.json_response(exc.status, {"error": str(exc)})
        except (OSError, ValueError):
            self.json_response(500, {"error": "读取考试内容失败，请检查本地文件。"})

    def do_POST(self) -> None:
        try:
            self.local_request()
            target = urlsplit(self.path)
            if (target.scheme or target.netloc or target.fragment
                    or target.path not in ("/api/submit", "/api/lessons")):
                raise ExamError(404, "接口不存在。")
            paper = self.server.paper(target.query)
            tokens = self.headers.get_all("X-Exam-Token", [])
            if (len(tokens) != 1 or not tokens[0].isascii()
                    or not secrets.compare_digest(tokens[0], paper.token)):
                raise ExamError(403, "考试令牌已失效，请刷新页面后重试。")
            content_types = self.headers.get_all("Content-Type", [])
            if (len(content_types) != 1
                    or content_types[0].split(";", 1)[0].strip().lower() != "application/json"):
                raise ExamError(415, "请以 application/json 提交答案。")
            lengths = self.headers.get_all("Content-Length", [])
            if (self.headers.get_all("Transfer-Encoding") or len(lengths) != 1
                    or not lengths[0].isascii() or not lengths[0].isdigit()):
                raise ExamError(400, "请求长度无效。")
            if len(lengths[0]) > 6:
                raise ExamError(413, "提交内容过大。")
            length = int(lengths[0])
            if length > MAX_BODY:
                raise ExamError(413, "提交内容过大。")
            body = self.rfile.read(length)
            if len(body) != length:
                raise ExamError(400, "提交内容不完整。")
            payload = parse_submission(body)
            if target.path == "/api/submit":
                report = paper.submit(payload)
            else:
                report = paper.lesson_supplement(payload)
            self.json_response(200, report)
        except ExamError as exc:
            self.json_response(exc.status, {"error": str(exc)})
        except (TimeoutError, socket.timeout):
            self.json_response(408, {"error": "提交超时，请重试。"})
        except (OSError, ValueError, KeyError, TypeError):
            self.json_response(500, {"error": "保存报告失败，请检查本地报告目录后重试。"})


def make_server(port: int = 0, report_dir: Path = REPORTS, static_dir: Path = STATIC) -> ExamServer:
    return ExamServer(port, Exam(report_dir, "combined"), static_dir)


def serve(port: int = 8765, open_browser: bool = True) -> None:
    with make_server(port) as server:
        url = server.origin + "/"
        print(f"考试页面：{url}", flush=True)
        print(f"{len(server.exam.questions)} 道单选题；交卷后自动评分并保存报告。按 Ctrl-C 结束服务。", flush=True)
        if open_browser:
            try:
                webbrowser.open(url)
            except webbrowser.Error:
                print("未能自动打开浏览器，请手动打开上面的地址。", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n考试服务已关闭。", flush=True)
