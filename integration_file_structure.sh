# =============================================================================
# TAB INTEGRATION SYSTEM - ФАЙЛЫН БҮТЭЦ
# =============================================================================

# Таны төслийн үндсэн директорт энэ бүтцийг үүсгэнэ үү:

tv_streaming_system/
├── 📁 core/
│   ├── __init__.py
│   ├── integration/                    # 🆕 ШИНЭ ХАВТАС
│   │   ├── __init__.py
│   │   ├── event_bus.py               # EventBus, SystemEvent классууд
│   │   ├── shared_data.py             # SharedDataManager, MediaInfo, etc.
│   │   ├── workflow_engine.py         # WorkflowEngine, Workflow классууд  
│   │   ├── tab_manager.py             # TabIntegrationManager
│   │   ├── monitoring.py              # SystemMonitor
│   │   ├── base_tab.py                # IntegratedTabBase
│   │   ├── mixins.py                  # MediaLibraryIntegration, etc.
│   │   ├── workflows.py               # PracticalWorkflows
│   │   ├── messages.py                # MongolianSystemMessages
│   │   ├── config.py                  # IntegrationConfig
│   │   └── setup.py                   # setup_integration_system функц
│   ├── config_manager.py
│   ├── logging.py
│   └── constants.py
│
├── 📁 ui/
│   ├── integration/                    # 🆕 ШИНЭ ХАВТАС  
│   │   ├── __init__.py
│   │   ├── enhanced_main_window.py    # EnhancedProfessionalStreamingStudio
│   │   ├── integration_dialogs.py     # Status, Settings диалогууд
│   │   ├── workflow_dialogs.py        # Workflow management UI
│   │   └── integration_utils.py       # integrate_with_existing_main_window
│   ├── tabs/
│   │   ├── media_library_tab.py
│   │   ├── playout_tab.py
│   │   ├── streaming_tab.py
│   │   └── scheduler_tab.py
│   └── main_window.py
│
├── 📁 examples/                       # 🆕 ШИНЭ ХАВТАС
│   ├── __init__.py
│   ├── integration_example.py         # CompleteIntegrationExample
│   ├── workflow_examples.py           # Workflow жишээнүүд
│   ├── custom_workflows.py            # Custom workflow үүсгэх жишээ
│   └── launcher.py                    # launch_enhanced_studio
│
├── 📁 data/
│   ├── integration_config.json        # Integration тохиргоо
│   ├── workflows/                     # Custom workflow файлууд
│   └── monitoring/                    # Monitoring өгөгдөл
│
├── main.py                           # Updated with integration
└── requirements.txt                  # Updated dependencies

# =============================================================================
# ХЭРХЭН ҮҮСГЭХ ВЭ? - STEP BY STEP
# =============================================================================

# 1. ХАВТАСНУУД ҮҮСГЭХ
mkdir -p core/integration
mkdir -p ui/integration  
mkdir -p examples
mkdir -p data/workflows
mkdir -p data/monitoring

# 2. __init__.py ФАЙЛУУД ҮҮСГЭХ
touch core/integration/__init__.py
touch ui/integration/__init__.py
touch examples/__init__.py

# 3. ҮНДСЭН ФАЙЛУУДЫГ ҮҮСГЭХ (дараагийн алхамд)

# =============================================================================
# ФАЙЛ ХУВААРИЛАЛТ - ДЭЛГЭРЭНГҮЙ
# =============================================================================