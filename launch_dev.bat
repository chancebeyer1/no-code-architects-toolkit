@echo off
cd /d %~dp0

REM Step 1: Set execution policy (silent)
powershell -Command "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force"

REM Step 2: Activate virtual environment
call venv\Scripts\activate.bat

REM Step 3: Install requirements
pip install -r requirements.txt

REM Step 4: Run test script
python test_run.py

pause
