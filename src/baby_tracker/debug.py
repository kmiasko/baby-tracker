"""BABY_TRACKER_DEBUG tracing for the detector. A no-op unless BABY_TRACKER_DEBUG is set."""

import os


def enabled():
    return bool(os.environ.get("BABY_TRACKER_DEBUG"))


def autocal(msg):
    if enabled():
        print("autocal:", msg)
