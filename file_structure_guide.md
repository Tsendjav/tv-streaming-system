# 📁 Tab Integration System - Файлын бүтэц ба хадгалах заавар

## 🎯 Хаана юуг хадгалах вэ?

### 1️⃣ **Үндсэн Integration системийн файлууд**

```
core/integration/          # 🆕 ШИНЭ ХАВТАС ҮҮСГЭХ
├── __init__.py            # Import-уудыг зохион байгуулах
├── event_bus.py           # EventBus, SystemEvent, EventType
├── shared_data.py         # SharedDataManager, MediaInfo, StreamInfo
├── tab_manager.py         # TabIntegrationManager
├── workflow_engine.py     # WorkflowEngine, Workflow, WorkflowStep
├── monitoring.py          # SystemMonitor
├── base_tab.py           # IntegratedTabBase, ITabIntegration
├── mixins.py             # MediaLibraryIntegration, PlayoutIntegration, etc.
├── workflows.py          # PracticalWorkflows
├── messages.py           # MongolianSystemMessages
├── config.py             # IntegrationConfig
├── setup.py              # setup_integration_system
└── tab_wrappers.py       # Tab wrapper functions
```

### 2️⃣ **UI Integration файлууд**

```
ui/integration/            # 🆕 ШИНЭ ХАВТАС ҮҮСГЭХ
├── __init__.py
├── enhanced_main_window.py    # EnhancedProfessionalStreamingStudio
├── integration_dialogs.py    # System Status, Settings диалогууд
├── workflow_dialogs.py       # Workflow management UI
└── integration_utils.py      # integrate_with_existing_main_window
```

### 3️⃣ **Жишээ ба туршилтын файлууд**

```
examples/                  # 🆕 ШИНЭ ХАВТАС ҮҮСГЭХ
├── __init__.py
├── integration_example.py     # CompleteIntegrationExample
├── workflow_examples.py       # Custom workflow жишээнүүд
├── custom_workflows.py        # Хэрхэн custom workflow үүсгэх
└── launcher.py               # launch_enhanced_studio
```

### 4️⃣ **Тохиргоо ба өгөгдлийн файлууд**

```
data/                     # Одоо байгаа хавтас
├── integration_config.json   # Integration тохиргоо
├── workflows/               # Custom workflow-ууд
│   ├── morning_show.json
│   ├── breaking_news.json
│   └── evening_broadcast.json
└── monitoring/             # Monitoring өгөгдөл
    ├── performance_logs/
    └── alerts_history/
```

## 🛠️ Хэрхэн үүсгэх вэ? - Step by Step

### **Алхам 1: Хавтаснуудыг үүсгэх**

```bash
# Таны төслийн үндсэн хавтаст энэ командуудыг ажиллуулна уу:

# Үндсэн integration хавтас
mkdir -p core/integration
mkdir -p ui/integration
mkdir -p examples
mkdir -p data/workflows
mkdir -p data/monitoring

# __init__.py файлууд үүсгэх
touch core/integration/__init__.py
touch ui/integration/__init__.py
touch examples/__init__.py
```

### **Алхам 2: Үндсэн файлуудыг үүсгэх**

1. **core/integration/__init__.py** файлд:
```python
"""
Core Integration System
Табуудын хоорондын ажиллагааны үндсэн систем
"""

from .event_bus import EventBus, SystemEvent, EventType
from .shared_data import SharedDataManager, MediaInfo, StreamInfo, PlayoutState
from .tab_manager import TabIntegrationManager
from .workflow_engine import WorkflowEngine, Workflow, WorkflowStep
from .monitoring import SystemMonitor
from .base_tab import IntegratedTabBase, ITabIntegration
from .mixins import (
    MediaLibraryIntegration, PlayoutIntegration, 
    StreamingIntegration, SchedulerIntegration
)
from .workflows import PracticalWorkflows
from .messages import MongolianSystemMessages
from .config import IntegrationConfig
from .setup import StreamingStudioIntegration, setup_integration_system

__all__ = [
    # Core components
    'EventBus', 'SystemEvent', 'EventType',
    'SharedDataManager', 'MediaInfo', 'StreamInfo', 'PlayoutState',
    'TabIntegrationManager', 'WorkflowEngine', 'Workflow', 'WorkflowStep',
    'SystemMonitor',
    
    # Tab integration
    'IntegratedTabBase', 'ITabIntegration',
    'MediaLibraryIntegration', 'PlayoutIntegration',
    'StreamingIntegration', 'SchedulerIntegration',
    
    # Utilities
    'PracticalWorkflows', 'MongolianSystemMessages',
    'IntegrationConfig', 'StreamingStudioIntegration',
    'setup_integration_system'
]
```

2. **core/integration/event_bus.py** - (Өмнө үүсгэсэн)

3. **core/integration/shared_data.py** - (Өмнө үүсгэсэн)

4. **core/integration/setup.py** - (Өмнө үүсгэсэн)

### **Алхам 3: Таны main.py файлыг шинэчлэх**

```python
# main.py файлын дээд хэсэгт нэмнэ үү:
try:
    from core.integration import setup_integration_system, IntegrationConfig
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    print("⚠️ Integration system import failed")

# main() function дотор:
def main():
    # ... existing code ...
    
    # Create main window
    from ui.main_window import ProfessionalStreamingStudio
    main_win = ProfessionalStreamingStudio(config_manager, app)
    
    # Add integration if available
    if INTEGRATION_AVAILABLE:
        try:
            integration_config = IntegrationConfig()
            integration_config.monitoring_enabled = True
            integration_config.automation_enabled = True
            
            integration_system, monitor = setup_integration_system(
                main_win, config_manager, integration_config
            )
            
            print("✅ Integration system амжилттай ачаалагдлаа!")
        except Exception as e:
            print(f"❌ Integration setup failed: {e}")
    
    main_win.show()
    # ... rest of code ...
```

### **Алхам 4: Remaining файлуудыг үүсгэх**

Би одоо бусад шаардлагатай файлуудыг үүсгэж өгье:

#### **core/integration/config.py**
```python
"""Integration системийн тохиргоо"""

class IntegrationConfig:
    def __init__(self):
        self.monitoring_enabled = True
        self.monitoring_interval = 5000  # ms
        self.automation_enabled = True
        self.emergency_auto_recovery = True
        self.event_history_limit = 1000
        self.performance_history_limit = 1000
        
        # Alert thresholds
        self.alert_thresholds = {
            "audio_level_low": -40.0,      # dB
            "memory_usage_high": 85.0,     # %
            "cpu_usage_high": 80.0,        # %
            "network_latency_high": 500.0, # ms
            "stream_bitrate_drop": 0.8,    # ratio
            "dropped_frames_high": 5.0     # %
        }
        
        # Language settings
        self.language = "mongolian"
        self.use_localized_messages = True
    
    def to_dict(self):
        return self.__dict__.copy()
    
    @classmethod  
    def from_dict(cls, data):
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
```

#### **core/integration/messages.py**
```python
"""Монгол хэлний системийн мессежүүд"""

class MongolianSystemMessages:
    MESSAGES = {
        # Event messages
        "media_loaded": "Медиа ачаалагдлаа: {filename}",
        "stream_started": "Стрим эхэллээ: {stream_key}",
        "stream_stopped": "Стрим зогслоо: {stream_key}",
        "playout_live": "Плейаут амьдаар гарлаа",
        "playout_stopped": "Плейаут зогслоо",
        "emergency_stop": "Яаралтай зогсоолт идэвхжлээ",
        
        # Alert messages
        "alert_audio_low": "Аудио түвшин доогуур: {level}dB",
        "alert_stream_disconnect": "Стримийн холболт тасарлаа: {stream_key}",
        "alert_memory_high": "Санах ойн ашиглалт өндөр: {usage}%",
        "alert_network_slow": "Сүлжээний хурд удаан: {latency}ms",
        
        # Workflow messages
        "workflow_started": "Автомат үйл ажиллагаа эхэллээ: {workflow_name}",
        "workflow_completed": "Автомат үйл ажиллагаа дууслаа: {workflow_name}",
        "workflow_failed": "Автомат үйл ажиллагаа амжилтгүй: {workflow_name}",
    }
    
    @staticmethod
    def get_message(key: str, **kwargs) -> str:
        """Get localized message with parameters"""
        message_template = MongolianSystemMessages.MESSAGES.get(key, key)
        try:
            return message_template.format(**kwargs)
        except KeyError:
            return message_template
```

## 📥 Хэрхэн import хийх вэ?

### **Таны өөр файлуудаас ашиглах:**

```python
# main.py дотор:
from core.integration import setup_integration_system, IntegrationConfig

# main_window.py дотор:
from core.integration import EventType, SystemEvent

# Таб файлуудаас:
from core.integration import IntegratedTabBase, MediaLibraryIntegration

# Examples ашиглах:
from examples.integration_example import CompleteIntegrationExample
```

## 🔄 requirements.txt шинэчлэх

```txt
# Таны requirements.txt файлд нэмэх (хэрэв байхгүй бол):
PyQt6>=6.4.0
# ... existing dependencies ...

# Optional performance monitoring:
psutil>=5.9.0  # System monitoring
```

## 🧪 Тестлэх

Integration система зөв ажиллаж байгааг шалгах:

```python
# test_integration.py үүсгэж энэ кодыг туршина уу:
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.integration import (
        EventBus, SystemEvent, EventType,
        SharedDataManager, IntegrationConfig,
        setup_integration_system
    )
    print("✅ Бүх integration модулууд амжилттай import хийгдлээ!")
    
    # Test EventBus
    event_bus = EventBus()
    print("✅ EventBus үүсгэгдлээ")
    
    # Test SharedDataManager  
    shared_data = SharedDataManager()
    print("✅ SharedDataManager үүсгэгдлээ")
    
    # Test config
    config = IntegrationConfig()
    print("✅ IntegrationConfig үүсгэгдлээ")
    
    print("\n🎉 Integration system бэлэн боллоо!")
    
except ImportError as e:
    print(f"❌ Import алдаа: {e}")
except Exception as e:
    print(f"❌ Алдаа: {e}")
```

## 🎯 Дараагийн алхамууд:

1. **Эхлээд энэ бүтцийг үүсгэнэ үү**
2. **Тест ажиллуулж шалгана уу**  
3. **main.py файлаа шинэчилнэ үү**
4. **Програмаа эхлүүлж туршина уу**

Integration система ингэж зохион байгуулснаар:
- ✅ Код цэвэр, ойлгомжтой болно
- ✅ Файлууд логик бүлгээр хуваагдана  
- ✅ Import хялбар болно
- ✅ Debugging хялбар болно
- ✅ Хөгжүүлэлт үргэлжлүүлэхэд хялбар болно

Ямар нэг файл дутуу эсвэл нэмэлт тусламж хэрэгтэй бол надаас асуугаарай! 😊