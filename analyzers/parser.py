from datetime import date

class ErrorSintactico(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consumir(self, tipo):
        token = self.actual()
        if token and token["token"] == tipo:
            self.pos += 1
            return token
        encontrado = token["token"] if token else "FIN DE ENTRADA"
        linea = token.get("linea", "?") if token else "?"
        raise ErrorSintactico(f"Línea {linea}: se esperaba {tipo}, se encontró {encontrado}.")

    def literal(self, tipo):
        return self.consumir(tipo)["lexema"]

    def inicio(self, operacion):
        self.consumir("PALABRA_RESERVADA")
        self.consumir("PARENTESIS_ABRE")

    def fin(self):
        self.consumir("PARENTESIS_CIERRA")
        self.consumir("PUNTO_COMA")

    def analizar_programa(self):
        instrucciones = []
        while self.actual() is not None:
            instrucciones.append(self.analizar_instruccion())
        if not instrucciones:
            raise ErrorSintactico("No se encontró ninguna instrucción.")
        return instrucciones

    def analizar_instruccion(self):
        token = self.actual()
        if not token or token["token"] != "PALABRA_RESERVADA":
            raise ErrorSintactico("Se esperaba una operación.")
        op = token["lexema"]
        self.inicio(op)
        if op == "REGISTRAR":
            nombre = self.literal("CADENA").strip('"'); self.consumir("COMA")
            concentracion = int(self.literal("NUMERO_ENTERO")); self.consumir("COMA")
            cantidad = int(self.literal("NUMERO_ENTERO")); self.consumir("COMA")
            precio_token = self.actual()
            if not precio_token or precio_token["token"] not in ("NUMERO_DECIMAL", "NUMERO_ENTERO"):
                raise ErrorSintactico("Se esperaba un precio numérico.")
            precio = float(precio_token["lexema"]); self.pos += 1
            self.consumir("COMA")
            vencimiento = self.literal("FECHA")
            self.fin()
            datos = {"operacion": op, "nombre": nombre, "concentracion": concentracion,
                     "cantidad": cantidad, "precio": precio, "vencimiento": vencimiento}
        elif op in ("ACTUALIZAR", "SALIDA"):
            nombre = self.literal("CADENA").strip('"'); self.consumir("COMA")
            cantidad = int(self.literal("NUMERO_ENTERO")); self.fin()
            datos = {"operacion": op, "nombre": nombre, "cantidad": cantidad}
        elif op in ("CONSULTAR", "ELIMINAR"):
            nombre = self.literal("CADENA").strip('"'); self.fin()
            datos = {"operacion": op, "nombre": nombre}
        else:
            raise ErrorSintactico(f"Operación no implementada: {op}.")
        datos["arbol"] = construir_arbol(datos)
        return datos

def construir_arbol(datos):
    op = datos["operacion"]
    hijos = [{"nombre": k.upper(), "valor": str(v)} for k, v in datos.items()
             if k not in ("operacion", "arbol")]
    return {"nombre": op, "hijos": hijos}
