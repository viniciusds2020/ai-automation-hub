const request = async (path, options = {}) => {
  const response = await fetch("/api" + path, Object.assign({
    headers: {"Content-Type": "application/json"}
  }, options));
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "Operação não concluída.");
  }
  return response.json();
};
const state = {resources: [], workflows: [], runs: []};
const safe = value => String(value).replace(/[&<>"']/g, char =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));
const empty = text => '<div class="empty">' + text + "</div>";
const badge = kind => '<span class="badge ' + kind + '">' + kind.toUpperCase() + "</span>";
const toast = text => {
  const node = document.querySelector("#toast");
  node.textContent = text; node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 2500);
};

async function refresh() {
  const data = await Promise.all([
    request("/dashboard"), request("/resources"), request("/workflows"), request("/runs")
  ]);
  const dashboard = data[0];
  state.resources = data[1]; state.workflows = data[2]; state.runs = data[3];
  const metrics = [["Skills", dashboard.skills], ["MCPs", dashboard.mcps],
    ["Workflows", dashboard.workflows], ["Execuções", dashboard.runs],
    ["Sucesso", dashboard.success_rate + "%"]];
  document.querySelector("#stats").innerHTML = metrics.map(item =>
    '<div class="stat"><b>' + item[1] + "</b><span>" + item[0] + "</span></div>"
  ).join("");
  renderResources(); renderWorkflows(); renderRuns();
  document.querySelector("#resource-options").innerHTML = state.resources.map(item =>
    '<option value="' + item.id + '">' + safe(item.name) + " (" + item.kind.toUpperCase() + ")</option>"
  ).join("");
}

function renderResources() {
  document.querySelector("#resource-list").innerHTML = state.resources.map(item =>
    '<article class="card"><div>' + badge(item.kind) + '</div><h3>' + safe(item.name) +
    "</h3><p>" + safe(item.description || "Sem descrição.") + "</p><footer><span>" +
    safe(item.endpoint || "Execução interna") + "</span><span>#" + item.id + "</span></footer></article>"
  ).join("") || empty("Nenhum recurso cadastrado.");
}

function workflowCard(item) {
  return '<article class="card"><div>' + badge("workflow") + '</div><h3>' + safe(item.name) +
    "</h3><p>" + safe(item.description || "Automação sem descrição.") +
    '</p><footer><span>' + item.steps.length + ' etapa(s)</span><button class="run" onclick="runWorkflow(' +
    item.id + ')">Executar →</button></footer></article>';
}

function renderWorkflows() {
  document.querySelector("#workflow-list").innerHTML =
    state.workflows.map(workflowCard).join("") || empty("Crie seu primeiro workflow.");
  document.querySelector("#recent-workflows").innerHTML = state.workflows.slice(0, 4).map(item =>
    '<div class="row">' + badge("wf") + '<div><b>' + safe(item.name) + "<small>" +
    item.steps.length + ' etapa(s)</small></div><button class="run" onclick="runWorkflow(' +
    item.id + ')">Executar</button></div>'
  ).join("") || empty("Nenhum workflow ainda.");
}

function renderRuns() {
  const line = item => '<div class="row">' + badge(item.status) + '<div><b>' +
    safe(item.workflow_name) + "<small>Execução #" + item.id + " · " + item.started_at +
    "</small></div></div>";
  document.querySelector("#run-list").innerHTML =
    state.runs.map(line).join("") || empty("Nenhuma execução registrada.");
  document.querySelector("#recent-runs").innerHTML =
    state.runs.slice(0, 5).map(line).join("") || empty("Sem atividade recente.");
}

window.runWorkflow = async id => {
  try {
    await request("/workflows/" + id + "/run", {
      method: "POST", body: JSON.stringify({input: {source: "dashboard"}})
    });
    toast("Workflow executado em modo simulação."); await refresh();
  } catch (error) { toast(error.message); }
};

function showView(id) {
  document.querySelectorAll(".view,nav button").forEach(node => node.classList.remove("active"));
  document.querySelector("#" + id).classList.add("active");
  document.querySelector('[data-view="' + id + '"]').classList.add("active");
  document.querySelector("#title").textContent =
    ({overview:"Visão geral",resources:"Skills & MCPs",workflows:"Workflows",runs:"Execuções"})[id];
}
document.querySelectorAll("nav button").forEach(button =>
  button.addEventListener("click", () => showView(button.dataset.view)));

const resourceDialog = document.querySelector("#resource-dialog");
const workflowDialog = document.querySelector("#workflow-dialog");
document.querySelector("#add-resource").onclick = () => resourceDialog.showModal();
document.querySelector("#add-workflow").onclick = () => workflowDialog.showModal();
document.querySelectorAll(".close").forEach(button =>
  button.onclick = () => button.closest("dialog").close());

document.querySelector("#resource-form").onsubmit = async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.endpoint = data.endpoint || null; data.config = {mode: "simulation"};
  try {
    await request("/resources", {method:"POST", body:JSON.stringify(data)});
    event.target.reset(); resourceDialog.close(); toast("Recurso adicionado."); await refresh();
  } catch (error) { toast(error.message); }
};

document.querySelector("#workflow-form").onsubmit = async event => {
  event.preventDefault();
  const raw = Object.fromEntries(new FormData(event.target));
  const data = {name:raw.name, description:raw.description,
    steps:[{resource_id:Number(raw.resource_id), action:raw.action}]};
  try {
    await request("/workflows", {method:"POST", body:JSON.stringify(data)});
    event.target.reset(); workflowDialog.close(); toast("Workflow criado."); await refresh();
  } catch (error) { toast(error.message); }
};
refresh().catch(error => toast(error.message));

