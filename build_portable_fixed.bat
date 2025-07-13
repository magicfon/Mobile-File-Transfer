@echo off
chcp 65001 >nul
title 手機檔案傳輸系統 - 打包工具

echo.
echo ========================================================
echo 手機檔案傳輸系統 - 打包成可執行文件
echo ========================================================
echo.

echo 檢查打包環境...

:: 檢查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 未安裝Python，無法進行打包
    echo 請先安裝Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python環境正常

:: 檢查PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安裝PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 錯誤: 安裝PyInstaller失敗
        pause
        exit /b 1
    )
)

echo PyInstaller已準備就緒

:: 安裝依賴套件
echo 檢查依賴套件...
pip install -r requirements.txt >nul 2>&1

:: 創建打包目錄
if not exist "dist" mkdir "dist"
if not exist "portable" mkdir "portable"

echo.
echo 開始打包程式...

:: 使用PyInstaller打包
echo 正在打包主程式...
pyinstaller --onefile --windowed --name "手機檔案傳輸" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import "PIL._tkinter_finder" ^
    app_improved.py

if errorlevel 1 (
    echo 錯誤: 打包失敗
    pause
    exit /b 1
)

echo 主程式打包完成

:: 複製必要檔案到便攜版目錄
echo 創建便攜版資料夾...
copy "dist\手機檔案傳輸.exe" "portable\"
xcopy "templates" "portable\templates\" /E /I /Y
xcopy "static" "portable\static\" /E /I /Y
if not exist "portable\uploads" mkdir "portable\uploads"

:: 創建便攜版啟動腳本
echo 創建便攜版啟動腳本...
echo @echo off > "portable\啟動檔案傳輸.bat"
echo chcp 65001 ^>nul >> "portable\啟動檔案傳輸.bat"
echo title 手機檔案傳輸系統 >> "portable\啟動檔案傳輸.bat"
echo. >> "portable\啟動檔案傳輸.bat"
echo echo ======================================================== >> "portable\啟動檔案傳輸.bat"
echo echo 手機檔案傳輸系統 - 便攜版 >> "portable\啟動檔案傳輸.bat"
echo echo ======================================================== >> "portable\啟動檔案傳輸.bat"
echo echo. >> "portable\啟動檔案傳輸.bat"
echo echo 正在啟動檔案傳輸伺服器... >> "portable\啟動檔案傳輸.bat"
echo echo QR Code視窗即將開啟 >> "portable\啟動檔案傳輸.bat"
echo echo 支援多IP自動切換功能 >> "portable\啟動檔案傳輸.bat"
echo echo 支援偏好IP記憶功能 >> "portable\啟動檔案傳輸.bat"
echo echo 按 Ctrl+C 可停止伺服器 >> "portable\啟動檔案傳輸.bat"
echo echo. >> "portable\啟動檔案傳輸.bat"
echo "手機檔案傳輸.exe" >> "portable\啟動檔案傳輸.bat"
echo pause >> "portable\啟動檔案傳輸.bat"

:: 創建說明檔案
echo 創建使用說明...
echo 手機檔案傳輸系統 - 便攜版 > "portable\使用說明.txt"
echo ================================== >> "portable\使用說明.txt"
echo. >> "portable\使用說明.txt"
echo 使用方式: >> "portable\使用說明.txt"
echo 1. 雙擊啟動檔案傳輸.bat >> "portable\使用說明.txt"
echo 2. QR Code視窗會自動開啟 >> "portable\使用說明.txt"
echo 3. 用手機掃描QR Code >> "portable\使用說明.txt"
echo 4. 選擇檔案上傳 >> "portable\使用說明.txt"
echo. >> "portable\使用說明.txt"
echo 多IP切換功能: >> "portable\使用說明.txt"
echo - 如果第一個IP無法連接 >> "portable\使用說明.txt"
echo - 點擊下一個IP按鈕嘗試其他IP >> "portable\使用說明.txt"
echo - 找到可用IP後可點擊設為預設IP >> "portable\使用說明.txt"
echo. >> "portable\使用說明.txt"
echo 上傳的檔案會儲存在uploads資料夾 >> "portable\使用說明.txt"
echo. >> "portable\使用說明.txt"
echo 系統需求: >> "portable\使用說明.txt"
echo - Windows 7/8/10/11 >> "portable\使用說明.txt"
echo - 手機和電腦連接同一WiFi >> "portable\使用說明.txt"
echo. >> "portable\使用說明.txt"
echo 版本資訊: >> "portable\使用說明.txt"
echo 版本: 偏好IP版 v1.0 >> "portable\使用說明.txt"
echo 更新日期: %date% >> "portable\使用說明.txt"

:: 創建壓縮包
echo 創建發布壓縮包...
if exist "手機檔案傳輸_便攜版.zip" del "手機檔案傳輸_便攜版.zip"

:: 使用PowerShell創建壓縮包
powershell -Command "Compress-Archive -Path 'portable\*' -DestinationPath '手機檔案傳輸_便攜版.zip'"

if exist "手機檔案傳輸_便攜版.zip" (
    echo 壓縮包創建成功: 手機檔案傳輸_便攜版.zip
) else (
    echo 警告: 壓縮包創建失敗，但便攜版資料夾已準備就緒
)

echo.
echo 打包完成！
echo.
echo 打包結果:
echo    便攜版資料夾: portable\
echo    主程式: portable\手機檔案傳輸.exe
echo    啟動腳本: portable\啟動檔案傳輸.bat
echo    使用說明: portable\使用說明.txt
if exist "手機檔案傳輸_便攜版.zip" (
    echo    發布包: 手機檔案傳輸_便攜版.zip
)
echo.
echo 部署方式:
echo    1. 將整個 portable 資料夾複製到目標電腦
echo    2. 或分享 手機檔案傳輸_便攜版.zip 檔案
echo    3. 在目標電腦解壓後執行啟動檔案傳輸.bat
echo.

choice /c YN /m "是否測試便攜版程式? (Y/N)"
if errorlevel 2 goto :end
if errorlevel 1 (
    echo 啟動測試...
    cd portable
    call "啟動檔案傳輸.bat"
    cd ..
)

:end
echo.
echo 打包完成！您現在可以將程式分享給其他電腦使用了。
pause 