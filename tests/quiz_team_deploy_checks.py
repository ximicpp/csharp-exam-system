"""Bootstrap checks use temporary directories, never the deployed database or actual credentials."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from quiz_team import create_app
from quiz_team_host import bootstrap, use_default_admin
from quiz_team_store import Store
import quiz_team_host as host

ROOT = Path(__file__).resolve().parents[1]


class DeploymentChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name).resolve()
        self.config = {"data_directory": str(self.directory), "database": str(self.directory / "team.sqlite3")}
        self.credentials = self.directory / "initial-admin.json"

    def tearDown(self):
        self.temporary.cleanup()

    def test_initial_admin_uses_random_password_without_required_change(self):
        bootstrap(self.config)
        credentials = json.loads(self.credentials.read_text(encoding="utf-8"))
        app = create_app(Path(self.config["database"]), "https://192.168.1.20:8443")
        client = app.test_client()
        response = client.post("/api/login", json={key: credentials[key] for key in ("username", "password")},
                               base_url="https://192.168.1.20:8443", headers={"Origin": "https://192.168.1.20:8443"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["role"], "admin")
        self.assertGreaterEqual(len(credentials["password"]), 24)
        self.assertFalse(response.get_json()["user"]["must_change"])
        self.assertIn("Secure", response.headers["Set-Cookie"])
        self.assertEqual(client.get("/api/admin/users", base_url="https://192.168.1.20:8443").status_code, 200)

    def test_separate_deployments_get_different_random_admin_passwords(self):
        bootstrap(self.config)
        first = json.loads(self.credentials.read_text(encoding="utf-8"))["password"]
        other = self.directory / "other"
        other.mkdir()
        bootstrap({"data_directory": str(other), "database": str(other / "team.sqlite3")})
        second = json.loads((other / "initial-admin.json").read_text(encoding="utf-8"))["password"]
        self.assertNotEqual(first, second)

    def test_prepare_again_preserves_accounts_and_password(self):
        bootstrap(self.config)
        before = self.credentials.read_bytes()
        with Store(Path(self.config["database"])).connect() as db:
            old_hash = db.execute("SELECT password_hash FROM users").fetchone()[0]
        bootstrap(self.config)
        self.assertEqual(self.credentials.read_bytes(), before)
        with Store(Path(self.config["database"])).connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT password_hash FROM users").fetchone()[0], old_hash)

    def test_existing_credential_file_is_never_replaced(self):
        self.credentials.write_text("preserve this earlier credential", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            bootstrap(self.config)
        self.assertEqual(self.credentials.read_text(encoding="utf-8"), "preserve this earlier credential")
        with Store(Path(self.config["database"])).connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)

    def test_existing_non_admin_database_is_not_silently_adopted(self):
        store = Store(Path(self.config["database"]))
        store.add_user("learner", "原有学员", "Preserve-Student-Password")
        with self.assertRaises(ValueError):
            bootstrap(self.config)
        self.assertFalse(self.credentials.exists())
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_explicit_default_admin_update_preserves_other_accounts_and_records(self):
        bootstrap(self.config)
        store = Store(Path(self.config["database"]))
        student = store.add_user("learner", "原学员", "Preserve-Student-Password", must_change=False)
        # Model the deployed account from the older random-password version.
        with store.transaction() as db:
            db.execute("UPDATE users SET username='quiz-admin' WHERE username='admin'")
        store.reset_password("quiz-admin", "Previously-Custom-Password")
        old_token, old_auth = store.login("quiz-admin", "Previously-Custom-Password")
        with store.transaction() as db:
            db.execute("INSERT INTO attempts(id,user_id,paper,mode,version,started,updated,state,report,submitted) "
                       "VALUES('preserved-attempt',?,'extension','exam','old-version',1,2,'old-draft','old-report',2)", (student["id"],))
            student_before = tuple(db.execute("SELECT * FROM users WHERE id=?", (student["id"],)).fetchone())
            report_before = tuple(db.execute("SELECT * FROM attempts").fetchone())
        use_default_admin(self.config)
        self.assertIsNone(store.session(old_token))
        _, auth = store.login("admin", json.loads(self.credentials.read_text(encoding="utf-8"))["password"])
        self.assertEqual(auth["user"]["id"], old_auth["user"]["id"])
        self.assertFalse(auth["user"]["must_change"])
        with store.connect() as db:
            self.assertEqual(tuple(db.execute("SELECT * FROM users WHERE id=?", (student["id"],)).fetchone()), student_before)
            self.assertEqual(tuple(db.execute("SELECT * FROM attempts").fetchone()), report_before)
        before = self.credentials.read_bytes()
        bootstrap(self.config)
        self.assertEqual(self.credentials.read_bytes(), before)

    def test_default_admin_update_does_not_adopt_a_colliding_student(self):
        store = Store(Path(self.config["database"]))
        store.add_user("quiz-admin", "原管理员", "Original-Admin-Password", admin=True)
        student = store.add_user("admin", "同名学员", "Original-Student-Password")
        with store.connect() as db:
            before = [tuple(row) for row in db.execute("SELECT * FROM users ORDER BY id")]
        with self.assertRaises(ValueError):
            use_default_admin(self.config)
        with store.connect() as db:
            self.assertEqual([tuple(row) for row in db.execute("SELECT * FROM users ORDER BY id")], before)
        self.assertFalse(self.credentials.exists())
        self.assertEqual(store.login("admin", "Original-Student-Password")[1]["user"]["id"], student["id"])

    def test_real_child_failure_recovers_without_restarting_healthy_sibling(self):
        helper = self.directory / "child.py"
        helper.write_text("""import os, pathlib, sys, time
directory, name = pathlib.Path(sys.argv[1]), sys.argv[2]
with (directory / (name + '.pids')).open('a') as stream:
    stream.write(str(os.getpid()) + '\\n')
once = directory / 'failed-once'
if name == 'backend' and not once.exists():
    once.touch()
    sys.exit(42)
while True:
    time.sleep(1)
""", encoding="utf-8")
        commands = {name: [sys.executable, str(helper), str(self.directory), name] for name in ("backend", "gateway")}
        stopped, children, errors = threading.Event(), [], []
        real_popen = subprocess.Popen

        def launch(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child

        with (self.directory / "children.log").open("ab", buffering=0) as log:
            def run():
                try:
                    host.maintain_children(commands, str(self.directory), log, stopped.is_set)
                except BaseException as error:
                    errors.append(error)

            with patch.object(host.subprocess, "Popen", side_effect=launch), self.assertLogs(host.LOGGER, level="INFO") as events:
                worker = threading.Thread(target=run)
                worker.start()
                try:
                    deadline = time.monotonic() + 18
                    while time.monotonic() < deadline:
                        backend = self.directory / "backend.pids"
                        if backend.exists() and len(backend.read_text().splitlines()) == 2:
                            break
                        time.sleep(0.1)
                    self.assertEqual(len(backend.read_text().splitlines()), 2)
                    self.assertEqual(len((self.directory / "gateway.pids").read_text().splitlines()), 1)
                finally:
                    stopped.set()
                    worker.join(timeout=15)
                self.assertFalse(worker.is_alive())
                self.assertEqual(errors, [])
                self.assertTrue(all(child.poll() is not None for child in children))
                self.assertTrue(any("code=42" in entry for entry in events.output))

    def test_rapid_exits_back_off_and_never_interrupt_a_healthy_child(self):
        clock, launches = [0], {"backend": [], "gateway": []}
        healthy = Mock(pid=10)
        healthy.poll.return_value = None

        def launch(command, **_):
            name = command[0]
            launches[name].append(clock[0])
            if name == "gateway":
                return healthy
            failed = Mock(pid=11)
            failed.poll.return_value = 1
            return failed

        with patch.object(host.subprocess, "Popen", side_effect=launch), \
                patch.object(host.time, "monotonic", side_effect=lambda: clock[0]), \
                patch.object(host.time, "sleep", side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)), \
                self.assertLogs(host.LOGGER, level="INFO"):
            host.maintain_children({"backend": ["backend"], "gateway": ["gateway"]}, str(self.directory), None, lambda: clock[0] >= 12)
        self.assertEqual(launches["backend"], [0, 2, 5, 10])
        self.assertEqual(launches["gateway"], [0])
        healthy.terminate.assert_called_once()

    def test_launch_error_is_retried_instead_of_exiting_the_supervisor(self):
        clock, calls = [0], []
        child = Mock(pid=20)
        child.poll.return_value = None

        def launch(*_, **__):
            calls.append(clock[0])
            if len(calls) == 1:
                raise OSError("temporary launch failure")
            return child

        with patch.object(host.subprocess, "Popen", side_effect=launch), \
                patch.object(host.time, "monotonic", side_effect=lambda: clock[0]), \
                patch.object(host.time, "sleep", side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)), \
                self.assertLogs(host.LOGGER, level="INFO") as events:
            host.maintain_children({"backend": ["backend"]}, str(self.directory), None, lambda: clock[0] >= 4)
        self.assertEqual(calls, [0, 1])
        self.assertTrue(any("LAUNCH_FAILED" in entry for entry in events.output))
        child.terminate.assert_called_once()

    @unittest.skipUnless(os.name == "nt", "Windows task definition")
    def test_task_definition_runs_without_logon_or_time_limit_and_stop_is_persistent(self):
        config = {**self.config, "repository": str(ROOT), "python": sys.executable, "web_port": 18080,
                  "backend_port": 18769, "protocol": "http", "public_url": "http://127.0.0.1:18080"}
        (self.directory / "deployment.json").write_text(json.dumps(config), encoding="utf-8")
        command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(ROOT / "scripts/quiz_team_windows.ps1"), "-DataDirectory", str(self.directory)]
        result = subprocess.run(command + ["-Action", "TaskDefinition"], capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        task = json.loads(result.stdout.decode("utf-8-sig"))
        self.assertEqual(task["Principal"]["LogonType"], 2)  # S4U, not an interactive token.
        self.assertEqual(task["Principal"]["RunLevel"], 0)
        self.assertEqual(task["Settings"]["ExecutionTimeLimit"], "PT0S")
        self.assertEqual(task["Settings"]["MultipleInstances"], 2)  # IgnoreNew.
        self.assertFalse(task["Settings"]["StopIfGoingOnBatteries"])
        self.assertFalse(task["Settings"]["DisallowStartIfOnBatteries"])
        self.assertTrue(any(trigger["Repetition"].get("Interval") == "PT1M" for trigger in task["Triggers"]))
        self.assertTrue(any(trigger["Type"] == "MSFT_TaskBootTrigger" for trigger in task["Triggers"]))
        self.assertIn("-Action Run", task["Actions"][0]["Arguments"])
        self.assertIn(str(self.directory), task["Actions"][0]["Arguments"])
        (self.directory / "maintenance.pause").touch()
        paused = subprocess.run(command + ["-Action", "Run"], capture_output=True, timeout=30)
        self.assertEqual(paused.returncode, 0, paused.stderr.decode(errors="replace"))
        self.assertFalse((self.directory / "host.pid").exists())
        self.assertFalse(Path(config["database"]).exists())

    @unittest.skipUnless(os.name == "nt", "Windows process jobs")
    def test_forced_host_exit_reaps_descendants_including_the_python_launcher(self):
        import ctypes
        from ctypes.wintypes import BOOL, DWORD, HANDLE

        helper = self.directory / "job_parent.py"
        parent_pid, child_pid = self.directory / "parent.pid", self.directory / "child.pid"
        helper.write_text("""import os, pathlib, subprocess, sys, time
sys.path.insert(0, sys.argv[1])
from quiz_team_host import own_process_job
job = own_process_job()
child = subprocess.Popen([sys.executable, '-c',
    'import os,pathlib,sys,time;pathlib.Path(sys.argv[1]).write_text(str(os.getpid()));time.sleep(60)', sys.argv[3]])
pathlib.Path(sys.argv[2]).write_text(str(os.getpid()))
time.sleep(60)
""", encoding="utf-8")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes, kernel.OpenProcess.restype = [DWORD, BOOL, DWORD], HANDLE
        kernel.WaitForSingleObject.argtypes, kernel.WaitForSingleObject.restype = [HANDLE, DWORD], DWORD
        kernel.TerminateProcess.argtypes, kernel.TerminateProcess.restype = [HANDLE, DWORD], BOOL
        kernel.CloseHandle.argtypes = [HANDLE]
        handles = []
        with (self.directory / "job.log").open("wb") as log:
            parent = subprocess.Popen([sys.executable, str(helper), str(ROOT / "scripts"), str(parent_pid), str(child_pid)], stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline and not (parent_pid.exists() and child_pid.exists()):
                    if parent.poll() is not None:
                        break
                    time.sleep(0.1)
                self.assertTrue(child_pid.exists(), (self.directory / "job.log").read_text(errors="replace"))
                for path in (parent_pid, child_pid):
                    handle = kernel.OpenProcess(0x100001, False, int(path.read_text()))  # SYNCHRONIZE | TERMINATE
                    self.assertTrue(handle)
                    handles.append(handle)
                self.assertEqual(kernel.WaitForSingleObject(handles[1], 0), 258)
                self.assertTrue(kernel.TerminateProcess(handles[0], 47))
                self.assertEqual(kernel.WaitForSingleObject(handles[1], 5000), 0, "orphaned descendant survived the host job")
                parent.wait(timeout=10)
            finally:
                for handle in handles:
                    if kernel.WaitForSingleObject(handle, 0) == 258:
                        kernel.TerminateProcess(handle, 48)
                    kernel.CloseHandle(handle)
                if parent.poll() is None:
                    parent.kill()
                    parent.wait(timeout=10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
