@echo off
echo Installing required modules for Python...
python -m pip install -r requirements.txt

echo.
echo Installing required modules for Python3 (if applicable)...
python3 -m pip install -r requirements.txt

echo.
echo Starting Efficio...
python src/main.py
pause
