@echo off
chcp 65001 >nul
title SIGMA VTT - بناء الملف التنفيذي المستقل (EXE Builder)
echo ====================================================================
echo             SIGMA VTT - Standalone EXE Packaging Engine
echo                       المطور: أصيل السويدي
echo ====================================================================
echo.

REM 1. التحقق من وجود PyInstaller
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo [*] PyInstaller غير مثبت. جاري التثبيت تلقائياً...
    pip install pyinstaller --quiet
)

echo [*] جاري بدء تجميع حزمة البرنامج التنفيذية عبر PyInstaller...
echo [*] تطبيق قواعد الأمان الصارمة: Zero-PyTorch مع حزم ONNX و FFmpeg...
echo.

cd /d "%~dp0backend"
pyinstaller sigma_vtt.spec --noconfirm --clean

if %errorlevel% equ 0 (
    echo.
    echo ====================================================================
    echo [OK] تم بناء الملف التنفيذي بنجاح!
    echo مسار الحزمة النهائي: %~dp0backend\dist\SIGMA_ASR_VTT\SIGMA_ASR_VTT.exe
    echo ====================================================================
) else (
    echo.
    echo [!] حدث خطأ أثناء عملية البناء. يرجى مراجعة السجلات أعلاه.
)

echo.
pause
