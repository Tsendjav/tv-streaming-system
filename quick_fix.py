#!/usr/bin/env python3
"""
Хурдан засварлах скрипт
Гол асуудлуудыг шийдэх
"""
import os
import shutil
from pathlib import Path

def fix_server_config_import():
    """server_config import алдааг засах"""
    print("🔧 server_config import алдаа засаж байна...")
    
    file_path = "streaming/refactored_streaming_tab.py"
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} файл олдсонгүй")
        return False
    
    try:
        # Файлыг унших
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Буруу import-г засах
        old_import = "from server_config import ServerConfig"
        new_import = "from models.server_config import ServerConfig"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            # Файлд буцаан бичих
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {file_path} файлын import засагдлаа")
            return True
        else:
            print(f"ℹ️ {file_path} файлд засах import олдсонгүй")
            return True
            
    except Exception as e:
        print(f"❌ Алдаа: {e}")
        return False

def find_missing_playout_tab():
    """playout_tab.py файлыг олох"""
    print("🔍 playout_tab.py файлыг хайж байна...")
    
    target_path = "ui/tabs/playout_tab.py"
    
    if os.path.exists(target_path):
        print(f"✅ {target_path} файл байна")
        return True
    
    # Backup хавтсуудаас хайх
    search_paths = [
        "backups/migration_*/playout_tab.py",
        "ui/tabs/playout_tab.py.backup",
        "playout_tab.py",
        "*/playout_tab.py"
    ]
    
    found_files = []
    for pattern in search_paths:
        found_files.extend(Path(".").glob(pattern))
    
    if found_files:
        print(f"📄 Олдсон файлууд:")
        for i, file_path in enumerate(found_files, 1):
            print(f"   {i}. {file_path}")
        
        # Хамгийн шинэ файлыг хуулах
        latest_file = max(found_files, key=lambda f: f.stat().st_mtime)
        
        try:
            # Хавтас үүсгэх
            os.makedirs("ui/tabs", exist_ok=True)
            
            # Файл хуулах
            shutil.copy2(latest_file, target_path)
            print(f"✅ {latest_file} → {target_path} хуулагдлаа")
            return True
            
        except Exception as e:
            print(f"❌ Хуулахад алдаа: {e}")
            return False
    else:
        print("❌ playout_tab.py файл олдсонгүй")
        return False

def analyze_streaming_files():
    """Streaming файлуудыг шинжилж, аль нь хэрэгтэйг тодорхойлох"""
    print("📊 Streaming файлуудыг шинжилж байна...")
    
    files_info = {
        "ui/tabs/streaming_tab.py": "Үндсэн streaming tab",
        "streaming/final_refactored_streaming_tab.py": "Шинэчлэгдсэн хувилбар",
        "streaming/refactored_streaming_tab.py": "Дунд хувилбар (import алдаатай)"
    }
    
    for file_path, description in files_info.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"📄 {file_path}")
            print(f"   📝 {description}")
            print(f"   📏 {size:,} bytes")
            
            # main.py-д ашиглагдаж байгаа эсэхийг шалгах
            if os.path.exists("main.py"):
                with open("main.py", 'r', encoding='utf-8') as f:
                    main_content = f.read()
                    file_name = os.path.basename(file_path).replace('.py', '')
                    if file_name in main_content:
                        print(f"   ✅ main.py-д ашиглагдаж байна")
                    else:
                        print(f"   ❌ main.py-д ашиглагдахгүй байна")
        else:
            print(f"❌ {file_path} олдсонгүй")

def test_application():
    """Програм ажиллагааг тест хийх"""
    print("🧪 Програм тест хийж байна...")
    
    try:
        # main.py structure тест
        result = os.system("python main.py structure")
        if result == 0:
            print("✅ Structure тест амжилттай")
        else:
            print("❌ Structure тест алдаатай")
        
        # main.py тест
        print("\n🧪 Үндсэн програм тест хийж байна...")
        result = os.system("python main.py")
        if result == 0:
            print("✅ Үндсэн програм тест амжилттай")
        else:
            print("❌ Үндсэн програм тест алдаатай")
            
    except Exception as e:
        print(f"❌ Тест хийхэд алдаа: {e}")

def create_simple_cleanup():
    """Энгийн цэвэрлэх команд үүсгэх"""
    print("🧹 Энгийн цэвэрлэх командууд үүсгэж байна...")
    
    commands = [
        "# Backup хавтсуудыг устгах",
        'rmdir /s /q "backups\\migration_1751423526"',
        'rmdir /s /q "backups\\migration_1751423840"',
        'rmdir /s /q "backups\\migration_1751423958"',
        'rmdir /s /q "backups\\migration_1751424107"',
        'rmdir /s /q "backups\\migration_1751424467"',
        'rmdir /s /q "backups\\migration_1751425256"',
        'rmdir /s /q "backups\\migration_1751425702"',
        "",
        "# Backup файлуудыг устгах",
        'del "main.py.backup"',
        'del "main.py.corrupted"',
        'del "ui\\main_window.py.backup"',
        'del "ui\\tabs\\streaming_tab_backup_20250702.py"',
        "",
        "# Тест файлуудыг устгах",
        'del "test_streaming.py"',
        'del "test_ubuntu_connection.py"',
        'del "integration_usage_example.py"',
        "",
        "# Давхардсан streaming файлыг устгах",
        'del "streaming\\refactored_streaming_tab.py"',
        "",
        "echo Цэвэрлэгдлээ!"
    ]
    
    with open("simple_cleanup.bat", 'w', encoding='ascii', errors='ignore') as f:
        f.write('\n'.join(commands))
    
    print("✅ simple_cleanup.bat файл үүсгэгдлээ")

def main():
    print("🚀 Хурдан засварлах скрипт эхэллээ")
    print("=" * 50)
    
    success_count = 0
    
    # 1. server_config import засах
    if fix_server_config_import():
        success_count += 1
    
    # 2. playout_tab.py файл олох
    if find_missing_playout_tab():
        success_count += 1
    
    # 3. Streaming файлууд шинжилэх
    analyze_streaming_files()
    
    # 4. Тест хийх
    if success_count >= 1:
        test_application()
    
    # 5. Энгийн цэвэрлэх команд үүсгэх
    create_simple_cleanup()
    
    print(f"\n📈 Дүн: {success_count}/2 асуудал шийдэгдлээ")
    
    if success_count == 2:
        print("🎉 Бүх асуудал шийдэгдлээ!")
        print("Дараагийн алхам: simple_cleanup.bat ажиллуулах")
    else:
        print("⚠️ Зарим асуудал шийдэгдээгүй байна")
        print("Гараар шалгах шаардлагатай")

if __name__ == "__main__":
    main()