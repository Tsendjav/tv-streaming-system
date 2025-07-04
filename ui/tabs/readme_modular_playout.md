# Modular & Responsive Playout System

Энэ нь professional broadcast системд зориулагдсан modular болон responsive playout системийн шинэчлэгдсэн хувилбар юм.

## 📁 Файлын Бүтэц

```
playout_components/
├── __init__.py                 # Package initialization
├── video_player.py            # Video player components
├── audio_control.py           # Audio control components  
├── ui_components.py           # UI components
└── playout_manager.py         # Core playout logic

playout_tab.py                 # Main playout tab (modular version)
scheduler_tab.py               # Scheduler integration
integration_example.py         # Integration example
README.md                      # This file
```

## 🔧 Компонентууд

### 1. **ResponsiveVideoPlayer** (`video_player.py`)
- VLC дэмжлэг бүхий video player
- Playlist management
- Media Library болон Scheduler integration
- Responsive design for different screen sizes

### 2. **ResponsiveAudioControlPanel** (`audio_control.py`)
- Professional audio processing
- Real-time audio monitoring
- EQ and effects controls
- Responsive layout

### 3. **UI Components** (`ui_components.py`)
- ResponsiveGroupBox
- AMCPControlSection
- LogSection
- TransportControls
- Responsive button components

### 4. **PlayoutManager** (`playout_manager.py`)
- Core playout logic
- State management
- Scheduler integration
- Media Library integration

## 🎯 Гол Шинэчлэлтүүд

### 1. **Modular Architecture**
```python
# Import individual components
from playout_components import ResponsiveVideoPlayer, ResponsiveAudioControlPanel

# Or import all at once
from playout_components import *
```

### 2. **Responsive Design**
- Жижиг дэлгэцтэй компьютерт автоматаар хянах
- Compact mode (< 1000px width)
- Full mode (≥ 1000px width)
- Dynamic button sizing and layout

### 3. **Scheduler Integration**
```python
# Scheduler-ээс playlist авах
def _handle_scheduler_request(self):
    playlist = self.playout_manager.get_scheduler_playlist()
    sender = self.sender()
    if sender:
        sender.set_scheduler_playlist(playlist)
```

### 4. **Media Library Integration**
```python
# Media Library-ээс файлууд авах
def _handle_media_library_request(self):
    media_files = self.playout_manager.get_media_library_files()
    sender = self.sender()
    if sender:
        sender.set_media_library_files(media_files)
```

## 🚀 Хэрэглэх Зааврууд

### 1. **Үндсэн Setup**
```python
from playout_tab import ResponsivePlayoutTab
from scheduler_tab import SchedulerTab

# Create tabs
config_manager = YourConfigManager()
playout_tab = ResponsivePlayoutTab(config_manager)
scheduler_tab = SchedulerTab(config_manager)

# Setup integration
playout_tab.set_scheduler_tab(scheduler_tab)
playout_tab.set_media_library_tab(media_library_tab)
```

### 2. **Scheduler Events үүсгэх**
```python
from scheduler_tab import ScheduleEvent, EventType
from datetime import datetime, timedelta

# Create media play event
event = ScheduleEvent(
    id="demo_event_1",
    name="Morning News",
    event_type=EventType.MEDIA_PLAY,
    scheduled_time=datetime.now() + timedelta(minutes=30),
    content="/path/to/morning_news.mp4",
    duration=timedelta(minutes=5),
    auto_execute=True
)

scheduler_tab.schedule_manager.add_event(event)
```

### 3. **Responsive Layout Control**
```python
# Check current layout mode
if playout_tab.is_compact_mode:
    print("Currently in compact mode")
else:
    print("Currently in full mode")

# Force layout update
playout_tab._update_layout_for_responsive()
```

## 🔄 Integration Example

`integration_example.py` файл scheduler болон playout систем хэрхэн холбогдохыг харуулна:

```bash
python integration_example.py
```

### Integration Features:
- **Auto-sync**: Scheduler events автоматаар playout системд илгээгдэх
- **Demo Events**: Жишээ events үүсгэх
- **Real-time Updates**: Scheduler болон playout хоорондын real-time мэдээлэл солилцоо
- **Status Monitoring**: Системийн төлөв шалгах

## 📱 Responsive Behavior

### Compact Mode (< 1000px width)
- Vertical layout
- Smaller buttons
- Hidden non-essential elements
- Condensed text

### Full Mode (≥ 1000px width)
- Horizontal layout
- Full-sized buttons
- All elements visible
- Complete text labels

## 🎮 Media Controls

### Video Players
- **Preview Player**: Нэвтрүүлгийн өмнө контент харах
- **Program Player**: Оуи гарах контент
- **Playlist Support**: Media Library болон Scheduler playlist

### Transport Controls
- **Send to Program**: Preview-ээс Program руу контент илгээх
- **Take to Air**: Program контентыг оуи гаргах
- **Stream Program**: Контентыг streaming хийх
- **Fade/Cut**: Програм зогсоох

## 🎵 Audio Features

### Professional Audio Control
- Master volume control
- Audio profiles (Movie, Music, News, Sports)
- Night mode
- EQ controls
- Real-time level monitoring

### Auto Audio Sync
- Файлын нэрээр автоматаар audio profile сонгох
- Smart content detection
- Automatic profile switching

## 🔧 Technical Requirements

### Dependencies
```python
# Core dependencies
PyQt6>=6.0.0
python-vlc>=3.0.0

# Audio system (optional)
# audio.tv_audio_engine
# audio.audio_profiles
# audio.jack_backend
```

### Optional Components
- VLC Media Player
- JACK Audio System
- Audio processing plugins

## 🐛 Troubleshooting

### Common Issues

1. **Components not loading**
   ```python
   # Check component availability
   from playout_components import COMPONENTS_AVAILABLE
   if not COMPONENTS_AVAILABLE:
       print("Components not available - check dependencies")
   ```

2. **Responsive layout issues**
   ```python
   # Force layout update
   playout_tab._handle_resize(playout_tab.size())
   ```

3. **Integration problems**
   ```python
   # Check integration status
   state = playout_tab.get_current_state()
   print(f"Scheduler available: {state['scheduler_available']}")
   print(f"Media library available: {state['media_library_available']}")
   ```

## 🔄 Migration from Old Version

### Old Code
```python
# Old monolithic approach
from playout_tab import PlayoutTab
playout = PlayoutTab(config)
```

### New Code
```python
# New modular approach
from playout_tab import ResponsivePlayoutTab
playout = ResponsivePlayoutTab(config)

# Same interface - backwards compatible
playout.load_preview_media("/path/to/media.mp4")
playout.take_to_air()
```

## 📈 Performance Improvements

### Modular Benefits
- **Faster Loading**: Зөвхөн шаардлагатай components load хийх
- **Better Memory Usage**: Unused components load хийхгүй
- **Easier Maintenance**: Тусдаа components засварлах
- **Scalability**: Шинэ components нэмэх

### Responsive Benefits
- **Better UX**: Жижиг дэлгэцэнд илүү сайн харагдах
- **Mobile Support**: Tablet болон mobile дэлгэцэнд ажиллах
- **Adaptive UI**: Дэлгэцийн хэмжээнд тохируулан харагдах

## 🔮 Future Enhancements

### Planned Features
- Touch interface support
- Mobile app version
- Cloud integration
- Advanced AI features
- Multi-language support

### Extensibility
- Plugin system
- Custom components
- Theme support
- Configuration management

## 📞 Support

Асуудал гарвал:
1. Check logs in playout system
2. Verify component availability
3. Test integration separately
4. Check responsive behavior

## 📄 License

This modular playout system is part of the professional broadcast package.
