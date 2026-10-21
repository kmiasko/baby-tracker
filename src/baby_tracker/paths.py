"""Per-user data directory and external tool lookup."""

import os
import shutil


def home():
    """~/.baby-tracker (C:\\Users\\<you>\\.baby-tracker on Windows); BABY_TRACKER_HOME overrides."""
    return os.environ.get("BABY_TRACKER_HOME") or os.path.join(
        os.path.expanduser("~"), ".baby-tracker"
    )


def path(name):
    return os.path.join(home(), name)


def require_tool(name):
    """Full path of an ffmpeg-suite binary, or exit with install instructions."""
    found = shutil.which(name)
    if found:
        return found
    hint = (
        "winget install Gyan.FFmpeg   (then reopen the terminal)"
        if os.name == "nt"
        else "install the ffmpeg package (e.g. apt/pacman/brew install ffmpeg)"
    )
    raise SystemExit("%s not found on PATH; %s" % (name, hint))
