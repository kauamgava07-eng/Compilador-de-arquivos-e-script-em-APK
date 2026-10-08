const fileInput = document.querySelector("#file");
const fileName = document.querySelector("#file-name");
const buildButton = document.querySelector("#build");
const statusBox = document.querySelector("#status");
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? `${file.name} (${(file.size/1024/1024).toFixed(2)} MB)` : "Toque para selecionar um arquivo ZIP";
  buildButton.disabled = !file;
  setStatus(file ? "Pronto para enviar o projeto." : "Selecione um ZIP para começar.");
});
function setStatus(message, type="") {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}
buildButton.addEventListener("click", async () => {
  const file = fileInput.files[0];
  const api = document.querySelector("#api").value.trim().replace(/\/+$/, "");
  if (!file || !file.name.toLowerCase().endsWith(".zip")) return setStatus("Selecione um arquivo .zip válido.", "err");
  buildButton.disabled = true;
  setStatus("Enviando projeto e analisando arquivos…");
  try {
    const data = new FormData();
    data.append("file", file);
    const response = await fetch(`${api}/api/build`, {method:"POST", body:data});
    const type = response.headers.get("content-type") || "";
    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `HTTP ${response.status}`);
    }
    if (type.includes("application/vnd.android.package-archive") || type.includes("application/octet-stream")) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "Script2APK-debug.apk"; a.click();
      URL.revokeObjectURL(url);
      setStatus("APK baixado. Como é um APK debug, instale apenas se confiar no projeto e na origem.", "ok");
    } else {
      const result = await response.json();
      setStatus(`${result.status || "resultado"}\n${result.message || "Processamento concluído."}${result.details ? "\n\nDetalhes:\n"+result.details : ""}${result.next_step ? "\n\nPróximo passo: "+result.next_step : ""}`, result.status === "error" ? "err" : "ok");
    }
  } catch (error) {
    setStatus(`Não foi possível conectar ou compilar.\n${error.message}\n\nConfira o endereço da API e se o servidor está em execução.`, "err");
  } finally {
    buildButton.disabled = !fileInput.files[0];
  }
});
