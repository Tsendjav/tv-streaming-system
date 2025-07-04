@echo off
chcp 65001
echo Creating backup...
xcopy /e /i /y . ..\tv_streaming_backup_%date:~-4%_%date:~3,2%_%date:~0,2%

echo Removing migration backups...
if exist "backups\migration_1751423526" rmdir /s /q "backups\migration_1751423526"
if exist "backups\migration_1751423840" rmdir /s /q "backups\migration_1751423840"
if exist "backups\migration_1751423958" rmdir /s /q "backups\migration_1751423958"
if exist "backups\migration_1751424107" rmdir /s /q "backups\migration_1751424107"
if exist "backups\migration_1751424467" rmdir /s /q "backups\migration_1751424467"
if exist "backups\migration_1751425256" rmdir /s /q "backups\migration_1751425256"
if exist "backups\migration_1751425702" rmdir /s /q "backups\migration_1751425702"

echo Removing backup files...
if exist "main.py.backup" del "main.py.backup"
if exist "main.py.corrupted" del "main.py.corrupted"
if exist "ui\main_window.py.backup" del "ui\main_window.py.backup"
if exist "ui\tabs\playout_tab.py.backup" del "ui\tabs\playout_tab.py.backup"
if exist "ui\tabs\streaming_tab_backup_20250702.py" del "ui\tabs\streaming_tab_backup_20250702.py"
if exist "ui\dialogs\servers\servers_backup_20250628_141621.json" del "ui\dialogs\servers\servers_backup_20250628_141621.json"

echo Removing test files...
if exist "test_streaming.py" del "test_streaming.py"
if exist "test_ubuntu_connection.py" del "test_ubuntu_connection.py"
if exist "integration_usage_example.py" del "integration_usage_example.py"
if exist "examples\integration_example.py" del "examples\integration_example.py"
if exist "ui\tabs\integration_example.py" del "ui\tabs\integration_example.py"

echo Cleaning __pycache__ directories...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Done! Testing the application...
python main.py structure
pause
