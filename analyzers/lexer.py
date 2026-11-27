import re

TOKEN_PATTERNS = [
    ("PALABRA_RESERVADA", r"\b(?:REGISTRAR|ACTUALIZAR|CONSULTAR|SALIDA|ELIMINAR)\b"),
    ("CADENA", r'"[^"\n]*"'),
    ("FECHA", r"\d{4}-\d{2}-\d{2}"),
    ("NUMERO_DECIMAL", r"\d+\.\d{1,2}"),
    ("NUMERO_ENTERO", r"\d+"),
    ("PARENTESIS_ABRE", r"\("),
    ("PARENTESIS_CIERRA", r"\)"),
    ("COMA", r","),
    ("PUNTO_COMA", r";"),
    ("ASIGNACION", r"="),
]

def analizar_lexico(texto):
    patron = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_PATTERNS))
    tokens, errores = [], []
    pos, linea = 0, 1
    while pos < len(texto):
        if texto[pos].isspace():
            if texto[pos] == "\n":
                linea += 1
            pos += 1
            continue
        match = patron.match(texto, pos)
        if match:
            tipo, lexema = match.lastgroup, match.group()
            tokens.append({"token": tipo, "lexema": lexema, "linea": linea, "posicion": pos})
            linea += lexema.count("\n")
            pos = match.end()
        else:
            errores.append({"caracter": texto[pos], "linea": linea, "posicion": pos})
            pos += 1
    return tokens, errores
