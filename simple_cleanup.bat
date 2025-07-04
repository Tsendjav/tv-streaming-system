# Backup  
rmdir /s /q "backups\migration_1751423526"
rmdir /s /q "backups\migration_1751423840"
rmdir /s /q "backups\migration_1751423958"
rmdir /s /q "backups\migration_1751424107"
rmdir /s /q "backups\migration_1751424467"
rmdir /s /q "backups\migration_1751425256"
rmdir /s /q "backups\migration_1751425702"

# Backup  
del "main.py.backup"
del "main.py.corrupted"
del "ui\main_window.py.backup"
del "ui\tabs\streaming_tab_backup_20250702.py"

#   
del "test_streaming.py"
del "test_ubuntu_connection.py"
del "integration_usage_example.py"

#  streaming  
del "streaming\refactored_streaming_tab.py"

echo !