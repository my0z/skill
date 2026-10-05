"""SourceFlow: paste links and save best quality video. Run: python app.py"""
import json, os, re, secrets, threading, uuid, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
from yt_dlp import YoutubeDL
import edit

OUT = Path(os.environ.get("SF_DIR", Path.home() / "Downloads" / "SourceFlow"))
OUT.mkdir(parents=True, exist_ok=True)
JOBS = {}  # id -> state dict. ponytail: in memory only so history resets on restart
TOKEN = secrets.token_hex(16)  # per run secret embedded in the page
MEDIA = {".mp4": "video/mp4", ".mkv": "video/x-matroska", ".webm": "video/webm", ".mov": "video/quicktime", ".gif": "image/gif",
         ".png": "image/png", ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".wav": "audio/wav", ".flac": "audio/flac"}  # anything else is sent as a download
FILE_HEADERS = (("Content-Security-Policy", "sandbox"), ("Content-Disposition", "attachment"))
HOSTS = {"127.0.0.1:8765", "localhost:8765"}
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


def run_edit(jid, req, names):
    j = JOBS[jid]
    with SEM:
        j["state"] = "run"
        try:
            j["file"] = edit.edit(req["op"], req.get("params") or {}, names, OUT)
            j["pct"], j["state"] = 100, "done"  # ponytail: no ffmpeg progress so the bar jumps 0 to 100
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
<h2>편집</h2>
<small>파일을 고르고 기능을 고르세요. 합치기는 파일 2개 이상 선택하며 목록 순서대로 이어집니다.</small><br>
<select id=ef multiple size=5 style="min-width:60%"></select>
<select id=eo onchange=fields()></select>
<div id=fl style="margin-top:8px"></div><button onclick=editGo()>편집 시작</button>
<div id=l></div>
<script>
let OPS=[],lastDone=-1;
async function init(){OPS=await (await fetch('/api/ops')).json();eo.replaceChildren(...OPS.map(o=>new Option(o.label,o.name)));fields()}
function fields(){const o=OPS.find(x=>x.name==eo.value);fl.replaceChildren(...o.fields.map(f=>{
const w=document.createElement('label');w.style.marginRight='12px';w.append(f.label+' ');let i;
if(f.type=='choice'){i=document.createElement('select');i.append(...f.options.map(v=>new Option(v,v)))}
else{i=document.createElement('input');if(f.type=='num'){i.type='number';i.min=f.min;i.max=f.max;i.step='any'}}
i.value=f.default;i.dataset.k=f.key;w.append(i);return w}))}
async function loadFiles(){const s=new Set([...ef.selectedOptions].map(o=>o.value));const n=await (await fetch('/api/files')).json();
ef.replaceChildren(...n.map(v=>{const o=new Option(v,v);o.selected=s.has(v);return o}))}
async function editGo(){const p={};fl.querySelectorAll('[data-k]').forEach(i=>p[i.dataset.k]=i.value);
const r=await fetch('/api/edit',{method:'POST',headers:{'X-SF-Token':'__TOKEN__','Content-Type':'application/json'},
body:JSON.stringify({op:eo.value,files:[...ef.selectedOptions].map(o=>o.value),params:p})});if(!r.ok)alert(await r.text())}
init();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function go(){const u=t.value;t.value='';await fetch('/api/add',{method:'POST',headers:{'X-SF-Token':'__TOKEN__'},body:u})}
async function tick(){const j=await (await fetch('/api/list')).json();
const d=j.filter(x=>x.state=='done').length;if(d!=lastDone){lastDone=d;loadFiles()}
l.innerHTML=j.map(x=>`<div class=r><b>${esc(x.title||x.url)}</b> <small>${esc(x.res)} ${esc(x.state)}</small>
${x.state=='done'?`<a href="/file/${encodeURIComponent(x.file)}">영상 저장</a>`:''}${x.err?`<br><small>${esc(x.err)}</small>`:''}
<div class=b><i style="width:${x.pct}%"></i></div></div>`).join('')}
setInterval(tick,1000);tick()
</script>"""


class H(BaseHTTPRequestHandler):
    def send(self, body, ctype="application/json", code=200, extra=()):
        body = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in extra:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def bad_host(self):
        # blocks DNS rebinding since a rebound page still sends its own hostname
        if self.headers.get("Host") not in HOSTS:
            self.send_error(403)
            return True

    def do_GET(self):
        if self.bad_host():
            return
        if self.path == "/":
            self.send(PAGE.replace("__TOKEN__", TOKEN), "text/html; charset=utf-8")
        elif self.path == "/api/list":
            self.send(json.dumps(list(JOBS.values())[::-1]))
        elif self.path == "/api/ops":
            self.send(json.dumps(edit.spec()))
        elif self.path == "/api/files":
            skip = (".part", ".ytdl")
            self.send(json.dumps([p.name for p in sorted(OUT.iterdir()) if p.is_file() and not p.name.endswith(skip)]))
        elif self.path.startswith("/file/"):
            f = OUT / Path(unquote(self.path[6:])).name  # name only blocks path traversal
            if f.is_file():
                self.send(f.read_bytes(), MEDIA.get(f.suffix.lower(), "application/octet-stream"), extra=FILE_HEADERS)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.bad_host():
            return
        if self.headers.get("X-SF-Token") != TOKEN:  # custom header forces CORS preflight so other sites cannot post
            return self.send_error(403)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        if self.path == "/api/edit":
            try:
                req = json.loads(body)
                label = edit.OPS[req["op"]][0]
                names = [str(n) for n in req["files"]]
            except (ValueError, KeyError, TypeError):
                return self.send("bad request", "text/plain", 400)
            jid = uuid.uuid4().hex[:8]
            JOBS[jid] = {"id": jid, "url": label, "title": f"{label}: {', '.join(names)}"[:120], "state": "wait", "pct": 0}
            threading.Thread(target=run_edit, args=(jid, req, names), daemon=True).start()
            return self.send("{}")
        if self.path != "/api/add":
            return self.send_error(404)
        text = body
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
