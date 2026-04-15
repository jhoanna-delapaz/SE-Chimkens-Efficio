@echo off
echo [Efficio QA] Running Automated Feature Tests...
pytest tests/automation/test_features.py -v
echo.
echo Tests Completed.
pause
