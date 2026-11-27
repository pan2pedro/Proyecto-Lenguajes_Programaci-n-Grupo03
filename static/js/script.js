const $ = (id) => document.getElementById(id);
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

async function cargarInventario(items) {
  if (!items) {
    const r = await fetch("/api/inventario");
    items = await r.json();
  }
  $("inventario").innerHTML = items.length ? items.map(x =>
    `<tr><td>${x.id}</td><td>${escapeHtml(x.nombre)}</td><td>${x.concentracion} mg</td><td>${x.cantidad}</td><td>S/ ${Number(x.precio).toFixed(2)}</td><td>${escapeHtml(x.vencimiento)}</td></tr>`
  ).join("") : '<tr><td colspan="6">No hay medicamentos registrados.</td></tr>';
}

function mostrarTokens(tokens=[]) {
  $("tokens").innerHTML = tokens.length ? tokens.map(t =>
    `<tr><td>${t.linea}</td><td>${escapeHtml(t.token)}</td><td><code>${escapeHtml(t.lexema)}</code></td></tr>`
  ).join("") : '<tr><td colspan="3">No se reconocieron tokens.</td></tr>';
}
function mostrarRegex(regex=[]) {
  $("regex").innerHTML = regex.map(x =>
    `<tr><td>${escapeHtml(x[0])}</td><td><code>${escapeHtml(x[1])}</code></td></tr>`
  ).join("");
}
function renderTree(node) {
  return `<li><strong>${escapeHtml(node.nombre)}</strong>${node.valor ? `: ${escapeHtml(node.valor)}` : ""}${node.hijos?.length ? `<ul>${node.hijos.map(renderTree).join("")}</ul>` : ""}</li>`;
}
function mostrarResultados(data) {
  const ok = !String(data.estado).startsWith("ERROR") && (data.resultados || []).every(x => x.valido);
  $("estado").className = `status ${ok ? "good" : "bad"}`;
  $("estado").textContent = `${data.estado}: ${data.mensaje || ""}`;
  const rows = data.resultados || [];
  if (data.errores) {
    $("resultados").innerHTML = data.errores.map(e => `<div class="result-item bad">Error léxico en línea ${e.linea}: carácter ${escapeHtml(e.caracter)}</div>`).join("");
  } else if (data.mensaje && !rows.length) {
    $("resultados").innerHTML = `<div class="result-item bad">${escapeHtml(data.mensaje)}</div>`;
  } else {
    $("resultados").innerHTML = rows.map(r => `<div class="result-item ${r.valido ? "" : "bad"}"><strong>${escapeHtml(r.operacion)}</strong> — ${escapeHtml(r.mensaje)}</div>`).join("");
  }
  mostrarTokens(data.tokens || []);
  mostrarRegex(data.regex || []);
  if (data.automata) {
    const a = data.automata;
    $("automata-info").textContent = `Token: ${a.token}\nExpresión regular: ${a.regex}\nQ = {${a.estados.join(", ")}}\nΣ = {${a.alfabeto}}\nEstado inicial: ${a.inicial}\nEstados finales: {${a.finales.join(", ")}}\nTransiciones:\n${a.transiciones.map(t => `${t.desde} --${t.entrada}--> ${t.hasta}`).join("\n")}\n${a.nota}`;
  }
  const trees = data.arboles || [];
  $("arboles").innerHTML = trees.length ? trees.map(t => `<div class="tree"><ul>${renderTree(t)}</ul></div>`).join("") : "No hay árboles disponibles.";
  if (data.inventario) cargarInventario(data.inventario);
}
$("analizar").addEventListener("click", async () => {
  const btn = $("analizar"); btn.disabled = true; btn.textContent = "Analizando…";
  try {
    const response = await fetch("/api/analizar", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({texto: $("codigo").value})
    });
    const data = await response.json();
    mostrarResultados(data);
  } catch (e) {
    $("estado").className = "status bad";
    $("estado").textContent = "No fue posible conectar con el servidor.";
  } finally { btn.disabled = false; btn.textContent = "Analizar instrucciones"; }
});
$("limpiar").addEventListener("click", () => {
  $("codigo").value = "";
  $("estado").className = "status neutral";
  $("estado").textContent = "A la espera de instrucciones.";
  $("resultados").innerHTML = ""; $("tokens").innerHTML = ""; $("arboles").textContent = "";
});
$("archivo").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  $("file-name").textContent = file.name;
  $("codigo").value = await file.text();
});
cargarInventario();
