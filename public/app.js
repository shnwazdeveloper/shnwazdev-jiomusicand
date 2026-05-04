const form = document.querySelector("#search-form");
const queryInput = document.querySelector("#query");
const detailsInput = document.querySelector("#details");
const resultStatus = document.querySelector("#result-status");
const resultLink = document.querySelector("#result-link");
const resultOutput = document.querySelector("#result-output");

function searchUrl() {
  const params = new URLSearchParams();
  params.set("query", queryInput.value.trim());
  if (detailsInput.checked) {
    params.set("details", "true");
  }
  return `/api/search?${params.toString()}`;
}

async function runSearch(event) {
  event.preventDefault();
  const url = searchUrl();

  resultStatus.textContent = "Loading";
  resultLink.href = url;
  resultLink.textContent = url;
  resultOutput.textContent = "Fetching response...";

  try {
    const response = await fetch(url);
    const payload = await response.json();
    resultStatus.textContent = response.ok ? "OK" : `HTTP ${response.status}`;
    resultOutput.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    resultStatus.textContent = "Error";
    resultOutput.textContent = JSON.stringify(
      {
        ok: false,
        error: "Unable to reach the local API.",
      },
      null,
      2
    );
  }
}

form.addEventListener("submit", runSearch);
