#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP檢測測試腳本
測試多IP檢測功能，不啟動伺服器
"""

import socket
import subprocess
import re

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

def get_all_local_ips():
    """獲取所有可用的本機IP位址"""
    ips = []
    methods_used = []
    
    print("🔍 開始檢測網路介面...")
    
    # 方法1: 使用socket獲取所有網路介面
    try:
        print("   📡 使用socket檢測...")
        hostname = socket.gethostname()
        
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if is_valid_ip(ip):
                ips.append(ip)
        
        methods_used.append("socket")
        print(f"      找到 {len([ip for ip in ips])} 個IP")
    except Exception as e:
        print(f"      ❌ socket方法失敗: {e}")
    
    # 方法2: 嘗試連接外部服務器獲取預設路由IP
    try:
        print("   🌐 檢測預設路由IP...")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        default_ip = s.getsockname()[0]
        s.close()
        if is_valid_ip(default_ip) and default_ip not in ips:
            ips.append(default_ip)
            print(f"      找到預設路由IP: {default_ip}")
        methods_used.append("default_route")
    except Exception as e:
        print(f"      ❌ 預設路由檢測失敗: {e}")
    
    # 方法3: 使用ipconfig命令 (Windows)
    try:
        print("   💻 使用ipconfig命令...")
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        ip_pattern = r'IPv4.*?(\d+\.\d+\.\d+\.\d+)'
        found_ips = re.findall(ip_pattern, result.stdout)
        initial_count = len(ips)
        for ip in found_ips:
            if is_valid_ip(ip) and ip not in ips:
                ips.append(ip)
        methods_used.append("ipconfig")
        new_count = len(ips) - initial_count
        print(f"      從ipconfig找到 {new_count} 個新IP")
    except Exception as e:
        print(f"      ❌ ipconfig命令失敗: {e}")
    
    # 移除重複並排序
    ips = list(set(ips))
    ips.sort()
    
    return ips, methods_used

def analyze_network_environment(ips):
    """分析網路環境"""
    print("\n🔬 網路環境分析:")
    
    if len(ips) == 0:
        print("   ❌ 未偵測到任何有效IP")
        return
    
    if len(ips) == 1:
        print("   ✅ 簡單網路環境（單一IP）")
        print(f"   📍 建議使用: {ips[0]}")
        return
    
    print(f"   🌐 複雜網路環境（{len(ips)} 個IP）")
    
    # 分析IP範圍
    networks = {}
    for ip in ips:
        network = '.'.join(ip.split('.')[:3])
        if network not in networks:
            networks[network] = []
        networks[network].append(ip)
    
    print(f"   📊 偵測到 {len(networks)} 個不同網段:")
    
    for network, network_ips in networks.items():
        print(f"      🏠 {network}.x 網段: {len(network_ips)} 個IP")
        for ip in network_ips:
            # 判斷IP類型
            if ip.startswith('192.168.1.'):
                ip_type = "（常見家用網路）"
            elif ip.startswith('192.168.0.'):
                ip_type = "（常見家用網路）"
            elif ip.startswith('192.168.56.'):
                ip_type = "（VirtualBox虛擬網路）"
            elif ip.startswith('192.168.'):
                ip_type = "（私人網路）"
            elif ip.startswith('172.'):
                ip_type = "（企業網路）"
            elif ip.startswith('10.'):
                ip_type = "（大型網路）"
            else:
                ip_type = "（其他）"
            
            print(f"         - {ip} {ip_type}")

def main():
    print("=" * 60)
    print("🧪 IP檢測測試工具")
    print("=" * 60)
    
    # 檢測所有IP
    ips, methods = get_all_local_ips()
    
    print(f"\n✅ 檢測完成！使用方法: {', '.join(methods)}")
    print(f"📊 總共找到 {len(ips)} 個有效IP位址:")
    
    if ips:
        for i, ip in enumerate(ips, 1):
            print(f"   {i}. {ip}")
    else:
        print("   ❌ 未找到任何有效IP")
    
    # 分析網路環境
    analyze_network_environment(ips)
    
    # 提供建議
    print("\n💡 使用建議:")
    if len(ips) == 1:
        print("   - 您的網路環境很簡單，直接使用原版程式即可")
    elif len(ips) > 1:
        print("   - 您的網路環境較複雜，建議使用改進版程式")
        print("   - 選擇與手機相同網段的IP")
        print("   - 如果不確定，可以使用 'a' 選項顯示所有QR Code")
    
    print("\n🔧 如果需要手動檢查網路設定:")
    print("   Windows: ipconfig")
    print("   手機: 設定 → WiFi → 查看IP位址")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 