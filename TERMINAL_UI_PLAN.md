# Clarity Terminal UI Implementation Plan

## Overview

This document provides a comprehensive implementation plan for adding a terminal user interface (TUI) to Clarity. The TUI will share the same backend architecture (Qt signals, models, queue management) as the existing QML GUI, proving that the application is truly UI-agnostic.

## Architecture Principles

### Core Design Goals
1. **Zero Backend Duplication** - TUI consumes the same `Backend`, `Interactions`, and `Queue` classes as QML
2. **Qt Signal-Driven** - All updates flow through Qt signals; TUI subscribes like QML does
3. **Model Reuse** - QueueModel, SearchModel, SettingsModel render to terminal instead of QML delegates
4. **Separation of Concerns** - TUI is pure presentation layer; business logic stays in existing modules

### What Stays Unchanged
- `src/universal.py` - All singletons (bgworker, asyncBgworker, queueInstance, settings, caches)
- `src/playback/queuemanager.py` - Queue + QueueModel + MediaPlayer backends
- `src/providerInterface/` - Song, Album, Provider system
- `src/app/Backend.py` - Backend QObject with all slots/signals
- `src/app/Interactions.py` - Interactions QObject with playback bindings
- Windows SMTC integration (stays active, coupled to queue)
- Discord RPC (stays active, coupled to queue)

### What's New
- `src/tui/` package - Terminal UI implementation
- `run.py` modified to support `--tui` flag
- urwid-based rendering with Qt event loop integration

## File Structure

```
src/
├── tui/
│   ├── __init__.py                 # Package init
│   ├── main.py                     # TUI entry point (replaces QML engine)
│   ├── app.py                      # ClarityTUI main application class
│   ├── qt_event_loop.py            # Qt + urwid event loop integration
│   ├── input_handler.py            # Keyboard bindings → actions
│   ├── theme.py                    # Terminal color schemes (Material You compatible)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── base_screen.py          # Base class for all screens
│   │   ├── queue_screen.py         # Queue view (main screen)
│   │   ├── search_screen.py        # Search interface
│   │   └── settings_screen.py      # Settings tree editor
│   └── widgets/
│       ├── __init__.py
│       ├── now_playing.py          # Top bar: current song info
│       ├── progress_bar.py         # Playback progress bar
│       ├── queue_list.py           # QueueModel → urwid list
│       ├── search_results.py       # SearchModel → urwid list
│       ├── status_bar.py           # Bottom bar: keybindings help
│       └── modal.py                # Generic modal dialog
```

## Phase 1: Basic Playback (MVP)

### Goal
Display queue, show now playing info, control playback (play/pause/next/prev), navigate queue. Read-only view of queue (no add/remove yet).

### Phase 1 Components

#### 1.1 Entry Point (`src/tui/main.py`)

**Purpose:** Initialize Qt app without QML engine, set up TUI, start event loop.

**Key Responsibilities:**
- Create QCoreApplication (no widgets needed)
- Initialize `universal` (already happens via import)
- Create Backend and Interactions instances
- Create ClarityTUI app instance
- Integrate urwid main loop with Qt event loop
- Handle cleanup on exit

**Implementation Pattern:**
```python
from PySide6.QtCore import QCoreApplication, QTimer
import sys
import urwid
from src import universal
from src.app import Backend, Interactions
from src.tui.app import ClarityTUI
from src.tui.qt_event_loop import QtUrwidEventLoop
from src.misc import cleanup

def main():
    # Create Qt application (no GUI)
    app = QCoreApplication(sys.argv)
    app.setApplicationName("Clarity TUI")
    
    # Initialize backend objects (same as GUI)
    backend = Backend.Backend()
    interactions = Interactions.Interactions()
    
    # Create TUI application
    tui_app = ClarityTUI(backend, interactions)
    
    # Create urwid main loop with Qt integration
    event_loop = QtUrwidEventLoop(app)
    loop = urwid.MainLoop(
        tui_app.root_widget,
        palette=tui_app.palette,
        event_loop=event_loop,
        unhandled_input=tui_app.handle_input
    )
    
    # Connect cleanup
    def quit_handler():
        loop.stop()
        cleanup.runCleanup()
    app.aboutToQuit.connect(quit_handler)
    
    # Start event loop
    try:
        loop.run()
    except KeyboardInterrupt:
        app.quit()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 1.2 Qt Event Loop Integration (`src/tui/qt_event_loop.py`)

**Purpose:** Bridge between urwid's event loop and Qt's QEventLoop so signals work.

**Key Challenge:** urwid needs to process terminal I/O while Qt needs to process signals/timers.

**Implementation Strategy:**
- Subclass urwid's SelectEventLoop
- Process Qt events on each urwid iteration
- Use QTimer to poll for Qt events
- Handle both urwid file descriptors and Qt events

**Code Template:**
```python
import urwid
from PySide6.QtCore import QCoreApplication, QTimer, QEventLoop

class QtUrwidEventLoop(urwid.SelectEventLoop):
    """
    Custom event loop that processes both urwid and Qt events.
    """
    
    def __init__(self, qt_app: QCoreApplication):
        super().__init__()
        self.qt_app = qt_app
        self._qt_timer = QTimer()
        self._qt_timer.timeout.connect(self._process_qt_events)
        self._qt_timer.setInterval(10)  # Process Qt events every 10ms
    
    def run(self):
        """Override run to start Qt timer."""
        self._qt_timer.start()
        super().run()
    
    def _process_qt_events(self):
        """Process pending Qt events."""
        self.qt_app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 10)
    
    def _loop(self):
        """Override main loop iteration to handle Qt."""
        # Process Qt events before urwid events
        self._process_qt_events()
        # Then process urwid events
        return super()._loop()
```

**Alternative Approach (if above doesn't work):**
Use QTimer.singleShot to repeatedly poll urwid's input in Qt's event loop instead. Would need urwid's AsyncioEventLoop or manual screen drawing.

#### 1.3 Main Application (`src/tui/app.py`)

**Purpose:** Top-level TUI application container. Manages screen layout and keyboard routing.

**Structure:**
```python
import urwid
from src.tui.widgets.now_playing import NowPlayingBar
from src.tui.widgets.queue_list import QueueListWidget
from src.tui.widgets.status_bar import StatusBar
from src.tui.theme import TUI_PALETTE

class ClarityTUI:
    """Main TUI application."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.palette = TUI_PALETTE
        
        # Create widgets
        self.now_playing = NowPlayingBar(interactions)
        self.queue_list = QueueListWidget(backend, interactions)
        self.status_bar = StatusBar()
        
        # Layout: [NowPlaying | QueueList | StatusBar]
        self.root_widget = urwid.Frame(
            body=self.queue_list,
            header=self.now_playing,
            footer=self.status_bar
        )
        
        # Track focus for keybinding context
        self.current_screen = "queue"
    
    def handle_input(self, key):
        """Global unhandled input handler."""
        # Global keybindings (work everywhere)
        if key == ' ':  # Space: play/pause
            self._toggle_playback()
            return True
        elif key == 'n':  # Next track
            self.interactions.nextSong()
            return True
        elif key == 'p':  # Previous track
            self.interactions.previousSong()
            return True
        elif key in ('+', '='):  # Volume up
            self._change_volume(+5)
            return True
        elif key == '-':  # Volume down
            self._change_volume(-5)
            return True
        elif key == 'q':  # Quit
            raise urwid.ExitMainLoop()
        
        # Screen-specific keybindings handled by widgets
        return False
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        from src.misc.enumerations.Song import PlayingStatus
        status = self.interactions.currentPlayingStatus
        if status == PlayingStatus.Playing.value:
            self.interactions.pause()
        else:
            self.interactions.play()
    
    def _change_volume(self, delta):
        """Change volume by delta."""
        current = self.interactions.volume
        new_volume = max(0, min(100, current + delta))
        self.interactions.setVolume(new_volume)
```

#### 1.4 Now Playing Bar (`src/tui/widgets/now_playing.py`)

**Purpose:** Display current song info and playback progress at top of screen.

**Qt Signal Connections:**
- `interactions.songChanged` → update title/artist
- `interactions.durationChanged` → update duration display
- `interactions.playingStatusChanged` → update play/pause icon
- Timer for progress bar updates (every 1s)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ ♪ Song Title - Artist Name              [02:34 / 04:15] │
│ [████████████████░░░░░░░░░░░] ▶ Playing      Vol: 75%  │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
```python
import urwid
from PySide6.QtCore import QTimer

class NowPlayingBar(urwid.WidgetWrap):
    """Top bar showing current song and playback status."""
    
    def __init__(self, interactions):
        self.interactions = interactions
        
        # Text widgets
        self.song_text = urwid.Text("")
        self.progress_text = urwid.Text("")
        self.status_text = urwid.Text("", align='right')
        
        # Layout
        top_line = urwid.Columns([
            ('weight', 2, self.song_text),
            ('pack', self.status_text),
        ])
        bottom_line = self.progress_text
        
        pile = urwid.Pile([top_line, bottom_line])
        box = urwid.LineBox(pile, title="Now Playing")
        
        super().__init__(box)
        
        # Connect Qt signals
        self.interactions.songChanged.connect(self._update_song_info)
        self.interactions.playingStatusChanged.connect(self._update_status)
        self.interactions.durationChanged.connect(self._update_duration)
        
        # Timer for progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        self.timer.start(1000)  # Update every second
        
        # Initial update
        self._update_song_info()
    
    def _update_song_info(self):
        """Update song title and artist."""
        title = self.interactions.currentSongTitle or "No song playing"
        artist = self.interactions.currentSongChannel or ""
        
        if artist:
            text = f"♪ {title} - {artist}"
        else:
            text = f"♪ {title}"
        
        self.song_text.set_text(text)
        self._update_progress()
    
    def _update_status(self):
        """Update playing status icon."""
        from src.misc.enumerations.Song import PlayingStatus
        status = self.interactions.currentPlayingStatus
        
        if status == PlayingStatus.Playing.value:
            icon = "▶ Playing"
        elif status == PlayingStatus.Paused.value:
            icon = "⏸ Paused"
        else:
            icon = "⏹ Stopped"
        
        volume = self.interactions.volume
        text = f"{icon}      Vol: {volume}%"
        self.status_text.set_text(text)
    
    def _update_duration(self):
        """Update duration display."""
        self._update_progress()
    
    def _update_progress(self):
        """Update progress bar and time."""
        current = self.interactions.currentSongTime
        duration = self.interactions.currentSongDuration
        
        if duration > 0:
            percentage = current / duration
            bar_width = 40
            filled = int(bar_width * percentage)
            bar = "█" * filled + "░" * (bar_width - filled)
            time_str = f"[{self._format_time(current)} / {self._format_time(duration)}]"
            self.progress_text.set_text(f"[{bar}] {time_str}")
        else:
            self.progress_text.set_text("")
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
```

#### 1.5 Queue List Widget (`src/tui/widgets/queue_list.py`)

**Purpose:** Display QueueModel as scrollable list. Highlight current playing song.

**Qt Signal Connections:**
- `queueModel.dataChanged` → refresh list
- `queueModel.rowsInserted` → refresh list
- `queueModel.rowsRemoved` → refresh list
- `interactions.songChanged` → update highlight

**Layout:**
```
┌─ Queue (12 songs) ─────────────────────────────────────┐
│ ► 01. Current Song - Artist 1                [03:45]   │
│   02. Next Song - Artist 2                   [04:12]   │
│   03. Another Song - Artist 3                [03:28]   │
│   04. Fourth Song - Artist 4                 [02:58]   │
│   ...                                                   │
└────────────────────────────────────────────────────────┘
```

**Implementation:**
```python
import urwid
from PySide6.QtCore import Qt

class QueueListWidget(urwid.WidgetWrap):
    """Display queue as scrollable list."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.queue_model = interactions.queueModel_
        
        # List walker for dynamic content
        self.list_walker = urwid.SimpleFocusListWalker([])
        self.list_box = urwid.ListBox(self.list_walker)
        
        box = urwid.LineBox(self.list_box, title="Queue")
        super().__init__(box)
        
        # Connect Qt signals
        self.queue_model.dataChanged.connect(self._refresh_list)
        self.queue_model.rowsInserted.connect(self._refresh_list)
        self.queue_model.rowsRemoved.connect(self._refresh_list)
        self.queue_model.modelReset.connect(self._refresh_list)
        self.interactions.songChanged.connect(self._update_highlight)
        
        # Initial population
        self._refresh_list()
    
    def _refresh_list(self):
        """Rebuild list from QueueModel."""
        self.list_walker.clear()
        
        count = self.queue_model.rowCount()
        current_index = self._get_current_song_index()
        
        for i in range(count):
            index = self.queue_model.index(i, 0)
            
            # Get data from model (using role names)
            title = self.queue_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            duration = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 2) or 0
            
            # Format line
            is_current = (i == current_index)
            prefix = "►" if is_current else " "
            time_str = self._format_time(duration)
            line = f"{prefix} {i+1:02d}. {title} - {artist}"
            line = line.ljust(60) + f"[{time_str}]"
            
            # Create text widget with appropriate style
            attr = 'queue_current' if is_current else 'queue_item'
            text = urwid.Text((attr, line))
            item = urwid.AttrMap(text, None, focus_map='queue_focus')
            
            self.list_walker.append(item)
        
        # Update title
        title = f"Queue ({count} songs)"
        self._w.set_title(title)
    
    def _update_highlight(self):
        """Update which item is highlighted as current."""
        self._refresh_list()  # Simple approach: full refresh
    
    def _get_current_song_index(self):
        """Get index of currently playing song."""
        try:
            current_id = self.interactions.currentSongId
            if not current_id:
                return -1
            
            # Find in model
            for i in range(self.queue_model.rowCount()):
                index = self.queue_model.index(i, 0)
                song_id = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 4)
                if song_id == current_id:
                    return i
        except Exception:
            pass
        return -1
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
    
    def keypress(self, size, key):
        """Handle queue-specific keys."""
        # Let list handle navigation (up/down)
        return super().keypress(size, key)
```

#### 1.6 Status Bar (`src/tui/widgets/status_bar.py`)

**Purpose:** Show keybinding help at bottom of screen.

**Layout:**
```
[Space] Play/Pause  [N] Next  [P] Prev  [+/-] Volume  [Q] Quit
```

**Implementation:**
```python
import urwid

class StatusBar(urwid.WidgetWrap):
    """Bottom status bar with keybinding hints."""
    
    def __init__(self):
        text = urwid.Text([
            ('key', '[Space]'), ' Play/Pause  ',
            ('key', '[N]'), ' Next  ',
            ('key', '[P]'), ' Prev  ',
            ('key', '[+/-]'), ' Volume  ',
            ('key', '[Q]'), ' Quit'
        ])
        
        attr = urwid.AttrMap(text, 'status')
        super().__init__(attr)
    
    def set_help(self, text):
        """Update help text (for context-specific hints)."""
        self._w.original_widget.set_text(text)
```

#### 1.7 Theme/Palette (`src/tui/theme.py`)

**Purpose:** Define urwid color palette.

**Implementation:**
```python
# Base 16-color palette (works in all terminals)
TUI_PALETTE = [
    # (name, foreground, background, mono, fg_high, bg_high)
    ('body', 'default', 'default'),
    ('header', 'white,bold', 'dark blue'),
    ('footer', 'white', 'dark blue'),
    
    # Queue list
    ('queue_item', 'default', 'default'),
    ('queue_current', 'yellow,bold', 'default'),
    ('queue_focus', 'black', 'yellow'),
    
    # Status bar
    ('status', 'black', 'light gray'),
    ('key', 'black,bold', 'light gray'),
    
    # Now playing
    ('playing', 'light green', 'default'),
    ('paused', 'yellow', 'default'),
    ('stopped', 'light red', 'default'),
]

# Extended 256-color palette (if terminal supports it)
TUI_PALETTE_256 = [
    # Material You-inspired colors
    ('body', 'default', 'default'),
    ('header', '#e8eaed', '#1f1f1f'),
    ('footer', '#e8eaed', '#1f1f1f'),
    
    ('queue_item', '#e8eaed', 'default'),
    ('queue_current', '#8ab4f8', 'default', 'bold'),
    ('queue_focus', '#1f1f1f', '#8ab4f8'),
    
    ('status', '#1f1f1f', '#9aa0a6'),
    ('key', '#1f1f1f', '#9aa0a6', 'bold'),
]
```

### Phase 1 Implementation Order

1. **Day 1: Event Loop Foundation**
   - Create `src/tui/qt_event_loop.py`
   - Create `src/tui/main.py` with minimal setup
   - Test that Qt signals work in urwid loop
   - Verify queue signals fire and can be captured

2. **Day 2: Basic Layout**
   - Create `src/tui/theme.py` with palette
   - Create `src/tui/widgets/status_bar.py`
   - Create `src/tui/widgets/now_playing.py` (static version)
   - Create `src/tui/app.py` with layout
   - Test rendering (no dynamic updates yet)

3. **Day 3: Queue Display**
   - Create `src/tui/widgets/queue_list.py`
   - Connect to QueueModel signals
   - Test list updates when queue changes
   - Add current song highlighting

4. **Day 4: Now Playing Updates**
   - Hook up signal handlers in `now_playing.py`
   - Add progress bar updates
   - Test real-time updates during playback

5. **Day 5: Playback Controls**
   - Implement keybindings in `app.py`
   - Connect to Interactions methods
   - Test play/pause/next/prev
   - Test volume control

6. **Day 6: Polish & Testing**
   - Fix rendering issues
   - Handle edge cases (empty queue, no song)
   - Test signal disconnection on exit
   - Verify cleanup works

### Phase 1 Testing Strategy

**Manual Testing:**
1. Start TUI: `python -m src.tui.main` or `python run.py --tui`
2. Load queue with songs (use existing cache or search)
3. Verify playback controls work
4. Verify display updates in real-time
5. Test edge cases (empty queue, seek, etc.)

**Validation Checklist:**
- [ ] TUI starts without errors
- [ ] Queue displays correctly
- [ ] Current song highlighted
- [ ] Now playing bar updates on song change
- [ ] Progress bar moves during playback
- [ ] Space toggles play/pause
- [ ] N/P skip tracks
- [ ] +/- adjust volume
- [ ] Q quits cleanly
- [ ] No Qt warnings about signals/threads
- [ ] Windows SMTC still works
- [ ] Discord RPC still works

---

## Phase 2: Interaction (Add/Remove/Search)

### Goal
Enable queue manipulation and search functionality. Users can add songs from search, remove from queue, and reorder.

### Phase 2 Components

#### 2.1 Screen Manager (`src/tui/screens/base_screen.py`)

**Purpose:** Base class for screens and screen switching logic.

**Implementation:**
```python
import urwid

class BaseScreen:
    """Base class for TUI screens."""
    
    def __init__(self, app):
        self.app = app
        self.widget = None
    
    def activate(self):
        """Called when screen becomes active."""
        pass
    
    def deactivate(self):
        """Called when screen becomes inactive."""
        pass
    
    def get_widget(self):
        """Return the urwid widget for this screen."""
        return self.widget
    
    def handle_input(self, key):
        """Handle screen-specific input. Return True if handled."""
        return False

class ScreenManager:
    """Manages multiple screens and switching."""
    
    def __init__(self, app):
        self.app = app
        self.screens = {}
        self.current_screen_name = None
        self.current_screen = None
    
    def register_screen(self, name, screen):
        """Register a screen."""
        self.screens[name] = screen
    
    def switch_to(self, name):
        """Switch to named screen."""
        if name not in self.screens:
            return False
        
        if self.current_screen:
            self.current_screen.deactivate()
        
        self.current_screen = self.screens[name]
        self.current_screen_name = name
        self.current_screen.activate()
        
        # Update body widget
        self.app.root_widget.body = self.current_screen.get_widget()
        return True
    
    def get_current(self):
        """Get current screen."""
        return self.current_screen
```

#### 2.2 Tab Bar (`src/tui/widgets/tab_bar.py`)

**Purpose:** Show available screens as tabs, allow switching.

**Layout:**
```
[Queue] [Search] [Settings]
```

**Implementation:**
```python
import urwid

class TabBar(urwid.WidgetWrap):
    """Tab bar for screen switching."""
    
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager
        self.tabs = [
            ('queue', 'Queue'),
            ('search', 'Search'),
            ('settings', 'Settings'),
        ]
        
        self.buttons = []
        widgets = []
        
        for name, label in self.tabs:
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', self._on_tab_click, name)
            self.buttons.append((name, btn))
            
            attr = urwid.AttrMap(btn, 'tab', focus_map='tab_focus')
            widgets.append(('pack', attr))
        
        cols = urwid.Columns(widgets)
        super().__init__(cols)
    
    def _on_tab_click(self, name, button):
        """Handle tab click."""
        self.screen_manager.switch_to(name)
        self._update_active()
    
    def _update_active(self):
        """Update visual state of tabs."""
        active = self.screen_manager.current_screen_name
        for name, btn in self.buttons:
            if name == active:
                btn.set_label(f"[{btn.label}]")
            else:
                btn.set_label(btn.label.strip('[]'))
```

#### 2.3 Queue Screen (`src/tui/screens/queue_screen.py`)

**Purpose:** Queue screen with manipulation capabilities (extends Phase 1 queue list).

**New Features:**
- Delete song (press `d` on focused item)
- Jump to song (press Enter)
- Clear queue (press `D`)

**Implementation:**
```python
import urwid
from PySide6.QtCore import Qt
from src.tui.screens.base_screen import BaseScreen

class QueueScreen(BaseScreen):
    """Queue management screen."""
    
    def __init__(self, app):
        super().__init__(app)
        
        self.queue_model = app.interactions.queueModel_
        self.list_walker = urwid.SimpleFocusListWalker([])
        self.list_box = urwid.ListBox(self.list_walker)
        
        # Store references for deletion
        self.song_ids = []
        
        box = urwid.LineBox(self.list_box, title="Queue")
        self.widget = box
        
        # Connect signals
        self.queue_model.dataChanged.connect(self._refresh_list)
        self.queue_model.rowsInserted.connect(self._refresh_list)
        self.queue_model.rowsRemoved.connect(self._refresh_list)
        self.queue_model.modelReset.connect(self._refresh_list)
        self.app.interactions.songChanged.connect(self._update_highlight)
        
        self._refresh_list()
    
    def handle_input(self, key):
        """Handle queue-specific keys."""
        if key == 'd':  # Delete focused song
            self._delete_focused_song()
            return True
        elif key == 'D':  # Clear queue
            self._clear_queue()
            return True
        elif key == 'enter':  # Jump to song
            self._jump_to_focused_song()
            return True
        return False
    
    def _delete_focused_song(self):
        """Delete the currently focused song."""
        focus_pos = self.list_box.focus_position
        if 0 <= focus_pos < len(self.song_ids):
            # Remove from queue via universal.queueInstance
            from src import universal
            universal.queueInstance.remove(focus_pos)
    
    def _clear_queue(self):
        """Clear entire queue."""
        from src import universal
        universal.queueInstance.clear()
    
    def _jump_to_focused_song(self):
        """Jump playback to focused song."""
        focus_pos = self.list_box.focus_position
        if 0 <= focus_pos < len(self.song_ids):
            from src import universal
            universal.queueInstance.goto(focus_pos)
    
    def _refresh_list(self):
        """Rebuild list from QueueModel."""
        self.list_walker.clear()
        self.song_ids.clear()
        
        count = self.queue_model.rowCount()
        current_index = self._get_current_song_index()
        
        for i in range(count):
            index = self.queue_model.index(i, 0)
            
            title = self.queue_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            duration = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 2) or 0
            song_id = self.queue_model.data(index, Qt.ItemDataRole.UserRole + 4) or ""
            
            self.song_ids.append(song_id)
            
            is_current = (i == current_index)
            prefix = "►" if is_current else " "
            time_str = self._format_time(duration)
            line = f"{prefix} {i+1:02d}. {title} - {artist}"
            line = line.ljust(60) + f"[{time_str}]"
            
            attr = 'queue_current' if is_current else 'queue_item'
            text = urwid.Text((attr, line))
            item = urwid.AttrMap(text, None, focus_map='queue_focus')
            
            self.list_walker.append(item)
        
        title = f"Queue ({count} songs)"
        self.widget.set_title(title)
    
    def _update_highlight(self):
        """Update highlighted item."""
        self._refresh_list()
    
    def _get_current_song_index(self):
        """Get index of currently playing song."""
        try:
            current_id = self.app.interactions.currentSongId
            if not current_id:
                return -1
            
            for i, song_id in enumerate(self.song_ids):
                if song_id == current_id:
                    return i
        except Exception:
            pass
        return -1
    
    @staticmethod
    def _format_time(seconds):
        """Format seconds as MM:SS."""
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"
```

#### 2.4 Search Screen (`src/tui/screens/search_screen.py`)

**Purpose:** Search for songs and add to queue.

**Layout:**
```
┌─ Search ───────────────────────────────────────────────┐
│ Query: [nevergonna give                              ] │
├────────────────────────────────────────────────────────┤
│ Results:                                               │
│   1. Never Gonna Give You Up - Rick Astley   [03:33]  │
│   2. Never Gonna Give - Various Artists      [04:12]  │
│   3. Never Gonna - Cover Band                [03:45]  │
│   ...                                                  │
└────────────────────────────────────────────────────────┘
[Enter] Add to Queue  [Shift+Enter] Add & Play  [Esc] Back
```

**Implementation:**
```python
import urwid
from PySide6.QtCore import Qt
from src.tui.screens.base_screen import BaseScreen

class SearchScreen(BaseScreen):
    """Search for songs."""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Search input
        self.search_edit = urwid.Edit("Query: ")
        urwid.connect_signal(self.search_edit, 'change', self._on_search_change)
        
        # Results list
        self.results_walker = urwid.SimpleFocusListWalker([])
        self.results_list = urwid.ListBox(self.results_walker)
        
        # Layout
        pile = urwid.Pile([
            ('pack', urwid.AttrMap(self.search_edit, 'search_input')),
            urwid.Divider(),
            ('pack', urwid.Text("Results:")),
            self.results_list,
        ])
        
        box = urwid.LineBox(pile, title="Search")
        self.widget = box
        
        # Search model from backend
        self.search_model = app.backend.searchModel
        self.search_model.dataChanged.connect(self._refresh_results)
        self.search_model.rowsInserted.connect(self._refresh_results)
        self.search_model.modelReset.connect(self._refresh_results)
        
        # Debounce timer for search
        from PySide6.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.result_ids = []
    
    def activate(self):
        """Focus search input when screen activates."""
        # Set focus to search edit
        pass
    
    def handle_input(self, key):
        """Handle search-specific keys."""
        if key == 'enter':
            self._add_focused_to_queue()
            return True
        elif key == 'shift enter':  # If terminal supports it
            self._add_focused_to_queue(and_play=True)
            return True
        return False
    
    def _on_search_change(self, edit, new_text):
        """Handle search input change (debounced)."""
        self.search_timer.stop()
        self.search_timer.start(500)  # 500ms debounce
    
    def _perform_search(self):
        """Execute search via backend."""
        query = self.search_edit.get_edit_text()
        if query.strip():
            self.app.backend.search(query)
    
    def _refresh_results(self):
        """Refresh results list from search model."""
        self.results_walker.clear()
        self.result_ids.clear()
        
        count = self.search_model.rowCount()
        
        for i in range(count):
            index = self.search_model.index(i, 0)
            
            # Get search result data (roles may differ from queue)
            title = self.search_model.data(index, Qt.ItemDataRole.DisplayRole) or "Unknown"
            artist = self.search_model.data(index, Qt.ItemDataRole.UserRole + 1) or "Unknown"
            result_id = self.search_model.data(index, Qt.ItemDataRole.UserRole + 4) or ""
            result_type = self.search_model.data(index, Qt.ItemDataRole.UserRole + 5) or "song"
            
            self.result_ids.append(result_id)
            
            # Format type icon
            type_icon = "♪" if result_type == "song" else "🎵"
            line = f"  {i+1}. {type_icon} {title} - {artist}"
            
            text = urwid.Text(line)
            item = urwid.AttrMap(text, 'search_result', focus_map='search_focus')
            
            self.results_walker.append(item)
    
    def _add_focused_to_queue(self, and_play=False):
        """Add focused result to queue."""
        focus_pos = self.results_list.focus_position
        if 0 <= focus_pos < len(self.result_ids):
            song_id = self.result_ids[focus_pos]
            
            # Add to queue via universal
            from src import universal
            universal.queueInstance.add(song_id, goto=and_play)
            
            # Show feedback (could be modal or status bar message)
            # For now, just log
            import logging
            logging.getLogger("TUI").info(f"Added {song_id} to queue")
```

#### 2.5 Modal Dialog (`src/tui/widgets/modal.py`)

**Purpose:** Generic modal for confirmations, messages, errors.

**Use Cases:**
- Confirm clear queue
- Show error messages
- Display info messages

**Implementation:**
```python
import urwid

class ModalDialog(urwid.WidgetWrap):
    """Modal dialog overlay."""
    
    def __init__(self, title, body, buttons):
        """
        Args:
            title: Dialog title
            body: Dialog body text or widget
            buttons: List of (label, callback) tuples
        """
        if isinstance(body, str):
            body = urwid.Text(body)
        
        button_widgets = []
        for label, callback in buttons:
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', callback)
            button_widgets.append(urwid.AttrMap(btn, 'button', focus_map='button_focus'))
        
        button_row = urwid.GridFlow(button_widgets, 12, 2, 1, 'center')
        
        pile = urwid.Pile([
            body,
            urwid.Divider(),
            button_row,
        ])
        
        box = urwid.LineBox(pile, title=title)
        filler = urwid.Filler(box, valign='middle')
        
        super().__init__(filler)

def show_modal(loop, title, body, buttons):
    """
    Show modal dialog over current screen.
    
    Args:
        loop: urwid MainLoop
        title: Dialog title
        body: Dialog body
        buttons: List of (label, callback)
    """
    original_widget = loop.widget
    
    def close_modal(*args):
        loop.widget = original_widget
    
    # Wrap callbacks to close modal after
    wrapped_buttons = []
    for label, callback in buttons:
        def wrapped_callback(button, original_callback=callback):
            original_callback()
            close_modal()
        wrapped_buttons.append((label, wrapped_callback))
    
    modal = ModalDialog(title, body, wrapped_buttons)
    overlay = urwid.Overlay(
        modal,
        original_widget,
        align='center',
        width=('relative', 60),
        valign='middle',
        height=('relative', 40),
    )
    
    loop.widget = overlay
```

### Phase 2 Updated App Structure

**Modified `src/tui/app.py`:**
```python
import urwid
from src.tui.widgets.now_playing import NowPlayingBar
from src.tui.widgets.tab_bar import TabBar
from src.tui.widgets.status_bar import StatusBar
from src.tui.screens.queue_screen import QueueScreen
from src.tui.screens.search_screen import SearchScreen
from src.tui.screens.base_screen import ScreenManager
from src.tui.theme import TUI_PALETTE

class ClarityTUI:
    """Main TUI application."""
    
    def __init__(self, backend, interactions):
        self.backend = backend
        self.interactions = interactions
        self.palette = TUI_PALETTE
        
        # Create screen manager
        self.screen_manager = ScreenManager(self)
        
        # Register screens
        self.screen_manager.register_screen('queue', QueueScreen(self))
        self.screen_manager.register_screen('search', SearchScreen(self))
        
        # Start with queue screen
        self.screen_manager.switch_to('queue')
        
        # Create widgets
        self.now_playing = NowPlayingBar(interactions)
        self.tab_bar = TabBar(self.screen_manager)
        self.status_bar = StatusBar()
        
        # Layout with tabs
        header = urwid.Pile([
            self.now_playing,
            self.tab_bar,
        ])
        
        # Body comes from screen manager
        self.root_widget = urwid.Frame(
            body=self.screen_manager.get_current().get_widget(),
            header=header,
            footer=self.status_bar
        )
    
    def handle_input(self, key):
        """Global unhandled input handler."""
        # Let current screen handle first
        current_screen = self.screen_manager.get_current()
        if current_screen and current_screen.handle_input(key):
            return True
        
        # Tab switching
        if key == 'tab':
            self._cycle_tabs()
            return True
        elif key == '1':
            self.screen_manager.switch_to('queue')
            return True
        elif key == '2':
            self.screen_manager.switch_to('search')
            return True
        elif key == '/':  # Quick search
            self.screen_manager.switch_to('search')
            return True
        
        # Global keybindings
        if key == ' ':
            self._toggle_playback()
            return True
        elif key == 'n':
            self.interactions.nextSong()
            return True
        elif key == 'p':
            self.interactions.previousSong()
            return True
        elif key in ('+', '='):
            self._change_volume(+5)
            return True
        elif key == '-':
            self._change_volume(-5)
            return True
        elif key == 'q':
            raise urwid.ExitMainLoop()
        
        return False
    
    def _cycle_tabs(self):
        """Switch to next tab."""
        tabs = ['queue', 'search']
        current = self.screen_manager.current_screen_name
        try:
            idx = tabs.index(current)
            next_idx = (idx + 1) % len(tabs)
            self.screen_manager.switch_to(tabs[next_idx])
        except ValueError:
            self.screen_manager.switch_to('queue')
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        from src.misc.enumerations.Song import PlayingStatus
        status = self.interactions.currentPlayingStatus
        if status == PlayingStatus.Playing.value:
            self.interactions.pause()
        else:
            self.interactions.play()
    
    def _change_volume(self, delta):
        """Change volume by delta."""
        current = self.interactions.volume
        new_volume = max(0, min(100, current + delta))
        self.interactions.setVolume(new_volume)
```

### Phase 2 Implementation Order

1. **Day 7: Screen Management**
   - Create `base_screen.py` and `ScreenManager`
   - Create `tab_bar.py`
   - Update `app.py` to use screen manager
   - Test tab switching

2. **Day 8: Queue Manipulation**
   - Convert `queue_list.py` to `queue_screen.py`
   - Add delete functionality
   - Add jump-to functionality
   - Add clear queue with confirmation

3. **Day 9: Search Infrastructure**
   - Create `search_screen.py` with input
   - Connect to Backend.search()
   - Display search results

4. **Day 10: Add to Queue**
   - Implement add-to-queue from search results
   - Add play-now functionality
   - Add feedback (modal or status message)

5. **Day 11: Modal Dialogs**
   - Create `modal.py`
   - Add confirmation dialog for clear queue
   - Add error/info modals

6. **Day 12: Polish**
   - Improve keyboard navigation
   - Update status bar for context-specific help
   - Handle edge cases

### Phase 2 Testing Strategy

**Manual Testing:**
1. Switch between Queue and Search tabs
2. Search for songs, verify results appear
3. Add songs to queue from search
4. Delete songs from queue
5. Clear queue (confirm modal appears)
6. Jump to song in queue
7. Verify all Phase 1 functionality still works

**Validation Checklist:**
- [ ] Tab switching works (Tab key, number keys)
- [ ] Search input accepts text
- [ ] Search executes and shows results
- [ ] Can add songs from search to queue
- [ ] Can delete individual songs from queue
- [ ] Clear queue shows confirmation
- [ ] Jump to song works
- [ ] Status bar shows context-appropriate help
- [ ] All keybindings documented

---

## Run.py Modification

**Add TUI launch flag:**

```python
# At top of run.py after imports
import sys

# Check for TUI mode
if "--tui" in sys.argv:
    import src.universal  # Initialize universal
    from src.tui import main as tui_main
    tui_main.main()
    sys.exit(0)

# Otherwise continue with GUI
import src.universal
from src.app import main
from src.misc.compiled import __compiled__

if __compiled__:
    main.main()
else:
    main.debug()
```

---

## Additional Considerations

### Thread Safety
- All Qt signal handlers automatically run on main thread
- urwid rendering happens on main thread
- Background workers (bgworker, asyncBgworker) still function normally
- No additional thread synchronization needed

### Performance
- Queue refresh: Only happens on Qt signals, not polling
- Progress bar: Updates every 1 second via QTimer
- Search: Debounced 500ms to avoid excessive API calls

### Windows Compatibility
- urwid works on Windows with windows-curses (already in dependencies)
- Qt event loop integration same on all platforms
- SMTC continues to function (queue-driven)

### Debugging
- Use logging instead of print statements
- Log to file: `logging.basicConfig(filename='tui.log', level=logging.DEBUG)`
- Can run with `--debug` flag for verbose logging
- urwid screen can be suspended to view logs: Ctrl+Z (Unix) or debug in file

### Error Handling
- Wrap signal handlers in try/except to prevent crashes
- Display errors in modal dialogs
- Log exceptions with full traceback
- Graceful degradation if models not available

---

## Success Criteria

### Phase 1 Complete When:
- TUI starts without errors
- Queue displays and updates in real-time
- Now playing bar shows current song
- Playback controls work (space, n, p, +/-, q)
- Progress bar updates during playback
- Current song highlighted in queue
- Can navigate queue with arrow keys
- Exits cleanly

### Phase 2 Complete When:
- Can switch between Queue and Search screens
- Search finds songs and displays results
- Can add songs to queue from search
- Can delete songs from queue
- Can jump to songs in queue
- Clear queue with confirmation works
- Status bar shows contextual help
- All keybindings functional and documented

---

## Future Extensions (Beyond Phase 2)

### Phase 3: Settings & Library
- Settings screen with tree navigation
- Edit settings values
- Library browser (saved playlists, liked songs)
- Download manager screen

### Phase 4: Advanced Features
- Command mode (`:play <url>`, `:volume 50`)
- Mouse support (click to jump to song)
- ASCII visualizer
- Song lyrics display
- Playlist management

### Phase 5: Polish
- Material You colors in terminal (if supported)
- Sixel/Kitty protocol thumbnails
- Custom keybinding configuration
- Multiple color themes
- Window resize handling
