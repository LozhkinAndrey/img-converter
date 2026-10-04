const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file");
const fileName = document.getElementById("file-name");
const operation = document.getElementById("operation");
const widthGroup = document.getElementById("width-group");
const angleGroup = document.getElementById("angle-group");
const errorBox = document.getElementById("error");
const resultSection = document.getElementById("result");
const resultImg = document.getElementById("result-img");
const downloadLink = document.getElementById("download-link");
const submitBtn = document.getElementById("submit-btn");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0] ? fileInput.files[0].name : "Выберите файл…";
});

operation.addEventListener("change", () => {
  widthGroup.hidden = operation.value !== "resize";
  angleGroup.hidden = operation.value !== "rotate";
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  const file = fileInput.files[0];
  if (!file) { showError("Выберите файл"); return; }

  const fd = new FormData();
  fd.append("file", file);
  fd.append("operation", operation.value);
  if (operation.value === "resize") fd.append("width", document.getElementById("width").value);
  if (operation.value === "rotate") fd.append("angle", document.getElementById("angle").value);

  submitBtn.disabled = true;
  submitBtn.textContent = "Обрабатываю…";
  try {
    const resp = await fetch("/api/transform", { method: "POST", body: fd });
    if (!resp.ok) {
      let msg = `Ошибка ${resp.status}`;
      try { msg = (await resp.json()).error || msg; } catch (_) {}
      throw new Error(msg);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    resultImg.src = url;
    const ext = blob.type.includes("jpeg") ? "jpg" : "png";
    downloadLink.href = url;
    downloadLink.download = `result.${ext}`;
    resultSection.hidden = false;
  } catch (err) {
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Обработать";
  }
});

function showError(text) { errorBox.textContent = text; errorBox.hidden = false; }
function hideError() { errorBox.hidden = true; }
