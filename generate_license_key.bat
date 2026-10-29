@echo off
chcp 65001 >nul
title SIGMA VTT - مولد تراخيص ومفاتيح الأجهزة
echo ====================================================================
echo             SIGMA VTT - Master License Key Generator
echo                       المطور: أصيل السويدي
echo ====================================================================
echo.
python "%~dp0backend\scripts\keygen.py"
echo.
echo ====================================================================
pause
