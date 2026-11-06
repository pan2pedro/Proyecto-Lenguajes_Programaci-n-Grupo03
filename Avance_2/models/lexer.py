"""MODELO 1 - Analizador léxico: convierte el texto en TOKENS y LEXEMAS."""
import re

KEYWORDS = {"INICIO": "INICIO", "FIN": "FIN", "SI": "SI",
            "ENTONCES": "ENTONCES", "SINO": "SINO"}

# Categorías del lenguaje de reglas empresariales (edítalas para tu propio lenguaje)
CATEGORIES = {
    "DEPARTAMENTO": ["VENTAS", "ALMACEN", "FINANZAS", "COMPRAS", "LOGISTICA"],
    "VERBO": ["RECIBE", "VERIFICA", "PREPARA", "APRUEBA", "ENVIA", "REGISTRA", "COBRA"],
    "OBJETO": ["PEDIDO", "STOCK", "FACTURA", "PAGO", "ENVIO", "CLIENTE"],
    "ESTADO": ["DISPONIBLE", "AGOTADO", "PAGADO", "PENDIENTE"],
}

LOOKUP = dict(KEYWORDS)
for _tipo, _lista in CATEGORIES.items():
    for _w in _lista:
        LOOKUP[_w] = _tipo

SCANNER = re.compile(r"[^\W\d]\w*|;|\s+|.", re.UNICODE)


def tokenize(text):
    text = text.replace("\r\n", "\n")
    tokens = []
    for m in SCANNER.finditer(text):
        lex = m.group()
        if lex.isspace():
            continue
        pos = m.start()
        line = text.count("\n", 0, pos) + 1
        col = pos - (text.rfind("\n", 0, pos) + 1) + 1
        tipo = "PUNTOCOMA" if lex == ";" else LOOKUP.get(lex, "ERROR")
        tokens.append({"type": tipo, "lexeme": lex, "line": line, "col": col, "pos": pos})
    return tokens
