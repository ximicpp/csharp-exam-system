"""Transactional account, progress and immutable score storage for the team service."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from uuid import UUID

from werkzeug.security import check_password_hash, generate_password_hash

from quiz_exam import Exam, ExamError, MAX_ELAPSED, encode_json, markdown_report

SESSION_SECONDS = 12 * 60 * 60


def canonical_id(value: object) -> bool:
    try:
        return isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        return False


def username(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}", value):
        raise ExamError(400, "账号应为 1–64 个英文字母、数字、点、横线或下划线。")
    return value.lower()


def password(value: object) -> str:
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        raise ExamError(400, "密码须为 12–128 个字符。")
    return value


def public_user(row) -> dict:
    return {key: row[key] for key in ("id", "username", "display_name", "role", "must_change")}


class Store:
    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3):
                raise ValueError("Unsupported team database schema; preserve the database before upgrading")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
                  password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','admin')),
                  disabled INTEGER NOT NULL DEFAULT 0, must_change INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS sessions (
                  token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                  csrf TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS login_failures (username TEXT NOT NULL, at REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS login_failure_time ON login_failures(username, at);
                CREATE TABLE IF NOT EXISTS attempts (
                  id TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                  paper TEXT NOT NULL, mode TEXT NOT NULL, version TEXT NOT NULL,
                  started REAL NOT NULL, updated REAL NOT NULL, state TEXT NOT NULL,
                  report TEXT, submitted REAL);
                CREATE TABLE IF NOT EXISTS progress (
                  user_id INTEGER NOT NULL REFERENCES users(id), paper TEXT NOT NULL, mode TEXT NOT NULL,
                  revision INTEGER NOT NULL, attempt_id TEXT NOT NULL REFERENCES attempts(id),
                  PRIMARY KEY(user_id,paper,mode));
                CREATE TABLE IF NOT EXISTS mutations (
                  user_id INTEGER NOT NULL REFERENCES users(id), id TEXT NOT NULL, request_hash TEXT NOT NULL,
                  response TEXT NOT NULL, PRIMARY KEY(user_id,id));
                CREATE TABLE IF NOT EXISTS roster_members (
                  id TEXT PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL REFERENCES users(id), name TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS identity_keys (
                  key TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                  member_id TEXT REFERENCES roster_members(id));
                CREATE TABLE IF NOT EXISTS session_identity (
                  token_hash TEXT PRIMARY KEY REFERENCES sessions(token_hash) ON DELETE CASCADE,
                  context TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS login_events (
                  id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                  at REAL NOT NULL, context TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempt_identity (
                  attempt_id TEXT PRIMARY KEY REFERENCES attempts(id), context TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS attempt_timers (
                  attempt_id TEXT PRIMARY KEY REFERENCES attempts(id) ON DELETE CASCADE,
                  elapsed_ms INTEGER NOT NULL DEFAULT 0, credited_until REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS timer_clients (
                  attempt_id TEXT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
                  client_id TEXT NOT NULL, sequence INTEGER NOT NULL, active_ms INTEGER NOT NULL,
                  seen REAL NOT NULL, PRIMARY KEY(attempt_id,client_id));
                PRAGMA user_version=3;
            """)
        self.dummy_hash = generate_password_hash(secrets.token_urlsafe(32))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    def add_user(self, name: str, display: str, secret: str, admin=False, must_change=True) -> dict:
        name, secret = username(name), password(secret)
        if not isinstance(display, str) or not display.strip() or len(display) > 80:
            raise ExamError(400, "显示姓名须为 1–80 个字符。")
        hashed = generate_password_hash(secret)
        try:
            with self.transaction() as db:
                cursor = db.execute("INSERT INTO users(username,display_name,password_hash,role,must_change) VALUES(?,?,?,?,?)",
                                    (name, display.strip(), hashed, "admin" if admin else "student", int(must_change)))
                return public_user(db.execute("SELECT * FROM users WHERE id=?", (cursor.lastrowid,)).fetchone())
        except sqlite3.IntegrityError as exc:
            raise ExamError(409, "该账号已存在。") from exc

    def login(self, name: str, secret: str) -> tuple[str, dict]:
        name = username(name)
        if not isinstance(secret, str) or len(secret) > 128:
            raise ExamError(401, "账号或密码不正确。")
        now = time.time()
        with self.connect() as db:
            row = db.execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
            failures = db.execute("SELECT count(*) FROM login_failures WHERE username=? AND at>?", (name, now - 300)).fetchone()[0]
        if failures >= 8:
            raise ExamError(429, "登录尝试过多，请 5 分钟后重试。")
        valid = check_password_hash(row["password_hash"] if row else self.dummy_hash, secret)
        with self.transaction() as db:
            db.execute("DELETE FROM login_failures WHERE at<?", (now - 300,))
            if not row or not valid or row["disabled"]:
                db.execute("INSERT INTO login_failures VALUES(?,?)", (name, now))
            else:
                # A concurrent disable/password reset invalidates this login as well.
                current = db.execute("SELECT * FROM users WHERE id=?", (row["id"],)).fetchone()
                if current["disabled"] or current["password_hash"] != row["password_hash"]:
                    raise ExamError(401, "账号或密码不正确。")
                db.execute("DELETE FROM login_failures WHERE username=?", (name,))
                db.execute("DELETE FROM sessions WHERE expires<?", (now,))
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (self.token_hash(token), row["id"], csrf, now + SESSION_SECONDS))
                return token, {"user": public_user(current), "csrf": csrf}
        raise ExamError(401, "账号或密码不正确。")

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def session(self, token: str | None) -> dict | None:
        if not token:
            return None
        with self.connect() as db:
            row = db.execute("SELECT users.*,sessions.csrf,session_identity.context FROM sessions JOIN users ON users.id=sessions.user_id "
                             "LEFT JOIN session_identity USING(token_hash) "
                             "WHERE token_hash=? AND expires>? AND disabled=0", (self.token_hash(token), time.time())).fetchone()
            if not row or row["context"] and row["role"] != "student":
                return None
            result = {"user": public_user(row), "csrf": row["csrf"]}
            if row["context"]:
                result["identity"] = json.loads(row["context"])
            return result

    def logout(self, token: str):
        with self.transaction() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (self.token_hash(token),))

    def change_password(self, user_id: int, old: str, new: str):
        password(new)
        if not isinstance(old, str) or len(old) > 128 or old == new:
            raise ExamError(400, "请输入旧密码和不同的新密码。")
        with self.connect() as db:
            row = db.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
        if not row or not check_password_hash(row[0], old):
            raise ExamError(403, "旧密码不正确。")
        hashed = generate_password_hash(new)
        with self.transaction() as db:
            changed = db.execute("UPDATE users SET password_hash=?,must_change=0 WHERE id=? AND password_hash=?",
                                 (hashed, user_id, row[0])).rowcount
            if not changed:
                raise ExamError(409, "密码已被更新，请重新登录。")
            db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))

    def reset_password(self, name: str, new: str):
        name, new = username(name), password(new)
        hashed = generate_password_hash(new)
        with self.transaction() as db:
            row = db.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()
            if not row:
                raise ExamError(404, "账号不存在。")
            db.execute("UPDATE users SET password_hash=?,must_change=1 WHERE id=?", (hashed, row[0]))
            db.execute("DELETE FROM sessions WHERE user_id=?", (row[0],))

    def disable_user(self, name: str):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM users WHERE username=?", (username(name),)).fetchone()
            if not row:
                raise ExamError(404, "账号不存在。")
            if row["role"] == "admin" and not row["disabled"] and db.execute(
                    "SELECT count(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0] <= 1:
                raise ExamError(409, "请先创建另一管理员，不能停用最后一个管理员。")
            db.execute("UPDATE users SET disabled=1 WHERE id=?", (row["id"],))
            db.execute("DELETE FROM sessions WHERE user_id=?", (row["id"],))

    @staticmethod
    def paper_key(paper: Exam) -> str:
        return paper.selected_group or "extension"

    def hydrate(self, row, paper: Exam) -> dict:
        state = json.loads(row["state"])
        state.update(startedAt=int(row["started"] * 1000), report=json.loads(row["report"]) if row["report"] else None)
        with self.connect() as db:
            timer = db.execute("SELECT elapsed_ms FROM attempt_timers WHERE attempt_id=?", (row["id"],)).fetchone()
        state.update(elapsedMs=timer[0] if timer else 0, timingMode="online-v1")
        return state

    def heartbeat(self, user_id: int, paper: Exam, payload: dict) -> dict:
        keys = {"attempt_id", "client_id", "sequence", "active_ms"}
        if (not isinstance(payload, dict) or set(payload) != keys
                or not canonical_id(payload["attempt_id"]) or not canonical_id(payload["client_id"])
                or type(payload["sequence"]) is not int or not 0 <= payload["sequence"] <= 2**53 - 1
                or type(payload["active_ms"]) is not int or not 0 <= payload["active_ms"] <= MAX_ELAPSED * 1000):
            raise ExamError(400, "在线计时请求无效。")
        now = time.time()
        with self.transaction() as db:
            attempt = db.execute("SELECT attempts.* FROM attempts JOIN progress ON progress.attempt_id=attempts.id "
                                 "WHERE attempts.id=? AND attempts.user_id=? AND attempts.paper=? AND attempts.mode='exam'",
                                 (payload["attempt_id"], user_id, self.paper_key(paper))).fetchone()
            if not attempt:
                raise ExamError(409, "本轮考试已归档或不属于当前账号，请刷新取得当前进度。")
            if attempt["report"]:
                return {"elapsed_ms": json.loads(attempt["report"])["elapsed_seconds"] * 1000}
            db.execute("INSERT OR IGNORE INTO attempt_timers(attempt_id) VALUES(?)", (attempt["id"],))
            timer = db.execute("SELECT * FROM attempt_timers WHERE attempt_id=?", (attempt["id"],)).fetchone()
            client = db.execute("SELECT * FROM timer_clients WHERE attempt_id=? AND client_id=?",
                                (attempt["id"], payload["client_id"])).fetchone()
            if client and payload["sequence"] <= client["sequence"]:
                if payload["sequence"] == client["sequence"] and payload["active_ms"] != client["active_ms"]:
                    raise ExamError(409, "同一计时编号不能用于不同内容。")
                return {"elapsed_ms": timer["elapsed_ms"]}
            credit = 0
            if client:
                delta = payload["active_ms"] - client["active_ms"]
                if delta < 0:
                    raise ExamError(400, "本页累计在线时间不能减少。")
                gap = now - client["seen"]
                # No extrapolation after a missing heartbeat; union overlapping tab intervals.
                if 0 <= gap <= 30 and delta <= 30000:
                    start = max(client["seen"], now - delta / 1000, timer["credited_until"])
                    credit = max(0, round((now - start) * 1000))
            total = min(MAX_ELAPSED * 1000, timer["elapsed_ms"] + credit)
            db.execute("UPDATE attempt_timers SET elapsed_ms=?,credited_until=? WHERE attempt_id=?",
                       (total, max(now, timer["credited_until"]) if credit else timer["credited_until"], attempt["id"]))
            db.execute("INSERT INTO timer_clients VALUES(?,?,?,?,?) ON CONFLICT(attempt_id,client_id) DO UPDATE SET "
                       "sequence=excluded.sequence,active_ms=excluded.active_ms,seen=excluded.seen",
                       (attempt["id"], payload["client_id"], payload["sequence"], payload["active_ms"], now))
            return {"elapsed_ms": total}

    def load(self, user_id: int, paper: Exam, mode: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT attempts.*,progress.revision FROM progress JOIN attempts ON attempts.id=progress.attempt_id "
                             "WHERE progress.user_id=? AND progress.paper=? AND progress.mode=?",
                             (user_id, self.paper_key(paper), mode)).fetchone()
            if row:
                return {"revision": row["revision"], "draft": self.hydrate(row, paper)}
            result = {"revision": 0, "draft": None}
            if paper.selected_group == "combined":
                answers, flagged = {}, set()
                for name, part in paper.parts.items():
                    previous = db.execute("SELECT attempts.* FROM progress JOIN attempts ON attempts.id=progress.attempt_id "
                                          "WHERE progress.user_id=? AND progress.paper=? AND progress.mode=?", (user_id, name, mode)).fetchone()
                    if not previous or previous["report"] is not None or previous["version"] != part.version:
                        continue
                    state = json.loads(previous["state"])
                    answers.update({qid: answer for qid, answer in state["answers"].items() if qid in part.question_ids and answer in ("A", "B", "C", "D")})
                    flagged.update(qid for qid in state["flagged"] if qid in part.question_ids)
                if answers or flagged:
                    result["carryover"] = {"answers": answers, "flagged": sorted(flagged)}
            return result

    @staticmethod
    def validate_state(state: dict, paper: Exam, mode: str):
        keys = {"version", "attemptId", "answers", "flagged", "index", "pending"}
        if mode != "exam" or not isinstance(state, dict) or set(state) != keys:
            raise ExamError(400, "作答记录字段无效。")
        paper.validate({"version": state["version"], "attempt_id": state["attemptId"], "answers": state["answers"], "elapsed_seconds": 0})
        if (not isinstance(state["flagged"], list) or len(state["flagged"]) > paper.combined_total + 120
                or any(not isinstance(qid, str) or qid not in paper.question_ids for qid in state["flagged"])
                or type(state["index"]) is not int or not 0 <= state["index"] < len(paper.questions)):
            raise ExamError(400, "题目位置或标记无效。")
        if state["pending"] is not None:
            paper.validate(state["pending"])
            if (state["pending"]["attempt_id"] != state["attemptId"] or state["pending"]["answers"] != state["answers"]):
                raise ExamError(400, "待提交答案与草稿不一致。")

    def save(self, user_id: int, paper: Exam, mode: str, payload: dict, *, identity: dict | None = None) -> dict:
        if (not isinstance(payload, dict) or set(payload) != {"revision", "mutation_id", "draft"}
                or type(payload["revision"]) is not int or payload["revision"] < 0 or not canonical_id(payload["mutation_id"])):
            raise ExamError(400, "保存请求字段无效。")
        state = payload["draft"]
        self.validate_state(state, paper, mode)
        request_hash = hashlib.sha256(encode_json({"paper": self.paper_key(paper), "mode": mode, **payload})).hexdigest()
        now = time.time()
        with self.transaction() as db:
            duplicate = db.execute("SELECT * FROM mutations WHERE user_id=? AND id=?", (user_id, payload["mutation_id"])).fetchone()
            if duplicate:
                if duplicate["request_hash"] != request_hash:
                    raise ExamError(409, "同一保存编号不能用于不同内容。")
                return json.loads(duplicate["response"])
            row = db.execute("SELECT attempts.*,progress.revision FROM progress JOIN attempts ON attempts.id=progress.attempt_id "
                             "WHERE progress.user_id=? AND progress.paper=? AND progress.mode=?",
                             (user_id, self.paper_key(paper), mode)).fetchone()
            revision = row["revision"] if row else 0
            if payload["revision"] != revision:
                raise ExamError(409, "另一个页面已更新进度。请下载本页记录，再刷新取得服务器进度。")
            previous = json.loads(row["state"]) if row and row["id"] == state["attemptId"] else None
            if previous:
                fixed = ("version", "attemptId", "answers", "pending")
                if (row["report"] or previous["pending"]) and any(state[key] != previous[key] for key in fixed):
                    raise ExamError(409, "本次交卷答案已固定；请开始新一轮。")
                started = row["started"]
            else:
                if db.execute("SELECT 1 FROM attempts WHERE id=?", (state["attemptId"],)).fetchone():
                    raise ExamError(409, "作答编号已使用，请开始新一轮。")
                started = now
            if previous:
                db.execute("UPDATE attempts SET state=?,updated=? WHERE id=?",
                           (encode_json(state).decode(), now, state["attemptId"]))
            else:
                db.execute("INSERT INTO attempts(id,user_id,paper,mode,version,started,updated,state) VALUES(?,?,?,?,?,?,?,?)",
                           (state["attemptId"], user_id, self.paper_key(paper), mode, paper.version, started, now,
                            encode_json(state).decode()))
                if identity:
                    db.execute("INSERT INTO attempt_identity VALUES(?,?)", (state["attemptId"], encode_json(identity).decode()))
            result = {"revision": revision + 1, "startedAt": int(started * 1000)}
            db.execute("INSERT INTO progress VALUES(?,?,?,?,?) ON CONFLICT(user_id,paper,mode) "
                       "DO UPDATE SET revision=excluded.revision,attempt_id=excluded.attempt_id",
                       (user_id, self.paper_key(paper), mode, revision + 1, state["attemptId"]))
            db.execute("INSERT INTO mutations VALUES(?,?,?,?)", (user_id, payload["mutation_id"], request_hash, encode_json(result).decode()))
            return result

    def submitted(self, user_id: int, attempt_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT report FROM attempts WHERE id=? AND user_id=? AND report IS NOT NULL", (attempt_id, user_id)).fetchone()
            if not row:
                raise ExamError(404, "成绩不存在。")
            return json.loads(row[0])

    def submit(self, user: dict, paper: Exam, payload: dict) -> dict:
        paper.validate(payload)
        now = time.time()
        with self.transaction() as db:
            row = db.execute("SELECT * FROM attempts WHERE id=? AND user_id=? AND paper=? AND mode='exam'",
                             (payload["attempt_id"], user["id"], self.paper_key(paper))).fetchone()
            if not row:
                raise ExamError(404, "请先保存本账号的考试草稿。")
            state = json.loads(row["state"])
            if state["version"] != payload["version"] or state["answers"] != payload["answers"]:
                raise ExamError(409, "提交与服务器草稿不一致，请先保存作答。")
            if row["report"]:
                return json.loads(row["report"])
            current = db.execute("SELECT attempt_id FROM progress WHERE user_id=? AND paper=? AND mode='exam'",
                                 (user["id"], self.paper_key(paper))).fetchone()
            if not current or current[0] != row["id"]:
                raise ExamError(409, "本次草稿已经归档，请继续当前考试。")
            timer = db.execute("SELECT elapsed_ms FROM attempt_timers WHERE attempt_id=?", (row["id"],)).fetchone()
            server_payload = {**payload, "elapsed_seconds": timer[0] // 1000 if timer else 0}
            report = paper.grade(server_payload)
            report.update(timing_mode="online-v1", user={"username": user["username"], "display_name": user["display_name"]},
                          paper=self.paper_key(paper), files={"json": "服务器账号成绩记录", "markdown": "可下载 Markdown 报告"})
            identity = db.execute("SELECT context FROM attempt_identity WHERE attempt_id=?", (row["id"],)).fetchone()
            if identity:
                report["identity"] = json.loads(identity[0])
            report["markdown"] = markdown_report(report) + f"\n\n账号：{user['username']}\n"
            if identity:
                context = report["identity"]
                report["markdown"] += f"身份来源：{context['source']}；归属：{context['status']}\n"
            db.execute("UPDATE attempts SET report=?,submitted=?,updated=? WHERE id=?",
                       (encode_json(report).decode(), now, now, row["id"]))
            return report

    def rows(self, user_id: int | None) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT attempts.*,users.username,users.display_name FROM attempts JOIN users ON users.id=attempts.user_id "
                              "WHERE (? IS NULL OR user_id=?) AND report IS NOT NULL ORDER BY submitted,id",
                              (user_id, user_id)).fetchall()
        return [dict(row) for row in rows]

    def backup(self, destination: Path):
        destination = Path(destination).resolve()
        if destination.exists() or destination == self.path:
            raise ValueError("Backup target must be a new file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Reserve without replacing a prior backup; SQLite backup includes committed WAL content.
        with destination.open("xb"):
            pass
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup integrity check failed")
