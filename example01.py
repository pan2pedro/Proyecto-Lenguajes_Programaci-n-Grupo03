from flask import Flask

app = Flask(__name__)

@app.route("/")
def hola_mundo():
    return "Hola Mundo con Flask"

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
