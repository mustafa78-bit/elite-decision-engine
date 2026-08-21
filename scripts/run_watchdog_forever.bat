@echo off
REM Restart-on-exit wrapper for watchdog.py. Loops forever: if the Python
REM process exits for any reason (crash, uncaught exception), it's
REM relaunched within 5 seconds. This is the "who watches the watchdog"
REM answer -- Task Scheduler's built-in restart-on-failure needs Administrator
REM rights this account's shell doesn't have elevated, so a plain batch loop
REM does the same job without that requirement.
cd /d C:\elite-decision-engine
:loop
"C:\Users\musta\AppData\Local\Python\pythoncore-3.14-64\python.exe" scripts\watchdog.py
echo watchdog.py exited, restarting in 5s...
timeout /t 5 /nobreak >nul
goto loop
