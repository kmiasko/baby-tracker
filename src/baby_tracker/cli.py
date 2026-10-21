#!/usr/bin/env python3
"""baby-tracker command dispatch. (Detection: tracker.py. Self-calibration: autocal.py. Alerts: notify.py.)

Commands:
  baby-tracker monitor --input SRC [--record DIR]
                            track a live source (.sdp file, rtsp:// or udp:// URL, device) until Ctrl-C and
                            notify when the baby is awake; --record also saves 10-minute .mkv segments.
                            A plain video file is replayed once instead.
  baby-tracker calibrate (--input FILE | --image PNG)
                            click crib ROI + lying line -> ~/.baby-tracker/roi.json
  baby-tracker calibrate --auto --input FILE
                            self-calibrate on a recording and save the discovered ROI
  baby-tracker evaluate --input FILE --wakes T1,T2,... [--tol SEC] [--csv OUT]
                            replay a recording, score awake alerts against labelled wake times (s)
  baby-tracker tune --clip FILE:T1,T2,... [--clip ...] [--tol SEC]
                            fit the self-calibrating detector's knobs on labelled recordings
  baby-tracker train --clip FILE:T1,T2,... [--clip ...] [--tol SEC]
                            fit the optional stage-2 classifier (~/.baby-tracker/classifier.json)
  baby-tracker doctor | selftest
  (needs ffmpeg on PATH; `baby-tracker doctor` checks the installation)
"""

import argparse
import os
import shutil
import sys
import time

from . import paths, tracker


def is_live(source):
    """A plain existing video file is replayed; anything else (.sdp, URL, device) is a live source."""
    return not (os.path.isfile(source) and not source.lower().endswith(".sdp"))


def do_monitor(source, record=None):
    if not is_live(source):
        if record:
            raise SystemExit("--record only works with a live source")
        tracker.run_file(source)
        return
    paths.require_tool("ffmpeg")
    live = tracker.LiveTracker(source, record, True)
    try:
        while live.thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        live.stop()


def selftest():
    """Run the repo's pytest suite when pytest and tests/ are available (a source checkout)."""
    tests = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "tests")
    try:
        import pytest
    except ImportError:
        pytest = None
    if pytest is None or not os.path.isdir(tests):
        print("selftest skipped: needs pytest and the source checkout's tests/")
        return
    code = pytest.main(["-q", os.path.normpath(tests)])
    if code:
        raise SystemExit(code)
    print("selftest ok")


def doctor():
    """Report what is installed; returns the process exit code."""
    import importlib

    from . import classifier, notify, seed

    ok = True
    found = shutil.which("ffmpeg")
    print("%-8s %s" % ("ffmpeg", found or "MISSING (needed for monitor)"))
    ok &= bool(found)
    for mod in ("numpy", "cv2"):
        try:
            importlib.import_module(mod)
            print("%-8s ok" % mod)
        except ImportError as e:
            print("%-8s MISSING (%s)" % (mod, e))
            ok = False
    try:
        cfg = tracker.load_config()
    except SystemExit:  # a broken roi.json is not doctor's business
        cfg = tracker.DEFAULTS
    sp, cp = seed.model_path(cfg), classifier.model_path(cfg)
    print(
        "seed     %s"
        % (
            "off"
            if sp is None
            else sp + (" ok" if os.path.isfile(sp) else " (downloaded on first use)")
        )
    )
    print(
        "classif  %s"
        % (
            "off"
            if cp is None
            else cp
            + (
                " ok"
                if os.path.isfile(cp)
                else " (none: rules; `baby-tracker train` makes one)"
            )
        )
    )
    print("notify   %s" % (notify.backend() or "none (messages are only logged)"))
    print("data dir %s" % paths.home())
    return 0 if ok else 1


def parser():
    p = argparse.ArgumentParser(prog="baby-tracker", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("monitor", help="track a live source or replay a file")
    m.add_argument("--input", required=True, metavar="SRC")
    m.add_argument("--record", metavar="DIR")
    c = sub.add_parser("calibrate", help="draw the crib ROI by hand or self-calibrate")
    c.add_argument("--input", metavar="FILE")
    c.add_argument("--image", metavar="PNG")
    c.add_argument("--auto", action="store_true")
    e = sub.add_parser("evaluate", help="score alerts on a labelled recording")
    e.add_argument("--input", required=True, metavar="FILE")
    e.add_argument("--wakes", required=True, metavar="T1,T2,...")
    e.add_argument("--tol", type=float, default=30.0)
    e.add_argument("--csv", metavar="OUT")
    for name, hlp in (("tune", "fit detector knobs"), ("train", "fit the classifier")):
        t = sub.add_parser(name, help=hlp)
        t.add_argument("--clip", action="append", required=True, metavar="FILE:T1,T2")
        t.add_argument("--tol", type=float, default=30.0)
    sub.add_parser("doctor", help="check the installation")
    sub.add_parser("selftest", help="run the test suite")
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    if a.cmd == "selftest":
        selftest()
    elif a.cmd == "doctor":
        sys.exit(doctor())
    elif a.cmd == "monitor":
        do_monitor(a.input, a.record)
    elif a.cmd == "calibrate":
        if a.auto:
            if not a.input:
                raise SystemExit("usage: baby-tracker calibrate --auto --input FILE")
            tracker.autocalibrate_file(a.input)
        else:
            tracker.calibrate(a.input, a.image)
    elif a.cmd == "evaluate":
        tracker.evaluate_file(
            a.input,
            [float(t) for t in a.wakes.split(",") if t],
            a.tol,
            a.csv,
        )
    else:
        from . import train, tune

        (tune if a.cmd == "tune" else train).run(a.clip, a.tol)


if __name__ == "__main__":
    main()
