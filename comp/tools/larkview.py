#!/usr/bin/env python3
"""larkview — a zero-dependency Lark source viewer.

Scans the reader-facing `repo/` tree for `.lark` files, embeds their raw text
into a single standalone HTML page, and (optionally) opens it. No server, no
network, no build step: the page runs from `file://`. Syntax highlighting is
done in-browser, so files you drag onto the page render exactly like the
bundled ones.

Usage:
    python3 tools/larkview.py            # scan repo/, write+open tools/larkview.html
    python3 tools/larkview.py --no-open  # write only
    python3 tools/larkview.py PATH ...   # scan the given dirs/files instead

The generated HTML is self-contained; you can copy it anywhere and it still
works. Re-run this script to refresh the bundled file list.
"""

import json
import os
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # stack/lark
OUT = os.path.join(HERE, "larkview.html")

DEFAULT_SCAN = [os.path.join(ROOT, "repo")]


def collect(paths):
    """Return a sorted list of {path, group, name, text} for every .lark file."""
    files = []
    seen = set()

    def add(fp):
        rp = os.path.relpath(fp, ROOT)
        if rp in seen:
            return
        seen.add(rp)
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            return
        group = os.path.dirname(rp) or "."
        files.append(
            {"path": rp, "group": group, "name": os.path.basename(rp), "text": text}
        )

    for p in paths:
        if os.path.isfile(p) and p.endswith(".lark"):
            add(p)
        elif os.path.isdir(p):
            for dirpath, _dirs, names in os.walk(p):
                for n in sorted(names):
                    if n.endswith(".lark"):
                        add(os.path.join(dirpath, n))

    files.sort(key=lambda f: (f["group"], f["name"]))
    return files


def build_html(files):
    data = json.dumps(files, ensure_ascii=False)
    # The page is written as one f-string-free template so braces in CSS/JS
    # need no escaping; the data blob is spliced in at the marker.
    return HTML_TEMPLATE.replace("/*__DATA__*/", data).replace(
        "__COUNT__", str(len(files))
    )


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>larkview — Lark source viewer</title>
<style>
:root{
  --bg:#ffffff; --panel:#f6f7f9; --border:#e2e5ea; --fg:#1c2024;
  --muted:#71767e; --accent:#4a4496; --sel:#e9e7f6;
  --kw:#8a2f7b; --typ:#1f6d5a; --str:#a3322a; --com:#71767e;
  --num:#8a5a00; --fn:#2b4a9b; --pun:#4a4f57; --ref:#7a5b00;
}
:root[data-theme="dark"]{
  --bg:#15171b; --panel:#1b1e24; --border:#2a2e36; --fg:#dfe3e8;
  --muted:#8a9099; --accent:#a9a2e6; --sel:#2c2960;
  --kw:#e08fce; --typ:#63c7a8; --str:#e7938a; --com:#7f858e;
  --num:#d8a24a; --fn:#8aa6ea; --pun:#9aa0a8; --ref:#d8b45a;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#15171b; --panel:#1b1e24; --border:#2a2e36; --fg:#dfe3e8;
    --muted:#8a9099; --accent:#a9a2e6; --sel:#2c2960;
    --kw:#e08fce; --typ:#63c7a8; --str:#e7938a; --com:#7f858e;
    --num:#d8a24a; --fn:#8aa6ea; --pun:#9aa0a8; --ref:#d8b45a;
  }
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  color:var(--fg);background:var(--bg);display:flex;height:100vh;overflow:hidden;
}
#side{
  width:300px;min-width:220px;max-width:52vw;flex:0 0 auto;background:var(--panel);
  border-right:1px solid var(--border);display:flex;flex-direction:column;
}
#side h1{
  font-size:14px;margin:0;padding:14px 14px 10px;letter-spacing:.02em;
  display:flex;align-items:center;gap:8px;
}
#side h1 .dot{color:var(--accent)}
#side h1 .count{color:var(--muted);font-weight:400;font-size:12px}
#filter{
  margin:0 12px 10px;padding:7px 10px;border:1px solid var(--border);
  border-radius:7px;background:var(--bg);color:var(--fg);font-size:13px;width:calc(100% - 24px);
}
#filter:focus{outline:2px solid var(--accent);outline-offset:-1px}
#list{overflow:auto;flex:1;padding-bottom:16px}
.grp{padding:9px 14px 3px;font-size:11px;text-transform:uppercase;
  letter-spacing:.06em;color:var(--muted);position:sticky;top:0;background:var(--panel)}
.file{padding:5px 14px 5px 20px;cursor:pointer;font-size:13px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.file:hover{background:var(--sel)}
.file.active{background:var(--sel);color:var(--accent);font-weight:600;
  box-shadow:inset 3px 0 0 var(--accent)}
#main{flex:1;display:flex;flex-direction:column;min-width:0}
#bar{
  display:flex;align-items:center;gap:12px;padding:10px 16px;
  border-bottom:1px solid var(--border);background:var(--panel);flex:0 0 auto;
}
#bar .name{font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#bar .path{color:var(--muted);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#bar .spacer{flex:1}
.btn{
  border:1px solid var(--border);background:var(--bg);color:var(--fg);
  padding:6px 12px;border-radius:7px;cursor:pointer;font-size:12px;
}
.btn:hover{border-color:var(--accent);color:var(--accent)}
#view{flex:1;overflow:auto;position:relative}
#drop{
  position:absolute;inset:0;display:none;align-items:center;justify-content:center;
  background:color-mix(in srgb,var(--accent) 12%,transparent);
  border:3px dashed var(--accent);color:var(--accent);font-size:18px;font-weight:600;z-index:5;
}
#drop.show{display:flex}
#empty{color:var(--muted);padding:40px;text-align:center;line-height:1.7}
pre.code{margin:0;padding:16px 16px 40px;font:13px/1.6 "SF Mono",Menlo,Consolas,
  "Liberation Mono",monospace;tab-size:4;display:grid;grid-template-columns:auto 1fr}
pre.code .ln{color:var(--muted);opacity:.55;text-align:right;padding-right:14px;
  user-select:none;white-space:pre}
pre.code .lc{white-space:pre;overflow-wrap:normal}
.t-kw{color:var(--kw);font-weight:600}
.t-typ{color:var(--typ)}
.t-str{color:var(--str)}
.t-com{color:var(--com);font-style:italic}
.t-num{color:var(--num)}
.t-fn{color:var(--fn)}
.t-pun{color:var(--pun)}
.t-ref{color:var(--ref);font-weight:600}
</style>
</head>
<body>
<aside id="side">
  <h1><span class="dot">&#9679;</span> larkview <span class="count" id="count">__COUNT__ files</span></h1>
  <input id="filter" type="search" placeholder="Filter files…" autocomplete="off">
  <div id="list"></div>
</aside>
<section id="main">
  <div id="bar">
    <div style="min-width:0">
      <div class="name" id="curName">No file open</div>
      <div class="path" id="curPath">Click a file, or drop a .lark file anywhere</div>
    </div>
    <div class="spacer"></div>
    <label class="btn" for="upload">Open file…</label>
    <input id="upload" type="file" accept=".lark" style="display:none" multiple>
    <button class="btn" id="themeBtn" title="Toggle light/dark">&#9681;</button>
  </div>
  <div id="view">
    <div id="drop">Drop .lark file to view</div>
    <div id="empty">
      <p><strong>Pick a file on the left</strong> to see it highlighted,<br>
      or drag a <code>.lark</code> file onto this window.</p>
    </div>
  </div>
</section>

<script>
const FILES = /*__DATA__*/;

/* ---- Lark tokenizer ------------------------------------------------------ */
const KEYWORDS = new Set([
  "module","import","type","fn","let","in","if","then","else","match","with",
  "end","of","impl","trait","for","measure","where","as","and","or","not",
  "true","false","forall","exists"
]);

function escapeHtml(s){
  return s.replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
}

// Return HTML for one full source string, with correct handling of nested
// (* *) comments, strings, refinement braces, keywords, types, numbers, calls.
function highlight(src){
  let out = "";
  let i = 0;
  const n = src.length;
  const push = (cls, text) => { out += cls
    ? '<span class="'+cls+'">'+escapeHtml(text)+'</span>'
    : escapeHtml(text); };

  const isIdStart = c => /[A-Za-z_]/.test(c);
  const isId = c => /[A-Za-z0-9_]/.test(c);

  while(i < n){
    const c = src[i];

    // nested block comment (* ... *)
    if(c === "(" && src[i+1] === "*"){
      let depth = 1, j = i + 2;
      while(j < n && depth > 0){
        if(src[j] === "(" && src[j+1] === "*"){ depth++; j += 2; }
        else if(src[j] === "*" && src[j+1] === ")"){ depth--; j += 2; }
        else j++;
      }
      push("t-com", src.slice(i, j)); i = j; continue;
    }

    // string
    if(c === '"'){
      let j = i + 1;
      while(j < n && src[j] !== '"'){ if(src[j] === "\\") j++; j++; }
      j = Math.min(j + 1, n);
      push("t-str", src.slice(i, j)); i = j; continue;
    }

    // number
    if(/[0-9]/.test(c)){
      let j = i + 1;
      while(j < n && /[0-9_]/.test(src[j])) j++;
      push("t-num", src.slice(i, j)); i = j; continue;
    }

    // identifier / keyword / type / call
    if(isIdStart(c)){
      let j = i + 1;
      while(j < n && isId(src[j])) j++;
      const word = src.slice(i, j);
      // lookahead past spaces for a '(' → function call
      let k = j; while(k < n && (src[k] === " " || src[k] === "\t")) k++;
      let cls = null;
      if(KEYWORDS.has(word)) cls = "t-kw";
      else if(/^[A-Z]/.test(word)) cls = "t-typ";
      else if(src[k] === "(") cls = "t-fn";
      push(cls, word); i = j; continue;
    }

    // refinement / structural punctuation worth accenting
    if(c === "{" || c === "}" || c === "|"){
      push("t-ref", c); i++; continue;
    }

    // multi-char operators
    const two = src.slice(i, i+2);
    if(["=>","->","==","!=",">=","<=","::","&&","||"].includes(two)){
      push("t-pun", two); i += 2; continue;
    }
    if("+-*/=<>:,.()[]".includes(c)){
      push("t-pun", c); i++; continue;
    }

    push(null, c); i++;
  }
  return out;
}

function render(name, path, text){
  document.getElementById("empty").style.display = "none";
  document.getElementById("curName").textContent = name;
  document.getElementById("curPath").textContent = path;
  const body_src = text.replace(/\n$/, "");
  const lines = body_src.split("\n");
  // Highlight the whole source in one pass (so multi-line (* *) comments stay
  // correct), then place it beside a line-number gutter. Both columns share the
  // same line-height, so numbers line up without splitting the highlighted HTML.
  const highlighted = highlight(body_src);
  const pre = document.createElement("pre");
  pre.className = "code";
  let gutter = "";
  for(let l = 1; l <= lines.length; l++) gutter += l + "\n";
  const g = document.createElement("span");
  g.className = "ln"; g.textContent = gutter;
  const body = document.createElement("span");
  body.className = "lc"; body.innerHTML = highlighted;
  pre.appendChild(g); pre.appendChild(body);
  const view = document.getElementById("view");
  const old = view.querySelector("pre.code");
  if(old) old.remove();
  view.appendChild(pre);
  view.scrollTop = 0;
}

/* ---- Sidebar ------------------------------------------------------------- */
const listEl = document.getElementById("list");
let activeEl = null;

function buildList(filter){
  listEl.innerHTML = "";
  const f = (filter || "").toLowerCase();
  let lastGroup = null;
  FILES.forEach((file, idx) => {
    if(f && !(file.path.toLowerCase().includes(f))) return;
    if(file.group !== lastGroup){
      const g = document.createElement("div");
      g.className = "grp"; g.textContent = file.group;
      listEl.appendChild(g); lastGroup = file.group;
    }
    const el = document.createElement("div");
    el.className = "file"; el.textContent = file.name; el.title = file.path;
    el.onclick = () => {
      if(activeEl) activeEl.classList.remove("active");
      el.classList.add("active"); activeEl = el;
      render(file.name, file.path, file.text);
    };
    listEl.appendChild(el);
  });
}
buildList("");
document.getElementById("filter").addEventListener("input", e => buildList(e.target.value));

/* ---- Upload + drag/drop -------------------------------------------------- */
function readFile(file){
  const r = new FileReader();
  r.onload = () => {
    if(activeEl){ activeEl.classList.remove("active"); activeEl = null; }
    render(file.name, "(uploaded) " + file.name, r.result);
  };
  r.readAsText(file);
}
document.getElementById("upload").addEventListener("change", e => {
  if(e.target.files.length) readFile(e.target.files[0]);
});
const drop = document.getElementById("drop");
window.addEventListener("dragover", e => { e.preventDefault(); drop.classList.add("show"); });
window.addEventListener("dragleave", e => { if(e.relatedTarget === null) drop.classList.remove("show"); });
window.addEventListener("drop", e => {
  e.preventDefault(); drop.classList.remove("show");
  const f = e.dataTransfer.files[0];
  if(f) readFile(f);
});

/* ---- Theme --------------------------------------------------------------- */
document.getElementById("themeBtn").addEventListener("click", () => {
  const root = document.documentElement;
  const now = getComputedStyle(root).getPropertyValue("--bg").trim();
  const dark = now === "#15171b" || now === "#15171B";
  root.setAttribute("data-theme", dark ? "light" : "dark");
});

/* Open the first sample automatically if one exists. */
if(FILES.length){
  const first = FILES.find(f => f.path.includes("sample")) || FILES[0];
  const idx = FILES.indexOf(first);
  // click its list row if visible
  const rows = listEl.querySelectorAll(".file");
  for(const r of rows){ if(r.title === first.path){ r.click(); break; } }
}
</script>
</body>
</html>
"""


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    no_open = "--no-open" in argv
    scan = [os.path.abspath(a) for a in args] if args else DEFAULT_SCAN
    files = collect(scan)
    if not files:
        print("larkview: no .lark files found under:", ", ".join(scan))
        return 1
    html = build_html(files)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    kb = len(html.encode("utf-8")) / 1024
    print("larkview: wrote {} ({} files, {:.0f} KB)".format(OUT, len(files), kb))
    if not no_open:
        webbrowser.open("file://" + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
