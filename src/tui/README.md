# Clarity Terminal UI (TUI)

## Overview

The Terminal UI is a text-based interface for Clarity that demonstrates the application's UI-agnostic architecture. It reuses the same backend classes (Backend, Interactions, Queue) as the QML GUI, proving that the core logic is completely separated from the presentation layer.

## Features

### Phase 1: Basic Playback (✓ Implemented)
- Display queue as a scrollable list
- Show now playing info with song title, artist, and playback status
- Display progress bar updating in real-time during playback
- Control playback with keyboard shortcuts:
  - `Space` - Toggle play/pause
  - `N` - Next track
  - `P` - Previous track
  - `Q` - Quit application
- Navigate queue with arrow keys
- Current song highlighted in the queue

### Phase 2: Interaction (✓ Implemented)
- Multi-screen support (Queue and Search screens)
- Tab switching:
  - `Tab` - Cycle between screens
  - `1` - Switch to Queue screen
  - `2` - Switch to Search screen
  - `/` - Quick jump to Search
- **Queue Screen:**
  - `D` - Delete focused song from queue
  - `Shift+D` - Clear entire queue
  - `Enter` - Jump playback to focused song
- **Search Screen:**
  - Type to search for songs (with 500ms debounce)
  - `Enter` - Add focused result to queue
  - Results display with song/album icons

## Usage

### Starting the TUI

```bash
python run.py --tui
```

Or directly:

```bash
python -m src.tui.main
```

### Keyboard Controls

**Global (work in any screen):**
- `Space` - Toggle play/pause
- `N` - Next track
- `P` - Previous track
- `Tab` - Switch between screens
- `1` - Queue screen
- `2` - Search screen
- `/` - Quick search
- `Q` - Quit

**Queue Screen:**
- `↑/↓` - Navigate queue
- `Enter` - Jump to song
- `D` - Delete focused song
- `Shift+D` - Clear queue

**Search Screen:**
- Type in search box to search
- `↑/↓` - Navigate results
- `Enter` - Add to queue

## Architecture

### Key Components

```
src/tui/
├── __init__.py              # Package init
├── main.py                  # TUI entry point
├── app.py                   # Main application container
├── qt_event_loop.py         # Qt + urwid event loop integration
├── theme.py                 # Terminal color palette
├── screens/
│   ├── base_screen.py       # Base screen class and ScreenManager
│   ├── queue_screen.py      # Queue management screen
│   └── search_screen.py     # Search screen
└── widgets/
    ├── now_playing.py       # Now playing bar with progress
    ├── queue_list.py        # Queue list widget (Phase 1)
    ├── status_bar.py        # Status bar with keybindings
    ├── tab_bar.py           # Tab bar for screen switching
    └── modal.py             # Modal dialog system
```

### Integration with Existing Backend

The TUI connects to the same backend components as the QML GUI:

- **Backend** (`src.app.Backend`): Provides search functionality and settings
- **Interactions** (`src.app.Interactions`): Exposes playback controls and queue access
- **QueueModel**: Qt model for queue data, rendered as terminal list
- **SearchModel**: Qt model for search results
- **Qt Signals**: All updates flow through Qt signals that the TUI subscribes to

### Event Loop Integration

The TUI uses a custom `QtUrwidEventLoop` that bridges urwid's terminal event loop with Qt's event loop. This allows:
- Qt signals to work properly
- Real-time updates from the queue
- Background workers to function normally
- Windows SMTC and Discord RPC integrations to remain active

## Design Principles

1. **Zero Backend Duplication** - TUI consumes the same classes as QML
2. **Qt Signal-Driven** - All updates flow through Qt signals
3. **Model Reuse** - QueueModel and SearchModel rendered to terminal
4. **Separation of Concerns** - TUI is pure presentation layer

## Technical Details

### Dependencies
- `urwid` - Terminal UI framework
- `PySide6` - Qt bindings for Python
- All existing Clarity dependencies

### Color Palette
- Basic 16-color palette for universal terminal support
- Extended 256-color palette for modern terminals (Material You inspired)

### Thread Safety
- All Qt signal handlers run on the main thread automatically
- urwid rendering happens on the main thread
- Background workers continue to function normally

## Future Enhancements (Not Yet Implemented)

### Phase 3: Settings & Library
- Settings screen with tree navigation
- Edit settings values
- Library browser
- Download manager screen

### Phase 4: Advanced Features
- Command mode (`:play <url>`, `:volume 50`)
- Mouse support
- ASCII visualizer
- Song lyrics display
- Playlist management

### Phase 5: Polish
- Material You colors in terminal
- Sixel/Kitty protocol for thumbnails
- Custom keybinding configuration
- Multiple color themes
- Window resize handling

## Known Issues

- Volume control not yet implemented in the backend
- Modal confirmations not yet wired up (clear queue confirmation)
- Some terminal emulators may not display Unicode symbols correctly
- Requires Python 3.12+ (project requirement)

## Testing

The TUI has been implemented according to the specification in `TERMINAL_UI_PLAN.md`. Manual testing is recommended to verify:

1. TUI starts without errors
2. Queue displays correctly
3. Current song highlighted
4. Now playing bar updates on song change
5. Progress bar moves during playback
6. Space toggles play/pause
7. N/P skip tracks
8. Tab switches screens
9. Search finds songs
10. Can add songs to queue
11. Can delete songs from queue
12. Q quits cleanly

## Contributing

When adding new features to the TUI:
1. Follow the existing architecture patterns
2. Reuse backend components - never duplicate logic
3. Subscribe to Qt signals for updates
4. Keep the presentation layer thin
5. Test across different terminal emulators

## License

Same as Clarity - GNU GPL v3
