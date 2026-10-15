const ruleInput = document.getElementById("rule");
const analyzeBtn = document.getElementById("analyzeBtn");
const clearBtn = document.getElementById("clearBtn");
const statusBox = document.getElementById("status");
const tokensBox = document.getElementById("tokens");
const syntaxBox = document.getElementById("syntax");

function showStatus(message, success) {
    statusBox.hidden = false;
    statusBox.className = `status ${success ? "success" : "error"}`;
    statusBox.textContent = message;
}

function renderTokens(tokens) {
    tokensBox.replaceChildren();

    if (!tokens || tokens.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty";
        empty.textContent = "No hay tokens para mostrar.";
        tokensBox.appendChild(empty);
        return;
    }

    tokens.forEach(token => {
        const item = document.createElement("div");
        item.className = "token";

        const type = document.createElement("strong");
        type.textContent = token.type;

        const value = document.createElement("code");
        value.textContent = token.value;

        item.append(type, value);
        tokensBox.appendChild(item);
    });
}

function renderSyntax(result) {
    syntaxBox.replaceChildren();

    const message = document.createElement("p");
    message.textContent = result.message;
    syntaxBox.appendChild(message);

    if (result.error) {
        const error = document.createElement("p");
        error.className = "empty";
        error.textContent = result.error;
        syntaxBox.appendChild(error);
    }
}

analyzeBtn.addEventListener("click", async () => {
    const rule = ruleInput.value.trim();

    if (!rule) {
        showStatus("Escribe una regla antes de analizarla.", false);
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analizando...";

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ rule })
        });

        const result = await response.json();

        showStatus(
            result.success
                ? "Análisis completado correctamente."
                : "La regla contiene un error.",
            result.success
        );

        renderTokens(result.tokens);
        renderSyntax(result);
    } catch (error) {
        showStatus(
            "No se pudo conectar con el servidor. Verifica que Flask esté ejecutándose.",
            false
        );
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analizar regla";
    }
});

clearBtn.addEventListener("click", () => {
    ruleInput.value = "";
    statusBox.hidden = true;
    tokensBox.replaceChildren();
    syntaxBox.replaceChildren();

    const tokenPlaceholder = document.createElement("p");
    tokenPlaceholder.className = "empty";
    tokenPlaceholder.textContent = "Todavía no hay resultados.";
    tokensBox.appendChild(tokenPlaceholder);

    const syntaxPlaceholder = document.createElement("p");
    syntaxPlaceholder.className = "empty";
    syntaxPlaceholder.textContent =
        "Aquí aparecerá el resultado de la validación.";
    syntaxBox.appendChild(syntaxPlaceholder);

    ruleInput.focus();
});

