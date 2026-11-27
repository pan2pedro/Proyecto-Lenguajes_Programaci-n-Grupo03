def automata_numero_entero():
    # AFD equivalente al patrón [0-9]+
    return {
        "token": "NUMERO_ENTERO",
        "regex": "[0-9]+",
        "estados": ["q0", "q1"],
        "alfabeto": "0-9",
        "inicial": "q0",
        "finales": ["q1"],
        "transiciones": [
            {"desde": "q0", "entrada": "0-9", "hasta": "q1"},
            {"desde": "q1", "entrada": "0-9", "hasta": "q1"}
        ],
        "nota": "El AFND y el AFD de este patrón son equivalentes; q1 es estado de aceptación."
    }
