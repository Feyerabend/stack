#!/usr/bin/env python3
"""Render tutorial.md to a syntax-coloured tutorial.html.

Pure standard library — no pip, no external Markdown engine — so it runs on any
Python 3. It understands the small Markdown subset the tutorial uses (headings,
paragraphs, fenced code blocks, blockquotes, pipe tables, a horizontal rule, and
inline code / bold / italic / links) and syntax-highlights the ```lark code
blocks with a tiny tokeniser.

Usage:  python3 render.py        # reads tutorial.md, writes tutorial.html (alongside this script)
"""

import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "tutorial.md"
OUT = HERE / "tutorial.html"

# --- Lark syntax highlighting -------------------------------------------------

KEYWORDS = {
    "module", "fn", "let", "in", "if", "then", "else",
    "match", "with", "end", "type", "trait", "impl", "for", "of",
}

# One scanner, tried left-to-right at each position. Comments and strings come
# first so keywords inside them are not re-coloured.
_LARK = re.compile(
    r"""
      (?P<co>\(\*.*?\*\))            # (* comment *)
    | (?P<st>"[^"]*")               # "string"
    | (?P<nu>\d+\.\d+|\d+)          # number
    | (?P<id>[A-Za-z_][A-Za-z0-9_]*)# identifier
    | (?P<op>->|=>|==|<=|>=|[-+*/=<>|])
    """,
    re.DOTALL | re.VERBOSE,
)


def highlight_lark(code: str) -> str:
    out, pos = [], 0
    for m in _LARK.finditer(code):
        if m.start() > pos:                       # plain gap (spaces, ()[],:.)
            out.append(html.escape(code[pos:m.start()]))
        kind = m.lastgroup
        text = html.escape(m.group())
        if kind == "id":
            word = m.group()
            if word in KEYWORDS:
                out.append(f'<span class="kw">{text}</span>')
            elif word[0].isupper():               # types and constructors
                out.append(f'<span class="ty">{text}</span>')
            else:
                out.append(text)                  # variables, fn names — plain
        else:
            out.append(f'<span class="{kind}">{text}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out)


# --- inline Markdown ----------------------------------------------------------

def inline(text: str) -> str:
    text = html.escape(text)
    codes: list[str] = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)                       # protect `code`
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)  # bold before
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)              # italic
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)
    return text


# --- block Markdown -----------------------------------------------------------

def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)

    def is_table(j):
        return j + 1 < n and lines[j].lstrip().startswith("|") \
            and set(lines[j + 1].strip()) <= set("|-: ")

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf = []
            while i < n and lines[i].strip() != "```":
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code = "\n".join(buf)
            body = highlight_lark(code) if lang == "lark" else html.escape(code)
            out.append(f'<pre><code class="lang-{lang or "text"}">{body}</code></pre>')
            continue

        # headings
        if stripped.startswith("## "):
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
            i += 1
            continue
        if stripped.startswith("# "):
            out.append(f"<h1>{inline(stripped[2:])}</h1>")
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # blockquote (consecutive '>' lines)
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue

        # pipe table
        if is_table(i):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2  # header + separator
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head = "".join(f"<th>{inline(c)}</th>" for c in header)
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue

        # paragraph (gather until a blank line or a new block starts)
        buf = []
        while i < n and lines[i].strip() and not lines[i].lstrip().startswith(("```", "#", ">", "|")) \
                and not re.fullmatch(r"-{3,}|\*{3,}", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")

    return "\n".join(out)


# --- page template ------------------------------------------------------------

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A Short Tour of Lark</title>
<style>
  :root {{ --ink:#1c1c1c; --dim:#5a5a5a; --rule:#e3e3e3; --bg:#fbfbf9;
          --code-bg:#f4f3ee; --accent:#7a3b2e; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.65 Georgia,"Iowan Old Style",serif; -webkit-font-smoothing:antialiased; }}
  main {{ max-width:760px; margin:0 auto; padding:3rem 1.25rem 5rem; }}
  h1 {{ font-size:2.1rem; line-height:1.15; margin:0 0 1.6rem; }}
  h2 {{ font-size:1.4rem; margin:2.6rem 0 .6rem; padding-top:1.4rem; border-top:1px solid var(--rule); }}
  p, li, td, th {{ color:var(--ink); }}
  a {{ color:var(--accent); }}
  code {{ font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace; font-size:.86em;
         background:var(--code-bg); padding:.08em .35em; border-radius:3px; }}
  pre {{ background:var(--code-bg); border:1px solid var(--rule); border-left:3px solid var(--accent);
        border-radius:5px; padding:1rem 1.1rem; overflow-x:auto; line-height:1.5; }}
  pre code {{ background:none; padding:0; font-size:.84rem; }}
  blockquote {{ margin:.6rem 0; padding:.5rem .9rem; background:#f0efe9; border-radius:4px;
               color:var(--dim); font-size:.92rem; }}
  blockquote strong {{ color:var(--ink); }}
  table {{ border-collapse:collapse; width:100%; font-size:.92rem; margin:.5rem 0; }}
  td, th {{ border-bottom:1px solid var(--rule); padding:.35rem .5rem; text-align:left; }}
  hr {{ border:0; border-top:1px solid var(--rule); margin:2.4rem 0 1rem; }}
  /* Lark syntax colours */
  .co {{ color:#8a8676; font-style:italic; }}   /* comment  */
  .st {{ color:#4a7a3a; }}                       /* string   */
  .kw {{ color:var(--accent); font-weight:bold; }} /* keyword */
  .ty {{ color:#2d6a8e; }}                       /* type / constructor */
  .nu {{ color:#9a5a00; }}                       /* number   */
  .op {{ color:#666; }}                          /* operator */
</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def main() -> None:
    md = SRC.read_text(encoding="utf-8")
    OUT.write_text(TEMPLATE.format(body=convert(md)), encoding="utf-8")
    print(f"wrote {OUT.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
