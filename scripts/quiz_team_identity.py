"""Explicit roster attribution; self-reported accounts never prove Windows identity."""
from __future__ import annotations

import json
from pathlib import Path
import re
import secrets
import time
import unicodedata

from quiz_exam import ExamError, encode_json
from quiz_team_store import SESSION_SECONDS, public_user


def account_text(value: object, *, optional: bool = False, limit: int = 128) -> str:
    if not isinstance(value, str) or len(value) > limit or any(unicodedata.category(c).startswith("C") for c in value):
        raise ExamError(400, f"请输入不含控制字符、长度不超过 {limit} 的账号或设备信息。")
    value = unicodedata.normalize("NFKC", value).strip()
    if len(value) > limit:
        raise ExamError(400, f"规范化后的账号或设备信息不能超过 {limit} 个字符。")
    if not optional and not value:
        raise ExamError(400, "请输入账号或完整姓名。")
    return value


def account_key(value: str) -> str:
    return account_text(value).casefold()


class IdentityService:
    def __init__(self, store, roster: Path):
        document = json.loads(Path(roster).read_text(encoding="utf-8-sig"))
        if not isinstance(document, dict) or set(document) != {"schema", "members"} or document["schema"] != 1:
            raise ValueError("Unsupported quiz roster format")
        members, aliases, ids = document["members"], {}, set()
        if not isinstance(members, list) or not members:
            raise ValueError("Quiz roster must contain members")
        for member in members:
            if (not isinstance(member, dict) or set(member) != {"id", "name", "aliases"}
                    or not isinstance(member["id"], str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", member["id"])
                    or member["id"] in ids or not isinstance(member["aliases"], list)):
                raise ValueError("Invalid or duplicate roster member")
            ids.add(member["id"])
            member["name"] = account_text(member["name"], limit=80)
            for alias in [member["name"], *member["aliases"]]:
                normalized = account_key(alias)
                if normalized in aliases and aliases[normalized] != member["id"]:
                    raise ValueError("A roster account alias must refer to exactly one member")
                aliases[normalized] = member["id"]
        self.store, self.members, self.aliases = store, members, aliases
        self.names = {account_key(member["name"]): member["id"] for member in members}
        self.user_ids = {}
        with store.transaction() as db:
            for member in members:
                row = db.execute("SELECT users.* FROM roster_members JOIN users ON users.id=roster_members.user_id "
                                 "WHERE roster_members.id=?", (member["id"],)).fetchone()
                if row:
                    if row["role"] != "student":
                        raise ValueError("Roster identities cannot grant or reuse administrator access")
                    db.execute("UPDATE users SET display_name=? WHERE id=?", (member["name"], row["id"]))
                    db.execute("UPDATE roster_members SET name=? WHERE id=?", (member["name"], member["id"]))
                else:
                    # Separate from password accounts: a coincident display name does not authorize adoption.
                    cursor = db.execute("INSERT INTO users(username,display_name,password_hash,role,must_change) VALUES(?,?,'','student',0)",
                                        ("person-" + secrets.token_hex(12), member["name"]))
                    db.execute("INSERT INTO roster_members VALUES(?,?,?)", (member["id"], cursor.lastrowid, member["name"]))
                self.user_ids[member["id"]] = db.execute("SELECT user_id FROM roster_members WHERE id=?", (member["id"],)).fetchone()[0]

    def allows(self, auth: dict) -> bool:
        if auth["user"]["role"] == "admin":
            return True
        identity = auth.get("identity", {})
        member = identity.get("member_id")
        return (identity.get("status") == "matched" and member in self.user_ids
                and self.user_ids[member] == auth["user"]["id"]
                and (identity.get("source") == "domain"
                     or identity.get("source") == "self_reported" and self.names.get(account_key(identity["account"])) == member))

    def options(self, domain: dict | None) -> dict:
        return {"passwordless": True, "names": [member["name"] for member in self.members],
                "domain_account": domain["account"] if domain else None}

    def login(self, entered: object, computer: object, ip: str, domain: dict | None = None) -> tuple[str, dict]:
        entered = account_text(entered, optional=domain is not None)
        computer = account_text(computer, optional=True, limit=80)
        account = account_text(domain["account"]) if domain else entered
        source = "domain" if domain else "self_reported"
        key = "domain:" + domain["sid"] if domain else "self:" + account_key(account)
        candidate = (self.aliases if domain else self.names).get(account_key(account))
        if not domain and candidate is None:
            raise ExamError(403, "姓名不在允许登录的名单中，请输入名单中的本人完整姓名。")
        now = time.time()
        with self.store.transaction() as db:
            identity = db.execute("SELECT * FROM identity_keys WHERE key=?", (key,)).fetchone()
            if identity:
                member_id, user_id = identity["member_id"], identity["user_id"]
                if candidate is not None and member_id != candidate:
                    raise ExamError(409, "这个账号已有不同归属的记录，请联系管理员核对；原记录已保留。")
            else:
                member_id = candidate
                user_id = self.user_ids.get(member_id)
            if member_id not in self.user_ids or user_id != self.user_ids[member_id]:
                raise ExamError(403, "该身份不在允许登录的名单中，请联系管理员核对。")
            if domain and entered and (claim := self.names.get(account_key(entered))) and claim != member_id:
                raise ExamError(409, "输入姓名与已验证域账号归属不同，不能自动合并；请联系管理员核对账号别名。")
            if not identity:
                db.execute("INSERT INTO identity_keys VALUES(?,?,?)", (key, user_id, member_id))
            user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            if user["disabled"] or user["role"] != "student":
                raise ExamError(403, "该学员账号已停用或不允许免密访问，请联系管理员。")
            context = {"source": source, "status": "matched" if member_id else "unmatched", "member_id": member_id,
                       "name": user["display_name"] if member_id else None, "account": account, "entered_account": entered,
                       "client_ip": ip, "computer_name": computer, "computer_name_source": "self_reported" if computer else "unavailable",
                       "domain_sid": domain["sid"] if domain else None}
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            token_hash, encoded = self.store.token_hash(token), encode_json(context).decode()
            db.execute("DELETE FROM sessions WHERE expires<?", (now,))
            db.execute("INSERT INTO sessions VALUES(?,?,?,?)", (token_hash, user_id, csrf, now + SESSION_SECONDS))
            db.execute("INSERT INTO session_identity VALUES(?,?)", (token_hash, encoded))
            db.execute("INSERT INTO login_events(user_id,at,context) VALUES(?,?,?)", (user_id, now, encoded))
            return token, {"user": public_user(user), "csrf": csrf, "identity": context}

    def users(self) -> list[dict]:
        with self.store.connect() as db:
            rows = db.execute("SELECT users.username,users.display_name,users.role,users.disabled,roster_members.id AS member_id, "
                              "EXISTS(SELECT 1 FROM identity_keys WHERE identity_keys.user_id=users.id) AS identified, "
                              "(SELECT context FROM login_events WHERE login_events.user_id=users.id ORDER BY at DESC,id DESC LIMIT 1) AS context "
                              "FROM users LEFT JOIN roster_members ON roster_members.user_id=users.id ORDER BY users.id").fetchall()
        result = []
        for row in rows:
            value = {key: row[key] for key in ("username", "display_name", "role", "disabled", "member_id")}
            value["attribution"] = "matched" if row["member_id"] else "unmatched" if row["identified"] else "legacy"
            value["last_identity"] = json.loads(row["context"]) if row["context"] else None
            result.append(value)
        return result
