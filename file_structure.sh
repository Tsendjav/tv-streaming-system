#!/bin/bash

# =============================================================================
# TAB INTEGRATION SYSTEM - ФАЙЛЫН БҮТЭЦ ҮҮСГЭХ СКРИПТ
# =============================================================================

echo "🎯 Creating Tab Integration System file structure..."

# Таны төслийн үндсэн директорт энэ скриптийг ажиллуулна уу

# =============================================================================
# 1. ХАВТАСНУУД ҮҮСГЭХ
# =============================================================================

echo "📁 Creating directories..."

# Core integration хавтас
mkdir -p core/integration
mkdir -p ui/integration  
mkdir -p examples
mkdir -p data/workflows
mkdir -p data/monitoring
mkdir -p data/configs

echo "   ✅ Core directories created"

# =============================================================================
# 2. __init__.py ФАЙЛУУД ҮҮСГЭХ
# =============================================================================

echo "📄 Creating __init__.py files..."

# Core integration __init__.py
cat > core/integration/__init__.py << 'EOF'
"""
Tab Integration System for TV Streaming Studio

This package provides comprehensive integration between all tabs in the streaming studio,
enabling cross-tab communication, automated workflows, and system monitoring.
"""

from .event_bus import EventBus, EventType, SystemEvent
from .shared_data import SharedDataManager, MediaInfo, StreamInfo, PlayoutState
from .tab_manager import TabIntegrationManager
from .workflow_engine import WorkflowEngine, Workflow, WorkflowStep
from .monitoring import SystemMonitor
from .base_tab import IntegratedTabBase, ITabIntegration
from .mixins import (
    MediaLibraryIntegration,
    PlayoutIntegration, 
    StreamingIntegration,
    SchedulerIntegration
)
from .workflows import PracticalWorkflows
from .messages import MongolianSystemMessages
from .config import IntegrationConfig
from .setup import (
    StreamingStudioIntegration,
    setup_integration_system,
    create_integrated_media_library_tab,
    create_integrated_playout_tab,
    create_integrated_streaming_tab,
    create_integrated_scheduler_tab,
    create_basic_integrated_tab
)

__version__ = "1.0.0"
__author__ = "TV Streaming Studio Team"

def quick_setup(main_window, config_manager):
    """Quick setup with default configuration"""
    config = IntegrationConfig()
    config.apply_defaults_for_broadcasting()
    return setup_integration_system(main_window, config_manager, config)

__all__ = [
    'EventBus', 'EventType', 'SystemEvent',
    'SharedDataManager', 'MediaInfo', 'StreamInfo', 'PlayoutState',
    'TabIntegrationManager',
    'WorkflowEngine', 'Workflow', 'WorkflowStep',
    'SystemMonitor',
    'IntegratedTabBase', 'ITabIntegration',
    'MediaLibraryIntegration', 'PlayoutIntegration',
    'StreamingIntegration', 'SchedulerIntegration',
    'PracticalWorkflows',
    'MongolianSystemMessages',
    'IntegrationConfig',
    'StreamingStudioIntegration',
    'setup_integration_system',
    'quick_setup',
    'create_integrated_media_library_tab',
    'create_integrated_playout_tab',
    'create_integrated_streaming_tab', 
    'create_integrated_scheduler_tab',
    'create_basic_integrated_tab'
]
EOF

# UI integration __init__.py
cat > ui/integration/__init__.py << 'EOF'
"""
UI Integration Components

This package provides enhanced UI components and dialogs for the integration system.
"""

__all__ = []
EOF

# Examples __init__.py
cat > examples/__init__.py << 'EOF'
"""
Integration System Examples

This package contains example implementations and usage patterns for the integration system.
"""

__all__ = []
EOF

echo "   ✅ __init__.py files created"

# =============================================================================
# 3. ТОХИРГООНЫ ФАЙЛУУД
# =============================================================================

echo "⚙️ Creating configuration files..."

# Integration config файл
cat > data/configs/integration_config.json << 'EOF'
{
    "monitoring_enabled": true,
    "monitoring_interval": 5000,
    "automation_enabled": true,
    "emergency_auto_recovery": true,
    "event_history_limit": 1000,
    "performance_history_limit": 1000,
    "alert_thresholds": {
        "audio_level_low": -40.0,
        "memory_usage_high": 85.0,
        "cpu_usage_high": 80.0,
        "network_latency_high": 500.0,
        "stream_bitrate_drop": 0.8,
        "dropped_frames_high": 5.0,
        "disk_space_low": 90.0,
        "stream_disconnect": 1,
        "playout_stopped": 1
    },
    "workflow_timeout_default": 30,
    "workflow_retry_attempts": 3,
    "workflow_retry_delay": 5000,
    "language": "mongolian",
    "use_localized_messages": true,
    "tab_settings": {
        "media_library": {
            "auto_scan_enabled": true,
            "scan_interval": 300000,
            "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
            "thumbnail_generation": true
        },
        "playout": {
            "auto_cue_enabled": true,
            "fade_duration": 1.0,
            "preview_auto_load": true,
            "audio_monitoring": true
        },
        "streaming": {
            "auto_start_on_take": false,
            "quality_adaptation": true,
            "backup_streams": true,
            "stream_health_check": true
        },
        "scheduler": {
            "automation_enabled": true,
            "look_ahead_time": 300,
            "auto_execute": true,
            "conflict_resolution": "warn"
        }
    }
}
EOF

# Workflow examples файл
cat > data/workflows/example_workflows.json << 'EOF'
{
    "custom_workflows": [
        {
            "name": "morning_startup",
            "description": "Өглөөний системийн эхлүүлэлт",
            "steps": [
                {"name": "system_check", "tab": "scheduler", "command": "health_check"},
                {"name": "load_schedule", "tab": "scheduler", "command": "load_daily_schedule"},
                {"name": "prepare_media", "tab": "media_library", "command": "scan_media"},
                {"name": "test_streams", "tab": "streaming", "command": "test_connections"}
            ]
        },
        {
            "name": "evening_shutdown",
            "description": "Оройн системийн хаалт",
            "steps": [
                {"name": "stop_automation", "tab": "scheduler", "command": "disable_automation"},
                {"name": "stop_streams", "tab": "streaming", "command": "stop_all_streams"},
                {"name": "backup_logs", "tab": "scheduler", "command": "backup_daily_logs"},
                {"name": "cleanup", "tab": "media_library", "command": "cleanup_temp"}
            ]
        }
    ]
}
EOF

# Monitoring config файл
cat > data/monitoring/monitor_config.json << 'EOF'
{
    "alert_rules": [
        {
            "name": "stream_quality_check",
            "condition": "bitrate < expected_bitrate * 0.8",
            "action": "quality_adaptive_workflow",
            "severity": 2
        },
        {
            "name": "audio_silence_check", 
            "condition": "audio_level < -50",
            "action": "audio_alert",
            "severity": 1
        },
        {
            "name": "memory_high_check",
            "condition": "memory_usage > 90",
            "action": "cleanup_workflow",
            "severity": 3
        }
    ],
    "performance_thresholds": {
        "cpu_warning": 75.0,
        "cpu_critical": 90.0,
        "memory_warning": 80.0,
        "memory_critical": 95.0,
        "disk_warning": 85.0,
        "disk_critical": 95.0,
        "network_latency_warning": 300.0,
        "network_latency_critical": 1000.0
    }
}
EOF

echo "   ✅ Configuration files created"

# =============================================================================
# 4. README ФАЙЛУУД
# =============================================================================

echo "📚 Creating documentation files..."

# Main README файл
cat > README_INTEGRATION.md << 'EOF'
# Tab Integration System - Таб Интеграцийн Систем

## 🎯 Тайлбар

Энэ систем нь TV Streaming Studio-ын бүх табуудыг нэгтгэн ажиллуулах үндсэн системийн хэрэгжүүлэлт юм.

## 🏗️ Файлын Бүтэц

```
tv_streaming_system/
├── core/integration/          # Үндсэн интеграцийн системийн кодууд
│   ├── event_bus.py          # Үйл явдлын удирдлага
│   ├── shared_data.py        # Хуваалцсан өгөгдөл
│   ├── tab_manager.py        # Таб удирдлага
│   ├── workflow_engine.py    # Workflow гүйцэтгэл
│   ├── monitoring.py         # Системийн мониторинг
│   ├── base_tab.py          # Үндсэн таб класс
│   ├── mixins.py            # Таб-н тусгайлсан функцууд
│   ├── workflows.py         # Практик workflow-ууд
│   ├── messages.py          # Монгол хэлний мессежүүд
│   ├── config.py           # Системийн тохиргоо
│   └── setup.py            # Системийн тохируулга
├── ui/integration/           # UI интеграцийн компонентууд
├── examples/                # Жишээ кодууд
│   └── integration_example.py
├── data/
│   ├── configs/             # Тохиргооны файлууд
│   ├── workflows/           # Workflow тодорхойлолт
│   └── monitoring/          # Мониторингийн тохиргоо
└── README_INTEGRATION.md    # Энэ файл
```

## 🚀 Хэрхэн Ашиглах

### 1. Энгийн Тохируулга

```python
from core.integration import quick_setup

# Main window дотор:
integration_system, monitor = quick_setup(self, config_manager)
```

### 2. Дэлгэрэнгүй Тохируулга

```python
from core.integration import setup_integration_system, IntegrationConfig

# Тохиргоо үүсгэх
config = IntegrationConfig()
config.apply_defaults_for_broadcasting()

# Системийг тохируулах
integration_system, monitor = setup_integration_system(
    main_window, config_manager, config
)
```

### 3. Workflow Ажиллуулах

```python
# Медиаг амьдаар гаргах
execution_id = integration_system.execute_workflow(
    "complete_media_to_air", 
    {"file_path": "video.mp4"}
)

# Стрим эхлүүлэх
integration_system.execute_workflow("live_streaming_setup")

# Яаралтай зогсоолт
integration_system.trigger_emergency_stop("Manual stop")
```

## 🔧 Онцлогууд

### ✅ Автомат Харилцаа
- Таб хоорондын автомат мэдээлэл солилцоо
- Media Library → Playout → Streaming автомат дарааллын ажиллагаа
- Schedule-ийн дагуу автомат гүйцэтгэл

### ✅ Бодит Цагийн Мониторинг
- Системийн гүйцэтгэлийн хяналт
- Аудио, видео, сүлжээний төлөвийн мониторинг
- Автомат алерт болон нөхөн сэргээлт

### ✅ Практик Workflow-ууд
- Media-to-Air: Файлаас эхлээд амьдаар гарах хүртэл
- Live Streaming: Стрим бэлтгэх, эхлүүлэх, хяналт
- Emergency Procedures: Яаралтай нөхцөлийн үйлдлүүд
- Quality Adaptation: Сүлжээний төлөвийн дагуу чанар тохируулах

### ✅ Монгол Хэлний Дэмжлэг
- Бүх системийн мессежүүд монгол хэлээр
- Алерт болон статусын мэдээлэл монгол хэлээр
- Локализацийн дэмжлэг

## 📊 Системийн Мониторинг

Систем нь дараах зүйлсийг мониторинг хийдэг:

- **Стримийн төлөв**: Битрейт, чанар, холболт
- **Аудио түвшин**: Дууны түвшин, дуу алдагдал
- **Системийн гүйцэтгэл**: CPU, RAM, Disk ашиглалт
- **Сүлжээний төлөв**: Хоцрогдол, холболтын чанар

## 🛠️ Тохиргоо

### Alert Thresholds
```json
{
    "audio_level_low": -40.0,      // dB
    "memory_usage_high": 85.0,     // %
    "network_latency_high": 500.0, // ms
    "stream_bitrate_drop": 0.8     // ratio
}
```

### Tab Settings
```json
{
    "playout": {
        "auto_cue_enabled": true,
        "fade_duration": 1.0,
        "preview_auto_load": true
    },
    "streaming": {
        "auto_start_on_take": false,
        "quality_adaptation": true,
        "backup_streams": true
    }
}
```

## 🎬 Жишээ Ашиглалт

`examples/integration_example.py` файлд бүрэн жишээ байгаа.

```bash
# Жишээг ажиллуулах
cd examples
python integration_example.py
```

## 🔍 Troubleshooting

### Түгээмэл Асуудлууд

1. **Integration системгүй**
   - `setup_integration_system()` дуудагдсан эсэхийг шалгана уу
   - Config manager байгаа эсэхийг шалгана уу

2. **Tab integration амжилтгүй**
   - Tab-ийн нэр зөв эсэхийг шалгана уу
   - Original tab-д шаардлагатай методууд байгаа эсэхийг шалгана уу

3. **Workflow ажиллахгүй**
   - Workflow бүртгэгдсэн эсэхийг шалгана уу
   - Tab command handler-ууд зөв бүртгэгдсэн эсэхийг шалгана уу

### Log Файлууд

Системийн log файлууд дараах байршилд байна:
- `logs/integration.log` - Үндсэн системийн лог
- `logs/monitoring.log` - Мониторингийн лог
- `logs/workflows.log` - Workflow гүйцэтгэлийн лог

## 📞 Дэмжлэг

Асуудал гарвал дараах алхмуудыг дагана уу:

1. Log файлуудыг шалгана уу
2. Configuration файлуудыг шалгана уу
3. Example кодуудыг туршина уу
4. Documentation-ийг дахин уншина уу

---

🎯 **TV Streaming Studio Integration System** - Мэргэжлийн broadcast системд зориулсан!
EOF

# Integration guide файл
cat > INTEGRATION_GUIDE.md << 'EOF'
# Integration System Setup Guide

## 📋 Step-by-Step Setup

### 1. Install Requirements

```bash
pip install PyQt6 psutil
```

### 2. Copy Integration Files

Та өөрийн төсөлд дараах файлуудыг хуулна уу:

```bash
cp -r core/integration/ your_project/core/
cp -r examples/ your_project/
cp -r data/ your_project/
```

### 3. Update Main Window

```python
# main_window.py файлдаа энийг нэмнэ үү:

from core.integration import setup_integration_system, IntegrationConfig

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_integration()  # Add this line
    
    def setup_integration(self):
        """Setup integration system"""
        try:
            config = IntegrationConfig()
            config.apply_defaults_for_broadcasting()
            
            self.integration_system, self.system_monitor = setup_integration_system(
                self, self.config_manager, config
            )
            
            print("✅ Integration system ready!")
            
        except Exception as e:
            print(f"❌ Integration setup failed: {e}")
```

### 4. Test Integration

```python
# Integration тест хийх
if hasattr(self, 'integration_system'):
    status = self.integration_system.get_system_status()
    print("System Status:", status)
    
    # Workflow туршиж үзэх
    self.integration_system.execute_workflow("media_to_air")
```

## 🔧 Customization

### Add Custom Workflows

```python
from core.integration import Workflow, WorkflowStep

custom_workflow = Workflow(
    name="my_custom_workflow",
    description="Миний тусгай workflow",
    steps=[
        WorkflowStep("step1", "media_library", "my_command"),
        WorkflowStep("step2", "playout", "my_other_command")
    ]
)

integration_system.workflow_engine.register_workflow(custom_workflow)
```

### Add Custom Messages

```python
from core.integration import MongolianSystemMessages

MongolianSystemMessages.add_custom_message(
    "my_message", 
    "Миний тусгай мессеж: {param}"
)

message = MongolianSystemMessages.get_message("my_message", param="test")
```

### Customize Monitoring

```python
# Alert threshold өөрчлөх
config = IntegrationConfig()
config.set_alert_threshold("audio_level_low", -35.0)
config.set_alert_threshold("memory_usage_high", 90.0)
```

## 🚀 Advanced Usage

### Event Handling

```python
# Event-д хариу үйлдэл хийх
from core.integration import EventType

def my_event_handler(event):
    if event.event_type == EventType.MEDIA_LOADED:
        print(f"Media loaded: {event.data}")

integration_system.event_bus.subscribe(
    EventType.MEDIA_LOADED, 
    my_event_handler
)
```

### Custom Tab Integration

```python
from core.integration import IntegratedTabBase

class MyCustomTab(IntegratedTabBase):
    def __init__(self):
        super().__init__("my_tab", config_manager)
    
    def _register_command_handlers(self):
        super()._register_command_handlers()
        self.command_handlers["my_command"] = self._handle_my_command
    
    def _handle_my_command(self, params):
        # Команд боловсруулах
        return {"success": True}

# Register custom tab
custom_tab = MyCustomTab()
integration_system.register_tab(custom_tab)
```
EOF

echo "   ✅ Documentation files created"

# =============================================================================
# 5. ДУУСГАЛТ
# =============================================================================

echo ""
echo "🎉 Tab Integration System файлын бүтэц амжилттай үүсгэгдлээ!"
echo ""
echo "📂 Үүсгэгдсэн файлууд:"
echo "   📁 core/integration/           - Үндсэн интеграцийн кодууд"
echo "   📁 ui/integration/             - UI компонентууд"  
echo "   📁 examples/                   - Жишээ кодууд"
echo "   📁 data/                       - Тохиргоо болон өгөгдөл"
echo "   📄 README_INTEGRATION.md       - Үндсэн заавар"
echo "   📄 INTEGRATION_GUIDE.md        - Тохиргооны заавар"
echo ""
echo "🚀 Дараагийн алхмууд:"
echo "   1. Integration кодуудыг өөрийн файлуудад хуулах"
echo "   2. main_window.py-д integration setup нэмэх"
echo "   3. examples/integration_example.py-г ажиллуулж туршиж үзэх"
echo "   4. README_INTEGRATION.md-г уншиж дэлгэрэнгүй мэдээлэл авах"
echo ""
echo "✅ Бэлэн! Таны ТВ стрим системд integration нэгтгэгдэнэ!"
echo ""
echo "📞 Тусламж хэрэгтэй бол INTEGRATION_GUIDE.md-г үзнэ үү"