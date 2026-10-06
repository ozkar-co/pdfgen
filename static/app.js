const drop = document.getElementById("drop");
const fileInput = document.getElementById("file");
const fileName = document.getElementById("file-name");
const contentEl = document.getElementById("content");
const formatEl = document.getElementById("format");
const templateEl = document.getElementById("template");
const titleEl = document.getElementById("title");
const generateBtn = document.getElementById("generate-btn");
const download = document.getElementById("download");
const statusEl = document.getElementById("status");
const preview = document.getElementById("preview");

let pdfUrl = null;
let baseName = "documento";

function setStatus(message) {
  statusEl.textContent = message;
}

async function loadTemplates() {
  const res = await fetch("/api/templates");
  if (!res.ok) {
    setStatus("No se pudieron cargar las plantillas");
    return;
  }
  const data = await res.json();
  for (const t of data.templates) {
    const opt = document.createElement("option");
    opt.value = t.id;
    opt.textContent = t.name;
    opt.title = t.description;
    templateEl.appendChild(opt);
  }
}

async function setFile(file) {
  if (!file) return;
  fileName.textContent = file.name;
  baseName = file.name.replace(/\.[^.]+$/, "") || "documento";
  formatEl.value = /\.html?$/i.test(file.name) ? "html" : "md";
  contentEl.value = await file.text();
  setStatus("Archivo cargado");
}

async function readError(res) {
  try {
    const data = await res.json();
    return data.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

async function generate() {
  const content = contentEl.value;
  if (!content.trim()) {
    setStatus("No hay contenido");
    return;
  }
  generateBtn.disabled = true;
  setStatus("Generando…");
  try {
    const res = await fetch("/api/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content,
        format: formatEl.value,
        template: templateEl.value || null,
        title: titleEl.value.trim() || null,
        filename: baseName,
      }),
    });
    if (!res.ok) throw new Error(await readError(res));
    const blob = await res.blob();
    if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    pdfUrl = URL.createObjectURL(blob);
    preview.src = pdfUrl;
    preview.classList.remove("hidden");
    download.href = pdfUrl;
    download.download = `${baseName}.pdf`;
    download.classList.remove("hidden");
    setStatus(`Listo · ${Math.round(blob.size / 1024)} KB`);
  } catch (error) {
    setStatus(`Error: ${error.message || error}`);
  } finally {
    generateBtn.disabled = false;
  }
}

drop.addEventListener("dragover", (event) => {
  event.preventDefault();
  drop.classList.add("over");
});
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (event) => {
  event.preventDefault();
  drop.classList.remove("over");
  setFile(event.dataTransfer.files && event.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => setFile(fileInput.files && fileInput.files[0]));
generateBtn.addEventListener("click", generate);

loadTemplates();
