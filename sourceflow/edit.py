"""ffmpeg edit ops. Each op is a UI spec plus an arg builder. Args go to subprocess as a list so no shell is involved."""
import json, os, subprocess, uuid
from pathlib import Path

AAC = ["-c:a", "aac", "-b:a", "192k"]
PROTO = ["-protocol_whitelist", "file"]  # inputs may read local files only so a playlist file cannot fetch urls
FORMATS = {"matroska", "webm", "mov", "mp4", "gif", "mp3", "wav", "flac", "png_pipe", "ogg", "mpegts", "avi", "flv"}


def enc(crf=16, preset="medium"):
    return ["-c:v", "libx264", "-crf", f"{crf:g}", "-preset", preset, "-pix_fmt", "yuv420p"] + AAC


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error"] + PROTO + ["-show_entries", "stream=codec_type,width,height", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    st = json.loads(out)["streams"]
    v = next((s for s in st if s["codec_type"] == "video"), {})
    return {"w": v.get("width", 0), "h": v.get("height", 0), "audio": any(s["codec_type"] == "audio" for s in st)}


def av(src, vf=None, af=None, crf=16, preset="medium"):
    """One input with optional video and audio filter. No video filter means the video stream is copied."""
    a = probe(src)["audio"]
    cmd = ["-i", str(src)] + (["-vf", vf] if vf else []) + (["-af", af] if af and a else [])
    if vf:
        return cmd + enc(crf, preset), "mp4"
    return cmd + ["-c:v", "copy"] + AAC, "mkv"  # mkv holds any copied codec


def num(key, label, lo, hi, d):
    return dict(key=key, label=label, type="num", min=lo, max=hi, default=d)


def choice(key, label, opts):
    return dict(key=key, label=label, type="choice", options=opts, default=opts[0])


def atempo(f):
    parts = []
    while f > 2:
        parts.append("atempo=2")
        f /= 2
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    return ",".join(parts + [f"atempo={f:g}"])


def trim(p, i):
    if p["end"] <= p["start"]:
        raise ValueError("end must be after start")
    # re-encode so the cut is frame accurate. Stream copy would snap to keyframes
    return ["-i", str(i[0]), "-ss", f'{p["start"]:g}', "-t", f'{p["end"] - p["start"]:g}'] + enc(), "mp4"


def crop(p, i):
    w, h = p["aspect"].split(":")
    return av(i[0], f"crop='min(iw,ih*{w}/{h})':'min(ih,iw*{h}/{w})'")


def fade(p, i):
    d = float(subprocess.run(
        ["ffprobe", "-v", "error"] + PROTO + ["-show_entries", "format=duration", "-of", "csv=p=0", str(i[0])],
        capture_output=True, text=True, check=True).stdout)
    s = p["seconds"]
    if s * 2 > d:
        raise ValueError("fade longer than half the clip")
    return av(i[0], f"fade=t=in:st=0:d={s:g},fade=t=out:st={d - s:g}:d={s:g}",
              f"afade=t=in:st=0:d={s:g},afade=t=out:st={d - s:g}:d={s:g}")


def text(p, i):
    t = "".join(c for c in p["text"] if c.isalnum() or c in " .!?-_@#")  # drop chars that break drawtext quoting
    if not t:
        raise ValueError("text empty")
    y = {"bottom": "h-th-60", "center": "(h-th)/2", "top": "60"}[p["position"]]
    font = os.environ.get("SF_FONT")  # set for Korean glyphs. ex /usr/share/fonts/truetype/nanum/NanumGothic.ttf
    f = f":fontfile={font}" if font else ""
    return av(i[0], f"drawtext=text='{t}':fontsize={p['size']:g}:fontcolor=white:borderw=2:x=(w-tw)/2:y={y}{f}")


def gif(p, i):
    vf = f"fps={p['fps']:g},scale={p['width']:g}:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse"
    return ["-i", str(i[0]), "-vf", vf, "-an", "-loop", "0"], "gif"


def audio(p, i):
    c = {"mp3": ["-c:a", "libmp3lame", "-q:a", "0"], "m4a": ["-c:a", "aac", "-b:a", "256k"], "wav": [], "flac": []}[p["format"]]
    return ["-i", str(i[0]), "-vn"] + c, p["format"]


def compress(p, i):
    h = p["height"]
    return av(i[0], "scale=-2:" + h if h != "original" else "null", crf=p["crf"], preset="slow")


def convert(p, i):
    f = p["format"]
    if f == "webm":
        return ["-i", str(i[0]), "-c:v", "libvpx-vp9", "-crf", "24", "-b:v", "0", "-c:a", "libopus"], "webm"
    return ["-i", str(i[0])] + enc(), f


def merge(p, i):
    d = probe(i[0])
    w, h = d["w"] - d["w"] % 2, d["h"] - d["h"] % 2  # every clip is fitted to the first clip size
    au = all(probe(x)["audio"] for x in i)
    n = len(i)
    seg = "".join(
        f"[{k}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{k}];"
        + (f"[{k}:a]aresample=48000[a{k}];" if au else "") for k in range(n))
    pads = "".join(f"[v{k}]" + (f"[a{k}]" if au else "") for k in range(n))
    fc = f"{seg}{pads}concat=n={n}:v=1:a={int(au)}[v]" + ("[a]" if au else "")
    ins = [x for f in i for x in ("-i", str(f))]
    return ins + ["-filter_complex", fc, "-map", "[v]"] + (["-map", "[a]"] if au else []) + enc(), "mp4"


ROT = {"90 right": "transpose=1", "90 left": "transpose=2", "180": "transpose=1,transpose=1",
       "mirror": "hflip", "flip upside down": "vflip"}

OPS = {
    "trim": ("구간 자르기", [num("start", "시작 초", 0, 86400, 0), num("end", "끝 초", 0, 86400, 10)], trim),
    "crop": ("비율 크롭", [choice("aspect", "비율", ["9:16", "1:1", "4:5", "16:9"])], crop),
    "resize": ("해상도 변경", [choice("height", "세로 픽셀", ["2160", "1440", "1080", "720", "480", "360"])],
               lambda p, i: av(i[0], f"scale=-2:{p['height']}")),
    "speed": ("배속", [num("factor", "배속", 0.25, 8, 2)],
              lambda p, i: av(i[0], f"setpts=PTS/{p['factor']:g}", atempo(p["factor"]))),
    "rotate": ("회전 반전", [choice("mode", "방식", list(ROT))], lambda p, i: av(i[0], ROT[p["mode"]])),
    "mute": ("소리 제거", [], lambda p, i: (["-i", str(i[0]), "-an", "-c:v", "copy"], "mkv")),
    "volume": ("볼륨", [num("factor", "배율", 0, 5, 1.5)], lambda p, i: av(i[0], af=f"volume={p['factor']:g}")),
    "fade": ("페이드 인아웃", [num("seconds", "초", 0.1, 30, 1)], fade),
    "reverse": ("거꾸로 재생", [], lambda p, i: av(i[0], "reverse", "areverse")),  # holds the whole clip in RAM so keep clips short
    "color": ("색보정", [num("brightness", "밝기", -1, 1, 0), num("contrast", "대비", 0, 3, 1.1), num("saturation", "채도", 0, 3, 1.2)],
              lambda p, i: av(i[0], f"eq=brightness={p['brightness']:g}:contrast={p['contrast']:g}:saturation={p['saturation']:g}")),
    "grayscale": ("흑백", [], lambda p, i: av(i[0], "hue=s=0")),
    "denoise": ("노이즈 제거", [num("level", "강도", 1, 10, 4)],
                lambda p, i: av(i[0], f"hqdn3d={p['level']:g}:{p['level'] * .75:g}:{p['level'] * 1.5:g}:{p['level'] * 1.1:g}")),
    "sharpen": ("선명하게", [num("amount", "강도", 0, 3, 1)], lambda p, i: av(i[0], f"unsharp=5:5:{p['amount']:g}:5:5:0")),
    "text": ("자막 문구", [dict(key="text", label="문구", type="text", default=""), choice("position", "위치", ["bottom", "center", "top"]),
                       num("size", "크기", 10, 200, 48)], text),
    "audio": ("음성 추출", [choice("format", "형식", ["mp3", "m4a", "wav", "flac"])], audio),
    "gif": ("GIF 만들기", [num("fps", "fps", 5, 30, 12), num("width", "가로 픽셀", 120, 1080, 480)], gif),
    "thumbnail": ("썸네일 PNG", [num("time", "초", 0, 86400, 1)],
                  lambda p, i: (["-ss", f"{p['time']:g}", "-i", str(i[0]), "-frames:v", "1"], "png")),
    "compress": ("용량 줄이기", [num("crf", "CRF 낮을수록 고화질", 18, 40, 28), choice("height", "세로 픽셀", ["original", "1080", "720", "480"])], compress),
    "convert": ("형식 변환", [choice("format", "형식", ["mp4", "webm", "mov", "mkv"])], convert),
    "merge": ("영상 합치기", [], merge),  # needs 2 to 10 files
}


def spec():
    return [dict(name=k, label=v[0], fields=v[1]) for k, v in OPS.items()]


def clean(fields, raw):
    out = {}
    for f in fields:
        v = raw.get(f["key"], f["default"])
        if f["type"] == "num":
            v = float(v)
            if not f["min"] <= v <= f["max"]:  # also rejects nan
                raise ValueError(f"{f['key']} out of range")
        elif f["type"] == "choice":
            if v not in f["options"]:
                raise ValueError(f"{f['key']} bad choice")
        else:
            v = str(v)[:80]
        out[f["key"]] = v
    return out


def edit(op, raw, names, outdir):
    """Run one op on files inside outdir. Returns the output file name."""
    if op not in OPS:
        raise ValueError("unknown op")
    _, fields, build = OPS[op]
    ins = [outdir / Path(n).name for n in names]  # name only blocks path traversal
    if op == "merge":
        if not 2 <= len(ins) <= 10:
            raise ValueError("merge needs 2 to 10 files")
    elif len(ins) != 1:
        raise ValueError("select exactly one file")
    if not all(f.is_file() for f in ins):
        raise ValueError("file not found")
    for f in ins:  # reject playlists and concat scripts that can point ffmpeg at other files
        names = subprocess.run(["ffprobe", "-v", "error"] + PROTO + ["-show_entries", "format=format_name", "-of", "csv=p=0", str(f)],
                               capture_output=True, text=True).stdout.strip().split(",")
        if not FORMATS.intersection(names):
            raise ValueError("unsupported file format")
    args, ext = build(clean(fields, raw), ins)
    args = [y for a in args for y in (PROTO + [a] if a == "-i" else [a])]
    out = outdir / f"{ins[0].stem}_{op}_{uuid.uuid4().hex[:4]}.{ext}"
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args + [str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else "ffmpeg failed")
    return out.name
