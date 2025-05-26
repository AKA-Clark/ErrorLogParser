@echo off
echo Starting Log Monitor...

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Run the Python script
python main.py

REM Optional message after script exits
echo Log Monitor stopped.
pause
