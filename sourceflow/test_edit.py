"""Smoke check: run every edit op on a generated clip. Run: python test_edit.py"""
import subprocess, tempfile
from pathlib import Path
from edit import OPS, edit

d = Path(tempfile.mkdtemp())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=3",
                "-f", "lavfi", "-i", "sine=duration=3", "-shortest", "-pix_fmt", "yuv420p", str(d / "a.mp4")], check=True)
for op in OPS:
    if op == "text":
        raw = {"text": "hello 안녕"}
    elif op == "trim":
        raw = {"start": 0.5, "end": 2}
    else:
        raw = {}
    names = ["a.mp4", "a.mp4"] if op == "merge" else ["a.mp4"]
    out = edit(op, raw, names, d)
    assert (d / out).stat().st_size > 0, op
    print("ok", op, out)
(d / "evil.mp4").write_text("#EXTM3U\n#EXTINF:1,\nfile:///etc/passwd\n")
for bad in ("evil.mp4",):
    try:
        edit("mute", {}, [bad], d)
        raise SystemExit("playlist accepted")
    except ValueError:
        pass
for bad in ("../etc/passwd", "nope.mp4"):
    try:
        edit("mute", {}, [bad], d)
        raise SystemExit("bad input accepted")
    except ValueError:
        pass
print("all ok")
