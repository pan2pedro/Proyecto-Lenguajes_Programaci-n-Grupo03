"""MODELO 3 - Analizador sintáctico/semántico: valida reglas y genera árboles de derivación."""
from html import escape

GRAMMAR = {  # gramática libre de contexto del lenguaje
    "SENTENCIA": [["ACCION", "PUNTOCOMA"], ["CONDICION", "PUNTOCOMA"], ["INICIO", "PUNTOCOMA"],
                  ["FIN", "PUNTOCOMA"], ["SINO", "PUNTOCOMA"]],
    "ACCION": [["DEPARTAMENTO", "VERBO", "OBJETO"]],
    "CONDICION": [["SI", "OBJETO", "ESTADO", "ENTONCES"]],
}
PATTERNS = {"INICIO": ["INICIO"], "FIN": ["FIN"], "SINO": ["SINO"],
            "CONDICION": ["SI", "OBJETO", "ESTADO", "ENTONCES"],
            "ACCION": ["DEPARTAMENTO", "VERBO", "OBJETO"]}
FIRST = {"INICIO": "INICIO", "FIN": "FIN", "SINO": "SINO", "SI": "CONDICION", "DEPARTAMENTO": "ACCION"}
NOMBRE = {"INICIO": "INICIO ;", "FIN": "FIN ;", "SINO": "SINO ;",
          "CONDICION": "SI OBJETO ESTADO ENTONCES ;", "ACCION": "DEPARTAMENTO VERBO OBJETO ;"}

VERBO_OBJETO = {  # reglas semánticas
    "RECIBE": ["PEDIDO", "PAGO"], "VERIFICA": ["STOCK", "PAGO", "PEDIDO", "CLIENTE"],
    "PREPARA": ["PEDIDO", "ENVIO"], "APRUEBA": ["PEDIDO", "PAGO"],
    "ENVIA": ["PEDIDO", "FACTURA", "ENVIO"], "REGISTRA": ["PEDIDO", "CLIENTE", "FACTURA", "PAGO"],
    "COBRA": ["FACTURA", "PAGO"]}
OBJETO_ESTADO = {"STOCK": ["DISPONIBLE", "AGOTADO"], "PAGO": ["PAGADO", "PENDIENTE"],
                 "FACTURA": ["PAGADO", "PENDIENTE"], "PEDIDO": ["PENDIENTE", "DISPONIBLE"],
                 "ENVIO": ["PENDIENTE"], "CLIENTE": ["PENDIENTE"]}


def _check(toks):
    body = [t for t in toks if t["type"] != "PUNTOCOMA"]
    has_semi = toks[-1]["type"] == "PUNTOCOMA"
    r = {"line": toks[0]["line"], "text": " ".join(t["lexeme"] for t in toks), "kind": None,
         "ok": False, "rule": "—", "detail": "", "body": body, "all": toks}
    errs = [t for t in body if t["type"] == "ERROR"]
    if errs:
        r["detail"] = f"Lexema no reconocido: '{errs[0]['lexeme']}' (columna {errs[0]['col']})"
        return r
    if not body:
        r["detail"] = "Sentencia vacía"
        return r
    kind = FIRST.get(body[0]["type"])
    if not kind:
        r["detail"] = f"Una regla no puede comenzar con {body[0]['type']} '{body[0]['lexeme']}'"
        return r
    r["kind"], r["rule"] = kind, NOMBRE[kind]
    pat, found, detail = PATTERNS[kind], [t["type"] for t in body], None
    for i, exp in enumerate(pat):
        if i >= len(found):
            detail = f"Se esperaba {exp} después de '{body[i-1]['lexeme']}'"; break
        if found[i] != exp:
            detail = f"Se esperaba {exp} y se encontró {found[i]} '{body[i]['lexeme']}'"; break
    else:
        if len(found) > len(pat):
            detail = f"Sobran símbolos desde '{body[len(pat)]['lexeme']}'"
    if detail is None and not has_semi:
        detail = "Falta ';' al final de la regla"
    if detail is None and kind == "ACCION":
        v, o = body[1]["lexeme"], body[2]["lexeme"]
        if o not in VERBO_OBJETO[v]:
            detail = f"Error semántico: {v} no es aplicable a {o}"
    if detail is None and kind == "CONDICION":
        o, e = body[1]["lexeme"], body[2]["lexeme"]
        if e not in OBJETO_ESTADO[o]:
            detail = f"Error semántico: el estado {e} no aplica a {o}"
    r["ok"], r["detail"] = detail is None, detail or "Regla válida"
    return r


def validate(tokens):
    stmts, cur = [], []
    for t in tokens:
        cur.append(t)
        if t["type"] == "PUNTOCOMA":
            stmts.append(cur); cur = []
    if cur:
        stmts.append(cur)
    res = [_check(s) for s in stmts]
    extra = []
    if res:
        if res[0]["kind"] != "INICIO":
            extra.append((res[0]["line"], "El programa debe comenzar con INICIO;"))
        if not any(r["kind"] == "FIN" for r in res):
            extra.append((res[-1]["line"], "Falta la regla FIN; al final del programa"))
        elif res[-1]["kind"] != "FIN":
            extra.append((res[-1]["line"], "Hay reglas después de FIN;"))
        open_si, seen_inicio = 0, False
        for r in res:
            if r["kind"] == "INICIO":
                if seen_inicio:
                    extra.append((r["line"], "INICIO; aparece más de una vez"))
                seen_inicio = True
            elif r["kind"] == "CONDICION":
                open_si += 1
            elif r["kind"] == "SINO":
                if open_si == 0:
                    extra.append((r["line"], "SINO; sin un SI ... ENTONCES; previo"))
                else:
                    open_si -= 1
    rows = [{"line": r["line"], "rule": r["rule"], "ok": r["ok"], "detail": r["detail"], "text": r["text"]} for r in res]
    for ln, d in extra:
        rows.append({"line": ln, "rule": "ESTRUCTURA", "ok": False, "detail": d, "text": ""})
    if res and not extra:
        rows.append({"line": "—", "rule": "ESTRUCTURA", "ok": True, "detail": "INICIO ... FIN correcto", "text": ""})
    return res, rows


# ---------- Árboles ----------
def _first(sym):
    return {sym} if sym not in GRAMMAR else set().union(*[_first(p[0]) for p in GRAMMAR[sym]])


def _build(sym, toks):
    if sym not in GRAMMAR:
        return {"label": sym, "lexeme": toks.pop(0)["lexeme"], "children": []}
    nxt = toks[0]["type"]
    for prod in GRAMMAR[sym]:
        if nxt in _first(prod[0]):
            return {"label": sym, "children": [_build(s, toks) for s in prod]}


def _html(n):
    txt = escape(n["label"]) + (f' <span class="lex">“{escape(n["lexeme"])}”</span>' if "lexeme" in n else "")
    if not n["children"]:
        return f"<li>{txt}</li>"
    return f"<li>{txt}<ul>" + "".join(_html(c) for c in n["children"]) + "</ul></li>"


def _derivation(tree):
    forms = [[tree]]
    while True:
        cur = forms[-1]
        i = next((k for k, n in enumerate(cur) if n["children"]), None)
        if i is None:
            break
        forms.append(cur[:i] + cur[i]["children"] + cur[i + 1:])
    steps = [" ".join(n["label"] for n in f) for f in forms]
    steps.append(" ".join(n.get("lexeme", n["label"]) for n in forms[-1]))
    return steps


def _node(label, *children):
    return {"label": label, "children": list(children)}


def _semantic(kind, b):
    lx = [t["lexeme"] for t in b]
    if kind == "ACCION":
        return _node("Acción", _node(f"actor: {lx[0]}"), _node(f"operación: {lx[1]}"), _node(f"objeto: {lx[2]}"))
    if kind == "CONDICION":
        return _node("Condición", _node(f"evalúa: {lx[1]}"), _node(f"estado esperado: {lx[2]}"),
                     _node("efecto: ejecuta las reglas siguientes"))
    return _node({"INICIO": "Inicio del proceso", "FIN": "Fin del proceso", "SINO": "Rama alternativa"}[kind])


def trees_for(r):
    tree = _build("SENTENCIA", list(r["all"]))
    return {"tree": "<ul class='tree'>" + _html(tree) + "</ul>", "derivation": _derivation(tree),
            "semantic": "<ul class='tree'>" + _html(_semantic(r["kind"], r["body"])) + "</ul>"}
