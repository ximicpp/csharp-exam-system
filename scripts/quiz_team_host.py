"""Windows deployment supervisor; local configuration and secrets never enter the repository."""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets
from pathlib import Path
import signal
import subprocess
import threading
import time

from werkzeug.security import generate_password_hash

from quiz_team_store import Store

DEFAULT_ADMIN_USERNAME = "admin"
LOGGER = logging.getLogger("quiz-team-host")


def configure_logging(directory: Path) -> None:
    handler = RotatingFileHandler(directory / "host-events.log", maxBytes=1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def service_commands(config: dict) -> dict[str, list[str]]:
    backend = [config["python"], "-u", str(Path(config["repository"]) / "scripts/quiz_team.py"),
               "--database", config["database"], "serve", "--bind", "127.0.0.1", "--port",
               str(config["backend_port"]), "--public-url", config["public_url"]]
    if config.get("allow_insecure_http", False):
        backend.append("--allow-insecure-http")
    for option, name in (("--roster", "roster"), ("--proxy-key-file", "proxy_key_file")):
        if config.get(name):
            backend.extend((option, config[name]))
    return {"backend": backend, "gateway": [config["caddy"], "run", "--config",
            str(Path(config["data_directory"]) / "Caddyfile"), "--adapter", "caddyfile"]}


def maintain_children(commands: dict[str, list[str]], repository: str, log, stopped) -> None:
    """Restart only failed children, with bounded backoff; stop touches only our own handles."""
    children, started, failures, retry_at = {}, {}, dict.fromkeys(commands, 0), dict.fromkeys(commands, 0.0)
    try:
        while not stopped():
            now = time.monotonic()
            for name, command in commands.items():
                child = children.get(name)
                if child is not None:
                    result = child.poll()
                    if result is None:
                        if now - started[name] >= 60:
                            failures[name] = 0
                        continue
                    children.pop(name)
                    failures[name] += 1
                    delay = min(30, 2 ** min(failures[name] - 1, 5))
                    retry_at[name] = now + delay
                    LOGGER.error("EXIT service=%s pid=%s code=%s retry_seconds=%s", name, child.pid, result, delay)
                if now < retry_at[name] or stopped():
                    continue
                try:
                    child = subprocess.Popen(command, cwd=repository, stdout=log, stderr=log,
                                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                except OSError as error:
                    failures[name] += 1
                    retry_at[name] = now + min(30, 2 ** min(failures[name] - 1, 5))
                    LOGGER.error("LAUNCH_FAILED service=%s error=%s retry_at=%.3f", name, error, retry_at[name])
                else:
                    children[name], started[name] = child, now
                    LOGGER.info("CHILD_START service=%s pid=%s", name, child.pid)
            time.sleep(1)
    finally:
        for name, child in reversed(list(children.items())):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    LOGGER.warning("FORCE_STOP service=%s pid=%s", name, child.pid)
                    child.kill()
                    child.wait()


def keep_awake(enabled: bool) -> None:
    """Hold only automatic system sleep; leave display timeout and saved power plans alone."""
    import ctypes

    execution_state = ctypes.windll.kernel32.SetThreadExecutionState
    execution_state.argtypes = [ctypes.c_uint]
    execution_state.restype = ctypes.c_uint
    result = execution_state(0x80000001 if enabled else 0x80000000)
    if not result:
        LOGGER.warning("POWER_REQUEST_FAILED enabled=%s", enabled)


def process_created_filetime() -> str:
    """Exact Windows creation time binds an owner-only PID record to its process lifetime."""
    import ctypes
    from ctypes.wintypes import BOOL, FILETIME, HANDLE

    times = [FILETIME() for _ in range(4)]
    get_times = ctypes.windll.kernel32.GetProcessTimes
    get_times.argtypes = [HANDLE, *([ctypes.POINTER(FILETIME)] * 4)]
    get_times.restype = BOOL
    if not get_times(HANDLE(-1), *(ctypes.byref(value) for value in times)):
        raise ctypes.WinError()
    return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)


def own_process_job():
    """Children inherit this job; the OS reaps the whole group if this host dies abruptly."""
    import ctypes
    from ctypes.wintypes import BOOL, DWORD, HANDLE, LPCWSTR

    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                    ("flags", DWORD), ("min_working_set", ctypes.c_size_t), ("max_working_set", ctypes.c_size_t),
                    ("active_processes", DWORD), ("affinity", ctypes.c_size_t), ("priority", DWORD), ("scheduling", DWORD)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("basic", BasicLimits), ("io_counters", ctypes.c_ulonglong * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, LPCWSTR]
    kernel.CreateJobObjectW.restype = HANDLE
    kernel.SetInformationJobObject.argtypes = [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD]
    kernel.SetInformationJobObject.restype = BOOL
    kernel.AssignProcessToJobObject.argtypes = [HANDLE, HANDLE]
    kernel.AssignProcessToJobObject.restype = BOOL
    kernel.CloseHandle.argtypes = [HANDLE]
    kernel.CloseHandle.restype = BOOL
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = ExtendedLimits()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(job, HANDLE(-1)):
        error = ctypes.get_last_error()
        kernel.CloseHandle(job)
        raise ctypes.WinError(error)
    # Deliberately keep this raw handle open until process exit. Closing it explicitly would
    # terminate this host too; the OS closes it after a graceful exit or a forced termination.
    return job


def use_default_admin(config: dict) -> None:
    """Explicit operator action; never reset an existing password during startup."""
    store = Store(Path(config["database"]))
    password = secrets.token_urlsafe(24)
    hashed = generate_password_hash(password)
    with store.transaction() as db:
        row = db.execute("SELECT id,role,disabled FROM users WHERE username=?", (DEFAULT_ADMIN_USERNAME,)).fetchone()
        if row is None:
            row = db.execute("SELECT id,role,disabled FROM users WHERE username='quiz-admin'").fetchone()
        if not row or row["role"] != "admin" or row["disabled"]:
            raise ValueError("An active admin or legacy quiz-admin administrator is required; no account was adopted or promoted")
        db.execute("UPDATE users SET username=?,password_hash=?,must_change=0 WHERE id=?",
                   (DEFAULT_ADMIN_USERNAME, hashed, row["id"]))
        db.execute("DELETE FROM sessions WHERE user_id=?", (row["id"],))
    credentials = Path(config["data_directory"]) / "initial-admin.json"
    credentials.write_text(json.dumps({"username": DEFAULT_ADMIN_USERNAME, "password": password,
                                      "note": "随机生成的管理员密码；请妥善保管。"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS: administrator password regenerated; prior administrator sessions invalidated", flush=True)


def bootstrap(config: dict) -> None:
    store = Store(Path(config["database"]))
    with store.connect() as db:
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        admins = db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND disabled=0").fetchone()[0]
    if count:
        if not admins:
            raise ValueError("Existing database has no active administrator; preserve it and repair access explicitly")
        print("PASS: existing accounts preserved", flush=True)
        return
    credentials = Path(config["data_directory"]) / "initial-admin.json"
    password = secrets.token_urlsafe(24)
    # Exclusive create prevents replacing an earlier bootstrap password.
    with credentials.open("x", encoding="utf-8") as stream:
        json.dump({"username": DEFAULT_ADMIN_USERNAME, "password": password,
                   "note": "随机生成的管理员密码；请妥善保管。"}, stream, ensure_ascii=False, indent=2)
    store.add_user(DEFAULT_ADMIN_USERNAME, "题库管理员", password, admin=True, must_change=False)
    print(f"PASS: administrator created; initial credentials: {credentials}", flush=True)


def supervise(config: dict) -> None:
    import msvcrt

    directory = Path(config["data_directory"])
    interrupted = threading.Event()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, lambda *_: interrupted.set())
    # Windows byte-range lock survives stale lock files and prevents duplicate supervisors.
    with (directory / "host.lock").open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            LOGGER.info("ALREADY_RUNNING singleton lock is held")
            return
        pid_file = directory / "host.pid"
        state_file = directory / "host-state.json"
        stop_file = directory / "stop.request"
        pause_file = directory / "maintenance.pause"
        if pause_file.exists():
            LOGGER.info("PAUSED explicit maintenance stop remains in effect")
            return
        job_handle = own_process_job()
        stop_file.unlink(missing_ok=True)
        temporary_state = directory / "host-state.tmp"
        temporary_state.write_text(json.dumps({"pid": os.getpid(), "created_filetime": process_created_filetime(),
                                               "data_directory": str(directory)}), encoding="utf-8")
        temporary_state.replace(state_file)
        pid_file.write_text(str(os.getpid()), encoding="ascii")
        LOGGER.info("HOST_START pid=%s parent=%s url=%s", os.getpid(), os.getppid(), config["public_url"])
        try:
            keep_awake(True)
            with (directory / "services.log").open("ab", buffering=0) as log:
                maintain_children(service_commands(config), config["repository"], log,
                                  lambda: interrupted.is_set() or stop_file.exists() or pause_file.exists())
        finally:
            reason = "maintenance" if pause_file.exists() else "request" if stop_file.exists() else "signal_or_error"
            keep_awake(False)
            pid_file.unlink(missing_ok=True)
            state_file.unlink(missing_ok=True)
            stop_file.unlink(missing_ok=True)
            LOGGER.info("HOST_STOP pid=%s reason=%s database preserved", os.getpid(), reason)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--bootstrap", action="store_true")
    actions.add_argument("--use-default-admin", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if args.bootstrap:
        bootstrap(config)
    elif args.use_default_admin:
        use_default_admin(config)
    else:
        configure_logging(Path(config["data_directory"]))
        try:
            supervise(config)
        except Exception:
            LOGGER.exception("HOST_FAILED pid=%s", os.getpid())
            raise


if __name__ == "__main__":
    main()
