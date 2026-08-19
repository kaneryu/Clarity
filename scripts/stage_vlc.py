"""Stages a portable copy of libvlc + plugins for the current platform.

The existing src/app/assets/libs/vlc/ bundle (committed directly to the
repo) is left alone - this writes to sibling vlc-mac/ and vlc-win/
directories instead, meant to be gitignored and regenerated per-machine.

On macOS this copies libvlc/libvlccore and the plugins directory out of
a locally installed VLC.app, rewrites their @rpath dependency to
@loader_path so the copies work outside of VLC.app's own bundle
layout, and re-signs them (ad-hoc) since modifying a signed Mach-O
invalidates its signature and arm64 refuses to load an invalidly
signed binary.

On Windows this copies libvlc.dll, libvlccore.dll, plugins/, and
vlc-cache-gen.exe out of a local VLC install, then runs vlc-cache-gen
once against the copy so the plugin cache is valid at the new path
(plugins.dat otherwise stays tied to the original install location).

Meant to be run after building the app (a Nuitka dist folder has
assets/ next to the executable, instead of the dev tree's
src/app/assets/). Pass --app-path, or leave it blank when prompted to
stage into the dev tree instead:
    python scripts/stage_vlc.py --app-path /path/to/dist/Clarity.exe
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_ASSETS_ROOT = REPO_ROOT / "src" / "app" / "assets"
PLATFORM_DIRNAME = "vlc-mac" if sys.platform.startswith("darwin") else "vlc-win"

RPATH_RE = re.compile(r"^\s*@rpath/(\S+)")


def resolve_assets_root(app_path: Path) -> Path:
    app_dir = app_path if app_path.is_dir() else app_path.parent
    assets_root = app_dir / "assets"
    if not assets_root.is_dir():
        raise SystemExit(
            f"No assets/ folder found at {assets_root} - is {app_path} the right build output?"
        )
    return assets_root


def find_vlc_app() -> Path:
    env_override = os.environ.get("VLC_APP_PATH")
    if env_override:
        return Path(env_override)

    candidates = [
        Path("/Applications/VLC.app"),
        Path.home() / "Applications" / "VLC.app",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    try:
        result = subprocess.run(
            ["mdfind", "kMDItemCFBundleIdentifier == 'org.videolan.vlc'"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            path = Path(line.strip())
            if path.exists():
                return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise SystemExit(
        "Could not find VLC.app. Install it (`brew install --cask vlc`) or "
        "set VLC_APP_PATH to point at it."
    )


def fix_dependencies(dylib: Path, lib_dest: Path) -> None:
    otool = subprocess.run(
        ["otool", "-L", str(dylib)], capture_output=True, text=True, check=True
    )

    changed = False
    for line in otool.stdout.splitlines()[1:]:
        match = RPATH_RE.match(line)
        if not match:
            continue
        dep_name = match.group(1)
        rel_prefix = os.path.relpath(lib_dest, dylib.parent)
        new_path = f"@loader_path/{rel_prefix}/{dep_name}".replace("/./", "/")
        subprocess.run(
            ["install_name_tool", "-change", f"@rpath/{dep_name}", new_path, str(dylib)],
            check=True,
        )
        changed = True

    if changed:
        subprocess.run(["codesign", "--force", "--sign", "-", str(dylib)], check=True)


def stage_mac(dest: Path, vlc_app: Path) -> None:
    lib_src = vlc_app / "Contents" / "MacOS" / "lib"
    plugins_src = vlc_app / "Contents" / "MacOS" / "plugins"
    if not lib_src.exists() or not plugins_src.exists():
        raise SystemExit(f"{vlc_app} doesn't look like a VLC.app bundle (missing lib/ or plugins/)")

    if dest.exists():
        shutil.rmtree(dest)
    lib_dest = dest / "lib"
    plugins_dest = dest / "plugins"

    shutil.copytree(lib_src, lib_dest, symlinks=True)
    shutil.copytree(plugins_src, plugins_dest, symlinks=True)

    real_dylibs = [
        p for p in list(lib_dest.iterdir()) + list(plugins_dest.rglob("*.dylib"))
        if p.is_file() and not p.is_symlink()
    ]
    for dylib in real_dylibs:
        fix_dependencies(dylib, lib_dest)

    print(f"Staged VLC ({vlc_app}) -> {dest}")
    print(f"  lib:     {lib_dest} ({len(list(lib_dest.iterdir()))} files)")
    print(f"  plugins: {plugins_dest} ({len(list(plugins_dest.glob('*.dylib')))} plugins)")


def find_vlc_install() -> Path:
    env_override = os.environ.get("VLC_INSTALL_PATH")
    if env_override:
        return Path(env_override)

    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "VideoLAN" / "VLC",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "VideoLAN" / "VLC",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    try:
        import winreg

        for subkey in (r"SOFTWARE\VideoLAN\VLC", r"SOFTWARE\WOW6432Node\VideoLAN\VLC"):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as key:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                    path = Path(install_dir)
                    if path.exists():
                        return path
            except OSError:
                continue
    except ImportError:
        pass

    raise SystemExit(
        "Could not find a VLC install. Install it from https://www.videolan.org/vlc/ "
        "or set VLC_INSTALL_PATH to point at the install directory."
    )


def stage_windows(dest: Path, vlc_install: Path) -> None:
    required = ["libvlc.dll", "libvlccore.dll", "plugins", "vlc-cache-gen.exe"]
    missing = [name for name in required if not (vlc_install / name).exists()]
    if missing:
        raise SystemExit(f"{vlc_install} is missing expected files: {', '.join(missing)}")

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for name in ("libvlc.dll", "libvlccore.dll", "vlc-cache-gen.exe"):
        shutil.copy2(vlc_install / name, dest / name)
    plugins_dest = dest / "plugins"
    shutil.copytree(vlc_install / "plugins", plugins_dest)

    try:
        subprocess.run(
            [str(dest / "vlc-cache-gen.exe"), str(plugins_dest)],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"warning: vlc-cache-gen failed against the staged copy: {e}")

    print(f"Staged VLC ({vlc_install}) -> {dest}")
    print(f"  plugins: {plugins_dest} ({len(list(plugins_dest.rglob('*.dll')))} plugins)")


def main() -> None:
    dev_dest = DEV_ASSETS_ROOT / "libs" / PLATFORM_DIRNAME

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app-path",
        type=Path,
        default=None,
        help="Path to the built app's executable (or its containing folder); "
        "stages into <that folder>/assets/libs/" + PLATFORM_DIRNAME,
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Exact directory to stage into, overriding --app-path and the prompt",
    )
    args = parser.parse_args()

    if args.dest is not None:
        dest = args.dest
    else:
        app_path = args.app_path
        if app_path is None:
            entered = input(
                "Path to the built app's executable "
                f"(blank to stage into the dev tree at {dev_dest}): "
            ).strip()
            app_path = Path(entered).expanduser() if entered else None

        dest = resolve_assets_root(app_path) / "libs" / PLATFORM_DIRNAME if app_path else dev_dest

    if sys.platform.startswith("darwin"):
        stage_mac(dest, find_vlc_app())
    elif sys.platform.startswith("win"):
        stage_windows(dest, find_vlc_install())
    else:
        raise SystemExit(f"No VLC staging logic for platform: {sys.platform}")


if __name__ == "__main__":
    main()
