# Backend/frontend watchdog

Standalone process supervisor for the live trial's backend (uvicorn, port
8000) and frontend (vite dev server, port 5173). Built 2026-08-21 after the
frontend crashed unnoticed during a live session -- neither process had any
process manager before this (just plain `nohup`), so a crash meant silent
downtime until someone happened to notice.

## What it does

- Checks `GET /health` and `http://localhost:5173` every 30s.
- After 2 consecutive failures (~60s of real downtime, not a single blip),
  kills whatever's on that port and relaunches it with the same command
  used throughout this project's manual restarts.
- Sends a Telegram alert (raw Bot API call, reads `TELEGRAM_TOKEN`/
  `TELEGRAM_CHAT_ID` straight from `.env`) whenever it detects a crash and
  when it restarts something.
- Logs to `logs/watchdog.log`.

## Why a `.bat` loop instead of Task Scheduler's restart-on-failure

Task Scheduler's `-RestartCount`/`-RestartInterval` (the natural way to make
the watchdog itself self-healing) requires `Register-ScheduledTask` to run
elevated. This account's shell isn't elevated in this environment
(`Register-ScheduledTask` returned "Access Denied" here), so
`run_watchdog_forever.bat` does the same job with a plain loop: if
`watchdog.py` exits for any reason, it's relaunched within 5 seconds. No
admin rights needed.

## Setup (already done on this machine, 2026-08-21)

1. A shortcut to `run_watchdog_forever.bat` was placed in the current user's
   Startup folder (`shell:startup`, i.e.
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`), so it starts
   automatically on every logon.
2. Started immediately the same day rather than waiting for the next logon.

## Setting this up again (new machine, or if the Startup shortcut is lost)

```powershell
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$startupFolder\NexusWatchdog.lnk")
$shortcut.TargetPath = "C:\elite-decision-engine\scripts\run_watchdog_forever.bat"
$shortcut.WorkingDirectory = "C:\elite-decision-engine"
$shortcut.WindowStyle = 7
$shortcut.Save()
```

Then start it immediately without waiting for the next logon:

```bash
cd /c/elite-decision-engine
nohup cmd //c "scripts\run_watchdog_forever.bat" > logs/watchdog_wrapper.log 2>&1 &
disown
```

## If this ever moves to a real elevated/admin context

Prefer Task Scheduler's native restart-on-failure over the `.bat` loop at
that point -- cleaner process tree, real Windows Event Log integration:

```powershell
$action = New-ScheduledTaskAction -Execute "<python.exe path>" -Argument "scripts\watchdog.py" -WorkingDirectory "C:\elite-decision-engine"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "NexusWatchdog" -Action $action -Trigger $trigger -Settings $settings -Force
```
