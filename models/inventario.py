import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "farmacia.db"

class Inventario:
    def __init__(self, path=DB_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.conectar() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS medicamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    concentracion INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio REAL NOT NULL,
                    vencimiento TEXT NOT NULL
                )
            """)

    def conectar(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def listar(self):
        with self.conectar() as con:
            return [dict(r) for r in con.execute(
                "SELECT * FROM medicamentos ORDER BY nombre"
            ).fetchall()]

    def obtener(self, nombre):
        with self.conectar() as con:
            row = con.execute(
                "SELECT * FROM medicamentos WHERE nombre = ?", (nombre,)
            ).fetchone()
            return dict(row) if row else None

    def ejecutar(self, datos):
        op, nombre = datos["operacion"], datos["nombre"]
        with self.conectar() as con:
            if op == "REGISTRAR":
                con.execute("""INSERT INTO medicamentos
                    (nombre, concentracion, cantidad, precio, vencimiento)
                    VALUES (?, ?, ?, ?, ?)""",
                    (nombre, datos["concentracion"], datos["cantidad"],
                     datos["precio"], datos["vencimiento"]))
                return f"Medicamento {nombre} registrado correctamente."
            if op == "ACTUALIZAR":
                con.execute("UPDATE medicamentos SET cantidad=? WHERE nombre=?",
                            (datos["cantidad"], nombre))
                return f"Existencias de {nombre} actualizadas."
            if op == "SALIDA":
                con.execute("UPDATE medicamentos SET cantidad=cantidad-? WHERE nombre=?",
                            (datos["cantidad"], nombre))
                return f"Salida registrada. Se retiraron {datos['cantidad']} unidades."
            if op == "CONSULTAR":
                row = con.execute("SELECT * FROM medicamentos WHERE nombre=?",
                                  (nombre,)).fetchone()
                return dict(row)
            if op == "ELIMINAR":
                con.execute("DELETE FROM medicamentos WHERE nombre=?", (nombre,))
                return f"Registro de {nombre} eliminado."
        raise ValueError("Operación no reconocida.")
