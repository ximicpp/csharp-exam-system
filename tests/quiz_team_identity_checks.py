"""Roster access, historical identity and migration checks use disposable databases only."""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from quiz_exam import Exam
from quiz_team import HTTP_COOKIE, create_app
from quiz_team_identity import IdentityService, account_key
from quiz_team_store import Store

ORIGIN = "http://192.168.1.20:8080"
PASSWORD = "Identity-Test-Password-Only"
PROXY_KEY = "Gateway-Test-Secret-Only-32-Characters"
SID = "S-1-5-21-100-200-300-400"
NAMES = ["示例学员01", "示例学员02", "示例学员03", "示例学员04", "示例学员05", "示例学员06", "示例学员07", "示例学员䶮", "示例学员09", "示例学员10", "示例学员11",
         "示例学员12", "示例学员13", "示例学员14", "示例学员15", "示例学员16", "示例学员17", "示例学员18", "示例学员19", "示例学员20", "示例学员21", "示例学员22", "示例学员23", "示例学员24"]


class IdentityChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        directory = Path(self.temporary.name)
        self.path, self.roster = directory / "team.sqlite3", directory / "roster.json"
        self.document = json.loads((ROOT / "data/quiz-team-roster.example.json").read_text(encoding="utf-8"))
        self.document["members"][0]["aliases"] = ["ex1", "game\\example.user"]
        self.write_roster()
        self.store = Store(self.path)
        self.manager = self.store.add_user("manager", "管理员", PASSWORD, admin=True, must_change=False)
        self.app = self.make_app()
        self.paper = Exam(selected_group="combined")

    def write_roster(self):
        self.roster.write_text(json.dumps(self.document, ensure_ascii=False), encoding="utf-8")

    def make_app(self):
        return create_app(self.path, ORIGIN, allow_insecure_http=True, roster=self.roster, proxy_key=PROXY_KEY)

    def post(self, client, path, data, csrf=None, headers=None):
        return client.post(path, json=data, base_url=ORIGIN,
                           headers={"Origin": ORIGIN, "X-Exam-Token": csrf or "", **(headers or {})})

    def get(self, client, path, headers=None):
        return client.get(path, base_url=ORIGIN, headers=headers or {})

    def identify(self, account, computer="", headers=None):
        client = self.app.test_client()
        response = self.post(client, "/api/identify", {"account": account, "computer_name": computer}, headers=headers)
        self.assertEqual(response.status_code, 200, response.get_json())
        return client, response.get_json()

    def draft(self, client, auth):
        state = self.state()
        result = self.post(client, "/api/progress", {"revision": 0, "mutation_id": str(uuid4()), "draft": state}, auth["csrf"])
        self.assertEqual(result.status_code, 200, result.get_json())
        return state

    def state(self):
        return {"version": self.paper.version, "attemptId": str(uuid4()), "answers": {"Q01": "B"},
                "flagged": [], "index": 1, "pending": None}

    def historical(self, account, computer=""):
        # Seed the previous release's unmatched session without enabling the removed login policy.
        user = self.store.add_user("history-" + uuid4().hex, "未归属：" + account, PASSWORD, must_change=False)
        token, auth = self.store.login(user["username"], PASSWORD)
        context = {"source": "self_reported", "status": "unmatched", "member_id": None, "name": None,
                   "account": account, "entered_account": account, "client_ip": "127.0.0.1", "computer_name": computer,
                   "computer_name_source": "self_reported" if computer else "unavailable", "domain_sid": None}
        with self.store.transaction() as db:
            db.execute("UPDATE users SET password_hash='' WHERE id=?", (user["id"],))
            db.execute("INSERT INTO identity_keys VALUES(?,?,NULL)", ("self:" + account_key(account), user["id"]))
            db.execute("INSERT INTO session_identity VALUES(?,?)", (self.store.token_hash(token), json.dumps(context)))
        auth["identity"] = context
        state = self.state()
        self.store.save(user["id"], self.paper, "exam", {"revision": 0, "mutation_id": str(uuid4()), "draft": state}, identity=context)
        client = self.app.test_client()
        client.set_cookie(HTTP_COOKIE, token, domain="192.168.1.20")
        return client, auth, state

    def submit(self, client, auth, state):
        response = self.post(client, "/api/submit", {"version": state["version"], "attempt_id": state["attemptId"],
                                                    "answers": state["answers"], "elapsed_seconds": 0}, auth["csrf"])
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def admin(self):
        client = self.app.test_client()
        response = self.post(client, "/api/login", {"username": "manager", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        return client

    def test_roster_contains_every_supplied_name_and_rare_character_exactly(self):
        session = self.get(self.app.test_client(), "/api/session").get_json()
        self.assertEqual(session["identity_options"]["names"], NAMES)
        self.assertIsNone(session["identity_options"]["domain_account"])
        self.assertIsNone(session["user"])
        for name in NAMES:
            _, auth = self.identify(name)
            self.assertEqual(auth["identity"]["name"], name)
            self.assertEqual(auth["identity"]["status"], "matched")
            self.assertEqual(auth["user"]["role"], "student")

    def test_exact_name_restores_one_user_across_devices_without_changing_report_identity(self):
        first, auth = self.identify(" 示例学员01 ", "PC-ONE")
        state = self.draft(first, auth)
        second, restored = self.identify("示例学员01", "PC-TWO")
        self.assertEqual(restored["user"]["id"], auth["user"]["id"])
        self.assertEqual(self.get(second, "/api/progress").get_json()["draft"]["answers"], state["answers"])
        self.assertEqual(restored["identity"]["computer_name"], "PC-TWO")
        third, report_auth = self.identify("示例学员01")
        report = self.submit(third, report_auth, state)
        self.assertEqual(report["identity"]["computer_name"], "PC-ONE")
        self.assertEqual(report["identity"]["source"], "self_reported")
        self.assertEqual(report["identity"]["name"], "示例学员01")

    def test_unknown_names_aliases_and_admin_names_are_rejected_without_creating_records(self):
        def counts():
            with self.store.connect() as db:
                return [db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                        for table in ("users", "identity_keys", "sessions", "login_events", "attempts")]
        before = counts()
        for name in ("未列名学员", "exampleuser", "示例学员", "示例 学员01", "示例学员龙", "ex1", "ＥＸ１", "game\\example.user", "manager"):
            client = self.app.test_client()
            response = self.post(client, "/api/identify", {"account": name, "computer_name": "SHARED-PC"})
            self.assertEqual(response.status_code, 403, name)
            self.assertIn("名单", response.get_json()["error"])
            self.assertIsNone(self.get(client, "/api/session").get_json()["user"])
            self.assertEqual(self.get(client, "/api/exam").status_code, 401)
        self.assertEqual(counts(), before)

    def test_historical_unmatched_session_cannot_bypass_roster_and_its_draft_is_retained(self):
        client, auth, state = self.historical("old-unknown")
        self.assertIsNone(self.get(client, "/api/session").get_json()["user"])
        for path in ("/api/exam", "/api/progress", "/api/history", "/api/results", "/api/attempts/" + state["attemptId"]):
            self.assertEqual(self.get(client, path).status_code, 401)
        self.assertEqual(self.post(client, "/api/submit", {"version": state["version"], "attempt_id": state["attemptId"],
                                                         "answers": state["answers"], "elapsed_seconds": 0}, auth["csrf"]).status_code, 401)
        self.assertEqual(self.post(client, "/api/identify", {"account": "old-unknown", "computer_name": ""}).status_code, 403)
        with self.store.connect() as db:
            row = db.execute("SELECT user_id,state,report FROM attempts WHERE id=?", (state["attemptId"],)).fetchone()
            self.assertEqual(row["user_id"], auth["user"]["id"])
            self.assertEqual(json.loads(row["state"]), state)
            self.assertIsNone(row["report"])

    def test_removing_member_or_old_alias_session_revokes_access_without_removing_records(self):
        client, auth = self.identify("示例学员01")
        state = self.draft(client, auth)
        token = client.get_cookie(HTTP_COOKIE, domain="192.168.1.20").value
        with self.store.transaction() as db:
            context = {**auth["identity"], "account": "ex1"}
            db.execute("UPDATE session_identity SET context=? WHERE token_hash=?", (json.dumps(context), self.store.token_hash(token)))
        self.assertEqual(self.get(client, "/api/exam").status_code, 401)
        client, auth = self.identify("示例学员01")
        self.document["members"].pop(0)
        self.write_roster()
        token = client.get_cookie(HTTP_COOKIE, domain="192.168.1.20").value
        self.app = self.make_app()
        client = self.app.test_client()
        client.set_cookie(HTTP_COOKIE, token, domain="192.168.1.20")
        self.assertIsNone(self.get(client, "/api/session").get_json()["user"])
        self.assertEqual(self.get(client, "/api/exam").status_code, 401)
        self.assertEqual(self.post(client, "/api/identify", {"account": "示例学员01", "computer_name": ""}).status_code, 403)
        with self.store.connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT state FROM attempts WHERE id=?", (state["attemptId"],)).fetchone()[0]), state)

    def test_same_network_does_not_merge_two_roster_members(self):
        first, a = self.identify("示例学员13", "SHARED-PC")
        self.draft(first, a)
        second, b = self.identify("示例学员07", "SHARED-PC")
        self.assertNotEqual(a["user"]["id"], b["user"]["id"])
        self.assertIsNone(self.get(second, "/api/progress").get_json()["draft"])

    def test_self_report_cannot_adopt_password_accounts_or_administrators(self):
        legacy = self.store.add_user("old-learner", "示例学员01", PASSWORD, must_change=False)
        client, named = self.identify("示例学员01")
        self.assertNotEqual(named["user"]["id"], legacy["id"])
        auth = named
        for path in ("/api/admin/users", "/api/results?scope=all"):
            self.assertEqual(self.get(client, path).status_code, 403)
        self.assertEqual(self.post(client, "/api/password", {"old_password": "", "new_password": PASSWORD}, auth["csrf"]).status_code, 403)
        self.assertEqual(self.post(client, "/api/admin/users", {"username": "evil", "display_name": "evil"}, auth["csrf"]).status_code, 403)

    def test_password_student_and_existing_password_session_cannot_bypass_roster(self):
        old = self.store.add_user("old-student", "示例学员01", PASSWORD, must_change=False)
        token, _ = self.store.login(old["username"], PASSWORD)
        client = self.app.test_client()
        client.set_cookie(HTTP_COOKIE, token, domain="192.168.1.20")
        self.assertIsNone(self.get(client, "/api/session").get_json()["user"])
        self.assertEqual(self.get(client, "/api/exam").status_code, 401)
        with self.store.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(self.post(client, "/api/login", {"username": "old-student", "password": PASSWORD}).status_code, 403)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0], count)
        admin = self.admin()
        csrf = self.get(admin, "/api/session").get_json()["csrf"]
        self.assertEqual(self.post(admin, "/api/admin/users", {"username": "new-student", "display_name": "名单外"}, csrf).status_code, 403)

    def test_untrusted_domain_and_forwarding_headers_do_not_override_input(self):
        headers = {"X-Quiz-Domain-Account": "game\\example.user", "X-Quiz-Domain-SID": SID,
                   "X-Quiz-Client-IP": "10.1.2.3", "X-Forwarded-For": "10.1.2.4", "X-Quiz-Proxy-Key": "wrong"}
        _, auth = self.identify("示例学员13", headers=headers)
        self.assertEqual(auth["identity"]["name"], "示例学员13")
        self.assertEqual(auth["identity"]["source"], "self_reported")
        self.assertEqual(auth["identity"]["client_ip"], "127.0.0.1")

    def test_trusted_gateway_domain_is_primary_and_sid_survives_account_rename(self):
        headers = {"X-Quiz-Proxy-Key": PROXY_KEY, "X-Quiz-Client-IP": "10.1.2.3",
                   "X-Quiz-Domain-Account": "game\\example.user", "X-Quiz-Domain-SID": SID}
        _, auth = self.identify("", headers=headers)
        self.assertEqual(auth["identity"]["source"], "domain")
        self.assertEqual(auth["identity"]["name"], "示例学员01")
        self.assertEqual(auth["identity"]["client_ip"], "10.1.2.3")
        unknown = self.post(self.app.test_client(), "/api/identify", {"account": "", "computer_name": ""},
                            headers=headers | {"X-Quiz-Domain-Account": "game\\unknown", "X-Quiz-Domain-SID": SID + "1"})
        self.assertEqual(unknown.status_code, 403)
        _, renamed = self.identify("", headers=headers | {"X-Quiz-Domain-Account": "game\\renamed"})
        self.assertEqual(renamed["user"]["id"], auth["user"]["id"])
        bad = self.post(self.app.test_client(), "/api/identify", {"account": "示例学员13", "computer_name": ""}, headers=headers)
        self.assertEqual(bad.status_code, 409)
        client, other = self.identify("示例学员13")
        self.assertEqual(self.get(client, "/api/exam", headers=headers).status_code, 401)

    def test_disabled_or_promoted_user_cannot_keep_a_passwordless_session(self):
        client, auth = self.identify("示例学员01")
        self.store.disable_user(auth["user"]["username"])
        self.assertEqual(self.get(client, "/api/exam").status_code, 401)
        self.assertEqual(self.post(self.app.test_client(), "/api/identify", {"account": "示例学员01", "computer_name": ""}).status_code, 403)
        client, auth = self.identify("示例学员13")
        with self.store.transaction() as db:
            db.execute("UPDATE users SET role='admin' WHERE id=?", (auth["user"]["id"],))
        self.assertEqual(self.get(client, "/api/admin/users").status_code, 401)

    def test_attributed_and_historical_unknown_scores_are_retained_separately_and_csv_keeps_evidence(self):
        first, a = self.identify("示例学员01", "PC-A")
        self.submit(first, a, self.draft(first, a))
        _, b, state = self.historical("=SUM(A1:A2)", "PC-B")
        report = self.store.submit(b["user"], self.paper, {"version": state["version"], "attempt_id": state["attemptId"],
                                                        "answers": state["answers"], "elapsed_seconds": 0})
        admin = self.admin()
        result = self.get(admin, "/api/results?scope=all").get_json()
        self.assertEqual({s["identity_status"] for s in result["summaries"]}, {"matched", "unmatched"})
        self.assertTrue(all(s["people"] == 1 for s in result["summaries"]))
        for kind in ("matched", "unmatched"):
            filtered = self.get(admin, "/api/results?scope=all&attribution=" + kind).get_json()
            self.assertEqual(len(filtered["records"]), 1)
            self.assertEqual(filtered["records"][0]["identity_status"], kind)
        exported = self.get(admin, "/api/results?scope=all&format=csv").get_data(as_text=True).lstrip("\ufeff")
        rows = list(csv.DictReader(io.StringIO(exported)))
        unknown = next(row for row in rows if row["identity_status"] == "unmatched")
        self.assertEqual(unknown["input_account"], "'=SUM(A1:A2)")
        self.assertEqual(unknown["computer_name"], "PC-B")
        listed = self.get(admin, "/api/admin/users").get_json()["users"]
        self.assertEqual(sum(row["attribution"] == "matched" for row in listed), len(NAMES))
        self.assertEqual(sum(row["attribution"] == "unmatched" for row in listed), 1)
        self.assertEqual(self.store.submitted(b["user"]["id"], state["attemptId"]), report)

    def test_invalid_input_and_cross_origin_login_do_not_create_records(self):
        with self.store.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        for account in ("", "   ", None, "示例学员01\u200b", "x" * 129):
            self.assertEqual(self.post(self.app.test_client(), "/api/identify", {"account": account, "computer_name": ""}).status_code, 400)
        self.assertEqual(self.post(self.app.test_client(), "/api/identify", {"account": "unknown", "computer_name": ""},
                                   headers={"Origin": "http://other.internal"}).status_code, 403)
        with self.store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], count)

    def test_ambiguous_alias_or_reassignment_never_automatically_merges_records(self):
        client, auth, state = self.historical("new-name")
        self.document["members"][0]["name"] = "new-name"
        self.write_roster()
        self.app = self.make_app()
        response = self.post(self.app.test_client(), "/api/identify", {"account": "new-name", "computer_name": ""})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.get(client, "/api/progress").status_code, 401)
        with self.store.connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT state FROM attempts WHERE id=?", (state["attemptId"],)).fetchone()[0]), state)
        duplicate = deepcopy(self.document)
        duplicate["members"][1]["aliases"].append("EX1")
        self.roster.write_text(json.dumps(duplicate), encoding="utf-8")
        with self.assertRaises(ValueError):
            IdentityService(self.store, self.roster)

    def test_schema_one_upgrade_preserves_old_credentials_draft_and_report(self):
        # Recreate the previous schema after producing a real password-account report.
        old_path = Path(self.temporary.name) / "old.sqlite3"
        old = Store(old_path)
        user = old.add_user("old-user", "原账号", PASSWORD, must_change=False)
        state = {"version": self.paper.version, "attemptId": str(uuid4()), "answers": {"Q01": "B"},
                 "flagged": [], "index": 0, "pending": None}
        old.save(user["id"], self.paper, "exam", {"revision": 0, "mutation_id": str(uuid4()), "draft": state})
        report = old.submit(user, self.paper, {"version": state["version"], "attempt_id": state["attemptId"], "answers": state["answers"], "elapsed_seconds": 0})
        with old.connect() as db:
            original_hash = db.execute("SELECT password_hash FROM users").fetchone()[0]
            for table in ("attempt_identity", "session_identity", "login_events", "identity_keys", "roster_members"):
                db.execute("DROP TABLE " + table)
            db.execute("PRAGMA user_version=1")
        upgraded = create_app(old_path, ORIGIN, allow_insecure_http=True, roster=self.roster)
        client = upgraded.test_client()
        login = self.post(client, "/api/login", {"username": "old-user", "password": PASSWORD})
        self.assertEqual(login.status_code, 403)
        upgraded_store = upgraded.extensions["quiz_store"]
        self.assertEqual(upgraded_store.submitted(user["id"], state["attemptId"]), report)
        with upgraded.extensions["quiz_store"].connect() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()[0], original_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
