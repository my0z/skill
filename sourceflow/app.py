"""SourceFlow: paste links and save best quality video. Run: python app.py"""
import json, os, re, threading, uuid, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from yt_dlp import YoutubeDL

OUT = Path(os.environ.get("SF_DIR", Path.home() / "Downloads" / "SourceFlow"))
OUT.mkdir(parents=True, exist_ok=True)
JOBS = {}  # id -> state dict. ponytail: in memory only so history resets on restart
SEM = threading.Semaphore(3)  # parallel downloads cap
URL_RE = re.compile(r"https?://[^\s]+")  # share text from Douyin or Xiaohongshu has extra words around the link


def run(jid, url):
    j = JOBS[jid]

    def hook(d):
        if d["status"] == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            j["pct"] = round(d["downloaded_bytes"] * 100 / tot, 1) if tot else 0
        elif d["status"] == "finished":
            j["pct"] = 100

    opts = {
        "format": "bv*+ba/b",  # best video plus best audio
        "merge_output_format": "mkv",  # mkv holds any codec so no re-encode and no quality loss
        "outtmpl": str(OUT / "%(extractor)s_%(id)s.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "cookiesfrombrowser": (os.environ["SF_BROWSER"],) if os.environ.get("SF_BROWSER") else None,
    }
    with SEM:
        j["state"] = "run"
        try:
            with YoutubeDL(opts) as y:
                info = y.extract_info(url)
                j["title"] = info.get("title") or url
                j["file"] = Path(y.prepare_filename(info)).with_suffix(".mkv").name
                j["res"] = f'{info.get("width")}x{info.get("height")}'
            j["state"] = "done"
        except Exception as e:
            j["state"], j["err"] = "err", str(e)[:200]


PAGE = """<!doctype html><meta charset=utf-8><title>SourceFlow</title>
<style>body{font:15px system-ui;max-width:760px;margin:40px auto;padding:0 16px;color:#1b2a24}
h1{color:#1f6b4f}textarea{width:100%;height:110px;padding:10px;border:1px solid #ccd;border-radius:8px;box-sizing:border-box}
button{background:#1f6b4f;color:#fff;border:0;padding:10px 20px;border-radius:8px;cursor:pointer;margin-top:8px}
.r{border:1px solid #dde;border-radius:8px;padding:10px;margin-top:8px}.b{height:6px;background:#eee;border-radius:3px;margin-top:6px}
.b i{display:block;height:6px;background:#1f6b4f;border-radius:3px}small{color:#678}</style>
<h1>링크 하나로 좋은 화질 그대로</h1>
<small>유튜브 인스타 틱톡 빌리빌리 더우인 샤오홍슈 지원. 한 번에 20개까지.</small>
<textarea id=t placeholder="영상 URL을 붙여 넣으세요"></textarea><br><button onclick=go()>다운로드 시작</button>
<div id=l></div>
<script>
async function go(){const u=t.value;t.value='';await fetch('/api/add',{method:'POST',body:u})}
async function tick(){const j=await (await fetch('/api/list')).json();
l.innerHTML=j.map(x=>`<div class=r><b>${x.title||x.url}</b> <small>${x.res||''} ${x.state}</small>
${x.state=='done'?`<a href="/file/${x.file}">영상 저장</a>`:''}${x.err?`<br><small>${x.err}</small>`:''}
<div class=b><i style="width:${x.pct}%"></i></div></div>`).join('')}
setInterval(tick,1000);tick()
</script>"""


class H(BaseHTTPRequestHandler):
    def send(self, body, ctype="application/json"):
        body = body if isinstance(body, bytes) else body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(PAGE, "text/html; charset=utf-8")
        elif self.path == "/api/list":
            self.send(json.dumps(list(JOBS.values())[::-1]))
        elif self.path.startswith("/file/"):
            f = OUT / Path(self.path[6:]).name  # name only blocks path traversal
            if f.is_file():
                self.send(f.read_bytes(), "video/x-matroska")
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/add":
            return self.send_error(404)
        text = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        for url in URL_RE.findall(text)[:20]:
            jid = uuid.uuid4().hex[:8]
            JOBS[jid] = {"id": jid, "url": url, "state": "wait", "pct": 0}
            threading.Thread(target=run, args=(jid, url), daemon=True).start()
        self.send("{}")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    s = ThreadingHTTPServer(("127.0.0.1", 8765), H)  # localhost only
    print("http://127.0.0.1:8765  saving to", OUT)
    webbrowser.open("http://127.0.0.1:8765")
    s.serve_forever()
