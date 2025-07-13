@echo off
chcp 65001 >nul
title 行動裝置檔案傳輸伺服器（原版）

echo.
echo ====================================================
echo 🚀 行動裝置檔案傳輸伺服器啟動程式（原版）
echo ====================================================
echo.

echo ✅ 檢查Python環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: 找不到Python，請先安裝Python 3.7或更高版本
    echo 📥 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ 檢查依賴套件...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安裝依賴套件...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 安裝依賴套件失敗，請檢查網路連接
        pause
        exit /b 1
    )
)

echo ✅ 檢查QR Code套件...
pip show qrcode >nul 2>&1
if errorlevel 1 (
    echo 📦 正在安裝QR Code套件...
    pip install qrcode[pil] Pillow
    if errorlevel 1 (
        echo ❌ 安裝QR Code套件失敗，請檢查網路連接
        pause
        exit /b 1
    )
)

echo.
echo 🌟 啟動伺服器（原版）...
echo 📲 QR Code視窗即將自動開啟
echo 📱 用手機掃描QR Code即可快速連接（支援任何檔案類型）
echo 💡 或者手動在瀏覽器輸入顯示的IP位址
echo ⏹️  按 Ctrl+C 可停止伺服器
echo.

python app.py

echo.
echo 👋 伺服器已停止
pause 