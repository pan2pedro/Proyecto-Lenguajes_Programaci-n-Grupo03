"""Analizador léxico/sintáctico didáctico para el lenguaje empresarial del prototipo."""
import re
from collections import deque

TOKEN_RULES = [
    ("T_INICIO", r"INICIO", ["INICIO"]),
    ("T_FIN", r"FIN", ["FIN"]),
    ("T_SI", r"SI", ["SI"]),
    ("T_ENTONCES", r"ENTONCES", ["ENTONCES"]),
    ("T_ACTOR", r"VENTAS | ALMACEN | CLIENTE", ["VENTAS", "ALMACEN", "CLIENTE"]),
    ("T_VERBO", r"RECIBE | VERIFICA | REGISTRA | PREPARA", ["RECIBE", "VERIFICA", "REGISTRA", "PREPARA"]),
    ("T_OBJETO", r"PEDIDO | PRODUCTO", ["PEDIDO", "PRODUCTO"]),
    ("T_CONDICION", r"STOCK | PAGO | DISPONIBLE", ["STOCK", "PAGO", "DISPONIBLE"]),
    ("T_PUNTO_COMA", r";", [";"]),
]
KEYWORDS = {}
for token_type, _regex, lexemes in TOKEN_RULES:
    for lexeme in lexemes:
        KEYWORDS[lexeme] = token_type

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|;", re.ASCII)
REGEX_ROWS = [{"type": t, "regex": r.replace(" | ", " | "), "lexemes": lex} for t, r, lex in TOKEN_RULES]
REGEX_ROWS.append({"type": "T_ESPACIO", "regex": r"[ \\t\\n]+", "lexemes": []})

def lex(source):
    tokens, errors = [], []
    line = column = 1
    pos = 0
    while pos < len(source):
        ch = source[pos]
        if ch.isspace():
            if ch == "\n":
                line, column = line + 1, 1
            else:
                column += 1
            pos += 1
            continue
        match = TOKEN_RE.match(source, pos)
        if not match:
            errors.append({"line": line, "column": column, "lexeme": ch,
                           "message": f"Carácter no reconocido: {ch!r}"})
            pos += 1
            column += 1
            continue
        lexeme = match.group(0)
        token_type = "T_PUNTO_COMA" if lexeme == ";" else KEYWORDS.get(lexeme)
        if token_type is None:
            errors.append({"line": line, "column": column, "lexeme": lexeme,
                           "message": f"Lexema no reconocido: {lexeme}"})
        else:
            tokens.append({"token": token_type, "lexeme": lexeme, "line": line,
                           "column": column, "position": pos + 1})
        pos = match.end()
        column += len(lexeme)
    return tokens, errors

def validate_lines(source):
    """Valida una gramática de líneas, acorde al ejemplo del documento."""
    results = []
    for number, raw in enumerate(source.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line == "INICIO;":
            valid, message = True, "Declaración de inicio válida."
        elif line == "FIN;":
            valid, message = True, "Declaración de fin válida."
        elif re.fullmatch(r"(VENTAS|ALMACEN|CLIENTE) (RECIBE|VERIFICA|REGISTRA|PREPARA) (PEDIDO|PRODUCTO|STOCK|PAGO|DISPONIBLE);", line):
            valid, message = True, "Instrucción empresarial válida."
        elif re.fullmatch(r"SI (STOCK|PAGO|DISPONIBLE) (STOCK|PAGO|DISPONIBLE) ENTONCES;", line):
            valid, message = True, "Condición SI/ENTONCES válida."
        else:
            valid, message = False, "Sintaxis no válida. Revise los tokens, el orden y el punto y coma."
        results.append({"line": number, "rule": line, "valid": valid, "message": message})
    return results

def build_trie(words):
    """Construye un autómata de prefijos para una expresión regular de alternativas literales."""
    transitions = {}
    accepting = set()
    next_state = 1
    for word in words:
        state = 0
        for char in word:
            key = (state, char)
            if key not in transitions:
                transitions[key] = next_state
                next_state += 1
            state = transitions[key]
        accepting.add(state)
    states = list(range(next_state))
    alphabet = sorted({char for word in words for char in word})
    table = []
    for state in states:
        row = {"state": state, "accepting": state in accepting, "transitions": {}}
        for char in alphabet:
            dest = transitions.get((state, char))
            row["transitions"][char] = dest
        table.append(row)
    return states, alphabet, transitions, accepting, table

def automaton_payload(token_type):
    rule = next((r for r in TOKEN_RULES if r[0] == token_type), None)
    if not rule:
        return None
    _name, regex, words = rule
    states, alphabet, trans, finals, table = build_trie(words)
    edges = [{"from": s, "symbol": ch, "to": d} for (s, ch), d in trans.items()]
    q = [f"q{s}" for s in states]
    delta = [f"δ(q{s}, {ch}) = q{d}" for (s, ch), d in trans.items()]
    return {
        "token": token_type, "regex": regex, "lexemes": words,
        "nfa": {"states": q, "alphabet": alphabet, "start": "q0",
                "finals": [f"q{s}" for s in sorted(finals)], "edges": edges,
                "table": table},
        # The trie is deterministic, so the subset construction results in the same DFA.
        "dfa": {"states": q, "alphabet": alphabet, "start": "q0",
                "finals": [f"q{s}" for s in sorted(finals)], "edges": edges,
                "table": table},
        "transformation": [
            {"nfa_state": f"{{q{s}}}", "dfa_state": f"D{s}",
             "subset": f"{{q{s}}}"} for s in states
        ],
        "delta": delta,
        "grammar": "TOKEN → " + " | ".join(repr(w) for w in words),
    }

def token_details(token_name):
    return automaton_payload(token_name)

def build_trees(line):
    """Árboles de derivación y semántico sencillos para cada regla reconocida."""
    if line == "INICIO;":
        syntax = {"name": "Línea", "children": [{"name": "INICIO"}, {"name": ";"}]}
        semantic = {"name": "InicioPrograma", "children": [{"name": "abre bloque"}]}
    elif line == "FIN;":
        syntax = {"name": "Línea", "children": [{"name": "FIN"}, {"name": ";"}]}
        semantic = {"name": "FinPrograma", "children": [{"name": "cierra bloque"}]}
    else:
        match = re.fullmatch(r"(VENTAS|ALMACEN|CLIENTE) (RECIBE|VERIFICA|REGISTRA|PREPARA) (PEDIDO|PRODUCTO|STOCK|PAGO|DISPONIBLE);", line)
        if match:
            actor, verb, obj = match.groups()
            syntax = {"name": "Instrucción", "children": [
                {"name": "Actor", "children": [{"name": actor}]},
                {"name": "Verbo", "children": [{"name": verb}]},
                {"name": "Complemento", "children": [{"name": obj}]},
                {"name": ";"}
            ]}
            semantic = {"name": "AcciónEmpresarial", "children": [
                {"name": f"actor = {actor}"},
                {"name": f"acción = {verb}"},
                {"name": f"objeto/condición = {obj}"}
            ]}
        else:
            match = re.fullmatch(r"SI (STOCK|PAGO|DISPONIBLE) (STOCK|PAGO|DISPONIBLE) ENTONCES;", line)
            if not match:
                return None, None
            cond1, cond2 = match.groups()
            syntax = {"name": "Condición", "children": [
                {"name": "SI"}, {"name": cond1}, {"name": cond2},
                {"name": "ENTONCES"}, {"name": ";"}
            ]}
            semantic = {"name": "Condicional", "children": [
                {"name": f"condición: {cond1} {cond2}"},
                {"name": "ejecutar bloque si se cumple"}
            ]}
    return syntax, semantic

def analyze_source(source):
    tokens, lexical_errors = lex(source)
    lines = validate_lines(source)
    for row in lines:
        row["syntax_tree"], row["semantic_tree"] = build_trees(row["rule"]) if row["valid"] else (None, None)
    token_types = []
    for token in tokens:
        if token["token"] not in token_types:
            token_types.append(token["token"])
    automata = {name: automaton_payload(name) for name in token_types}
    return {
        "source": source,
        "tokens": tokens,
        "regex_table": REGEX_ROWS,
        "lines": lines,
        "lexical_errors": lexical_errors,
        "automata": automata,
        "token_types": token_types,
        "summary": {
            "tokens": len(tokens),
            "valid_lines": sum(1 for row in lines if row["valid"]),
            "invalid_lines": sum(1 for row in lines if not row["valid"]),
            "lexical_errors": len(lexical_errors),
        },
    }
