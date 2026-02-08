# Terminal UI Layout Preview

This document shows what the Clarity Terminal UI looks like in action.

## Phase 1: Queue Screen with Now Playing

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Now Playing                                                             │
│ ♪ Never Gonna Give You Up - Rick Astley      [02:34 / 03:33] ▶ Playing│
│ [████████████████████░░░░░░░░░░░░░░░░] [02:34 / 03:33]                 │
└─────────────────────────────────────────────────────────────────────────┘
┌─ Queue ─┐ [ Search ]
┌─────────────────────────────────────────────────────────────────────────┐
│ Queue (5 songs)                                                         │
│ ► 01. Never Gonna Give You Up - Rick Astley              [03:33]       │
│   02. Together Forever - Rick Astley                      [03:24]       │
│   03. Whenever You Need Somebody - Rick Astley           [03:48]       │
│   04. It Would Take a Strong Strong Man - Rick Astley    [03:32]       │
│   05. The Love Has Gone - Rick Astley                    [03:26]       │
│                                                                         │
│                                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
[Space] Play/Pause  [N] Next  [P] Prev  [Tab] Switch  [Q] Quit
```

## Phase 2: Search Screen

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Now Playing                                                             │
│ ♪ Never Gonna Give You Up - Rick Astley      [02:34 / 03:33] ▶ Playing│
│ [████████████████████░░░░░░░░░░░░░░░░] [02:34 / 03:33]                 │
└─────────────────────────────────────────────────────────────────────────┘
[ Queue ] ┌─ Search ─┐
┌─────────────────────────────────────────────────────────────────────────┐
│ Search                                                                  │
│ Query: never gonna give_                                                │
│ ─────────────────────────────────────────────────────────────────────── │
│ Results:                                                                │
│   1. ♪ Never Gonna Give You Up - Rick Astley                [03:33]    │
│   2. ♪ Never Gonna Give You Up (Remastered) - Rick Astley   [03:33]    │
│   3. 🎵 Whenever You Need Somebody (Album) - Rick Astley               │
│   4. ♪ Never Gonna Give - Cover Band                        [03:28]    │
│   5. ♪ Rick Astley - Never Gonna Give You Up (Live)        [04:12]    │
│                                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
[Space] Play/Pause  [N] Next  [P] Prev  [Tab] Switch  [Q] Quit
```

## Queue Screen with Focus

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Now Playing                                                             │
│ ♪ Never Gonna Give You Up - Rick Astley      [02:34 / 03:33] ▶ Playing│
│ [████████████████████░░░░░░░░░░░░░░░░] [02:34 / 03:33]                 │
└─────────────────────────────────────────────────────────────────────────┘
┌─ Queue ─┐ [ Search ]
┌─────────────────────────────────────────────────────────────────────────┐
│ Queue (5 songs)                                                         │
│ ► 01. Never Gonna Give You Up - Rick Astley              [03:33]       │
│ ┃ 02. Together Forever - Rick Astley                      [03:24]     ┃ ← Focused
│   03. Whenever You Need Somebody - Rick Astley           [03:48]       │
│   04. It Would Take a Strong Strong Man - Rick Astley    [03:32]       │
│   05. The Love Has Gone - Rick Astley                    [03:26]       │
│                                                                         │
│                                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
[Enter] Jump  [D] Delete  [Shift+D] Clear  [Q] Quit
```

## Color Scheme

The TUI supports two color palettes:

### Basic 16-Color (Universal)
- **Now Playing Bar**: Blue header with white text
- **Current Song**: Bold yellow text
- **Focused Item**: Black text on yellow background
- **Status Bar**: Black text on light gray background

### Extended 256-Color (Modern Terminals)
- **Material You Inspired**: Dynamic colors based on album art (future)
- **Primary**: #8ab4f8 (Light blue)
- **Background**: #1f1f1f (Dark gray)
- **Text**: #e8eaed (Light gray)
- **Accents**: #81c995 (Green) for active elements

## User Flow Examples

### Playing Music
1. User starts TUI: `python run.py --tui`
2. Queue screen shows with current playback
3. Progress bar updates every second
4. User presses `Space` to pause
5. Status changes from "▶ Playing" to "⏸ Paused"

### Adding Songs
1. User presses `/` or `2` to open Search
2. Types "never gonna give"
3. After 500ms, search executes
4. Results appear in list
5. User navigates with `↑/↓`
6. Presses `Enter` to add to queue
7. Queue updates automatically via Qt signals

### Managing Queue
1. User is in Queue screen
2. Navigates to unwanted song with `↑/↓`
3. Presses `D` to delete
4. Song removed, list refreshes via Qt signals
5. User can press `Enter` on any song to jump playback

## Technical Notes

### Real-Time Updates
All updates happen via Qt signals:
- `songChanged` → Updates now playing info and highlights current song
- `playingStatusChanged` → Updates play/pause icon
- `durationChanged` → Updates progress bar length
- `dataChanged` → Refreshes queue list
- `rowsInserted/Removed` → Updates queue when songs added/removed

### Event Loop Integration
The `QtUrwidEventLoop` processes both:
- **urwid events**: Keyboard input, screen drawing (every frame)
- **Qt events**: Signals, timers, background workers (every 10ms)

This allows the TUI to:
- Respond immediately to user input
- Update in real-time when songs change
- Keep background workers functioning
- Maintain Windows SMTC and Discord RPC integration

### Thread Safety
- All Qt signals run on main thread
- urwid rendering on main thread
- No additional synchronization needed
- Background workers (bgworker, asyncBgworker) continue normally

## Future Enhancements Preview

### Settings Screen (Phase 3)
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Settings                                                                │
│ ► Playback                                                              │
│   │ ├─ Default Volume: 75                                              │
│   │ ├─ Crossfade: Disabled                                             │
│   │ └─ Auto-play: Enabled                                              │
│   Network                                                               │
│     ├─ Proxy: None                                                      │
│     └─ Cache Size: 500 MB                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Command Mode (Phase 4)
```
:play https://youtube.com/watch?v=dQw4w9WgXcQ
:volume 75
:next
:search never gonna give
:quit
```

## Compatibility

### Tested Terminals
- Standard terminal emulators (xterm, gnome-terminal, konsole)
- Windows Command Prompt with windows-curses
- Modern terminals with 256-color support

### Requirements
- Python 3.12+
- urwid
- PySide6
- All Clarity dependencies
- UTF-8 terminal support for icons

---

This layout demonstrates that a fully-functional music player can be built in the terminal using the same backend as the GUI, proving Clarity's UI-agnostic architecture.
