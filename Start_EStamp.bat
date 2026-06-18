@echo off

cd /d "%~dp0"

start "E-Stamp Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn main:app --reload"

timeout /t 5 > nul

start "E-Stamp Frontend" cmd /k ".\venv\Scripts\python.exe -m streamlit run app.py"

timeout /t 4 > nul

start http://localhost:8501