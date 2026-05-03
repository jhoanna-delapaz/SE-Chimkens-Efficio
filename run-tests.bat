@echo off
echo =======================================================
echo [Efficio QA] Running Professional Quality Suite
echo =======================================================
echo.
echo Phase 1: Functional Suitability (Feature Tests)...
pytest tests/automation/test_features.py -v
echo.
echo Phase 2: ISO 25010 Compliance (Security, Portability, Maintainability)...
pytest tests/automation/test_iso25010_compliance.py -v
echo.
echo =======================================================
echo All Verification Phases Completed.
echo =======================================================
pause
