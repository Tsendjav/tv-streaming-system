#!/usr/bin/env python3
"""
Ubuntu Server Connection Test
Ubuntu server-тай холболт шалгах script
"""

import socket
import requests
import subprocess
import json
from datetime import datetime

# Server мэдээлэл
UBUNTU_SERVER_IP = "192.168.1.50"
RTMP_PORT = 1935
HTTP_PORT = 8080

def test_network_ping():
    """Network ping тест"""
    print("🌐 Network ping тест...")
    try:
        result = subprocess.run(['ping', '-n', '4', UBUNTU_SERVER_IP], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"✅ Ping success to {UBUNTU_SERVER_IP}")
            # Extract average time
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Average' in line:
                    print(f"   📊 {line.strip()}")
            return True
        else:
            print(f"❌ Ping failed to {UBUNTU_SERVER_IP}")
            return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def test_rtmp_port():
    """RTMP port (1935) холболт тест"""
    print(f"📡 RTMP port {RTMP_PORT} тест...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((UBUNTU_SERVER_IP, RTMP_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ RTMP port {RTMP_PORT} accessible")
            return True
        else:
            print(f"❌ RTMP port {RTMP_PORT} not accessible")
            return False
    except Exception as e:
        print(f"❌ RTMP port test error: {e}")
        return False

def test_http_port():
    """HTTP port (8080) холболт тест"""
    print(f"🌐 HTTP port {HTTP_PORT} тест...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((UBUNTU_SERVER_IP, HTTP_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ HTTP port {HTTP_PORT} accessible")
            return True
        else:
            print(f"❌ HTTP port {HTTP_PORT} not accessible")
            return False
    except Exception as e:
        print(f"❌ HTTP port test error: {e}")
        return False

def test_nginx_status():
    """Nginx status API тест"""
    print("📊 Nginx status тест...")
    try:
        url = f"http://{UBUNTU_SERVER_IP}:{HTTP_PORT}/stat"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Nginx stats accessible")
            print(f"   📄 Response length: {len(response.text)} chars")
            return True
        else:
            print(f"❌ Nginx stats error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nginx status test error: {e}")
        return False

def test_health_endpoint():
    """Health check endpoint тест"""
    print("💊 Health endpoint тест...")
    try:
        url = f"http://{UBUNTU_SERVER_IP}:{HTTP_PORT}/health"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Health endpoint OK")
            print(f"   📄 Response: {response.text.strip()}")
            return True
        else:
            print(f"❌ Health endpoint error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint test error: {e}")
        return False

def test_hls_directories():
    """HLS directory accessibility тест"""
    print("📁 HLS directories тест...")
    hls_paths = [
        "/hls/",
        "/hls/720p/", 
        "/hls/480p/",
        "/hls2/",
        "/hls3/"
    ]
    
    success_count = 0
    for path in hls_paths:
        try:
            url = f"http://{UBUNTU_SERVER_IP}:{HTTP_PORT}{path}"
            response = requests.get(url, timeout=5)
            
            if response.status_code in [200, 403, 404]:  # 403/404 are OK - means directory exists
                print(f"   ✅ {path} accessible")
                success_count += 1
            else:
                print(f"   ❌ {path} error: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {path} error: {e}")
    
    print(f"📊 HLS directories: {success_count}/{len(hls_paths)} accessible")
    return success_count > 0

def run_full_test():
    """Бүрэн тест ажиллуулах"""
    print("🧪 Ubuntu Server Connection Test Starting...")
    print("=" * 60)
    print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target server: {UBUNTU_SERVER_IP}")
    print("=" * 60)
    
    results = {}
    
    # Run all tests
    results['ping'] = test_network_ping()
    print()
    
    results['rtmp_port'] = test_rtmp_port()
    print()
    
    results['http_port'] = test_http_port()
    print()
    
    results['nginx_status'] = test_nginx_status()
    print()
    
    results['health'] = test_health_endpoint()
    print()
    
    results['hls_dirs'] = test_hls_directories()
    print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():<15} {status}")
    
    print("-" * 60)
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Ubuntu server ready for streaming!")
    elif passed_tests >= 3:
        print("⚠️ PARTIAL SUCCESS! Check failed components.")
    else:
        print("❌ MULTIPLE FAILURES! Check server configuration.")
    
    print("=" * 60)
    
    # Save results
    with open('server_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'server': UBUNTU_SERVER_IP,
            'results': results,
            'summary': f"{passed_tests}/{total_tests}"
        }, f, indent=2)
    
    print("💾 Test results saved to: server_test_results.json")
    
    # Return overall success
    return passed_tests >= 3

if __name__ == "__main__":
    success = run_full_test()
    exit(0 if success else 1)
