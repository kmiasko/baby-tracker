# CLAUDE.md

Standalone baby-awake tracker: reads any ffmpeg input (SDP/rtsp/file/device), detects "baby is upright", notifies. Python ≥3.10, package `src/baby_tracker`, entry point `baby_tracker.cli:main`. Needs `ffmpeg` on PATH. Split out of the ImCam repo; ImCam launches it as a subprocess.

## Commands

    pip install -e ".[test,dev]"
    pytest -q
    baby-tracker doctor

**Before every commit, run `ruff format .`** (CI runs `ruff format --check .`).

## Architecture

- **cli.py** – argparse dispatch only (`monitor`, `calibrate`, `evaluate`, `tune`, `train`, `doctor`, `selftest`).
- **tracker.py** – ffmpeg command (`ffmpeg_cmd(cfg, source, ...)`), background subtraction in the ROI, `Tracker` debounce, `LiveTracker`, manual `calibrate`. numpy/cv2 are imported lazily. All settings are in `DEFAULTS`; config file `~/.baby-tracker/roi.json`.
- **autocal.py** – self-calibration (ROI discovery, lying baseline, drift check). **seed.py** – YOLOX person detector hint. **classifier.py / train.py / tune.py** – optional stage-2 classifier and knob fitting.
- **notify.py** – event delivery (log, desktop, `hook` command with `BABY_TRACKER_EVENT`/`BABY_TRACKER_MESSAGE`); `send()` never raises.
- **paths.py / debug.py** – data dir (`BABY_TRACKER_HOME`), `BABY_TRACKER_DEBUG` tracing.

Keep the tracker independent of any camera: no imports of ImCam code. Keep new logic out of `cli.py`.
