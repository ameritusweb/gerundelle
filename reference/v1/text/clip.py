"""The gerund AST's text form. Only `parse` is here: it's all the domains use from the training code this file was taken
from, and keeping it alone means running them doesn't need torch."""
import re


def parse(s):
    """'kind(role:type, role, role=kind(...))' or a slot type -> (label, [(role, child), ...])."""
    s = s.strip()
    if "(" not in s:
        return ("slot:" + (s if s != "_" else ""), [])
    kind, body = s[:s.index("(")], s[s.index("(") + 1:-1]
    parts, depth, cur = [], 0, ""
    for ch in body:
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
            continue
        depth += ch == "("
        depth -= ch == ")"
        cur += ch
    if cur.strip():
        parts.append(cur.strip())
    kids = []
    for p in parts:
        m = re.match(r"^(\w+)([=:])(.*)$", p)
        if m and m.group(2) == "=":
            kids.append((m.group(1), parse(m.group(3))))
        elif m:
            kids.append((m.group(1), ("slot:" + m.group(3), [])))
        else:
            kids.append((p, ("slot:", [])))  # a flag role: 'event', 'not', 'hedge', ...
    return (kind, kids)
