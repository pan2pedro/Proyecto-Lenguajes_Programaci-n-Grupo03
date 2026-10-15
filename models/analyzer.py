import re

TOKEN_PATTERN = re.compile(
    r"""
    (?P<SPACE>\s+)
    |(?P<NUMBER>\d+(?:\.\d+)?)
    |(?P<STRING>'[^']*'|"[^"]*")
    |(?P<OP>>=|<=|==|!=|>|<)
    |(?P<LPAREN>\()
    |(?P<RPAREN>\))
    |(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)

KEYWORDS = {"AND", "OR", "NOT", "TRUE", "FALSE"}
COMPARISONS = {">", "<", ">=", "<=", "==", "!="}


class AnalysisError(Exception):
    pass

def tokenize(source):
    """Convierte el texto en una secuencia de tokens."""
    tokens = []
    position = 0

    while position < len(source):
        match = TOKEN_PATTERN.match(source, position)

        if not match:
            raise AnalysisError(
                f"Carácter no válido en la posición {position}: "
                f"{source[position]!r}"
            )

        kind = match.lastgroup
        value = match.group()
        start = position
        position = match.end()

        if kind == "SPACE":
            continue

        if kind == "IDENT" and value.upper() in KEYWORDS:
            kind = value.upper()

        tokens.append({
            "type": kind,
            "value": value,
            "position": start,
        })

    tokens.append({
        "type": "EOF",
        "value": "",
        "position": len(source),
    })

    return tokens


class Parser:
    """Analizador sintáctico descendente recursivo."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def current(self):
        return self.tokens[self.index]

    def accept(self, *types):
        if self.current()["type"] in types:
            token = self.current()
            self.index += 1
            return token
        return None

    def expect(self, *types):
        token = self.accept(*types)
        if token is None:
            current = self.current()
            expected = " o ".join(types)
            raise AnalysisError(
                f"Se esperaba {expected} en la posición "
                f"{current['position']}, pero se encontró "
                f"{current['value']!r}."
            )
        return token

    def parse(self):
        if self.current()["type"] == "EOF":
            raise AnalysisError("La regla no puede estar vacía.")

        self.expression()
        self.expect("EOF")

    def expression(self):
        self.and_expression()

        while self.accept("OR"):
            self.and_expression()

    def and_expression(self):
        self.not_expression()

        while self.accept("AND"):
            self.not_expression()

    def not_expression(self):
        if self.accept("NOT"):
            self.not_expression()
        else:
            self.comparison()

    def comparison(self):
        if self.accept("LPAREN"):
            self.expression()
            self.expect("RPAREN")
            return

        self.operand()

        if self.current()["type"] in COMPARISONS:
            self.index += 1
            self.operand()

    def operand(self):
        self.expect("IDENT", "NUMBER", "STRING", "TRUE", "FALSE")


def analyze(source):
    """Ejecuta el análisis léxico y el sintáctico."""
    try:
        tokens = tokenize(source)
        Parser(tokens).parse()

        visible_tokens = [
            token for token in tokens
            if token["type"] != "EOF"
        ]

        return {
            "success": True,
            "tokens": visible_tokens,
            "message": "La regla es sintácticamente válida.",
            "error": None,
        }

    except AnalysisError as error:
        return {
            "success": False,
            "tokens": [],
            "message": "No se pudo validar la regla.",
            "error": str(error),
        }
