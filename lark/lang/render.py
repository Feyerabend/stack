#!/usr/bin/env python3
"""
docs/render.py - Convert docs/tutorial.md -> docs/tutorial.html.

    python3 docs/render.py            # generate and open in browser
    python3 docs/render.py --no-open  # generate only

No external dependencies - pure stdlib.
"""

from __future__ import annotations
import html as _html, pathlib, re, sys, webbrowser

HERE = pathlib.Path(__file__).parent
SRC  = HERE / "tutorial.md"
OUT  = HERE / "tutorial.html"

# -- Lark syntax highlighter --

_KEYWORDS = frozenset({
    "and", "else", "end", "export", "false", "fn", "if", "impl", "import",
    "in", "let", "match", "module", "not", "of", "or", "then", "trait",
    "true", "type", "with",
})

def _hl(code: str) -> str:
    """Tokenise a Lark source snippet and wrap tokens in <span> tags."""
    h, out, i, n = _html.escape, [], 0, len(code)
    while i < n:
        # Nested comment  (* ... *)
        if code[i:i+2] == "(*":
            depth, j = 1, i + 2
            while j < n - 1 and depth:
                if   code[j:j+2] == "(*": depth += 1; j += 2
                elif code[j:j+2] == "*)": depth -= 1; j += 2
                else:                      j += 1
            out.append(f'<span class=c>{h(code[i:j])}</span>'); i = j; continue
        # String literal
        if code[i] == '"':
            j = i + 1
            while j < n:
                if   code[j] == "\\": j += 2
                elif code[j] == '"':  j += 1; break
                else:                  j += 1
            out.append(f'<span class=s>{h(code[i:j])}</span>'); i = j; continue
        # Identifier, keyword, or constructor/type name
        if code[i].isalpha() or code[i] == "_":
            j = i
            while j < n and (code[j].isalnum() or code[j] == "_"): j += 1
            w = code[i:j]
            if w in _KEYWORDS:   out.append(f'<span class=k>{h(w)}</span>')
            elif w[0].isupper(): out.append(f'<span class=t>{h(w)}</span>')
            else:                out.append(h(w))
            i = j; continue
        # Numeric literal (int or float)
        if code[i].isdigit():
            j = i
            while j < n and (code[j].isdigit() or code[j] == "."): j += 1
            out.append(f'<span class=n>{h(code[i:j])}</span>'); i = j; continue
        # Everything else: escape and emit verbatim
        out.append(h(code[i])); i += 1
    return "".join(out)


# -- Inline markdown --

def _inline(text: str) -> str:
    """Render **bold**, *italic*, and `inline code` within a text span."""
    h, out, i, n = _html.escape, [], 0, len(text)
    while i < n:
        if text[i:i+2] == "**":
            j = text.find("**", i + 2)
            if j != -1:
                out.append(f"<strong>{_inline(text[i+2:j])}</strong>")
                i = j + 2; continue
        if text[i] == "*":
            j = text.find("*", i + 1)
            if j != -1:
                out.append(f"<em>{_inline(text[i+1:j])}</em>")
                i = j + 1; continue
        if text[i] == "`":
            j = text.find("`", i + 1)
            if j != -1:
                out.append(f"<code>{h(text[i+1:j])}</code>")
                i = j + 1; continue
        out.append(h(text[i])); i += 1
    return "".join(out)


# -- Block markdown --

def _md(src: str) -> str:
    lines = src.split("\n")
    out:  list[str] = []
    para: list[str] = []
    i, n = 0, len(lines)

    def flush():
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    while i < n:
        raw  = lines[i]
        line = raw.strip()

        # Blank line
        if not line:
            flush(); i += 1; continue

        # Horizontal rule
        if line == "---":
            flush(); out.append("<hr>"); i += 1; continue

        # Heading
        m = re.match(r"^(#{1,4})\s+(.*)", raw)
        if m:
            flush()
            lvl  = len(m.group(1))
            text = m.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append(f'<h{lvl} id="{slug}">{_inline(text)}</h{lvl}>')
            i += 1; continue

        # Fenced code block
        m = re.match(r"^```(\w*)", raw)
        if m:
            flush()
            lang = m.group(1)
            i   += 1
            code_lines: list[str] = []
            while i < n and not lines[i].startswith("```"):
                code_lines.append(lines[i]); i += 1
            i += 1   # consume closing ```
            code = "\n".join(code_lines)
            body = _hl(code) if lang == "lark" else _html.escape(code)
            cls  = f' class="lang-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{body}</code></pre>")
            continue

        # Table
        if raw.startswith("|"):
            flush()
            rows: list[str] = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1

            def cells(row: str) -> list[str]:
                return [c.strip() for c in row.strip().strip("|").split("|")]

            parts = ["<table><thead><tr>"]
            for c in cells(rows[0]):
                parts.append(f"<th>{_inline(c)}</th>")
            parts.append("</tr></thead><tbody>")
            for row in rows[2:]:   # rows[1] is the |---|---| separator
                parts.append("<tr>")
                for c in cells(row):
                    parts.append(f"<td>{_inline(c)}</td>")
                parts.append("</tr>")
            parts.append("</tbody></table>")
            out.append("".join(parts))
            continue

        # Unordered list (supports continuation lines indented with spaces/tabs)
        if line.startswith("- "):
            flush()
            items: list[str] = []
            while i < n:
                stripped = lines[i].strip()
                if stripped.startswith("- "):
                    items.append(stripped[2:])
                    i += 1
                elif items and lines[i] and lines[i][0] in (" ", "\t"):
                    items[-1] += " " + stripped
                    i += 1
                else:
                    break
            out.append(
                "<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>"
            )
            continue

        # Regular paragraph text
        para.append(line); i += 1

    flush()
    return "\n".join(out)


# -- Table of contents --

def _toc(src: str) -> str:
    items = []
    for line in src.split("\n"):
        m = re.match(r"^## (.+)", line)
        if m:
            text = m.group(1)
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            items.append(f'<li><a href="#{slug}">{_html.escape(text)}</a></li>')
    return "<nav><ul>" + "".join(items) + "</ul></nav>" if items else ""


# -- CSS --

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0 }

body {
  font: 16px/1.75 system-ui, -apple-system, "Segoe UI", sans-serif;
  color: #1a1a2e;
  background: #f0f2f5;
  padding: 2rem 1rem 5rem;
}

article {
  max-width: 820px;
  margin: 0 auto;
  background: #fff;
  padding: 2.5rem 3rem 3rem;
  border: 1px solid #dde3ea;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,.08);
}

/* -- Navigation (TOC) -- */
nav {
  background: #f8f9fb;
  border: 1px solid #dde3ea;
  border-radius: 6px;
  padding: 1rem 1.4rem;
  margin-bottom: 2.5rem;
}
nav ul { list-style: none; columns: 2; gap: 1rem }
nav li { margin: .2rem 0 }
nav a  { text-decoration: none; color: #0550ae; font-size: .9rem }
nav a:hover { text-decoration: underline }

/* -- Headings -- */
h1 { font-size: 2rem; margin-bottom: .4rem; color: #0d1117 }
h1 + p { color: #57606a; margin-bottom: 1.6rem }
h2 {
  font-size: 1.3rem;
  margin: 2.4rem 0 .6rem;
  padding-bottom: .35rem;
  border-bottom: 2px solid #dde3ea;
  color: #0d1117;
}
h3 { font-size: 1.05rem; margin: 1.6rem 0 .4rem; color: #24292f }

hr { border: none; border-top: 1px solid #e6e8eb; margin: 2rem 0 }

p  { margin: .65rem 0 }

/* -- Inline code -- */
code {
  font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, monospace;
  font-size: .87em;
  background: #eef1f5;
  padding: .12em .35em;
  border-radius: 4px;
  border: 1px solid #dde3ea;
}

/* -- Code blocks -- */
pre {
  background: #f6f8fa;
  border: 1px solid #dde3ea;
  border-radius: 8px;
  padding: 1.1rem 1.3rem;
  overflow-x: auto;
  margin: .7rem 0 1.1rem;
  line-height: 1.55;
}
pre code {
  font-size: .875rem;
  background: none;
  padding: 0;
  border: none;
  border-radius: 0;
}

/* -- Tables -- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: .8rem 0 1.2rem;
  font-size: .9rem;
}
th, td { text-align: left; padding: .45rem .85rem; border: 1px solid #dde3ea }
th { background: #f0f3f7; font-weight: 600 }
tr:nth-child(even) td { background: #fafbfc }

/* -- Lists -- */
ul { margin: .5rem 0 .8rem 1.6rem }
li { margin: .3rem 0 }

strong { font-weight: 600 }
em     { font-style: italic }

/* -- Lark syntax colours (VS Code Light palette) -- */
.k { color: #0000cc; font-weight: bold }   /* keyword           */
.t { color: #267f99 }                       /* type / constructor */
.s { color: #a31515 }                       /* string literal     */
.c { color: #6a9955; font-style: italic }   /* comment            */
.n { color: #098658 }                       /* numeric literal    */

@media (max-width: 600px) {
  article { padding: 1.4rem 1.2rem }
  nav ul  { columns: 1 }
}
"""

# -- HTML template --

TMPL = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A Tour of Lark</title>
<style>{css}</style>
</head>
<body>
<article>
{toc}
{body}
</article>
</body>
</html>
"""


# -- Entry point --

def main() -> None:
    md   = SRC.read_text(encoding="utf-8")
    page = TMPL.format(css=CSS, toc=_toc(md), body=_md(md))
    OUT.write_text(page, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"wrote {OUT}  ({size:,} bytes)")
    if "--no-open" not in sys.argv:
        webbrowser.open(OUT.as_uri())


if __name__ == "__main__":
    main()
