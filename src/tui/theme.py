"""Terminal color theme/palette for Clarity TUI."""

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
    
    # Search
    ('search_input', 'default', 'default'),
    ('search_result', 'default', 'default'),
    ('search_focus', 'black', 'light cyan'),
    
    # Tabs
    ('tab', 'default', 'default'),
    ('tab_focus', 'black', 'light cyan'),
    
    # Modal/Button
    ('button', 'default', 'default'),
    ('button_focus', 'black', 'light green'),
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
    
    ('search_input', '#e8eaed', 'default'),
    ('search_result', '#e8eaed', 'default'),
    ('search_focus', '#1f1f1f', '#8ab4f8'),
    
    ('tab', '#e8eaed', 'default'),
    ('tab_focus', '#1f1f1f', '#8ab4f8'),
    
    ('button', '#e8eaed', 'default'),
    ('button_focus', '#1f1f1f', '#81c995'),
]
