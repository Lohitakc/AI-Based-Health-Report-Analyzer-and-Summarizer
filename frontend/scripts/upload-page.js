const uploadForm = document.getElementById("uploadForm");
const submitButton = document.getElementById("submitButton");
const statusText = document.getElementById("statusText");
const fileInput = document.getElementById("pdfFile");
const filePrompt = document.getElementById("filePrompt");

fileInput.addEventListener("change", () => {
  if (!fileInput.files.length) {
    filePrompt.textContent = "Drag & drop your PDF here";
    statusText.textContent = "Ready to analyze";
    return;
  }

  filePrompt.textContent = `Selected: ${fileInput.files[0].name}`;
  statusText.textContent = "File selected. Click Analyze and Continue.";
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    statusText.textContent = "Please choose a PDF file.";
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Analyzing...";
  statusText.textContent = "Analyzing your report. Please wait...";

  try {
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || "Upload failed.");
    }

    const data = await response.json();
    const serialized = JSON.stringify(data);
    const cleanName = (fileInput.files[0].name || "Pathology_Report").replace(/\.pdf$/i, "");

    sessionStorage.setItem("analysis_result", serialized);
    sessionStorage.setItem("analysis_file_name", cleanName);
    localStorage.setItem("analysis_result", serialized);
    localStorage.setItem("analysis_file_name", cleanName);
    window.location.href = "/report";
  } catch (error) {
    statusText.textContent = `Error: ${error.message}`;
    submitButton.disabled = false;
    submitButton.textContent = "Analyze and Continue";
  }
});
