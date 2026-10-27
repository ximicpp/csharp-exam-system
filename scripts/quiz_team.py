"""Team quiz: authenticated web service, server progress, score summaries and administration."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import getpass
import io
import ipaddress
import json
from pathlib import Path
import secrets
import re
import sqlite3
import sys
from urllib.parse import urlsplit

from flask import Flask, g, jsonify, make_response, redirect, request
from werkzeug.exceptions import HTTPException

from quiz_exam import Exam, ExamError, ROOT, STATIC, encode_json, parse_submission
from quiz_team_store import SESSION_SECONDS, Store
from quiz_team_identity import IdentityService, account_text

DATABASE = ROOT / "artifacts/quiz-team/team.sqlite3"
COOKIE = "quiz_team_session"
HTTP_COOKIE = "quiz_team_session_http"


def summarize(rows: list[dict], policy: str) -> dict:
    """Select submitted exams within each user/paper/version; drafts never count as scores."""
    records = []
    for row in rows:
        report = json.loads(row["report"])
        questions = report["questions"]
        correct = sum(q["status"] == "correct" for q in questions)
        total = report["total"]
        date = row["submitted"]
        identity = report.get("identity", {})
        records.append({"attempt_id": row["id"], "username": row["username"], "display_name": row["display_name"],
                        "identity_status": identity.get("status", "legacy"), "identity_source": identity.get("source", "password"),
                        "input_account": identity.get("account", row["username"]), "member_id": identity.get("member_id"),
                        "client_ip": identity.get("client_ip", ""), "computer_name": identity.get("computer_name", ""),
                        "paper": row["paper"], "mode": row["mode"], "version": row["version"],
                        "_sort_time": date,
                        "time": datetime.fromtimestamp(date, timezone.utc).isoformat(timespec="seconds"),
                        "correct": correct, "wrong": sum(q["status"] == "wrong" for q in questions),
                        "unanswered": report["unanswered"], "total": total,
                        "score": report["score"],
                        "percent": round(correct / total * 100, 1) if total else None,
                        "elapsed_seconds": report["elapsed_seconds"],
                        "questions": questions})
    buckets = {}
    for item in records:
        key = (item["username"], item["paper"], item["version"], item["mode"])
        buckets.setdefault(key, []).append(item)
    selected = []
    for values in buckets.values():
        values.sort(key=lambda item: (item["_sort_time"], item["attempt_id"]))
        selected.extend(values if policy == "all" else [values[0] if policy == "first" else values[-1] if policy == "latest"
                        else max(values, key=lambda item: (item["correct"] / item["total"], item["_sort_time"]))])
    stats = {}
    for item in selected:
        key = (item["paper"], item["version"], item["mode"], item["identity_status"])
        bucket = stats.setdefault(key, {"paper": key[0], "version": key[1], "mode": key[2], "people": set(), "attempts": 0,
                                      "identity_status": key[3],
                                      "percentages": [], "groups": {}, "questions": {}})
        bucket["people"].add(item["username"])
        bucket["attempts"] += 1
        if item["percent"] is not None:
            bucket["percentages"].append(item["correct"] / item["total"] * 100)
        for question in item["questions"]:
            group = bucket["groups"].setdefault(question["group"], {"label": question["group_label"], "correct": 0, "total": 0})
            group["correct"] += question["status"] == "correct"
            group["total"] += 1
            value = bucket["questions"].setdefault(question["id"], {"id": question.get("display_id", question["id"]),
                                                                   "title": question["title"], "correct": 0, "wrong": 0,
                                                                   "unanswered": 0, "total": 0})
            value[question["status"]] += 1
            value["total"] += 1
    summaries = []
    for bucket in stats.values():
        percentages = bucket.pop("percentages")
        bucket["people"] = len(bucket["people"])
        bucket["average_percent"] = round(sum(percentages) / len(percentages), 1) if percentages else None
        bucket["groups"] = list(bucket["groups"].values())
        bucket["questions"] = list(bucket["questions"].values())
        summaries.append(bucket)
    selected.sort(key=lambda item: (item["_sort_time"], item["attempt_id"]), reverse=True)
    for item in selected:
        del item["questions"]
        del item["_sort_time"]
    return {"policy": policy, "records": selected, "summaries": summaries}


def csv_export(records: list[dict]) -> str:
    stream = io.StringIO(newline="")
    fields = ("username", "display_name", "paper", "mode", "version", "attempt_id", "time", "score", "total", "percent",
              "correct", "wrong", "unanswered", "elapsed_seconds", "identity_status", "identity_source", "input_account", "member_id",
              "client_ip", "computer_name")
    writer = csv.writer(stream)
    writer.writerow(fields)
    for record in records:
        # Spreadsheet formula injection is prevented for user-controlled text.
        writer.writerow(["'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@"))
                         else value for value in (record[field] for field in fields)])
    return "\ufeff" + stream.getvalue()


def create_app(database: Path = DATABASE, public_url: str = "http://127.0.0.1:8768", *, allow_insecure_http: bool = False,
               roster: Path | None = None, proxy_key: str | None = None) -> Flask:
    origin = urlsplit(public_url)
    network_http = origin.scheme == "http" and origin.hostname not in ("127.0.0.1", "localhost", "::1")
    if (origin.scheme not in ("http", "https") or not origin.hostname or origin.username or origin.password
            or origin.path not in ("", "/") or origin.query or origin.fragment
            or network_http and not allow_insecure_http):
        raise ValueError("Use an HTTPS public origin, or explicitly opt into unencrypted LAN HTTP")
    # Secure HTTPS cookies cannot be overwritten by HTTP on the same host, even on another port.
    cookie_name = HTTP_COOKIE if network_http else COOKIE
    public_url = public_url.rstrip("/")
    app = Flask(__name__, static_folder=None)
    app.config.update(MAX_CONTENT_LENGTH=65_536, TRUSTED_HOSTS=[origin.hostname])
    store = Store(database)
    app.extensions["quiz_store"] = store
    identities = IdentityService(store, roster) if roster else None
    if proxy_key is not None and (not proxy_key.isascii() or len(proxy_key) < 32):
        raise ValueError("Proxy key must contain at least 32 ASCII characters")
    combined = Exam(selected_group="combined")
    papers = {None: combined, "combined": combined, "extension": combined.parts["extension"], "microsoft": combined.parts["microsoft"]}

    def body():
        if request.mimetype != "application/json":
            raise ExamError(415, "请使用 application/json。")
        return parse_submission(request.get_data())

    def paper():
        group = request.args.get("group")
        if group not in papers or len(request.args.getlist("group")) > 1:
            raise ExamError(404, "题库不存在。")
        return papers[group]

    def mode():
        value = request.args.get("mode", "exam")
        if value != "exam" or len(request.args.getlist("mode")) > 1:
            raise ExamError(400, "作答模式无效。")
        return value

    def user(admin=False, allow_password_change=False):
        if not g.auth:
            raise ExamError(401, "请先登录。")
        if g.auth["user"]["must_change"] and not allow_password_change:
            raise ExamError(403, "请先修改初始密码。")
        if admin and g.auth["user"]["role"] != "admin":
            raise ExamError(403, "只有管理员可以查看全部成绩或管理账号。")
        return g.auth["user"]

    @app.before_request
    def boundaries():
        # Preserve the externally configured Host through the reverse proxy; do not trust arbitrary forwarded headers.
        if request.host.lower() != origin.netloc.lower():
            raise ExamError(403, "请通过配置的题库地址访问。")
        if request.headers.get("Origin") not in (None, public_url):
            raise ExamError(403, "不允许跨来源请求。")
        if request.headers.get("Sec-Fetch-Site") not in (None, "same-origin", "none"):
            raise ExamError(403, "不允许跨来源请求。")
        g.auth = store.session(request.cookies.get(cookie_name))
        if g.auth and identities and not identities.allows(g.auth):
            g.auth = None
        supplied_key = request.headers.get("X-Quiz-Proxy-Key", "")
        trusted_proxy = proxy_key is not None and supplied_key.isascii() and secrets.compare_digest(proxy_key, supplied_key)
        try:
            g.client_ip = str(ipaddress.ip_address(request.headers.get("X-Quiz-Client-IP", "") if trusted_proxy else request.remote_addr))
        except ValueError:
            g.client_ip = ""
        g.domain = None
        if identities and trusted_proxy and request.headers.get("X-Quiz-Domain-Account"):
            sid = request.headers.get("X-Quiz-Domain-SID", "")
            if not re.fullmatch(r"S-1-(?:[0-9]+-)+[0-9]+", sid) or len(sid) > 184:
                raise ExamError(403, "认证入口未提供有效 Windows SID。")
            g.domain = {"account": account_text(request.headers["X-Quiz-Domain-Account"]), "sid": sid}
        if g.domain and g.auth and g.auth["user"]["role"] != "admin" and g.auth.get("identity", {}).get("domain_sid") != g.domain["sid"]:
            g.auth = None
        if request.method not in ("GET", "HEAD"):
            if request.method != "POST" or request.headers.get("Origin") != public_url:
                raise ExamError(403, "保存与登录须来自题库页面。")
            if request.path not in ("/api/login", "/api/identify"):
                user(allow_password_change=request.path in ("/api/password", "/api/logout"))
                token = request.headers.get("X-Exam-Token", "")
                if not token.isascii() or not secrets.compare_digest(token, g.auth["csrf"]):
                    raise ExamError(403, "登录令牌失效，请重新登录。")

    @app.after_request
    def security_headers(response):
        response.headers.update({"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                                 "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                                 "img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
        return response

    @app.errorhandler(ExamError)
    def expected_error(error):
        return jsonify(error=str(error)), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error="请求未被接受。"), error.code

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        app.logger.error("Team database operation failed: %s", type(error).__name__)
        return jsonify(error="服务器暂未能保存。请保留页面并重试，或联系管理员检查数据库。"), 503

    def cookie(response, token):
        response.set_cookie(cookie_name, token, max_age=SESSION_SECONDS, httponly=True, secure=origin.scheme == "https", samesite="Strict", path="/")
        return response

    @app.get("/api/session")
    def session():
        auth = g.auth
        if g.domain and auth and auth["user"]["role"] != "admin" and auth.get("identity", {}).get("domain_sid") != g.domain["sid"]:
            auth = None
        result = dict(auth or {"user": None})
        if identities:
            result["identity_options"] = identities.options(g.domain)
        return jsonify(result)

    @app.post("/api/identify")
    def identify():
        if not identities:
            raise ExamError(404, "免密学员入口未启用。")
        payload = body()
        if set(payload) != {"account", "computer_name"}:
            raise ExamError(400, "请输入账号或姓名，计算机名可留空。")
        token, auth = identities.login(payload["account"], payload["computer_name"], g.client_ip, g.domain)
        if request.cookies.get(cookie_name):
            store.logout(request.cookies[cookie_name])
        return cookie(jsonify(auth), token)

    @app.post("/api/login")
    def login():
        payload = body()
        if set(payload) != {"username", "password"}:
            raise ExamError(400, "请输入账号和密码。")
        token, auth = store.login(payload["username"], payload["password"])
        if identities and auth["user"]["role"] != "admin":
            store.logout(token)
            raise ExamError(403, "学员请使用名单中的本人完整姓名登录，账号密码入口仅供管理员使用。")
        if request.cookies.get(cookie_name):
            store.logout(request.cookies[cookie_name])
        return cookie(jsonify(auth), token)

    @app.post("/api/logout")
    def logout():
        store.logout(request.cookies.get(cookie_name, ""))
        response = jsonify(ok=True)
        response.delete_cookie(cookie_name, path="/", secure=origin.scheme == "https", httponly=True, samesite="Strict")
        return response

    @app.post("/api/password")
    def change_password():
        account = user(allow_password_change=True)
        if g.auth.get("identity"):
            raise ExamError(403, "免密学员入口无需设置密码；原账号请使用账号密码入口。")
        payload = body()
        if set(payload) != {"old_password", "new_password"}:
            raise ExamError(400, "请输入旧密码和新密码。")
        store.change_password(account["id"], payload["old_password"], payload["new_password"])
        token, auth = store.login(account["username"], payload["new_password"])
        return cookie(jsonify(auth), token)

    @app.get("/api/exam")
    def exam():
        user()
        result = paper().public()
        result["token"] = g.auth["csrf"]
        result["practice_compatible_versions"] = []
        return jsonify(result)

    @app.route("/api/progress", methods=["GET", "POST"])
    def progress():
        account, selected, selected_mode = user(), paper(), mode()
        if request.method == "GET":
            return jsonify(store.load(account["id"], selected, selected_mode))
        return jsonify(store.save(account["id"], selected, selected_mode, body(), identity=g.auth.get("identity")))

    @app.post("/api/submit")
    def submit():
        return jsonify(store.submit(user(), paper(), body()))

    @app.post("/api/timing")
    def timing():
        return jsonify(store.heartbeat(user()["id"], paper(), body()))

    @app.post("/api/lessons")
    def lessons():
        selected, account, payload = paper(), user(), body()
        selected.validate(payload)
        report = store.submitted(account["id"], payload["attempt_id"])
        answers = {q["id"]: q["selected"] for q in report["questions"] if q["selected"] is not None}
        if report["version"] != payload["version"] or answers != payload["answers"]:
            raise ExamError(409, "报告与作答不一致。")
        return jsonify(lessons=report["lessons"], markdown=report["markdown"])

    @app.get("/api/reports/<attempt_id>")
    def report(attempt_id):
        account = user()
        # Administrators see summaries, not a route that bypasses per-user report ownership.
        return jsonify(store.submitted(account["id"], attempt_id))

    @app.get("/api/attempts/<attempt_id>")
    def old_attempt(attempt_id):
        account = user()
        with store.connect() as db:
            row = db.execute("SELECT * FROM attempts WHERE id=? AND user_id=?", (attempt_id, account["id"])).fetchone()
        if not row:
            raise ExamError(404, "作答记录不存在。")
        return jsonify(store.hydrate(row, papers[row["paper"]]))

    @app.get("/api/history")
    def history():
        account = user()
        with store.connect() as db:
            rows = db.execute("SELECT id,paper,version,updated,state,report FROM attempts WHERE user_id=? AND mode='exam' ORDER BY updated DESC", (account["id"],)).fetchall()
        return jsonify(attempts=[{"attempt_id": row["id"], "paper": row["paper"], "version": row["version"],
                                  "time": datetime.fromtimestamp(row["updated"], timezone.utc).isoformat(timespec="seconds"),
                                  "answered": len(json.loads(row["state"])["answers"]), "submitted": row["report"] is not None} for row in rows])

    @app.get("/api/results")
    def results():
        account = user(admin=request.args.get("scope") == "all")
        policy = request.args.get("policy", "first")
        selected_paper, selected_mode = request.args.get("paper", "all"), request.args.get("mode", "exam")
        attribution = request.args.get("attribution", "all")
        if (policy not in ("first", "latest", "best", "all") or selected_paper not in ("all", "combined", "extension", "microsoft")
                or selected_mode != "exam" or request.args.get("scope", "self") not in ("self", "all")
                or attribution not in ("all", "matched", "unmatched", "legacy")):
            raise ExamError(400, "汇总筛选参数无效。")
        rows = store.rows(None if request.args.get("scope") == "all" else account["id"])
        start, end = request.args.get("from"), request.args.get("to")
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
            end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None
        except ValueError as exc:
            raise ExamError(400, "日期应为 YYYY-MM-DD。") from exc
        if start_date and end_date and start_date > end_date:
            raise ExamError(400, "开始日期不能晚于结束日期。")
        rows = [row for row in rows if row["mode"] == selected_mode and (selected_paper == "all" or row["paper"] == selected_paper)
                and (attribution == "all" or json.loads(row["report"]).get("identity", {}).get("status", "legacy") == attribution)
                and (not request.args.get("version") or row["version"] == request.args["version"])
                and (not start_date or datetime.fromtimestamp(row["submitted"], timezone.utc).date() >= start_date)
                and (not end_date or datetime.fromtimestamp(row["submitted"], timezone.utc).date() <= end_date)]
        result = summarize(rows, policy)
        if request.args.get("format") == "csv":
            response = make_response(csv_export(result["records"]))
            response.headers.update({"Content-Type": "text/csv; charset=utf-8", "Content-Disposition": 'attachment; filename="quiz-results.csv"'})
            return response
        return jsonify(result)

    @app.route("/api/admin/users", methods=["GET", "POST"])
    def users():
        user(admin=True)
        if request.method == "GET":
            if identities:
                return jsonify(users=identities.users())
            with store.connect() as db:
                return jsonify(users=[dict(row) for row in db.execute("SELECT username,display_name,role,disabled FROM users ORDER BY username")])
        if identities:
            raise ExamError(403, "当前仅允许名单中的学员登录，请通过名单源文件维护学员。")
        payload = body()
        if set(payload) != {"username", "display_name"}:
            raise ExamError(400, "请输入账号与显示姓名。")
        initial = secrets.token_urlsafe(18)
        account = store.add_user(payload["username"], payload["display_name"], initial)
        return jsonify(user=account, initial_password=initial), 201

    @app.get("/")
    @app.get("/index.html")
    def index():
        if request.args.get("group") in ("microsoft", "extension"):
            return redirect("/")
        html = (STATIC / "index.html").read_text(encoding="utf-8").replace('<body>', '<body data-team="true">')
        html = html.replace('<script src="/app.js"', '<link rel="stylesheet" href="/team.css">\n  <script src="/team-sync.js" defer></script>\n  <script src="/app.js"')
        return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})

    @app.get("/results")
    @app.get("/admin")
    def dashboard():
        return make_response((STATIC / "team-results.html").read_text(encoding="utf-8"), 200, {"Content-Type": "text/html; charset=utf-8"})

    @app.get("/<name>")
    def assets(name):
        if name not in ("id.js", "app.js", "styles.css", "team-sync.js", "team-results.js", "team.css"):
            raise ExamError(404, "页面不存在。")
        return make_response((STATIC / name).read_bytes(), 200,
                             {"Content-Type": "text/javascript; charset=utf-8" if name.endswith(".js") else "text/css; charset=utf-8"})

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE)
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--bind", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8768)
    serve.add_argument("--public-url", default="http://127.0.0.1:8768")
    serve.add_argument("--allow-insecure-http", action="store_true", help="Explicitly allow unencrypted LAN HTTP")
    serve.add_argument("--threads", type=int, default=8)
    serve.add_argument("--roster", type=Path, help="Enable passwordless students using an explicit roster")
    serve.add_argument("--proxy-key-file", type=Path, help="Owner-only gateway key file; never pass its value on the command line")
    add = commands.add_parser("add-user")
    add.add_argument("username")
    add.add_argument("--name", required=True)
    add.add_argument("--admin", action="store_true")
    add.add_argument("--password-stdin", action="store_true", help="Read one password line for provisioning; never put passwords on command lines")
    reset = commands.add_parser("reset-password")
    reset.add_argument("username")
    commands.add_parser("disable-user").add_argument("username")
    commands.add_parser("backup").add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "serve":
        if not 1 <= args.port <= 65535 or not 1 <= args.threads <= 64:
            parser.error("Port must be 1–65535 and threads 1–64")
        proxy_key = args.proxy_key_file.read_text(encoding="ascii").strip() if args.proxy_key_file else None
        app = create_app(args.database, args.public_url, allow_insecure_http=args.allow_insecure_http, roster=args.roster, proxy_key=proxy_key)
        from waitress import serve as waitress_serve
        print(f"Team quiz: {args.public_url}; listening on {args.bind}:{args.port}", flush=True)
        waitress_serve(app, host=args.bind, port=args.port, threads=args.threads, max_request_body_size=65_536,
                       connection_limit=200, channel_timeout=30, clear_untrusted_proxy_headers=True)
    else:
        store = Store(args.database)
        if args.command == "add-user":
            secret = sys.stdin.readline().rstrip("\r\n") if args.password_stdin else getpass.getpass("Initial password (12–128 characters): ")
            if not args.password_stdin and secret != getpass.getpass("Repeat password: "):
                parser.error("Passwords differ")
            account = store.add_user(args.username, args.name, secret, args.admin, must_change=not args.admin)
            print(f"PASS: created {account['role']} {account['username']}")
        elif args.command == "reset-password":
            secret = getpass.getpass("New initial password: ")
            if secret != getpass.getpass("Repeat password: "):
                parser.error("Passwords differ")
            store.reset_password(args.username, secret)
            print("PASS: password reset; prior sessions invalidated")
        elif args.command == "disable-user":
            store.disable_user(args.username)
            print("PASS: account disabled; records preserved")
        else:
            store.backup(args.destination)
            print("PASS: consistent database backup")


if __name__ == "__main__":
    try:
        main()
    except (ExamError, OSError, ValueError, sqlite3.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
