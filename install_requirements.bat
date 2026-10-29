@echo off
chcp 65001 >nul
echo ==========================================================
echo    🌟 تثبيت متطلبات ومكتبات تشغيل Sigma VTT (حزمة assel)
echo ==========================================================
echo.

echo [1/3] التحقق من بايثون وتثبيت مكتبات الـ Backend (requirements.txt)...
cd /d "%~dp0backend"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ❌ حدث خطأ أثناء تثبيت مكاتب بايثون. تأكد من تثبيت Python وإضافته لـ PATH.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] تثبيت حزم الواجهة الأمامية (Frontend npm modules)...
cd /d "%~dp0frontend"
call npm install
if %ERRORLEVEL% neq 0 (
    echo ❌ حدث خطأ أثناء تثبيت حزم Node.js. تأكد من تثبيت Node.js و npm.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] إزالة أي قيود أمنية على ملفات ffmpeg (Unblock Mark-of-the-Web)...
powershell -NoProfile -Command "if (Test-Path 'C:\ffmpeg\bin') { Unblock-File -Path 'C:\ffmpeg\bin\*.exe' -ErrorAction SilentlyContinue }"

echo.
echo ==========================================================
echo    ✅ اكتمل تثبيت كافة المتطلبات والمكتبات بنجاح تام!
echo    يمكنك الآن تشغيل الأداة بالنقر على: run_sigma_vtt.bat
echo ==========================================================
pause
