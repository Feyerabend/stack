#!/usr/bin/env python3
"""Balance-check lcore source: reports net paren depth per :let/:data line and
the depth at the top-level ` : ` type annotation of each `:let`. lcore is
line-based, so every :let must be one physical line and close to net 0.

Usage: parens.py FILE [FILE...]      (defaults to stdin)
Exit 1 if any line is unbalanced."""
import sys

def scan(line):
    depth = 0; mind = 0
    for c in line:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            mind = min(mind, depth)
    return depth, mind

def check(name, text):
    bad = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not (s.startswith(':let') or s.startswith(':data') or s.startswith('data ')):
            continue
        depth, mind = scan(line)
        flag = ''
        if depth != 0:
            flag = f'  <<< NET {depth:+d}'; bad = True
        if mind < 0:
            flag += f'  <<< went NEGATIVE ({mind})'; bad = True
        tok = s.split()[1] if len(s.split()) > 1 else '?'
        if flag:
            print(f'{name}:{i}: {tok}{flag}')
    return bad

if __name__ == '__main__':
    files = sys.argv[1:]
    bad = False
    if not files:
        bad = check('<stdin>', sys.stdin.read())
    for f in files:
        bad |= check(f, open(f).read())
    if not bad:
        print('OK: all :let/:data lines balanced')
    sys.exit(1 if bad else 0)
