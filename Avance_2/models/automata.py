"""MODELO 2 - ER -> AFND (Thompson) -> AFD (subconjuntos) -> tabla, quíntupla y gráfico SVG.
El gráfico se genera por código (no es una imagen)."""
import math
from collections import defaultdict, deque
from html import escape

EPS = "ε"


class RegexError(ValueError):
    pass


# ---------- 1. Parser de expresiones regulares: | * + ? ( ) y concatenación ----------
def parse_regex(er):
    pos = 0

    def peek():
        return er[pos] if pos < len(er) else None

    def expr():
        nonlocal pos
        node = term()
        while peek() == "|":
            pos += 1
            node = ("alt", node, term())
        return node

    def term():
        node = None
        while peek() is not None and peek() not in "|)":
            f = factor()
            node = f if node is None else ("cat", node, f)
        return node or ("eps",)

    def factor():
        nonlocal pos
        node = atom()
        while peek() in ("*", "+", "?"):
            node = ({"*": "star", "+": "plus", "?": "opt"}[er[pos]], node)
            pos += 1
        return node

    def atom():
        nonlocal pos
        c = peek()
        if c == "(":
            pos += 1
            n = expr()
            if peek() != ")":
                raise RegexError("Falta ')'")
            pos += 1
            return n
        if c is None or c in "*+?|)":
            raise RegexError(f"Símbolo inesperado en la posición {pos}")
        pos += 1
        return ("sym", c)

    ast = expr()
    if pos != len(er):
        raise RegexError("Expresión regular mal formada")
    return ast


# ---------- 2. ER -> AFND (construcción de Thompson) ----------
def regex_to_nfa(er):
    ast = parse_regex(er)
    n = [0]
    delta = defaultdict(lambda: defaultdict(set))

    def new():
        n[0] += 1
        return n[0] - 1

    def add(a, s, b):
        delta[a][s].add(b)

    def build(node):
        t = node[0]
        if t == "sym":
            s, f = new(), new(); add(s, node[1], f); return s, f
        if t == "eps":
            s, f = new(), new(); add(s, EPS, f); return s, f
        if t == "cat":
            s1, f1 = build(node[1]); s2, f2 = build(node[2])
            add(f1, EPS, s2); return s1, f2
        if t == "alt":
            s, f = new(), new()
            s1, f1 = build(node[1]); s2, f2 = build(node[2])
            add(s, EPS, s1); add(s, EPS, s2); add(f1, EPS, f); add(f2, EPS, f)
            return s, f
        s1, f1 = build(node[1])
        s, f = new(), new()
        add(s, EPS, s1); add(f1, EPS, f)
        if t in ("star", "plus"):
            add(f1, EPS, s1)
        if t in ("star", "opt"):
            add(s, EPS, f)
        return s, f

    start, final = build(ast)
    order, seen, q = [start], {start}, deque([start])      # renumerar q0, q1, ... por BFS
    while q:
        u = q.popleft()
        for sym in sorted(delta[u], key=lambda x: (x != EPS, x)):
            for v in sorted(delta[u][sym]):
                if v not in seen:
                    seen.add(v); order.append(v); q.append(v)
    names = {old: f"q{i}" for i, old in enumerate(order)}
    nd = {names[u]: {s: sorted((names[v] for v in ts), key=lambda x: int(x[1:]))
                     for s, ts in delta[u].items()} for u in order}
    alphabet = sorted({s for m in nd.values() for s in m if s != EPS})
    return {"kind": "AFND", "states": [names[u] for u in order], "alphabet": alphabet,
            "delta": nd, "start": names[start], "accept": [names[final]]}


# ---------- 3. AFND -> AFD (construcción de subconjuntos) ----------
def _closure(delta, states):
    res, stack = set(states), list(states)
    while stack:
        u = stack.pop()
        for v in delta.get(u, {}).get(EPS, []):
            if v not in res:
                res.add(v); stack.append(v)
    return frozenset(res)


def nfa_to_dfa(nfa):
    d = nfa["delta"]
    start = _closure(d, {nfa["start"]})
    sets, idx, rows = [start], {start: 0}, {}
    i = 0
    while i < len(sets):
        S = sets[i]; row = {}
        for a in nfa["alphabet"]:
            T = set()
            for u in S:
                T.update(d.get(u, {}).get(a, []))
            if not T:
                continue
            T = _closure(d, T)
            if T not in idx:
                idx[T] = len(sets); sets.append(T)
            row[a] = [idx[T]]
        rows[i] = row
        i += 1
    nm = lambda k: chr(65 + k) if k < 26 else f"S{k}"
    delta = {nm(k): {a: [nm(t[0])] for a, t in r.items()} for k, r in rows.items()}
    acc = [nm(k) for k, S in enumerate(sets) if set(nfa["accept"]) & S]
    subsets = [(nm(k), "{" + ", ".join(sorted(S, key=lambda x: int(x[1:]))) + "}") for k, S in enumerate(sets)]
    return {"kind": "AFD", "states": [nm(k) for k in range(len(sets))], "alphabet": nfa["alphabet"],
            "delta": delta, "start": "A", "accept": acc, "subsets": subsets}


# ---------- 4. Tabla, transiciones y quíntupla ----------
def table(a):
    rows = []
    for s in a["states"]:
        mark = ("→" if s == a["start"] else "") + ("*" if s in a["accept"] else "")
        cells = [(a["delta"].get(s, {}).get(c) or ["—"])[0] for c in a["alphabet"]]
        rows.append({"state": f"{mark}{s}", "cells": cells})
    return {"cols": a["alphabet"], "rows": rows}


def transitions(a):
    return [f"δ({s}, {c}) = {t[0]}" for s in a["states"] for c, t in a["delta"].get(s, {}).items()]


def quintuple(a):
    return {"Q": "{" + ", ".join(a["states"]) + "}",
            "Sigma": "{" + ", ".join(a["alphabet"]) + "}",
            "delta": "δ: Q × Σ → Q  (ver tabla y lista de transiciones)",
            "q0": a["start"], "F": "{" + ", ".join(a["accept"]) + "}"}


# ---------- 5. Gráfico SVG generado por código ----------
def to_svg(a, uid="a"):
    R, DX, DY = 20, 95, 78
    adj, edges = defaultdict(list), {}
    for u, m in a["delta"].items():
        for s, ts in m.items():
            for v in ts:
                labs = edges.setdefault((u, v), [])
                if s not in labs:
                    labs.append(s)
                if v not in adj[u]:
                    adj[u].append(v)
    depth, q = {a["start"]: 0}, deque([a["start"]])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in depth:
                depth[v] = depth[u] + 1; q.append(v)
    layers = defaultdict(list)
    for s in a["states"]:
        depth.setdefault(s, 0); layers[depth[s]].append(s)
    maxn, maxd = max(len(l) for l in layers.values()), max(layers)
    W, H = 120 + maxd * DX + 40, 110 + (maxn - 1) * DY + 40
    pos = {}
    for d, l in layers.items():
        off = (maxn - len(l)) * DY / 2
        for i, s in enumerate(l):
            pos[s] = (60 + d * DX, 85 + off + i * DY)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<style>.e{fill:none;stroke:#334155;stroke-width:1.5}.n{fill:#fff;stroke:#334155;stroke-width:1.6}'
           '.s{fill:#dbeafe}.t{font:13px sans-serif;fill:#0f172a}</style>',
           f'<defs><marker id="{uid}m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#334155"/></marker></defs>']
    sx0, sy0 = pos[a["start"]]
    out.append(f'<line x1="{sx0-45}" y1="{sy0}" x2="{sx0-R-2}" y2="{sy0}" class="e" marker-end="url(#{uid}m)"/>')

    def trim(px, py, tx, ty, r):
        dd = math.hypot(tx - px, ty - py) or 1
        return px + (tx - px) / dd * r, py + (ty - py) / dd * r

    for (u, v), labs in edges.items():
        lab = escape(",".join(labs))
        x1, y1 = pos[u]; x2, y2 = pos[v]
        if u == v:
            out.append(f'<path d="M{x1-9},{y1-R+2} C{x1-34},{y1-R-38} {x1+34},{y1-R-38} {x1+9},{y1-R+2}" '
                       f'class="e" marker-end="url(#{uid}m)"/>')
            out.append(f'<text x="{x1}" y="{y1-R-32}" class="t" text-anchor="middle">{lab}</text>')
            continue
        L = math.hypot(x2 - x1, y2 - y1) or 1
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        rev = (v, u) in edges
        c = 26 if rev else (34 if abs(depth[v] - depth[u]) != 1 else 0)
        cx, cy = (x1 + x2) / 2 + nx * c * 2, (y1 + y2) / 2 + ny * c * 2
        sx, sy = trim(x1, y1, cx, cy, R); ex, ey = trim(x2, y2, cx, cy, R + 3)
        out.append(f'<path d="M{sx:.1f},{sy:.1f} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" class="e" marker-end="url(#{uid}m)"/>')
        mx, my = .25 * sx + .5 * cx + .25 * ex, .25 * sy + .5 * cy + .25 * ey
        lx, ly = (mx + nx * 10, my + ny * 10) if c else (mx, my - 7)
        out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" class="t" text-anchor="middle">{lab}</text>')

    for s, (x, y) in pos.items():
        out.append(f'<circle cx="{x}" cy="{y}" r="{R}" class="n{" s" if s == a["start"] else ""}"/>')
        if s in a["accept"]:
            out.append(f'<circle cx="{x}" cy="{y}" r="{R-5}" class="n" style="fill:none"/>')
        out.append(f'<text x="{x}" y="{y+4}" class="t" text-anchor="middle">{escape(s)}</text>')
    out.append("</svg>")
    return "".join(out)


def build_all(er):
    """Devuelve todo lo que pide la Etapa 2 para una ER."""
    nfa = regex_to_nfa(er)
    dfa = nfa_to_dfa(nfa)
    return {"er": er,
            "afnd": {"svg": to_svg(nfa, "n"), "n_states": len(nfa["states"])},
            "afd": {"svg": to_svg(dfa, "d"), "table": table(dfa), "transitions": transitions(dfa),
                    "quintuple": quintuple(dfa), "subsets": dfa["subsets"]}}
