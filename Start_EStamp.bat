@echo off

cd /d "%~dp0"

start cmd /k "estamp-billing-system\venv\Scripts\python.exe -m uvicorn main:app --reload"

timeout /t 4 > nul

start cmd /k "estamp-billing-system\venv\Scripts\python.exe -m streamlit run app.py"

timeout /t 5 > nul

start http://localhost:8501