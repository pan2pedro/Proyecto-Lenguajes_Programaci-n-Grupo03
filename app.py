from flask import Flask, render_template, request, jsonify
from analyzers.lexer import analizar_lexico, TOKEN_PATTERNS
from analyzers.parser import Parser, ErrorSintactico
from analyzers.semantic import validar_operacion
from analyzers.automata import automata_numero_entero
from models.inventario import Inventario

app = Flask(__name__)
app.config["SECRET_KEY"] = "cambiar-en-produccion"
db = Inventario()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/inventario")
def listar_inventario():
    return jsonify(db.listar())

@app.post("/api/analizar")
def analizar():
    payload = request.get_json(silent=True) or {}
    source = payload.get("texto", "")
    if not isinstance(source, str) or not source.strip():
        return jsonify({"estado": "ERROR", "mensaje": "Ingrese una instrucción o cargue un archivo."}), 400

    tokens, errores = analizar_lexico(source)
    if errores:
        return jsonify({
            "estado": "ERROR LÉXICO",
            "mensaje": "Se encontraron caracteres no reconocidos.",
            "errores": errores,
            "tokens": tokens,
            "regex": TOKEN_PATTERNS
        })

    try:
        instrucciones = Parser(tokens).analizar_programa()
    except ErrorSintactico as exc:
        return jsonify({
            "estado": "ERROR SINTÁCTICO",
            "mensaje": str(exc),
            "tokens": tokens,
            "regex": TOKEN_PATTERNS
        })

    resultados = []
    for datos in instrucciones:
        valido, mensaje = validar_operacion(datos, db)
        if not valido:
            resultados.append({"operacion": datos["operacion"], "valido": False, "mensaje": mensaje})
            continue
        try:
            resultado = db.ejecutar(datos)
            resultados.append({"operacion": datos["operacion"], "valido": True, "mensaje": resultado})
        except ValueError as exc:
            resultados.append({"operacion": datos["operacion"], "valido": False, "mensaje": str(exc)})

    todo_ok = all(item["valido"] for item in resultados)
    return jsonify({
        "estado": "OPERACIÓN PROCESADA" if todo_ok else "VALIDACIÓN EMPRESARIAL",
        "mensaje": "Análisis léxico y sintáctico completado.",
        "tokens": tokens,
        "regex": TOKEN_PATTERNS,
        "instrucciones": instrucciones,
        "resultados": resultados,
        "inventario": db.listar(),
        "automata": automata_numero_entero(),
        "arboles": [item["arbol"] for item in instrucciones]
    })

if __name__ == "__main__":
    app.run(debug=True)
