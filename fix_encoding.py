#!/usr/bin/env python3
"""
BOM (Byte Order Mark) алдаа засах скрипт
Windows дээр encoding асуудлыг шийдэх
"""
import os
import codecs
from pathlib import Path

def remove_bom_from_file(file_path):
    """Файлаас BOM устгах"""
    try:
        # UTF-8-BOM-тайгаар унших
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # UTF-8 (BOM-гүй) байдлаар дахин бичих
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Алдаа {file_path}: {e}")
        return False

def fix_all_python_files(project_root="."):
    """Бүх Python файлын BOM-г засах"""
    print("🔧 Python файлуудын BOM-г засаж байна...")
    
    python_files = list(Path(project_root).rglob("*.py"))
    fixed_count = 0
    error_count = 0
    
    for file_path in python_files:
        # Backup хавтсанд байгаа файлуудыг алгасах
        if "backup" in str(file_path).lower() or "__pycache__" in str(file_path):
            continue
            
        # BOM байгаа эсэхийг шалгах
        try:
            with open(file_path, 'rb') as f:
                first_bytes = f.read(3)
                if first_bytes == b'\xef\xbb\xbf':  # UTF-8 BOM
                    if remove_bom_from_file(file_path):
                        print(f"✅ Засав: {file_path}")
                        fixed_count += 1
                    else:
                        error_count += 1
        except Exception as e:
            print(f"⚠️ Шалгах алдаа {file_path}: {e}")
            error_count += 1
    
    print(f"\n📊 Дүн:")
    print(f"   ✅ Засагдсан файлууд: {fixed_count}")
    print(f"   ⚠️ Алдаатай файлууд: {error_count}")
    print(f"   📁 Нийт шалгасан: {len(python_files)}")

def create_safe_cleanup_script():
    """Аюулгүй цэвэрлэх Windows batch скрипт үүсгэх"""
    
    # ASCII-ээр batch скрипт үүсгэх
    batch_content = """@echo off
chcp 65001
echo Creating backup...
xcopy /e /i /y . ..\\tv_streaming_backup_%date:~-4%_%date:~3,2%_%date:~0,2%

echo Removing migration backups...
if exist "backups\\migration_1751423526" rmdir /s /q "backups\\migration_1751423526"
if exist "backups\\migration_1751423840" rmdir /s /q "backups\\migration_1751423840"
if exist "backups\\migration_1751423958" rmdir /s /q "backups\\migration_1751423958"
if exist "backups\\migration_1751424107" rmdir /s /q "backups\\migration_1751424107"
if exist "backups\\migration_1751424467" rmdir /s /q "backups\\migration_1751424467"
if exist "backups\\migration_1751425256" rmdir /s /q "backups\\migration_1751425256"
if exist "backups\\migration_1751425702" rmdir /s /q "backups\\migration_1751425702"

echo Removing backup files...
if exist "main.py.backup" del "main.py.backup"
if exist "main.py.corrupted" del "main.py.corrupted"
if exist "ui\\main_window.py.backup" del "ui\\main_window.py.backup"
if exist "ui\\tabs\\playout_tab.py.backup" del "ui\\tabs\\playout_tab.py.backup"
if exist "ui\\tabs\\streaming_tab_backup_20250702.py" del "ui\\tabs\\streaming_tab_backup_20250702.py"
if exist "ui\\dialogs\\servers\\servers_backup_20250628_141621.json" del "ui\\dialogs\\servers\\servers_backup_20250628_141621.json"

echo Removing test files...
if exist "test_streaming.py" del "test_streaming.py"
if exist "test_ubuntu_connection.py" del "test_ubuntu_connection.py"
if exist "integration_usage_example.py" del "integration_usage_example.py"
if exist "examples\\integration_example.py" del "examples\\integration_example.py"
if exist "ui\\tabs\\integration_example.py" del "ui\\tabs\\integration_example.py"

echo Cleaning __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Done! Testing the application...
python main.py structure
pause
"""
    
    # ASCII байдлаар бичих
    with open('cleanup_safe.bat', 'w', encoding='ascii', errors='ignore') as f:
        f.write(batch_content)
    
    print("✅ Цэвэрлэх скрипт үүсгэлээ: cleanup_safe.bat")
    print("   Ажиллуулах: cleanup_safe.bat")

def analyze_streaming_files():
    """Streaming файлуудын ашиглалтыг шалгах"""
    print("\n🔍 Streaming файлуудын шалгалт:")
    
    streaming_files = [
        "streaming/final_refactored_streaming_tab.py",
        "streaming/refactored_streaming_tab.py", 
        "ui/tabs/streaming_tab.py"
    ]
    
    for file_path in streaming_files:
        if os.path.exists(file_path):
            print(f"\n📄 {file_path}:")
            
            # Файлын хэмжээ
            size = os.path.getsize(file_path)
            print(f"   📏 Хэмжээ: {size} bytes")
            
            # Import-уудыг олох
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Import мөрүүдийг олох
                import_lines = [line.strip() for line in content.split('\n') 
                               if line.strip().startswith(('import ', 'from '))]
                print(f"   📦 Import тоо: {len(import_lines)}")
                
                # Класс тодорхойлолтыг олох
                class_count = content.count('class ')
                print(f"   🏗️ Класс тоо: {class_count}")
                
                # Функц тодорхойлолтыг олох  
                def_count = content.count('def ')
                print(f"   ⚙️ Функц тоо: {def_count}")
                
            except Exception as e:
                print(f"   ⚠️ Уншихад алдаа: {e}")
        else:
            print(f"❌ Олдсонгүй: {file_path}")

def main():
    print("🛠️ BOM алдаа засах болон цэвэрлэх скрипт")
    print("=" * 50)
    
    # 1. BOM алдаануудыг засах
    fix_all_python_files()
    
    # 2. Streaming файлуудыг шалгах
    analyze_streaming_files()
    
    # 3. Аюулгүй цэвэрлэх скрипт үүсгэх
    create_safe_cleanup_script()
    
    print(f"\n🎉 Бэлтгэл ажил дуусав!")
    print(f"Дараагийн алхам:")
    print(f"1. cleanup_safe.bat ажиллуулах")
    print(f"2. python main.py тест хийх")
    print(f"3. Import алдаануудыг засах")

if __name__ == "__main__":
    main()