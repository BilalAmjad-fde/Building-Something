const resumeInput = document.querySelector("#resume-file");
const dropZone = document.querySelector("#drop-zone");
const uploadTitle = document.querySelector("#upload-title");
const uploadSubtitle = document.querySelector("#upload-subtitle");
const fileError = document.querySelector("#file-error");
const queryInput = document.querySelector("#job-query");
const charCount = document.querySelector("#char-count");
const queryError = document.querySelector("#query-error");
const formStatus = document.querySelector("#form-status");
const searchForm = document.querySelector("#search-form");

const maxFileSize = 10 * 1024 * 1024;

function showFile(file) {
  fileError.textContent = "";
  formStatus.textContent = "";

  if (!file) return;
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    resumeInput.value = "";
    uploadTitle.textContent = "Drop your resume here";
    uploadSubtitle.innerHTML = 'or <span class="browse-link">browse files</span> from your device';
    fileError.textContent = "Please choose a PDF file.";
    return;
  }
  if (file.size > maxFileSize) {
    resumeInput.value = "";
    uploadTitle.textContent = "Drop your resume here";
    uploadSubtitle.innerHTML = 'or <span class="browse-link">browse files</span> from your device';
    fileError.textContent = "This file is larger than 10 MB. Choose a smaller PDF.";
    return;
  }

  uploadTitle.textContent = file.name;
  uploadSubtitle.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to preview`;
}

resumeInput.addEventListener("change", () => showFile(resumeInput.files[0]));

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  resumeInput.files = transfer.files;
  showFile(file);
});

queryInput.addEventListener("input", () => {
  charCount.textContent = `${queryInput.value.length} / 500`;
  queryError.textContent = "";
  formStatus.textContent = "";
});

document.querySelectorAll(".suggestion-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const currentQuery = queryInput.value.trim();
    const suggestion = chip.textContent;
    if (!currentQuery.toLowerCase().includes(suggestion.toLowerCase())) {
      queryInput.value = currentQuery ? `${currentQuery}, ${suggestion}` : suggestion;
      queryInput.dispatchEvent(new Event("input"));
    }
    queryInput.focus();
  });
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  formStatus.textContent = "";
  fileError.textContent = "";
  queryError.textContent = "";

  const file = resumeInput.files[0];
  const query = queryInput.value.trim();
  let isValid = true;

  if (!file) {
    fileError.textContent = "Add a PDF resume to preview your search.";
    isValid = false;
  }
  if (!query) {
    queryError.textContent = "Tell us a little about the role you're looking for.";
    isValid = false;
  }
  if (!isValid) return;

  formStatus.textContent = "Your search is ready to preview. This page doesn't upload or store your resume yet.";
});
