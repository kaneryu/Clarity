import asyncio
import winrt.windows.media.control as wmctrl
import winrt.windows.media.playback as wmp
import winrt.windows.media as wmedia
import winrt.windows.storage.streams as wss
import winrt.windows.foundation as wf
from datetime import datetime, timezone, timedelta

async def main():
    mgr = await wmctrl.GlobalSystemMediaTransportControlsSessionManager.request_async()
    session = mgr.get_current_session()
    if session is None:
        print("No active media session.")
        return

    props = await session.try_get_media_properties_async()
    if not props:
        print("Failed to get media properties.")
        return
    title = props.title or ""
    artist = props.artist or ""
    album = props.album_title or ""
    print(f"Now playing: {title} — {artist} ({album})")

if __name__ == "__main__":
    asyncio.run(main())

# --- SMTC publishing (create your own session) ---
_player: wmp.MediaPlayer | None = None

def _get_player():
    global _player
    if _player is None:
        _player = wmp.MediaPlayer()
        smtc = _player.system_media_transport_controls
        smtc.is_enabled = True
        smtc.is_play_enabled = True
        smtc.is_pause_enabled = True
        smtc.is_stop_enabled = True
    return _player


def set_now_playing(title: str = "", artist: str = "", album_title: str = "", art_uri: str | None = None) -> None:
    """Publish metadata for your own app's SMTC session. art_uri can be an http(s) or file URI."""
    p = _get_player()
    
    smtc = p.system_media_transport_controls
    du = smtc.display_updater
    du.type = wmedia.MediaPlaybackType.MUSIC
    music = du.music_properties
    music.title = title or ""
    music.artist = artist or ""
    music.album_title = album_title or ""
    if art_uri:
        du.thumbnail = wss.RandomAccessStreamReference.create_from_uri(wf.Uri(art_uri))
    du.update()
    smtc.playback_status = wmedia.MediaPlaybackStatus.PLAYING


def set_album_art_file(path: str) -> None:
    """Set album art from a local file path."""
    from pathlib import Path
    p = _get_player()
    du = p.system_media_transport_controls.display_updater
    file_uri = wf.Uri(Path(path).resolve().as_uri())
    du.thumbnail = wss.RandomAccessStreamReference.create_from_uri(file_uri)
    du.update()


def playback_play() -> None:
    _get_player().system_media_transport_controls.playback_status = wmedia.MediaPlaybackStatus.PLAYING


def playback_pause() -> None:
    _get_player().system_media_transport_controls.playback_status = wmedia.MediaPlaybackStatus.PAUSED


def playback_stop() -> None:
    _get_player().system_media_transport_controls.playback_status = wmedia.MediaPlaybackStatus.STOPPED


def clear_now_playing() -> None:
    p = _get_player()
    du = p.system_media_transport_controls.display_updater
    du.clear_all()
    du.update()


# --- Extra SMTC publisher helpers (your own session) ---

def set_transport_capabilities(*, play=True, pause=True, stop=True, next=False, previous=False, seek=True, fast_forward=False, rewind=False) -> None:
    smtc = _get_player().system_media_transport_controls
    smtc.is_enabled = True
    smtc.is_play_enabled = bool(play)
    smtc.is_pause_enabled = bool(pause)
    smtc.is_stop_enabled = bool(stop)
    smtc.is_next_enabled = bool(next)
    smtc.is_previous_enabled = bool(previous)
    smtc.is_seek_enabled = bool(seek)
    smtc.is_fast_forward_enabled = bool(fast_forward)
    smtc.is_fast_rewind_enabled = bool(rewind)


def update_timeline(duration_s: float | None = None, position_s: float | None = None, *, min_seek_s: float = 0.0, max_seek_s: float | None = None) -> None:
    """Report timeline to SMTC so the OS shows duration/position. Call whenever things change."""
    smtc = _get_player().system_media_transport_controls
    tl = wmedia.SystemMediaTransportControlsTimelineProperties()
    # Start and min seek
    tl.start_time = timedelta(seconds=0)
    tl.min_seek_time = timedelta(seconds=max(0.0, float(min_seek_s)))
    # End/max seek
    end = timedelta(seconds=float(duration_s)) if duration_s is not None else timedelta(seconds=0)
    tl.end_time = end
    tl.max_seek_time = timedelta(seconds=float(max_seek_s)) if max_seek_s is not None else end
    # Position
    if position_s is not None:
        tl.position = timedelta(seconds=max(0.0, float(position_s)))
    # Stamp update time in UTC
    # tl.last_updated_time = datetime.now(timezone.utc)
    smtc.update_timeline_properties(tl)


# Optional: handle hardware/media key presses for your own session
_button_token = None

def set_button_handler(handler) -> None:
    """Register a callback(sender, args) for SMTC button presses. Replaces any existing handler."""
    global _button_token
    smtc = _get_player().system_media_transport_controls
    if _button_token is not None:
        try:
            smtc.remove_button_pressed(_button_token)
        except Exception:
            pass
        _button_token = None
    _button_token = smtc.add_button_pressed(handler)


# # --- Control other apps' system media sessions ---
# async def _get_session(app_id_substr: str | None = None):
#     mgr = await wmctrl.GlobalSystemMediaTransportControlsSessionManager.request_async()
#     if app_id_substr:
#         for s in mgr.get_sessions():
#             sid = s.source_app_user_model_id or ""
#             if app_id_substr.lower() in sid.lower():
#                 return s
#     return mgr.get_current_session()


# async def system_play(app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_play_async()


# async def system_pause(app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_pause_async()


# async def system_stop(app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_stop_async()


# async def system_next(app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_skip_next_async()


# async def system_previous(app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_skip_previous_async()


# async def system_set_position(seconds: float, app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_change_playback_position_async(timedelta(seconds=float(seconds)))


# async def system_set_shuffle(enabled: bool, app_id: str | None = None):
#     s = await _get_session(app_id)
#     if s:
#         await s.try_change_shuffle_active_async(bool(enabled))


# async def system_set_repeat(mode: str, app_id: str | None = None):
#     """mode: 'none' | 'track' | 'list'"""
#     s = await _get_session(app_id)
#     if not s:
#         return
#     m = (mode or "none").lower()
#     if m == "track":
#         val = wmctrl.GlobalSystemMediaTransportControlsSessionPlaybackAutoRepeatMode.track
#     elif m == "list":
#         val = wmctrl.GlobalSystemMediaTransportControlsSessionPlaybackAutoRepeatMode.list
#     else:
#         val = wmctrl.GlobalSystemMediaTransportControlsSessionPlaybackAutoRepeatMode.none
#     await s.try_change_auto_repeat_mode_async(val)