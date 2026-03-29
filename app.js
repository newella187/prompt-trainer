const form = document.getElementById("prompt-form");
const output = document.getElementById("output");
const copyBtn = document.getElementById("copy-btn");

const sanitiseLabel = (value) => {
  const lower = value.toLowerCase();
  if (lower.includes("transcript")) {
    return "source material";
  }
  return value;
};

const sanitiseContent = (value) =>
  value.replace(/transcript/gi, "source material").trim();

const buildPrompt = (type, rawInput) => {
  const inputType = sanitiseLabel(type);
  const userContent = sanitiseContent(rawInput);

  return `Role:
You are a highly experienced ISO certification auditor with expertise in ISO 9001, ISO 14001, and ISO 45001.

Task:
Use only the provided ${inputType} and supporting source material to produce an audit-ready response. Explain how the organisation manages quality, environmental responsibilities, and health and safety controls.

Context:
Write in clear UK English in a natural human style. Provide the response in a couple of coherent paragraphs suitable for an ISO audit discussion. Keep the tone objective, factual, and evidence based.

Input material:
${userContent}

Rules:
1) Use only the information provided in the input material.
2) Do not add assumptions, inventions, or external facts.
3) Avoid unnecessary jargon and keep language clear.
4) Maintain an objective, evidence-based tone throughout.
5) Deliver the output as naturally written human paragraphs suitable for audit records.`;
};

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const type = document.getElementById("input-type").value;
  const text = document.getElementById("user-input").value;

  if (!text.trim()) {
    output.textContent = "Please add some source material before generating the prompt.";
    return;
  }

  output.textContent = buildPrompt(type, text);
});

copyBtn.addEventListener("click", async () => {
  const content = output.textContent.trim();

  if (!content || content === "Your generated prompt will appear here.") {
    return;
  }

  try {
    await navigator.clipboard.writeText(content);
    copyBtn.textContent = "Copied";
    setTimeout(() => {
      copyBtn.textContent = "Copy";
    }, 1200);
  } catch {
    copyBtn.textContent = "Copy failed";
    setTimeout(() => {
      copyBtn.textContent = "Copy";
    }, 1500);
  }
});
