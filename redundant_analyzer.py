#!/usr/bin/env python3
"""
Шуурхай илүүдэл файл олох скрипт
Таны tv_streaming_system төслийн хавтсанд хадгалж ажиллуулна уу
"""
import os
import ast
import json
from pathlib import Path
from datetime import datetime

class RedundantCodeAnalyzer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.imports_map = {}
        self.file_usage = {}
        
    def analyze_imports(self):
        """Бүх Python файлуудын import-уудыг шинжилнэ"""
        print("🔍 Import-уудыг шинжилж байна...")
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # AST ашиглан import-уудыг олох
                tree = ast.parse(content)
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                self.imports_map[str(file_path)] = imports
                
            except Exception as e:
                print(f"⚠️ Алдаа {file_path}: {e}")
        
        print(f"✅ {len(python_files)} файлыг шинжилж дуусав")
    
    def find_backup_files(self):
        """Backup файлуудыг олох"""
        backup_patterns = [
            "*.backup",
            "*.corrupted", 
            "*_backup_*",
            "main.py.backup",
            "migration_*"
        ]
        
        backup_files = []
        for pattern in backup_patterns:
            backup_files.extend(self.project_root.rglob(pattern))
        
        return backup_files
    
    def find_test_files(self):
        """Тест файлуудыг олох"""
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "example*.py",
            "*example*.py"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.rglob(pattern))
        
        return test_files
    
    def find_duplicate_files(self):
        """Давхардсан файлуудыг олох"""
        duplicates = []
        
        # Streaming tab файлуудыг шалгах
        streaming_files = list(self.project_root.rglob("*streaming_tab*.py"))
        if len(streaming_files) > 1:
            duplicates.extend(streaming_files)
        
        # Main файлуудыг шалгах  
        main_files = list(self.project_root.rglob("main*.py"))
        if len(main_files) > 1:
            duplicates.extend(main_files)
            
        return duplicates
    
    def analyze_usage(self):
        """Файлуудын ашиглагдаж байгаа байдлыг шалгах"""
        print("🔍 Файлуудын ашиглалтыг шинжилж байна...")
        
        # Бүх модулуудыг жагсаах
        all_modules = set()
        for file_path in self.project_root.rglob("*.py"):
            # Файлын замыг модулын нэр болгон хувиргах
            rel_path = file_path.relative_to(self.project_root)
            module_name = str(rel_path).replace(os.sep, '.').replace('.py', '')
            all_modules.add(module_name)
        
        # Import хийгдсэн модулуудыг олох
        imported_modules = set()
        for imports in self.imports_map.values():
            imported_modules.update(imports)
        
        # Ашиглагдаагүй модулуудыг олох
        potentially_unused = []
        for module in all_modules:
            is_used = False
            for imported in imported_modules:
                if module in imported or imported in module:
                    is_used = True
                    break
            
            if not is_used:
                potentially_unused.append(module)
        
        return potentially_unused
    
    def generate_report(self):
        """Илүүдэл файлуудын тайлан үүсгэх"""
        print("\n📊 ИЛҮҮДЭЛ ФАЙЛУУДЫН ТАЙЛАН")
        print("=" * 50)
        
        # Backup файлууд
        backup_files = self.find_backup_files()
        print(f"\n🗂️ BACKUP ФАЙЛУУД ({len(backup_files)} байна):")
        for file in backup_files:
            print(f"   📄 {file}")
        
        # Тест файлууд
        test_files = self.find_test_files()
        print(f"\n🧪 ТЕСТ ФАЙЛУУД ({len(test_files)} байна):")
        for file in test_files:
            print(f"   📄 {file}")
        
        # Давхардсан файлууд
        duplicate_files = self.find_duplicate_files()
        print(f"\n🔄 ДАВХАРДСАН ФАЙЛУУД ({len(duplicate_files)} байна):")
        for file in duplicate_files:
            print(f"   📄 {file}")
        
        # Ашиглагдаагүй файлууд
        unused_modules = self.analyze_usage()
        print(f"\n❌ АШИГЛАГДААГҮЙ ФАЙЛУУД ({len(unused_modules)} байна):")
        for module in unused_modules:
            print(f"   📄 {module}")
        
        # Нийт дүгнэлт
        total_redundant = len(backup_files) + len(test_files) + len(duplicate_files)
        print(f"\n📈 НИЙТ ДҮГНЭЛТ:")
        print(f"   🗑️ Аюулгүй устгаж болох: {total_redundant} файл")
        print(f"   ⚠️ Шалгах шаардлагатай: {len(unused_modules)} файл")
        
        return {
            'backup_files': [str(f) for f in backup_files],
            'test_files': [str(f) for f in test_files],
            'duplicate_files': [str(f) for f in duplicate_files],
            'unused_modules': unused_modules,
            'total_redundant': total_redundant
        }
    
    def create_cleanup_script(self, report_data):
        """Цэвэрлэх скрипт үүсгэх"""
        script_content = f"""#!/bin/bash
# Автомат үүсгэсэн цэвэрлэх скрипт
# Огноо: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "🚀 Backup үүсгэж байна..."
cp -r . ../tv_streaming_system_backup_$(date +%Y%m%d_%H%M%S)

echo "🧹 Илүүдэл файлуудыг устгаж байна..."

"""
        
        # Backup файлуудыг устгах
        for file_path in report_data['backup_files']:
            script_content += f'rm -rf "{file_path}"\n'
        
        # Тест файлуудыг устгах
        for file_path in report_data['test_files']:
            script_content += f'rm -f "{file_path}"\n'
        
        script_content += '\necho "✅ Цэвэрлэж дуусав!"'
        
        # Скрипт файлд бичих
        with open('cleanup_redundant.sh', 'w') as f:
            f.write(script_content)
        
        os.chmod('cleanup_redundant.sh', 0o755)
        print(f"\n✅ Цэвэрлэх скрипт үүсгэлээ: cleanup_redundant.sh")
        print("   Ажиллуулах: ./cleanup_redundant.sh")

def main():
    print("🎯 TV Streaming System - Илүүдэл код шинжилгээ")
    print("=" * 60)
    
    analyzer = RedundantCodeAnalyzer()
    
    # Import-уудыг шинжилэх
    analyzer.analyze_imports()
    
    # Тайлан үүсгэх
    report = analyzer.generate_report()
    
    # JSON тайлан хадгалах
    with open('redundant_code_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Дэлгэрэнгүй тайлан хадгалагдлаа: redundant_code_report.json")
    
    # Цэвэрлэх скрипт үүсгэх
    analyzer.create_cleanup_script(report)
    
    print(f"\n🎉 Шинжилгээ дуусав!")
    print(f"   💡 Зөвлөмж: Эхлээд backup үүсгээд cleanup_redundant.sh ажиллуулна уу")

if __name__ == "__main__":
    main()