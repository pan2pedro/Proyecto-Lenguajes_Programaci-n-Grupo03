from datetime import date

def validar_operacion(datos, inventario):
    op, nombre = datos["operacion"], datos["nombre"].strip()
    if not nombre:
        return False, "El nombre del medicamento no puede estar vacío."
    actual = inventario.obtener(nombre)
    if op == "REGISTRAR":
        if actual:
            return False, "El medicamento ya existe en el inventario."
        if datos["concentracion"] <= 0:
            return False, "La concentración debe ser mayor que cero."
        if datos["cantidad"] < 0:
            return False, "La cantidad inicial no puede ser negativa."
        if datos["precio"] <= 0:
            return False, "El precio debe ser mayor que cero."
        try:
            vencimiento = date.fromisoformat(datos["vencimiento"])
        except ValueError:
            return False, "La fecha no es válida en el calendario."
        if vencimiento <= date.today():
            return False, "La fecha de vencimiento debe ser futura."
        return True, "Reglas de registro cumplidas."
    if not actual:
        return False, "El medicamento no está registrado."
    if op == "ACTUALIZAR" and datos["cantidad"] < 0:
        return False, "La cantidad no puede ser negativa."
    if op == "SALIDA":
        if datos["cantidad"] <= 0:
            return False, "La salida debe ser mayor que cero."
        if datos["cantidad"] > actual["cantidad"]:
            return False, f"Stock insuficiente: disponibles {actual['cantidad']}."
    return True, "Reglas empresariales cumplidas."
