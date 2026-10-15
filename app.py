from flask import Flask, render_template, request, jsonify
from models.analyzer import analyze

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_rule():
    data = request.get_json(silent=True) or {}
    source = data.get("rule", "")

    if not isinstance(source, str):
        return jsonify({
            "success": False,
            "message": "La regla debe ser un texto.",
            "error": "Tipo de dato no válido.",
            "tokens": [],
        }), 400

    if not source.strip():
        return jsonify({
            "success": False,
            "message": "Escribe una regla antes de analizarla.",
            "error": "Entrada vacía.",
            "tokens": [],
        }), 400

    result = analyze(source)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)

