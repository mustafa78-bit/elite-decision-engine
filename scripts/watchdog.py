"""Standalone process supervisor for the NEXUS live backend (uvicorn, port
8000) and frontend (vite dev server, port 5173).

Built 2026-08-21 after the frontend dev server crashed unnoticed during a
live debugging session -- neither process has any process manager (no
systemd/pm2/Docker in the current trial deployment, just plain `nohup`),
so a crash meant silent downtime until someone happened to notice.

Deliberately standalone (its own process, not a FastAPI background task)
so a backend crash can't also kill its own supervisor. Reads TELEGRAM_TOKEN/
TELEGRAM_CHAT_ID directly from .env via a raw HTTP POST to Telegram's Bot
API -- not the app's TelegramBotManager, which pulls in the full
python-telegram-bot Application/polling machinery this script doesn't need.

Run this itself under something that restarts it on exit (Windows Task
Scheduler, "restart on failure") -- see scripts/README_WATCHDOG.md for the
setup steps. That closes the "who watches the watchdog" gap with an OS-level
mechanism instead of a second custom script.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

import requests

REPO_ROOT = Path(r"C:\elite-decision-engine")
PYTHON_EXE = r"C:\Users\musta\AppData\Local\Python\pythoncore-3.14-64\python.exe"

BACKEND_HEALTH_URL = "http://localhost:8000/health"
FRONTEND_URL = "http://localhost:5173"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

CHECK_INTERVAL_SECONDS = 30
# Require 2 consecutive failed checks (~60s of real downtime) before acting --
# a single missed check (e.g. the process is momentarily busy) must not
# trigger a restart; that would just add more disruption on top of a
# transient blip instead of a genuine crash.
FAILURES_BEFORE_RESTART = 2
HEALTH_CHECK_TIMEOUT_SECONDS = 5

LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
WATCHDOG_LOG = LOG_DIR / "watchdog.log"
BACKEND_LOG = LOG_DIR / "backend_live.log"
FRONTEND_LOG = LOG_DIR / "vite_live.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(WATCHDOG_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("watchdog")


def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


_ENV = _load_env()
TELEGRAM_TOKEN = _ENV.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = _ENV.get("TELEGRAM_CHAT_ID", "")


def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_TOKEN/TELEGRAM_CHAT_ID not set -- skipping alert: %s", message)
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
    except requests.RequestException as e:
        logger.warning("Failed to send Telegram alert: %s", e)


def _pid_listening_on_port(port: int) -> int | None:
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.warning("netstat failed: %s", e)
        return None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and f":{port}" in parts[1] and parts[-1] != "0":
            try:
                return int(parts[-1])
            except ValueError:
                continue
    return None


def _kill_pid(pid: int) -> None:
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=15)
        logger.info("Killed PID %d", pid)
    except Exception as e:
        logger.warning("Failed to kill PID %d: %s", pid, e)


def check_backend() -> bool:
    try:
        r = requests.get(BACKEND_HEALTH_URL, timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        return r.status_code == 200
    except requests.RequestException:
        return False


def check_frontend() -> bool:
    try:
        r = requests.get(FRONTEND_URL, timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        return r.status_code == 200
    except requests.RequestException:
        return False


def restart_backend() -> None:
    pid = _pid_listening_on_port(BACKEND_PORT)
    if pid is not None:
        _kill_pid(pid)
        time.sleep(2)
    with open(BACKEND_LOG, "a", encoding="utf-8") as log_f:
        subprocess.Popen(
            [PYTHON_EXE, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
            cwd=str(REPO_ROOT),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    logger.info("Backend restart issued")


def restart_frontend() -> None:
    pid = _pid_listening_on_port(FRONTEND_PORT)
    if pid is not None:
        _kill_pid(pid)
        time.sleep(2)
    with open(FRONTEND_LOG, "a", encoding="utf-8") as log_f:
        subprocess.Popen(
            ["npm", "run", "dev", "--", "--host"],
            cwd=str(REPO_ROOT / "frontend"),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            shell=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    logger.info("Frontend restart issued")


def main() -> None:
    logger.info("Watchdog started -- checking every %ds", CHECK_INTERVAL_SECONDS)
    send_telegram_alert("🐕 <b>Watchdog başladı</b> -- backend ve frontend izleniyor.")

    backend_fail_count = 0
    frontend_fail_count = 0

    while True:
        time.sleep(CHECK_INTERVAL_SECONDS)

        if check_backend():
            backend_fail_count = 0
        else:
            backend_fail_count += 1
            logger.warning("Backend health check failed (%d/%d)", backend_fail_count, FAILURES_BEFORE_RESTART)
            if backend_fail_count >= FAILURES_BEFORE_RESTART:
                logger.error("Backend down -- restarting")
                send_telegram_alert("🔴 <b>Backend çöktü, yeniden başlatılıyor...</b>")
                try:
                    restart_backend()
                except Exception as e:
                    logger.error("Backend restart failed: %s", e)
                    send_telegram_alert(f"⚠️ Backend restart BAŞARISIZ: {e}")
                backend_fail_count = 0
                time.sleep(15)  # give it real time to boot before the next check

        if check_frontend():
            frontend_fail_count = 0
        else:
            frontend_fail_count += 1
            logger.warning("Frontend health check failed (%d/%d)", frontend_fail_count, FAILURES_BEFORE_RESTART)
            if frontend_fail_count >= FAILURES_BEFORE_RESTART:
                logger.error("Frontend down -- restarting")
                send_telegram_alert("🔴 <b>Frontend çöktü, yeniden başlatılıyor...</b>")
                try:
                    restart_frontend()
                except Exception as e:
                    logger.error("Frontend restart failed: %s", e)
                    send_telegram_alert(f"⚠️ Frontend restart BAŞARISIZ: {e}")
                frontend_fail_count = 0
                time.sleep(15)


if __name__ == "__main__":
    main()
