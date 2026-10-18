@echo off
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges...
    python main.py
) else (
    echo Elevating privileges for Windows NetQoS control...
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"%~dp0\" && python main.py' -Verb runAs"
)
