"""Modal dialog widget for confirmations and messages."""
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
