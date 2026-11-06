"""CONTROLADOR - rutas de Flask. Une los modelos (lexer, automata, parser) con la vista (templates)."""
from flask import Flask, render_template, request
from models.lexer import tokenize
from models.automata import build_all, RegexError
from models.parser import validate, trees_for

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1 MB

# >>> EDITA ESTE TEXTO: es el enunciado de tu proyecto (vacío de conocimiento, 6 antecedentes, solución) <<<
ENUNCIADO = {
    "titulo": "RuleCheck: detección de errores en procesos empresariales",
    "texto": ("Los 6 antecedentes revisados no ofrecen una herramienta que valide formalmente, con autómatas "
              "y gramáticas, las reglas escritas por las áreas de una empresa. Este proyecto define un lenguaje "
              "de reglas empresariales, identifica sus tokens y lexemas, genera sus expresiones regulares y "
              "autómatas (AFND/AFD) y valida la sintaxis y semántica del proceso."),
}

EJEMPLO = """INICIO;
VENTAS RECIBE PEDIDO;
VENTAS VERIFICA STOCK;
SI STOCK DISPONIBLE ENTONCES;
ALMACEN PREPARA PEDIDO;
SINO;
COMPRAS REGISTRA PEDIDO;
FINANZAS COBRA FACTURA;
FIN;"""


def analizar(texto):
    tokens = tokenize(texto)
    stmts, rows = validate(tokens)

    # --- ER por lexema y por clase (tipo) ---
    por_tipo, vistos = {}, {}
    for t in tokens:
        if t["type"] == "ERROR":
            continue
        vistos.setdefault(t["lexeme"], t["type"])
        por_tipo.setdefault(t["type"], [])
        if t["lexeme"] not in por_tipo[t["type"]]:
            por_tipo[t["type"]].append(t["lexeme"])

    er_rows, automatas = [], []
    for lex, tipo in vistos.items():
        er_rows.append({"tipo": tipo, "lexema": lex, "er": lex})
        automatas.append({"label": f"{lex}  ({tipo})", "er": lex})
    for tipo, lexs in por_tipo.items():
        if len(lexs) > 1:
            er = "(" + "|".join(lexs) + ")"
            er_rows.append({"tipo": tipo, "lexema": "(clase completa)", "er": er})
            automatas.append({"label": f"Clase {tipo}", "er": er})
    for a in automatas:
        try:
            a.update(build_all(a["er"]))
        except RegexError as e:
            a["error"] = str(e)

    # --- árboles para cada regla válida ---
    arboles = []
    for r in stmts:
        if r["ok"]:
            arboles.append({"label": f"Línea {r['line']}: {r['text']}", **trees_for(r)})

    return {"tokens": tokens, "n_tokens": len(tokens), "er_rows": er_rows, "rows": rows,
            "errores": sum(1 for r in rows if not r["ok"]), "automatas": automatas, "arboles": arboles,
            "vacio": not tokens}


@app.route("/", methods=["GET", "POST"])
def index():
    texto, resultado, aviso = EJEMPLO, None, None
    if request.method == "POST":
        f = request.files.get("archivo")
        if f and f.filename:
            if f.filename.lower().endswith(".txt"):
                texto = f.read().decode("utf-8", "replace")
            else:
                aviso = "Solo se admiten archivos .txt"
                texto = request.form.get("texto", "")
        else:
            texto = request.form.get("texto", "")
        if not aviso:
            resultado = analizar(texto)
    return render_template("index.html", texto=texto, r=resultado, aviso=aviso, enunciado=ENUNCIADO)


if __name__ == "__main__":
    app.run(debug=True)
