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