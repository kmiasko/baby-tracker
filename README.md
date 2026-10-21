# baby-tracker

baby-tracker watches a video stream of a crib. It sends a notification when the baby is awake and upright.

It reads any video source that ffmpeg can read: an SDP file, an RTSP or UDP URL, a camera device, or a video file.
It does not depend on a specific camera.

## How it works

1. ffmpeg decodes the stream into small frames (3 frames each second).
2. A background model finds the moving shape (the "blob") in the crib area.
3. The shape is "upright" when it is tall, or when its top is above the lying level.
4. If the shape stays upright for `hold_s` seconds (default 5), baby-tracker sends a notification.
5. After a notification, baby-tracker waits `cooldown_s` seconds (default 600) before the next one.

By default, baby-tracker calibrates itself. During the first `auto_cal_s` seconds (default 120), it finds the crib area and the lying appearance of the baby.
A person detector (YOLOX-S, 35 MB) helps to find the crib. It downloads once to `~/.baby-tracker/models/`.

## Install

Requirements: Python 3.10 or higher, and `ffmpeg` on the PATH.

    pip install .
    baby-tracker doctor

`baby-tracker doctor` shows what is installed and what is missing.

## Monitor a stream

    baby-tracker monitor --input stream.sdp
    baby-tracker monitor --input rtsp://camera/stream --record ~/recordings

- `--input` is a file, URL, device, or `.sdp` file. For an `.sdp` file, baby-tracker adds the ffmpeg option `-protocol_whitelist file,udp,rtp`.
- `--record DIR` also saves the stream in 10-minute `.mkv` files.
- A plain video file is replayed one time. Use this to test.
- Press Ctrl-C to stop.

If ffmpeg stops, baby-tracker starts it again after 2 seconds. If no frame comes for `stream_lost_s` seconds, it sends a "stream lost" message.

### Use with ImCam

`imcam monitor` starts baby-tracker for you. It gives baby-tracker the file `~/.imcam/track.sdp`.

## Notifications

baby-tracker writes each event to the log. It also sends a desktop notification (`notify-send` on Linux, `winotify` on Windows).

To run your own command, set `hook` in `roi.json`. The command gets two environment variables:

- `BABY_TRACKER_EVENT`: the event name.
- `BABY_TRACKER_MESSAGE`: the message text.

## Calibration

Automatic calibration is the default. You do not need to do anything.

To use a manual calibration:

    baby-tracker calibrate --input recording.mp4
    baby-tracker calibrate --image frame.png

1. Click the corners of the crib. Push Enter.
2. Click 2 points at the head level when the baby is lying. Push Enter.

baby-tracker saves the result in `~/.baby-tracker/roi.json`.

To discover the area from a recording and save it:

    baby-tracker calibrate --auto --input recording.mp4

A manual calibration stays fixed. An automatic calibration is made again on each run.

## Settings

All settings are in `~/.baby-tracker/roi.json`. Coordinates are normalized (0 to 1). Each key has a default.
`examples/roi.json` is an example. The full list of keys and their meaning is in `DEFAULTS` in `src/baby_tracker/tracker.py`.

| Key | Default | Meaning |
| --- | --- | --- |
| `hold_s` | 5 | Time the baby must be upright before a notification |
| `cooldown_s` | 600 | Minimum time between notifications |
| `aspect_thresh` | 1.5 | Height/width ratio above which the shape is upright |
| `fps` | 3 | Analysis frames each second |
| `hwaccel` | `auto` | ffmpeg `-hwaccel` value (`""` turns it off) |
| `hook` | `""` | Command to run on each event |

## Train it

Training is optional. Use it if the default detector gives false alerts or misses wakes in your room.
You need recordings and the times (in seconds) when the baby woke up in each recording.

### 1. Record

    baby-tracker monitor --input stream.sdp --record ~/recordings

### 2. Label

Open each recording in a video player. Write down the time of each wake as seconds from the start.
Name a clip with this format: `FILE:T1,T2,...`. Example: `night1.mkv:1830,5400`.
A clip with no wake has no times: `night2.mkv:`.

### 3. Evaluate

    baby-tracker evaluate --input night1.mkv --wakes 1830,5400 --tol 30 --csv out.csv

This replays the recording and prints how many wakes were found, how many were missed, and how many false alerts occurred each hour.
An alert is correct if it comes within `--tol` seconds (default 30) of a label.

### 4. Tune the detector

    baby-tracker tune --clip night1.mkv:1830,5400 --clip night2.mkv:

This tests a grid of values for `rise_mult`, `lying_len_mult`, `min_area_ratio`, `hold_s`, and `gap_s`.
It scores each clip with values fitted on the other clips (leave-one-out). This is a fair estimate.
It prints the best values as `roi.json` keys. Copy them into `~/.baby-tracker/roi.json`.

### 5. Train the classifier

    baby-tracker train --clip night1.mkv:1830,5400 --clip night2.mkv:

This fits a second-stage classifier on your clips. A frame is "upright" from a labelled wake until `train_window_s` seconds later (default 15).
baby-tracker saves `~/.baby-tracker/classifier.json` only if it does better than the rules on held-out clips.
If it does not, the rules stay in use.

To use the rules only, set `"classifier": ""` in `roi.json`.
`examples/` does not contain a `classifier.json`, because the file depends on your room. Make your own with `train`.

Use at least 3 clips with different lighting. More clips give a better result.

## Files

| Path | Content |
| --- | --- |
| `~/.baby-tracker/roi.json` | Settings and calibration |
| `~/.baby-tracker/classifier.json` | Trained classifier (optional) |
| `~/.baby-tracker/models/` | Downloaded person detector |

Set `BABY_TRACKER_HOME` to use a different directory. Set `BABY_TRACKER_DEBUG=1` to show calibration messages.

## Move from ImCam

Earlier versions of ImCam kept these files in `~/.imcam`. Copy them:

    mkdir -p ~/.baby-tracker
    cp ~/.imcam/roi.json ~/.imcam/classifier.json ~/.baby-tracker/
    cp -r ~/.imcam/models ~/.baby-tracker/

## Develop

    pip install -e ".[test,dev]"
    pytest -q
    ruff format .

Run `ruff format .` before each commit.
