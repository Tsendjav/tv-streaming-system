#!/usr/bin/env python3
"""
core/integration/messages.py
Mongolian language system messages for better localization
"""

# =============================================================================
# MONGOLIAN LANGUAGE SYSTEM MESSAGES
# =============================================================================

class MongolianSystemMessages:
    """Mongolian language system messages for better localization"""
    
    MESSAGES = {
        # Event messages
        "media_loaded": "Медиа ачаалагдлаа: {filename}",
        "stream_started": "Стрим эхэллээ: {stream_key}",
        "stream_stopped": "Стрим зогслоо: {stream_key}",
        "playout_live": "Плейаут амьдаар гарлаа",
        "playout_stopped": "Плейаут зогслоо",
        "emergency_stop": "Яаралтай зогсоолт идэвхжлээ",
        
        # Workflow messages
        "workflow_started": "Автомат үйл ажиллагаа эхэллээ: {workflow_name}",
        "workflow_completed": "Автомат үйл ажиллагаа дууслаа: {workflow_name}",
        "workflow_failed": "Автомат үйл ажиллагаа амжилтгүй: {workflow_name}",
        
        # Alert messages
        "alert_audio_low": "Аудио түвшин доогуур: {level}dB ({channel})",
        "alert_stream_disconnect": "Стримийн холболт тасарлаа: {stream_key}",
        "alert_memory_high": "Санах ойн ашиглалт өндөр: {usage}%",
        "alert_network_slow": "Сүлжээний хурд удаан: {latency}ms",
        "alert_disk_space_low": "Дискний зай бага: {usage}%",
        "alert_recovery_attempt": "{type} нөхөн сэргээлт эхэллээ",
        "alert_recovery_failed": "{type} нөхөн сэргээлт амжилтгүй: {error}",
        
        # Status messages
        "system_healthy": "Система эрүүл ажиллаж байна",
        "system_warning": "Системд анхааруулга байна",
        "system_critical": "Системд чухал асуудал байна",
        "tabs_connected": "{count} таб холбогдсон",
        "automation_enabled": "Автоматжуулалт идэвхтэй",
        "automation_disabled": "Автоматжуулалт идэвхгүй",
        
        # Command messages
        "command_executed": "Команд гүйцэтгэгдлээ: {command}",
        "command_failed": "Команд амжилтгүй: {command} - {error}",
        "file_not_found": "Файл олдсонгүй: {filepath}",
        "server_not_available": "Сервер боломжгүй: {server_name}",
        
        # Integration messages
        "tab_registered": "Таб бүртгэгдлээ: {tab_name}",
        "tab_activated": "Таб идэвхжлээ: {tab_name}",
        "event_broadcast": "Үйл явдал дамжуулагдлаа: {event_type}",
        "shared_data_updated": "Хуваалцсан өгөгдөл шинэчлэгдлээ",
        
        # Monitoring messages
        "monitoring_started": "Системийн мониторинг эхэллээ",
        "monitoring_stopped": "Системийн мониторинг зогслоо",
        "health_excellent": "🟢 Система маш сайн ажиллаж байна",
        "health_good": "🟡 Система сайн ажиллаж байна",
        "health_warning": "🟠 Системд анхааруулга байна",
        "health_critical": "🔴 Системд чухал асуудал байна",
        
        # Workflow status messages
        "workflow_step_started": "Алхам эхэллээ: {step_name}",
        "workflow_step_completed": "Алхам дууслаа: {step_name}",
        "workflow_step_failed": "Алхам амжилтгүй: {step_name} - {error}",
        
        # Stream quality messages
        "quality_excellent": "Стримийн чанар маш сайн",
        "quality_good": "Стримийн чанар сайн",
        "quality_fair": "Стримийн чанар дунд зэрэг",
        "quality_poor": "Стримийн чанар муу",
        
        # Audio messages
        "audio_levels_normal": "Аудио түвшин хэвийн",
        "audio_levels_low": "Аудио түвшин бага",
        "audio_levels_high": "Аудио түвшин өндөр",
        "audio_muted": "Аудио хаагдсан",
        "audio_unmuted": "Аудио нээгдсэн",
        
        # Media library messages
        "media_scan_started": "Медиа файл скан эхэллээ",
        "media_scan_completed": "Медиа файл скан дууслаа: {count} файл олдлоо",
        "media_file_added": "Медиа файл нэмэгдлээ: {filename}",
        "media_file_removed": "Медиа файл хасагдлаа: {filename}",
        "media_library_empty": "Медиа сан хоосон байна",
        
        # Schedule messages
        "schedule_loaded": "Хуваарь ачаалагдлаа: {event_count} үйл явдал",
        "schedule_event_triggered": "Хуваарийн үйл явдал гүйцэтгэгдлээ: {event_name}",
        "schedule_event_skipped": "Хуваарийн үйл явдал алгасагдлаа: {event_name}",
        "automation_rule_triggered": "Автомат дүрэм идэвхжлээ: {rule_name}",
        
        # Network and connectivity messages
        "network_connected": "Сүлжээнд холбогдлоо",
        "network_disconnected": "Сүлжээний холболт тасарлаа",
        "server_connected": "Серверт холбогдлоо: {server_name}",
        "server_disconnected": "Серверийн холболт тасарлаа: {server_name}",
        "bandwidth_sufficient": "Сүлжээний өргөн зурвас хангалттай",
        "bandwidth_insufficient": "Сүлжээний өргөн зурвас хангалтгүй",
        
        # Error messages
        "error_general": "Алдаа гарлаа: {error}",
        "error_file_access": "Файл уншиж чадсангүй: {filepath}",
        "error_network": "Сүлжээний алдаа: {error}",
        "error_stream": "Стримийн алдаа: {error}",
        "error_audio": "Аудио алдаа: {error}",
        "error_configuration": "Тохиргооны алдаа: {error}",
        
        # Success messages
        "operation_successful": "Үйлдэл амжилттай гүйцэтгэгдлээ",
        "file_saved": "Файл хадгалагдлаа: {filepath}",
        "configuration_saved": "Тохиргоо хадгалагдлаа",
        "backup_created": "Нөөшлөлт үүсгэгдлээ: {backup_name}",
        "restore_completed": "Сэргээлт дууслаа",
        
        # Performance messages
        "performance_good": "Системийн гүйцэтгэл сайн",
        "performance_degraded": "Системийн гүйцэтгэл буурчээ",
        "memory_usage_normal": "Санах ойн хэрэглээ хэвийн",
        "memory_usage_high": "Санах ойн хэрэглээ өндөр",
        "cpu_usage_normal": "Процессорын ачаалал хэвийн",
        "cpu_usage_high": "Процессорын ачаалал өндөр",
        
        # Integration system messages
        "integration_initialized": "Integration систем эхэллээ",
        "integration_failed": "Integration систем амжилтгүй",
        "tab_integration_successful": "Таб амжилттай интеграцилагдлаа: {tab_name}",
        "tab_integration_failed": "Таб интеграцилагдсангүй: {tab_name}",
        "workflow_registered": "Workflow бүртгэгдлээ: {workflow_name}",
        "event_bus_ready": "Event bus бэлэн боллоо",
        "shared_data_ready": "Shared data manager бэлэн боллоо"
    }
    
    @staticmethod
    def get_message(key: str, **kwargs) -> str:
        """Get localized message with parameters"""
        message_template = MongolianSystemMessages.MESSAGES.get(key, key)
        try:
            return message_template.format(**kwargs)
        except KeyError as e:
            # If formatting fails, return the template with missing parameter info
            return f"{message_template} (Missing parameter: {e})"
        except Exception:
            # If any other error occurs, return the key
            return key
    
    @staticmethod
    def get_all_messages() -> dict:
        """Get all available messages"""
        return MongolianSystemMessages.MESSAGES.copy()
    
    @staticmethod
    def add_custom_message(key: str, message: str):
        """Add custom message to the system"""
        MongolianSystemMessages.MESSAGES[key] = message
    
    @staticmethod
    def get_health_message(health_status: str) -> str:
        """Get health status message"""
        health_messages = {
            "excellent": MongolianSystemMessages.get_message("health_excellent"),
            "good": MongolianSystemMessages.get_message("health_good"),
            "warning": MongolianSystemMessages.get_message("health_warning"),
            "critical": MongolianSystemMessages.get_message("health_critical")
        }
        return health_messages.get(health_status, f"Unknown health status: {health_status}")
    
    @staticmethod
    def get_quality_message(quality_level: str) -> str:
        """Get stream quality message"""
        quality_messages = {
            "excellent": MongolianSystemMessages.get_message("quality_excellent"),
            "good": MongolianSystemMessages.get_message("quality_good"),
            "fair": MongolianSystemMessages.get_message("quality_fair"),
            "poor": MongolianSystemMessages.get_message("quality_poor")
        }
        return quality_messages.get(quality_level, f"Unknown quality level: {quality_level}")