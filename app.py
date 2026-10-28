from flask import Flask, render_template, request, jsonify
from models.analyzer import analyze_source, token_details

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify({"error": "El contenido debe ser texto."}), 400
    if len(source) > 100_000:
        return jsonify({"error": "El texto supera el límite de 100 000 caracteres."}), 413
    return jsonify(analyze_source(source))

@app.get("/token/<token_name>")
def token_info(token_name):
    info = token_details(token_name)
    if info is None:
        return jsonify({"error": "Token desconocido."}), 404
    return jsonify(info)

if __name__ == "__main__":
    app.run(debug=True)
