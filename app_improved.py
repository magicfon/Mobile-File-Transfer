#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行動裝置檔案傳輸伺服器 (改進版)
支援Android和iPhone透過WiFi上傳圖片和影片到Windows PC
新增多IP選擇功能，適用於多WiFi分享器環境
支援QR Code切換功能
"""

import os
import socket
import threading
import webbrowser
import subprocess
import re
import json
from datetime import datetime
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import mimetypes
import qrcode
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 設定上傳資料夾
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB限制

# 設定檔案路徑
CONFIG_FILE = 'ip_preferences.json'

def allowed_file(filename):
    """檢查檔案類型是否被允許（現在允許所有檔案類型）"""
    return filename and filename.strip() != ''

def save_preferred_ip(ip):
    """儲存偏好的IP到設定檔"""
    try:
        config = {
            'preferred_ip': ip,
            'last_updated': datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"儲存偏好IP失敗: {e}")
        return False

def load_preferred_ip():
    """從設定檔載入偏好的IP"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('preferred_ip')
    except Exception as e:
        print(f"載入偏好IP失敗: {e}")
    return None

def reorder_ips_by_preference(available_ips):
    """根據偏好重新排序IP列表"""
    preferred_ip = load_preferred_ip()
    if preferred_ip and preferred_ip in available_ips:
        # 將偏好IP移到第一位
        reordered = [preferred_ip] + [ip for ip in available_ips if ip != preferred_ip]
        return reordered, preferred_ip
    return available_ips, None

def get_all_local_ips():
    """獲取所有可用的本機IP位址"""
    ips = []
    
    try:
        # 方法1: 使用socket獲取所有網路介面
        hostname = socket.gethostname()
        
        # 獲取所有IP位址
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if is_valid_ip(ip):
                ips.append(ip)
        
        # 方法2: 嘗試連接外部服務器獲取預設路由IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            default_ip = s.getsockname()[0]
            s.close()
            if is_valid_ip(default_ip) and default_ip not in ips:
                ips.append(default_ip)
        except:
            pass
        
        # 方法3: 使用ipconfig命令 (Windows)
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            ip_pattern = r'IPv4.*?(\d+\.\d+\.\d+\.\d+)'
            found_ips = re.findall(ip_pattern, result.stdout)
            for ip in found_ips:
                if is_valid_ip(ip) and ip not in ips:
                    ips.append(ip)
        except:
            pass
            
    except Exception as e:
        print(f"獲取IP位址時發生錯誤: {e}")
    
    # 移除重複並排序
    ips = list(set(ips))
    ips.sort()
    
    return ips if ips else ["127.0.0.1"]

def is_valid_ip(ip):
    """檢查IP位址是否有效（排除無效的IP）"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        # 排除無效的IP範圍
        if (ip.startswith('127.') or          # 本地回環
            ip.startswith('169.254.') or      # APIPA
            ip.startswith('0.') or            # 無效
            ip == '0.0.0.0' or               # 無效
            ip.startswith('224.') or          # 多播
            ip.startswith('255.')):           # 廣播
            return False
            
        # 檢查每個部分是否在有效範圍內
        for part in parts:
            if not (0 <= int(part) <= 255):
                return False
                
        return True
    except:
        return False

def generate_qr_code(url):
    """生成QR code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    return qr_image

def show_switchable_qr_window(available_ips, port):
    """顯示可切換的QR code視窗"""
    if not available_ips:
        messagebox.showerror("錯誤", "未找到可用的IP位址")
        return
    
    # 檢查偏好IP
    preferred_ip = load_preferred_ip()
    
    try:
        root = tk.Tk()
        root.title("📱 手機檔案傳輸 - IP切換")
        root.geometry("520x720")
        root.resizable(False, False)
        root.eval('tk::PlaceWindow . center')
        
        # 當前IP索引
        current_ip_index = tk.IntVar(value=0)
        
        # 主框架
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 標題
        title_label = tk.Label(main_frame, text="📱 手機檔案傳輸", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 可用IP數量顯示 - 增加背景和邊框使其更明顯
        ip_count_frame = tk.Frame(main_frame, bg="#E3F2FD", relief="ridge", bd=1)
        ip_count_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        ip_count_label = tk.Label(ip_count_frame, 
                                 text=f"🔍 偵測到 {len(available_ips)} 個可用IP位址", 
                                 font=("Arial", 12, "bold"), fg="#1976D2", bg="#E3F2FD")
        ip_count_label.pack(pady=8)
        
        # IP切換資訊框架
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # IP計數器
        ip_counter_label = tk.Label(info_frame, text="", font=("Arial", 12, "bold"), fg="blue")
        ip_counter_label.pack()
        
        # 當前IP顯示
        current_ip_label = tk.Label(info_frame, text="", font=("Arial", 14, "bold"), fg="darkgreen")
        current_ip_label.pack(pady=(5, 0))
        
        # QR Code框架
        qr_frame = tk.Frame(main_frame)
        qr_frame.pack(pady=10)
        
        qr_label = tk.Label(qr_frame)
        qr_label.pack()
        
        # URL顯示
        url_label = tk.Label(main_frame, text="", font=("Arial", 10), fg="blue", wraplength=450)
        url_label.pack(pady=(10, 5))
        
        # 說明文字
        instruction_label = tk.Label(main_frame, 
                                   text="📱 用手機掃描QR Code\n如果無法連接，請點擊「下一個IP」嘗試其他選項", 
                                   font=("Arial", 11), justify=tk.CENTER, fg="gray")
        instruction_label.pack(pady=(5, 15))
        
        # 按鈕框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # 網路分析框架
        analysis_frame = tk.LabelFrame(main_frame, text="🔍 IP分析", font=("Arial", 10))
        analysis_frame.pack(fill=tk.X, pady=(10, 0))
        
        analysis_text = tk.Text(analysis_frame, height=4, font=("Arial", 9), wrap=tk.WORD)
        analysis_text.pack(fill=tk.X, padx=5, pady=5)
        
        def get_ip_analysis(ip):
            """獲取IP分析資訊"""
            if ip.startswith('192.168.1.'):
                return "常見家用網路 - 大多數路由器的預設網段"
            elif ip.startswith('192.168.0.'):
                return "常見家用網路 - 部分路由器的預設網段"
            elif ip.startswith('192.168.56.'):
                return "VirtualBox虛擬網路 - 通常無法與手機連接"
            elif ip.startswith('192.168.'):
                return "私人網路 - WiFi延伸器或特殊設定"
            elif ip.startswith('172.'):
                return "企業網路 - 公司或組織網路環境"
            elif ip.startswith('10.'):
                return "大型網路 - 企業或學校網路"
            else:
                return "其他網路類型"
        
        def update_qr_display():
            """更新QR Code顯示"""
            current_index = current_ip_index.get()
            ip = available_ips[current_index]
            url = f"http://{ip}:{port}"
            
            # 更新計數器
            ip_counter_label.config(text=f"IP選項: {current_index + 1} / {len(available_ips)}")
            
            # 更新當前IP，顯示是否為偏好IP
            ip_display = f"{ip}"
            if ip == preferred_ip:
                ip_display += " ⭐"
            current_ip_label.config(text=ip_display)
            
            # 生成並顯示QR code
            qr_image = generate_qr_code(url)
            qr_image = qr_image.resize((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(qr_image)
            qr_label.config(image=photo)
            qr_label.image = photo  # 保持引用
            
            # 更新URL
            url_label.config(text=f"網址: {url}")
            
            # 更新分析資訊
            analysis_text.delete(1.0, tk.END)
            analysis_info = f"當前IP: {ip}\n類型: {get_ip_analysis(ip)}\n"
            if len(available_ips) > 1:
                analysis_info += f"如果此IP無法連接，請嘗試其他 {len(available_ips)-1} 個選項"
            else:
                analysis_info += "這是唯一偵測到的IP位址"
            analysis_text.insert(1.0, analysis_info)
            analysis_text.config(state=tk.DISABLED)
        
        def next_ip():
            """切換到下一個IP"""
            current_index = current_ip_index.get()
            next_index = (current_index + 1) % len(available_ips)
            current_ip_index.set(next_index)
            update_qr_display()
        
        def prev_ip():
            """切換到上一個IP"""
            current_index = current_ip_index.get()
            prev_index = (current_index - 1) % len(available_ips)
            current_ip_index.set(prev_index)
            update_qr_display()
        
        def copy_current_url():
            """複製當前URL"""
            current_index = current_ip_index.get()
            ip = available_ips[current_index]
            url = f"http://{ip}:{port}"
            root.clipboard_clear()
            root.clipboard_append(url)
            messagebox.showinfo("已複製", f"網址已複製到剪貼簿\n{url}")
        
        def open_current_browser():
            """在瀏覽器開啟當前URL"""
            current_index = current_ip_index.get()
            ip = available_ips[current_index]
            url = f"http://{ip}:{port}"
            webbrowser.open(url)
        
        def set_as_preferred():
            """將當前IP設為偏好IP"""
            current_index = current_ip_index.get()
            ip = available_ips[current_index]
            if save_preferred_ip(ip):
                messagebox.showinfo("設定成功", 
                                   f"已將 {ip} 設為預設IP\n下次啟動時會優先使用此IP")
            else:
                messagebox.showerror("設定失敗", "無法儲存偏好設定")
        
        # 建立按鈕 - 增加按鈕高度
        if len(available_ips) > 1:
            prev_btn = tk.Button(button_frame, text="⬅️ 上一個IP", command=prev_ip,
                               bg="#FF9800", fg="white", font=("Arial", 11), padx=15, pady=12)
            prev_btn.pack(side=tk.LEFT, padx=5)
            
            next_btn = tk.Button(button_frame, text="下一個IP ➡️", command=next_ip,
                               bg="#4CAF50", fg="white", font=("Arial", 11), padx=15, pady=12)
            next_btn.pack(side=tk.LEFT, padx=5)
        
        copy_btn = tk.Button(button_frame, text="📋 複製網址", command=copy_current_url,
                           bg="#2196F3", fg="white", font=("Arial", 10), padx=10, pady=12)
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        browser_btn = tk.Button(button_frame, text="🌐 瀏覽器", command=open_current_browser,
                              bg="#9C27B0", fg="white", font=("Arial", 10), padx=10, pady=12)
        browser_btn.pack(side=tk.LEFT, padx=5)
        
        # 新增按鈕框架，用於放置第二行按鈕
        button_frame2 = tk.Frame(main_frame)
        button_frame2.pack(pady=(5, 0))
        
        prefer_btn = tk.Button(button_frame2, text="⭐ 設為預設IP", command=set_as_preferred,
                             bg="#FF5722", fg="white", font=("Arial", 10, "bold"), padx=12, pady=12)
        prefer_btn.pack()
        
        # 狀態資訊
        status_label = tk.Label(main_frame, text="🟢 伺服器運行中", 
                              font=("Arial", 10), fg="green")
        status_label.pack(pady=(15, 0))
        
        # 鍵盤快捷鍵
        def on_key_press(event):
            if event.keysym == 'Right' or event.keysym == 'space':
                if len(available_ips) > 1:
                    next_ip()
            elif event.keysym == 'Left':
                if len(available_ips) > 1:
                    prev_ip()
            elif event.keysym == 'c' and event.state & 0x4:  # Ctrl+C
                copy_current_url()
        
        root.bind('<KeyPress>', on_key_press)
        root.focus_set()
        
        # 在底部添加快捷鍵說明
        if len(available_ips) > 1:
            shortcut_label = tk.Label(main_frame, 
                                    text="⌨️ 快捷鍵: ← → 或空白鍵切換IP，Ctrl+C 複製網址", 
                                    font=("Arial", 8), fg="gray")
            shortcut_label.pack(pady=(5, 0))
        
        # 初始化顯示
        update_qr_display()
        
        # 如果只有一個IP，顯示提示
        if len(available_ips) == 1:
            single_ip_info = tk.Label(main_frame, 
                                    text="💡 只偵測到一個IP位址，如果無法連接請檢查網路設定", 
                                    font=("Arial", 9), fg="orange", wraplength=450)
            single_ip_info.pack(pady=(10, 0))
        
        root.mainloop()
        
    except Exception as e:
        print(f"無法顯示QR code視窗: {e}")

def start_qr_window(available_ips, port):
    """啟動QR code視窗"""
    qr_thread = threading.Thread(target=show_switchable_qr_window, args=(available_ips, port))
    qr_thread.daemon = True
    qr_thread.start()

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """處理檔案上傳"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': '沒有選擇檔案'})
    
    files = request.files.getlist('files')
    uploaded_files = []
    errors = []
    
    for file in files:
        if file.filename == '':
            errors.append('檔案名稱為空')
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(filepath)
                uploaded_files.append(filename)
            except Exception as e:
                errors.append(f'儲存檔案 {file.filename} 時發生錯誤: {str(e)}')
        else:
            errors.append(f'檔案名稱無效: {file.filename}')
    
    if uploaded_files:
        message = f'成功上傳 {len(uploaded_files)} 個檔案'
        if errors:
            message += f'，但有 {len(errors)} 個檔案上傳失敗'
        return jsonify({'success': True, 'message': message, 'files': uploaded_files})
    else:
        return jsonify({'success': False, 'message': '沒有檔案上傳成功', 'errors': errors})

@app.route('/status')
def status():
    """系統狀態"""
    upload_count = len([f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))])
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(UPLOAD_FOLDER):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    
    size_mb = round(total_size / (1024 * 1024), 2)
    
    return jsonify({
        'upload_folder': UPLOAD_FOLDER,
        'total_files': upload_count,
        'total_size_mb': size_mb,
        'available_ips': get_all_local_ips()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("📱 行動裝置檔案傳輸伺服器 (IP切換版)")
    print("=" * 60)
    
    # 獲取所有可用IP
    original_ips = get_all_local_ips()
    available_ips, preferred_ip = reorder_ips_by_preference(original_ips)
    
    print(f"🔍 偵測到 {len(available_ips)} 個網路介面:")
    for i, ip in enumerate(available_ips, 1):
        prefix = "⭐ " if ip == preferred_ip else "   "
        print(f"{prefix}{i}. {ip}")
    
    print(f"📁 檔案將儲存到: {os.path.abspath(UPLOAD_FOLDER)}")
    print("✅ 檔案類型: 支援所有類型的檔案上傳")
    
    port = 5000
    
    if len(available_ips) == 1:
        print(f"\n🌐 伺服器將啟動在: http://{available_ips[0]}:{port}")
        print("📱 將顯示QR Code視窗...")
    else:
        print(f"\n🌐 伺服器將啟動在埠號: {port}")
        print("📱 將顯示可切換IP的QR Code視窗...")
        print("🔄 可使用「下一個IP」按鈕或快捷鍵切換不同網路")
    
    print("\n💡 使用提示:")
    if preferred_ip:
        print(f"   - ⭐ 將優先使用偏好IP: {preferred_ip}")
    print("   - 先嘗試第一個IP")
    print("   - 如果手機無法連接，點擊「下一個IP」")
    print("   - 連接成功後，可點擊「⭐ 設為預設IP」儲存偏好")
    print("   - 可使用 ← → 鍵或空白鍵快速切換")
    print("   - Ctrl+C 可快速複製當前網址")
    
    print("\n按 Ctrl+C 停止伺服器")
    print("=" * 60)
    
    # 啟動QR code視窗
    start_qr_window(available_ips, port)
    
    import time
    time.sleep(1)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 伺服器已停止")
    except Exception as e:
        print(f"\n❌ 伺服器錯誤: {e}") 