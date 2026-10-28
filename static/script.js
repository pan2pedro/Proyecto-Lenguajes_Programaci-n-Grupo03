const $ = (id) => document.getElementById(id);
let analysis = null;

$("fileInput").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".txt")) {
    $("alert").hidden = false; $("alert").textContent = "Selecciona un archivo .txt.";
    event.target.value = ""; return;
  }
  $("source").value = await file.text();
  $("fileName").textContent = file.name;
});

$("analyzeButton").addEventListener("click", runAnalysis);
$("clearButton").addEventListener("click", () => {
  $("source").value = ""; $("fileInput").value = "";
  $("fileName").textContent = "Ningún archivo seleccionado";
  $("alert").hidden = true; analysis = null;
  $("summary").textContent = "Ejecuta el análisis para ver los resultados.";
  ["tokensBody","regexBody","linesBody"].forEach(id => $(id).replaceChildren());
  $("automataContent").textContent = "Los autómatas aparecerán aquí.";
  $("syntaxTree").textContent = "Sin árbol disponible.";
  $("semanticTree").textContent = "Sin árbol disponible.";
  $("tokenSelect").replaceChildren(new Option("Primero analiza una entrada", ""));
  $("lineSelect").replaceChildren(new Option("Primero analiza una entrada", ""));
});

async function runAnalysis() {
  $("analyzeButton").disabled = true;
  $("analyzeButton").textContent = "Analizando…";
  try {
    const response = await fetch("/analyze", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({source: $("source").value})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "No se pudo analizar la entrada.");
    analysis = data; renderResults(data);
  } catch (error) {
    $("alert").hidden = false; $("alert").textContent = error.message;
  } finally {
    $("analyzeButton").disabled = false;
    $("analyzeButton").textContent = "Analizar entrada";
  }
}

function cell(text, parent, tag="td") {
  const el = document.createElement(tag); el.textContent = text ?? ""; parent.appendChild(el); return el;
}
function renderResults(data) {
  $("alert").hidden = data.lexical_errors.length === 0;
  $("alert").textContent = data.lexical_errors.map(e => `Línea ${e.line}, columna ${e.column}: ${e.message}`).join(" · ");
  $("summary").textContent = `${data.summary.tokens} tokens · ${data.summary.valid_lines} líneas válidas · ${data.summary.invalid_lines} líneas inválidas · ${data.summary.lexical_errors} errores léxicos`;
  const tb = $("tokensBody"); tb.replaceChildren();
  if (!data.tokens.length) { const tr=tb.insertRow(); cell("No se reconocieron tokens.",tr).colSpan=5; }
  data.tokens.forEach(t => { const tr=tb.insertRow(); [t.token,t.lexeme,t.line,t.column,t.position].forEach(v=>cell(v,tr)); });
  const rb = $("regexBody"); rb.replaceChildren();
  data.regex_table.forEach(r => {const tr=rb.insertRow(); cell(r.type,tr); cell(r.regex,tr);});
  const lb = $("linesBody"); lb.replaceChildren();
  data.lines.forEach(r => {const tr=lb.insertRow(); cell(r.line,tr); cell(r.rule,tr); const td=cell("",tr); const badge=document.createElement("span"); badge.className=`pill ${r.valid?"ok":"bad"}`; badge.textContent=r.valid?"VÁLIDA":"INVÁLIDA"; td.appendChild(badge); cell(r.message,tr);});
  const tokenSelect=$("tokenSelect"); tokenSelect.replaceChildren();
  data.token_types.forEach(t=>tokenSelect.add(new Option(t,t)));
  if (!data.token_types.length) tokenSelect.add(new Option("No hay tokens", ""));
  tokenSelect.onchange=()=>renderAutomaton(data.automata[tokenSelect.value]);
  if(data.token_types.length) {tokenSelect.value=data.token_types[0]; renderAutomaton(data.automata[tokenSelect.value]);}
  const validLines=data.lines.filter(r=>r.valid && r.syntax_tree);
  const lineSelect=$("lineSelect"); lineSelect.replaceChildren();
  validLines.forEach((r,i)=>lineSelect.add(new Option(`Línea ${r.line}: ${r.rule}`,String(i))));
  lineSelect.onchange=()=>renderTrees(validLines[Number(lineSelect.value)]);
  if(validLines.length){lineSelect.value="0";renderTrees(validLines[0]);}
  else {lineSelect.add(new Option("No hay líneas válidas", ""));$("syntaxTree").textContent="No hay árbol sintáctico disponible.";$("semanticTree").textContent="No hay árbol semántico disponible.";}
}
function renderAutomaton(a) {
  const root=$("automataContent"); root.replaceChildren();
  if(!a){root.textContent="No hay datos de autómata.";return;}
  const p=document.createElement("p"); p.innerHTML="<strong>Expresión regular:</strong> "; p.appendChild(document.createTextNode(a.regex)); root.appendChild(p);
  const note=document.createElement("p"); note.className="footnote"; note.textContent="Para las alternativas literales de este prototipo se construye un autómata de prefijos determinista; el mismo grafo también es un AFND válido. La tabla de transformación muestra los subconjuntos alcanzables."; root.appendChild(note);
  const grid=document.createElement("div"); grid.className="automata-grid"; root.appendChild(grid);
  makeAutoCard(grid,"Autómata Finito No Determinista (AFND)",a.nfa,"AFND");
  makeAutoCard(grid,"Autómata Finito Determinista (AFD)",a.dfa,"AFD");
  const transTitle=document.createElement("h3"); transTitle.textContent="Transformación AFND → AFD"; root.appendChild(transTitle);
  const transform=document.createElement("div"); transform.className="table-wrap"; root.appendChild(transform);
  const table=document.createElement("table"); table.className="small-table"; transform.appendChild(table);
  const head=table.createTHead().insertRow(); ["Conjunto AFND","Estado AFD","Subconjunto"].forEach(v=>cell(v,head,"th"));
  const body=table.createTBody(); a.transformation.forEach(r=>{const tr=body.insertRow();[r.nfa_state,r.dfa_state,r.subset].forEach(v=>cell(v,tr));});
  const deltaTitle=document.createElement("h3"); deltaTitle.textContent="Función de transición δ";root.appendChild(deltaTitle);
  const ul=document.createElement("ul"); root.appendChild(ul); a.delta.forEach(d=>cell(d,ul,"li"));
}
function makeAutoCard(parent,title,data,label) {
  const card=document.createElement("div");card.className="auto-card";parent.appendChild(card);
  const h=document.createElement("h3");h.textContent=title;card.appendChild(h);
  const graph=document.createElement("div");graph.className="graph";card.appendChild(graph);graph.appendChild(drawGraph(data));
  const q=document.createElement("div");q.className="quad";card.appendChild(q);
  [["Q",data.states.join(", ")],["Σ",data.alphabet.map(x=>JSON.stringify(x)).join(", ")||"∅"],["δ","Ver tabla de transiciones"],["q₀",data.start],["F",data.finals.join(", ")||"∅"]].forEach(([k,v])=>{cell(k,q,"div");cell(v,q,"div");});
  const title2=document.createElement("p");title2.className="subheading";title2.textContent="Tabla de transiciones";card.appendChild(title2);
  const wrap=document.createElement("div");wrap.className="table-wrap";card.appendChild(wrap);
  const table=document.createElement("table");table.className="small-table";wrap.appendChild(table);
  const head=table.createTHead().insertRow();cell("Estado",head,"th");data.alphabet.forEach(ch=>cell(ch,head,"th"));
  const body=table.createTBody();
  data.table.forEach(row=>{const tr=body.insertRow();cell(`${row.state===0?"→":""}${row.accepting?"*":""}q${row.state}`,tr);data.alphabet.forEach(ch=>cell(row.transitions[ch]===null?"—":`q${row.transitions[ch]}`,tr));});
}
function drawGraph(data) {
  const ns="http://www.w3.org/2000/svg", svg=document.createElementNS(ns,"svg");
  const count=data.states.length, spacing=72, width=Math.max(360, count*spacing+60), height=150;
  svg.setAttribute("viewBox",`0 0 ${width} ${height}`);
  const defs=document.createElementNS(ns,"defs"), marker=document.createElementNS(ns,"marker");
  marker.setAttribute("id","arrow");marker.setAttribute("markerWidth","8");marker.setAttribute("markerHeight","8");marker.setAttribute("refX","7");marker.setAttribute("refY","3");marker.setAttribute("orient","auto");
  const path=document.createElementNS(ns,"path");path.setAttribute("d","M0,0 L0,6 L7,3 z");path.setAttribute("fill","#65748b");marker.appendChild(path);defs.appendChild(marker);svg.appendChild(defs);
  const positions={};data.states.forEach((s,i)=>positions[s]=[35+i*spacing,75]);
  // Start arrow
  const startLine=document.createElementNS(ns,"line");startLine.setAttribute("x1","3");startLine.setAttribute("y1","75");startLine.setAttribute("x2","17");startLine.setAttribute("y2","75");startLine.setAttribute("stroke","#65748b");startLine.setAttribute("marker-end","url(#arrow)");svg.appendChild(startLine);
  data.edges.forEach(e=>{
    const [x1,y1]=positions[`q${e.from}`], [x2,y2]=positions[`q${e.to}`];
    const line=document.createElementNS(ns,"line");line.setAttribute("x1",x1+17);line.setAttribute("y1",y1);line.setAttribute("x2",x2-18);line.setAttribute("y2",y2);line.setAttribute("stroke","#65748b");line.setAttribute("marker-end","url(#arrow)");svg.appendChild(line);
    const text=document.createElementNS(ns,"text");text.setAttribute("x",(x1+x2)/2);text.setAttribute("y",y1-10);text.setAttribute("text-anchor","middle");text.setAttribute("font-size","11");text.setAttribute("fill","#26364d");text.textContent=e.symbol;svg.appendChild(text);
  });
  data.states.forEach(s=>{
    const [x,y]=positions[s];const circle=document.createElementNS(ns,"circle");circle.setAttribute("cx",x);circle.setAttribute("cy",y);circle.setAttribute("r","17");circle.setAttribute("fill","#eef3ff");circle.setAttribute("stroke","#315bd6");circle.setAttribute("stroke-width","1.5");svg.appendChild(circle);
    if(data.finals.includes(s)){const inner=document.createElementNS(ns,"circle");inner.setAttribute("cx",x);inner.setAttribute("cy",y);inner.setAttribute("r","12");inner.setAttribute("fill","none");inner.setAttribute("stroke","#315bd6");svg.appendChild(inner);}
    const text=document.createElementNS(ns,"text");text.setAttribute("x",x);text.setAttribute("y",y+4);text.setAttribute("text-anchor","middle");text.setAttribute("font-size","10");text.textContent=s;svg.appendChild(text);
  });
  return svg;
}
function renderTrees(row) {
  renderTreeInto($("syntaxTree"),row.syntax_tree);
  renderTreeInto($("semanticTree"),row.semantic_tree);
}
function renderTreeInto(target,node) {
  target.replaceChildren();target.classList.remove("empty-state");
  if(!node){target.textContent="No hay árbol disponible.";return;}
  const build=(n)=>{const li=document.createElement("li");const span=document.createElement("span");span.className="node";span.textContent=n.name;li.appendChild(span);if(n.children&&n.children.length){const ul=document.createElement("ul");n.children.forEach(c=>ul.appendChild(build(c)));li.appendChild(ul);}return li;};
  const ul=document.createElement("ul");ul.appendChild(build(node));target.appendChild(ul);
}
