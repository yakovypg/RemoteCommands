@echo off
cd /d "C:\Users\%USERNAME%\Documents\Executor"
call .venv\Scripts\activate
python executor.py
