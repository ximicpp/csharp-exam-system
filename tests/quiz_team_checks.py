"""Team service correctness checks in temporary databases; no learner records or credentials."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from uuid import uuid4
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from quiz_exam import Exam, ExamError
from quiz_team import COOKIE, HTTP_COOKIE, create_app

ORIGIN = "http://127.0.0.1:8768"
PASSWORD = "Temporary-Test-Password-42"


class TeamChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temporary.name) / "team.sqlite3"
        cls.app = create_app(cls.path, ORIGIN)
        cls.store = cls.app.extensions["quiz_store"]
        cls.paper = Exam(selected_group="combined")
        cls.companion = Exam(selected_group="microsoft")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        with self.store.transaction() as db:
            for table in ("mutations", "progress", "attempts", "sessions", "login_failures", "users"):
                db.execute(f"DELETE FROM {table}")
        self.alice = self.store.add_user("alice", "甲", PASSWORD, must_change=False)
        self.bob = self.store.add_user("bob", "乙", PASSWORD, must_change=False)
        self.admin = self.store.add_user("manager", "管理", PASSWORD, admin=True, must_change=False)
        self.client, self.csrf = self.client_for("alice")

    def client_for(self, name):
        client = self.app.test_client()
        response = client.post("/api/login", json={"username": name, "password": PASSWORD}, base_url=ORIGIN, headers={"Origin": ORIGIN})
        self.assertEqual(response.status_code, 200, response.get_json())
        return client, response.get_json()["csrf"]

    def get(self, path, client=None):
        return (client or self.client).get(path, base_url=ORIGIN)

    def post(self, path, payload, client=None, csrf=None):
        return (client or self.client).post(path, json=payload, base_url=ORIGIN,
                                          headers={"Origin": ORIGIN, "X-Exam-Token": csrf or self.csrf})

    def state(self, answers=None, paper=None, practice=False):
        paper = paper or self.paper
        return {"version": paper.version, "attemptId": str(uuid4()), "answers": answers or {}, "flagged": [], "index": 0,
                "pending": None}

    def save(self, state, revision=0, practice=False, group=None, client=None, csrf=None, mutation=None):
        path = "/api/progress?mode=" + ("practice" if practice else "exam") + ("&group=" + group if group else "")
        return self.post(path, {"revision": revision, "mutation_id": mutation or str(uuid4()), "draft": state}, client, csrf)

    def submit(self, state, client=None, csrf=None, group=None):
        return self.post("/api/submit" + ("?group=" + group if group else ""),
                         {"version": state["version"], "attempt_id": state["attemptId"], "answers": state["answers"], "elapsed_seconds": 99999}, client, csrf)

    def test_anonymous_cannot_read_papers_progress_results_or_report(self):
        client = self.app.test_client()
        for path in ("/api/exam", "/api/progress", "/api/results", "/api/admin/users", "/api/reports/any", "/api/attempts/any"):
            self.assertEqual(self.get(path, client).status_code, 401, path)

    def test_public_paper_has_no_answers_and_token_is_account_session_specific(self):
        data = self.get("/api/exam").get_json()
        self.assertEqual(data["token"], self.csrf)
        self.assertEqual(data["total"], 160)
        self.assertNotIn("answers", data["questions"][0])
        self.assertNotIn("rationale", data["questions"][0])
        bob, token = self.client_for("bob")
        self.assertNotEqual(token, self.csrf)
        self.assertEqual(self.post("/api/progress", {}, bob, self.csrf).status_code, 403)

    def test_account_isolation_and_refresh_recovery(self):
        state = self.state({"Q01": "B"})
        self.assertEqual(self.save(state).status_code, 200)
        new_browser, _ = self.client_for("alice")
        restored = self.get("/api/progress", new_browser).get_json()
        self.assertEqual(restored["draft"]["answers"], state["answers"])
        self.assertEqual(restored["draft"]["attemptId"], state["attemptId"])
        bob, token = self.client_for("bob")
        self.assertIsNone(self.get("/api/progress", bob).get_json()["draft"])
        self.assertEqual(self.save(state, client=bob, csrf=token).status_code, 409)
        self.assertEqual(self.get("/api/attempts/" + state["attemptId"], bob).status_code, 404)

    def test_mode_and_paper_are_independent(self):
        self.assertEqual(self.save(self.state()).status_code, 200)
        self.assertEqual(self.save(self.state(practice=True), practice=True).status_code, 400)
        self.assertEqual(self.save(self.state(paper=self.companion), group="microsoft").status_code, 200)
        self.assertEqual(self.get("/api/progress?mode=exam").get_json()["revision"], 1)
        self.assertEqual(self.get("/api/progress?mode=practice").status_code, 400)
        self.assertEqual(self.get("/api/progress?group=microsoft").get_json()["revision"], 1)

    def test_combined_carries_compatible_drafts_without_rewriting_originals(self):
        old_states = {}
        for name, part in self.paper.parts.items():
            qid = part.questions[0]["id"]
            state = self.state({qid: "B"}, part)
            state["flagged"] = [qid]
            self.assertEqual(self.save(state, group=name).status_code, 200)
            old_states[name] = self.get("/api/progress?group=" + name).get_json()
        history_before = self.get("/api/history").get_json()
        current = self.get("/api/progress").get_json()
        self.assertEqual((current["revision"], current["draft"]), (0, None))
        self.assertEqual(current["carryover"], {"answers": {"Q121": "B", "Q01": "B"}, "flagged": ["Q01", "Q121"]})
        self.assertEqual(self.get("/api/history").get_json(), history_before)
        self.assertIsNone(self.get("/api/progress", self.client_for("bob")[0]).get_json()["draft"])
        state = self.state(current["carryover"]["answers"])
        state["flagged"] = current["carryover"]["flagged"]
        self.assertEqual(self.save(state).status_code, 200)
        restored = self.get("/api/progress", self.client_for("alice")[0]).get_json()
        self.assertEqual(restored["draft"]["answers"], state["answers"])
        self.assertNotIn("carryover", restored)
        for name in old_states:
            self.assertEqual(self.get("/api/progress?group=" + name).get_json(), old_states[name])
        self.assertEqual(self.submit(state).get_json()["total"], 160)

    def test_combined_does_not_carry_submitted_or_stale_old_drafts(self):
        extension = self.paper.parts["extension"]
        old = self.state({"Q01": "B"}, extension)
        self.save(old, group="extension")
        report = self.submit(old, group="extension").get_json()
        basic = self.state({"Q121": "A"}, self.companion)
        self.save(basic, group="microsoft")
        with self.store.transaction() as db:
            db.execute("UPDATE attempts SET version=? WHERE id=?", ("0" * 64, basic["attemptId"]))
        self.assertEqual(self.get("/api/progress").get_json(), {"revision": 0, "draft": None})
        self.assertEqual(self.get("/api/reports/" + old["attemptId"]).get_json(), report)
        self.assertEqual(report["total"], 40)
        current = self.state()
        self.save(current); self.submit(current)
        rows = self.get("/api/results?policy=all").get_json()
        self.assertEqual({(row["paper"], row["total"]) for row in rows["records"]}, {("extension", 40), ("combined", 160)})
        self.assertEqual(len(rows["summaries"]), 2)

    def test_old_links_redirect_to_the_single_exam(self):
        for group in ("microsoft", "extension"):
            response = self.get("/?group=" + group)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.headers["Location"], "/")



    def test_removed_practice_is_rejected_and_old_exam_round_stays_downloadable(self):
        self.assertEqual(self.post("/api/practice", {}).status_code, 404)
        self.assertEqual(self.get("/api/results?mode=practice").status_code, 400)
        old = self.state({"Q01": "A"})
        self.assertEqual(self.save(old).status_code, 200)
        self.assertEqual(self.save(self.state(), 1).status_code, 200)
        self.assertEqual(self.get("/api/attempts/" + old["attemptId"]).get_json()["answers"], {"Q01": "A"})
        self.assertEqual(len(self.get("/api/history").get_json()["attempts"]), 2)

    def test_conflict_does_not_overwrite_and_retry_is_idempotent(self):
        state, mutation = self.state(), str(uuid4())
        original = self.save(state, mutation=mutation)
        self.assertEqual(original.status_code, 200)
        self.assertEqual(self.save(state, mutation=mutation).get_json(), original.get_json())
        state["answers"] = {"Q01": "A"}
        self.assertEqual(self.save(state, mutation=mutation).status_code, 409)
        self.assertEqual(self.save(state, 0).status_code, 409)
        self.assertEqual(self.get("/api/progress").get_json()["draft"]["answers"], {})
        self.assertEqual(self.save(state, 1).status_code, 200)

    def test_submission_is_owned_immutable_idempotent_and_server_timed(self):
        state = self.state({self.paper.questions[0]["id"]: self.paper.questions[0]["answers"][0]})
        self.assertEqual(self.save(state).status_code, 200)
        report = self.submit(state)
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.get_json()["score"], 1)
        self.assertLess(report.get_json()["elapsed_seconds"], 10)
        self.assertEqual(self.submit(state).get_json(), report.get_json())
        bob, token = self.client_for("bob")
        self.assertEqual(self.submit(state, bob, token).status_code, 404)
        self.assertEqual(self.get("/api/reports/" + state["attemptId"], bob).status_code, 404)
        state["answers"] = {}
        self.assertEqual(self.save(state, 1).status_code, 409)
        self.assertEqual(self.submit(state).status_code, 409)

    def pulse(self, state, client_id, sequence, active_ms, at):
        with patch("quiz_team_store.time.time", return_value=at):
            return self.store.heartbeat(self.alice["id"], self.paper,
                                       {"attempt_id": state["attemptId"], "client_id": client_id,
                                        "sequence": sequence, "active_ms": active_ms})["elapsed_ms"]

    def test_online_timer_excludes_closed_gap_and_resumes_on_another_device(self):
        state, client = self.state({"Q121": "B"}), str(uuid4())
        self.save(state)
        self.assertEqual(self.pulse(state, client, 1, 0, 100), 0)
        self.assertEqual(self.pulse(state, client, 2, 15000, 115), 15000)
        other = str(uuid4())
        self.assertEqual(self.pulse(state, other, 1, 0, 900000), 15000)
        self.assertEqual(self.pulse(state, other, 2, 5000, 900005), 20000)
        loaded = self.get("/api/progress").get_json()["draft"]
        self.assertEqual(loaded["elapsedMs"], 20000)
        self.assertEqual(loaded["answers"], state["answers"])

    def test_online_timer_deduplicates_retry_out_of_order_and_overlapping_tabs(self):
        state, first, second = self.state(), str(uuid4()), str(uuid4())
        self.save(state)
        self.pulse(state, first, 1, 0, 100)
        self.pulse(state, second, 1, 0, 105)
        self.assertEqual(self.pulse(state, first, 2, 15000, 115), 15000)
        self.assertEqual(self.pulse(state, first, 2, 15000, 116), 15000)
        self.assertEqual(self.pulse(state, second, 2, 15000, 120), 20000)
        self.assertEqual(self.pulse(state, first, 1, 0, 121), 20000)
        with self.assertRaises(ExamError):
            self.pulse(state, first, 2, 16000, 122)

    def test_online_timer_ignores_long_sleep_gap_client_forgery_and_wall_clock_rollback(self):
        state, client = self.state(), str(uuid4())
        self.save(state)
        self.pulse(state, client, 1, 0, 100)
        self.assertEqual(self.pulse(state, client, 2, 3600000, 3700), 0)
        self.assertEqual(self.pulse(state, client, 3, 7200000, 3715), 0)
        self.assertEqual(self.pulse(state, client, 4, 7215000, 3730), 15000)
        self.assertEqual(self.pulse(state, client, 5, 7230000, 3720), 15000)

    def test_online_timer_submission_uses_saved_time_and_freezes_the_result(self):
        state, client = self.state(), str(uuid4())
        self.save(state)
        self.pulse(state, client, 1, 0, 100)
        self.pulse(state, client, 2, 15000, 115)
        report = self.submit(state).get_json()
        self.assertEqual(report["elapsed_seconds"], 15)
        self.assertEqual(report["timing_mode"], "online-v1")
        self.assertEqual(self.pulse(state, client, 3, 30000, 130), 15000)
        self.assertEqual(self.submit(state).get_json(), report)

    def test_online_timer_endpoint_is_authenticated_owned_and_independent_of_answer_revision(self):
        state = self.state()
        self.save(state)
        payload = {"attempt_id": state["attemptId"], "client_id": str(uuid4()), "sequence": 1, "active_ms": 0}
        self.assertEqual(self.post("/api/timing", payload).status_code, 200)
        self.assertEqual(self.get("/api/progress").get_json()["revision"], 1)
        bob, csrf = self.client_for("bob")
        self.assertEqual(self.post("/api/timing", payload, bob, csrf).status_code, 409)
        self.assertEqual(self.post("/api/timing", payload, csrf="invalid").status_code, 403)
        for changed in ({"active_ms": -1}, {"active_ms": True}, {"sequence": "1"}, {"client_id": "bad"}):
            self.assertEqual(self.post("/api/timing", payload | changed).status_code, 400)
        self.save(self.state(), 1)
        self.assertEqual(self.post("/api/timing", payload).status_code, 409)

    def test_legacy_unsubmitted_time_is_not_inferred_from_start_date(self):
        state = self.state({"Q121": "B"})
        self.save(state)
        with self.store.transaction() as db:
            db.execute("UPDATE attempts SET started=1")
        self.assertEqual(self.get("/api/progress").get_json()["draft"]["elapsedMs"], 0)
        self.assertEqual(self.submit(state).get_json()["elapsed_seconds"], 0)

    def test_exam_pending_locks_answers_but_navigation_can_be_saved(self):
        state = self.state()
        state["pending"] = {"version": state["version"], "attempt_id": state["attemptId"], "answers": {}, "elapsed_seconds": 0}
        self.assertEqual(self.save(state).status_code, 200)
        state["index"] = 2
        self.assertEqual(self.save(state, 1).status_code, 200)
        state["pending"] = None
        self.assertEqual(self.save(state, 2).status_code, 409)

    def test_admin_summary_policies_do_not_mix_paper_mode_or_version(self):
        correct = {q["id"]: q["answers"][0] for q in self.paper.questions}
        one = self.state()
        self.save(one); self.submit(one)
        two = self.state(correct)
        self.save(two, 1); self.submit(two)
        ms = self.state(paper=self.companion)
        self.save(ms, group="microsoft"); self.submit(ms, group="microsoft")
        manager, token = self.client_for("manager")
        for policy, score, count in (("first", 0, 2), ("latest", 160, 2), ("best", 160, 2), ("all", 160, 3)):
            data = self.get("/api/results?scope=all&policy=" + policy, manager).get_json()
            self.assertEqual(len(data["records"]), count)
            extension = [row for row in data["records"] if row["paper"] == "combined"]
            self.assertEqual(max(row["score"] for row in extension), score)
            self.assertEqual(len(data["summaries"]), 2)
            self.assertTrue(all(row["mode"] == "exam" for row in data["records"]))
        self.assertEqual(self.get("/api/results?scope=all").status_code, 403)
        self.assertEqual(self.get("/api/results?policy=invalid").status_code, 400)
        self.assertEqual(self.get("/api/results?from=2026-11-01&to=2026-10-01").status_code, 400)
        self.assertEqual(self.get("/api/results?version=other").get_json()["records"], [])
        # Historical report snapshots survive a later paper version and retain separate first-score buckets.
        historical = Exam(selected_group="combined")
        historical.version = "0" * 64
        old = self.state({"Q01": correct["Q01"]}, historical)
        self.store.save(self.alice["id"], historical, "exam", {"revision": 2, "mutation_id": str(uuid4()), "draft": old})
        self.store.submit(self.alice, historical, {"version": historical.version, "attempt_id": old["attemptId"],
                                                "answers": old["answers"], "elapsed_seconds": 0})
        with self.store.transaction() as db:
            db.execute("UPDATE attempts SET submitted=? WHERE id=?", (0, old["attemptId"]))
        result = self.get("/api/results?paper=combined&policy=first").get_json()
        self.assertEqual({row["version"] for row in result["records"]}, {self.paper.version, historical.version})
        self.assertEqual(len(result["summaries"]), 2)
        self.assertEqual(self.get("/api/results?paper=combined&version=" + historical.version).get_json()["records"][0]["score"], 1)
        dated = self.get("/api/results?paper=combined&from=1970-01-01&to=1970-01-01").get_json()
        self.assertEqual([row["attempt_id"] for row in dated["records"]], [old["attemptId"]])
        self.assertEqual(self.get("/api/results?paper=combined&from=not-a-date").status_code, 400)

    def test_csv_formula_injection_and_examination_counts(self):
        with self.store.transaction() as db:
            db.execute("UPDATE users SET display_name='=1+1' WHERE id=?", (self.alice["id"],))
        self.save(state := self.state()); self.submit(state)
        response = self.get("/api/results?format=csv")
        self.assertIn("'=1+1", response.get_data(as_text=True))
        self.assertIn(",0,160,0.0,0,0,160,", response.get_data(as_text=True))
        self.assertIn("attachment", response.headers["Content-Disposition"])

    def test_host_origin_csrf_and_payload_limits(self):
        self.assertEqual(self.client.get("/api/session", base_url="http://evil.invalid").status_code, 400)
        self.assertEqual(self.client.get("/api/session", base_url="http://127.0.0.1:9999").status_code, 403)
        for headers in ({}, {"Origin": "https://evil.invalid", "X-Exam-Token": self.csrf}, {"Origin": ORIGIN, "X-Exam-Token": "wrong"}):
            response = self.client.post("/api/progress", json={}, base_url=ORIGIN, headers=headers)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post("/api/login", data='{"username":"a","username":"b"}', base_url=ORIGIN,
                                          headers={"Origin": ORIGIN, "Content-Type": "application/json"}).status_code, 400)
        self.assertEqual(self.client.post("/api/progress", data="x" * 70000, base_url=ORIGIN,
                                          headers={"Origin": ORIGIN, "X-Exam-Token": self.csrf, "Content-Type": "application/json"}).status_code, 413)
        self.assertEqual(self.get("/api/exam?group=types").status_code, 404)

    def test_invalid_drafts_and_changed_bank_do_not_replace_records(self):
        self.save(state := self.state())
        invalid = [state | {"version": "old"}, state | {"attemptId": "not-uuid"}, state | {"index": -1},
                   state | {"answers": {"Q04": "A"}}, state | {"answers": {"Q01": "AB"}}, state | {"flagged": [None]}]
        for value in invalid:
            self.assertIn(self.save(value, 1).status_code, (400, 409))
        self.assertEqual(self.get("/api/progress").get_json()["revision"], 1)

    def test_initial_password_change_revokes_other_sessions(self):
        self.store.reset_password("alice", PASSWORD)
        client, token = self.client_for("alice")
        other, _ = self.client_for("alice")
        self.assertEqual(self.get("/api/exam", client).status_code, 403)
        result = self.post("/api/password", {"old_password": PASSWORD, "new_password": "Different-Test-Password-84"}, client, token)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_json()["user"]["must_change"], 0)
        self.assertEqual(self.get("/api/exam", client).status_code, 200)
        self.assertEqual(self.get("/api/exam", other).status_code, 401)

    def test_admin_creation_cannot_escalate_roles_and_login_rate_is_limited(self):
        payload = {"username": "newuser", "display_name": "新人"}
        self.assertEqual(self.post("/api/admin/users", payload).status_code, 403)
        manager, token = self.client_for("manager")
        response = self.post("/api/admin/users", payload, manager, token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["role"], "student")
        self.assertGreaterEqual(len(response.get_json()["initial_password"]), 12)
        self.assertEqual(self.post("/api/admin/users", payload | {"role": "admin"}, manager, token).status_code, 400)
        self.assertEqual(self.post("/api/admin/users", payload, manager, token).status_code, 409)
        for _ in range(8):
            self.assertEqual(self.post("/api/login", {"username": "nobody", "password": PASSWORD}).status_code, 401)
        self.assertEqual(self.post("/api/login", {"username": "nobody", "password": PASSWORD}).status_code, 429)

    def test_session_cookie_expiry_logout_and_disable(self):
        client = self.app.test_client()
        response = client.post("/api/login", json={"username": "bob", "password": PASSWORD}, base_url=ORIGIN, headers={"Origin": ORIGIN})
        cookie = response.headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie); self.assertIn("SameSite=Strict", cookie)
        self.store.disable_user("bob")
        self.assertEqual(self.get("/api/exam", client).status_code, 401)
        with self.assertRaises(ExamError):
            self.store.disable_user("manager")
        self.assertEqual(self.post("/api/logout", {}).status_code, 200)
        self.assertEqual(self.get("/api/exam").status_code, 401)
        new, _ = self.client_for("alice")
        with self.store.transaction() as db:
            db.execute("UPDATE sessions SET expires=0")
        self.assertEqual(self.get("/api/exam", new).status_code, 401)

    def test_https_origin_uses_secure_cookie_and_rejects_insecure_network_origins(self):
        with self.assertRaises(ValueError):
            create_app(self.path, "http://192.168.1.2:8768")
        https_app = create_app(self.path, "https://quiz.example.internal")
        response = https_app.test_client().post("/api/login", json={"username": "alice", "password": PASSWORD},
                                               base_url="https://quiz.example.internal", headers={"Origin": "https://quiz.example.internal"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Secure", response.headers["Set-Cookie"])

    def test_opted_in_lan_http_preserves_records_and_access_boundaries(self):
        state = self.state({"Q01": "B"})
        self.save(state)
        report = self.submit(state).get_json()
        origin = "http://192.168.1.2:8080"
        app = create_app(self.path, origin, allow_insecure_http=True)
        anonymous = app.test_client()
        for path in ("/api/exam", "/api/progress", "/api/results", "/api/admin/users"):
            self.assertEqual(anonymous.get(path, base_url=origin).status_code, 401)
        self.assertEqual(anonymous.get("/question-bank.md", base_url=origin).status_code, 404)
        html = anonymous.get("/", base_url=origin).get_data(as_text=True)
        self.assertLess(html.index('/id.js'), html.index('/team-sync.js'))
        self.assertEqual(anonymous.get("/id.js", base_url=origin).status_code, 200)
        client = app.test_client()
        client.set_cookie(COOKIE, "old-https-cookie", domain="192.168.1.2", secure=True)
        login = client.post("/api/login", json={"username": "alice", "password": PASSWORD},
                            base_url=origin, headers={"Origin": origin})
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.headers["Set-Cookie"].startswith(HTTP_COOKIE + "="))
        self.assertNotIn("Secure", login.headers["Set-Cookie"])
        self.assertIn("HttpOnly", login.headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", login.headers["Set-Cookie"])
        restored = client.get("/api/progress", base_url=origin).get_json()
        self.assertEqual(restored["draft"]["report"], report)
        self.assertEqual(restored["draft"]["answers"], state["answers"])
        self.assertEqual(client.get("/api/results?scope=all", base_url=origin).status_code, 403)
        for headers in ({"Origin": "http://other.internal"}, {"Origin": origin, "X-Exam-Token": "wrong"}, {}):
            self.assertEqual(client.post("/api/logout", json={}, base_url=origin, headers=headers).status_code, 403)
        self.assertEqual(client.post("/api/logout", json={}, base_url=origin,
                                    headers={"Origin": origin, "Host": "other.internal"}).status_code, 400)
        self.assertEqual(client.post("/api/logout", json={}, base_url=origin,
                                    headers={"Origin": origin, "X-Exam-Token": login.get_json()["csrf"]}).status_code, 200)
        self.assertEqual(client.get("/api/exam", base_url=origin).status_code, 401)

    def test_restart_and_consistent_wal_backup_preserve_progress_and_scores(self):
        self.save(state := self.state()); self.submit(state)
        backup = Path(self.temporary.name) / (str(uuid4()) + ".sqlite3")
        self.store.backup(backup)
        restored = create_app(backup, ORIGIN).extensions["quiz_store"]
        self.assertEqual(restored.load(self.alice["id"], self.paper, "exam")["draft"]["report"]["attempt_id"], state["attemptId"])
        with self.assertRaises(ValueError):
            self.store.backup(backup)
        restarted = create_app(self.path, ORIGIN).test_client()
        restarted.set_cookie(COOKIE, self.client.get_cookie(COOKIE, domain="127.0.0.1").value, domain="127.0.0.1")
        self.assertEqual(restarted.get("/api/exam", base_url=ORIGIN).status_code, 200)

    def test_parallel_saves_are_isolated_and_same_revision_has_one_winner(self):
        users = [self.store.add_user("parallel" + str(i), "并发", PASSWORD, must_change=False) for i in range(16)]
        def write(account):
            state = self.state({"Q01": "A"})
            return self.store.save(account["id"], self.paper, "exam", {"revision": 0, "mutation_id": str(uuid4()), "draft": state})
        with ThreadPoolExecutor(max_workers=8) as workers:
            self.assertEqual(len(list(workers.map(write, users))), 16)
        barrier = threading.Barrier(2)
        def race(_):
            barrier.wait()
            try:
                write(self.alice)
                return 200
            except ExamError as exc:
                return exc.status
        with ThreadPoolExecutor(max_workers=2) as workers:
            self.assertEqual(sorted(workers.map(race, range(2))), [200, 409])
        self.assertTrue(all(self.store.load(account["id"], self.paper, "exam")["revision"] == 1 for account in users))


if __name__ == "__main__":
    unittest.main()
