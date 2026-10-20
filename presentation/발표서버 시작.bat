@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0serve_deck.py" %*
    goto done
)
where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0serve_deck.py" %*
    goto done
)
echo Windows Python 3 is required. Install Python and run this file again.
:done
pause