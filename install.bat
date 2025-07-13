@echo off
chcp 65001 >nul
title 📱 手機檔案傳輸系統 - 一鍵安裝

echo.
echo ========================================================
echo 📱 手機檔案傳輸系統 - 雲端一鍵安裝
echo ========================================================
echo.

echo ✅ 檢查系統環境...

:: 檢查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未安裝Python，正在開啟下載頁面...
    start https://www.python.org/downloads/
    echo 📥 請先安裝Python 3.7或更高版本後重新執行此腳本
    pause
    exit /b 1
)

echo ✅ Python環境正常

:: 檢查curl或powershell
curl --version >nul 2>&1
if errorlevel 1 (
    echo 📡 使用PowerShell下載檔案...
    set "DOWNLOAD_METHOD=powershell"
) else (
    echo 📡 使用curl下載檔案...
    set "DOWNLOAD_METHOD=curl"
)

:: 創建安裝目錄
set "INSTALL_DIR=%USERPROFILE%\Desktop\手機檔案傳輸"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

echo.
echo 📂 安裝目錄: %INSTALL_DIR%
echo.

:: GitHub Raw URLs (需要替換為實際的GitHub倉庫)
set "BASE_URL=https://raw.githubusercontent.com/你的用戶名/Mobile-File-Transfer/main"

:: 檔案列表
set "FILES=app_improved.py requirements.txt start_server.bat"
set "DIRS=templates static uploads"
set "TEMPLATE_FILES=templates/index.html"
set "STATIC_FILES=static/style.css"

echo 📥 正在下載程式檔案...

:: 下載主要檔案
for %%f in (%FILES%) do (
    echo   下載 %%f...
    if "%DOWNLOAD_METHOD%"=="curl" (
        curl -s -L -o "%%f" "%BASE_URL%/%%f"
    ) else (
        powershell -Command "Invoke-WebRequest -Uri '%BASE_URL%/%%f' -OutFile '%%f'"
    )
    if not exist "%%f" (
        echo   ❌ 下載 %%f 失敗
        goto :download_error
    )
)

:: 創建目錄
for %%d in (%DIRS%) do (
    if not exist "%%d" mkdir "%%d"
)

:: 下載模板檔案
for %%f in (%TEMPLATE_FILES%) do (
    echo   下載 %%f...
    if "%DOWNLOAD_METHOD%"=="curl" (
        curl -s -L -o "%%f" "%BASE_URL%/%%f"
    ) else (
        powershell -Command "Invoke-WebRequest -Uri '%BASE_URL%/%%f' -OutFile '%%f'"
    )
)

:: 下載靜態檔案
for %%f in (%STATIC_FILES%) do (
    echo   下載 %%f...
    if "%DOWNLOAD_METHOD%"=="curl" (
        curl -s -L -o "%%f" "%BASE_URL%/%%f"
    ) else (
        powershell -Command "Invoke-WebRequest -Uri '%BASE_URL%/%%f' -OutFile '%%f'"
    )
)

echo.
echo 📦 安裝Python依賴套件...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ 安裝依賴套件失敗，請檢查網路連接
    pause
    exit /b 1
)

echo.
echo ✅ 安裝完成！
echo.
echo 📁 程式安裝在: %INSTALL_DIR%
echo 🚀 使用方式:
echo    1. 雙擊 start_server.bat 啟動程式
echo    2. 用手機掃描QR Code上傳檔案
echo    3. 如果無法連接，點擊「下一個IP」按鈕
echo.

:: 創建桌面快捷方式
echo 🔗 正在創建桌面快捷方式...
set "SHORTCUT=%USERPROFILE%\Desktop\📱手機檔案傳輸.bat"
echo @echo off > "%SHORTCUT%"
echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT%"
echo start_server.bat >> "%SHORTCUT%"

echo ✅ 桌面快捷方式已創建: 📱手機檔案傳輸.bat
echo.

choice /c YN /m "是否立即啟動程式? (Y/N)"
if errorlevel 2 goto :end
if errorlevel 1 (
    echo 🚀 啟動程式...
    call start_server.bat
)

goto :end

:download_error
echo.
echo ❌ 下載失敗，可能的原因:
echo    1. 網路連接問題
echo    2. GitHub倉庫不存在或私有
echo    3. 檔案路徑錯誤
echo.
echo 💡 請檢查網路連接後重試，或手動下載檔案
pause
exit /b 1

:end
echo.
echo 🎉 感謝使用手機檔案傳輸系統！
pause 