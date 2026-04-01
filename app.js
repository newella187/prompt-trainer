const output = document.getElementById("output");
const groundBtn = document.getElementById("ground-btn");
const copyBtn = document.getElementById("copy-btn");
const clearBtn = document.getElementById("clear-btn");
const quizForm = document.getElementById("quiz-form");
const quizResult = document.getElementById("quiz-result");
const certificate = document.getElementById("certificate");
const studentNameInput = document.getElementById("student-name");
const studentNameDisplay = document.getElementById("student-name-display");
const downloadCoursePdfBtn = document.getElementById("download-course-pdf");
const downloadCertPdfBtn = document.getElementById("download-cert-pdf");

const PASS_MARK = 4;

const makeGroundedPrompt = (rawPrompt) => {
  const prompt = rawPrompt.trim();

  return `Role:\nYou are a reliable assistant that produces grounded answers only.\n\nTask:\nAnswer the user's request using only the approved source material provided below.\n\nUser request:\n${prompt}\n\nGrounding instructions:\n1) Use only facts from the provided source material.\n2) If information is missing, state exactly what is missing.\n3) Do not invent names, figures, dates, or claims.\n4) Separate confirmed facts from unknowns.\n5) Cite which part of the provided source supports each key point.\n\nOutput format:\n- Summary\n- Evidence-backed points\n- Gaps / Unknowns\n- Recommended next action\n\nProvided source material:\n[Paste approved internal notes, reports, or policy text here.]`;
};

const escapePdfText = (value) => value.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");

const createSimplePdf = (lines) => {
  const textRows = lines.map((line, idx) => `BT /F1 12 Tf 50 ${760 - idx * 20} Td (${escapePdfText(line)}) Tj ET`).join("\n");
  const stream = `${textRows}`;
  const objects = [
    "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
    "2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj",
    "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
    `4 0 obj << /Length ${stream.length} >> stream\n${stream}\nendstream endobj`,
    "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj"
  ];

  let pdf = "%PDF-1.4\n";
  const offsets = [0];

  objects.forEach((obj) => {
    offsets.push(pdf.length);
    pdf += `${obj}\n`;
  });

  const xrefOffset = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n`;
  pdf += "0000000000 65535 f \n";
  offsets.slice(1).forEach((offset) => {
    pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
  });

  pdf += `trailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return new Blob([pdf], { type: "application/pdf" });
};

const downloadPdf = (filename, lines) => {
  const blob = createSimplePdf(lines);
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(link.href);
  link.remove();
};

groundBtn.addEventListener("click", () => {
  const rawPrompt = document.getElementById("user-prompt").value;

  if (!rawPrompt.trim()) {
    output.textContent = "Please enter a prompt before converting.";
    return;
  }

  output.textContent = makeGroundedPrompt(rawPrompt);
});

copyBtn.addEventListener("click", async () => {
  const content = output.textContent.trim();

  if (!content || content === "Your grounded prompt will appear here.") {
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

clearBtn.addEventListener("click", () => {
  document.getElementById("user-prompt").value = "";
  output.textContent = "Your grounded prompt will appear here.";
});

quizForm.addEventListener("submit", (event) => {
  event.preventDefault();

  const answers = {
    q1: "b",
    q2: "c",
    q3: "b",
    q4: "a",
    q5: "b"
  };

  const formData = new FormData(quizForm);
  const score = Object.entries(answers).reduce((total, [question, correct]) => {
    return total + (formData.get(question) === correct ? 1 : 0);
  }, 0);

  if (score >= PASS_MARK) {
    quizResult.textContent = `Passed: ${score}/5. You can now download your certificate.`;
    quizResult.className = "status pass";
    certificate.classList.remove("hidden");
  } else {
    quizResult.textContent = `Not yet passed: ${score}/5. Review the course and try again.`;
    quizResult.className = "status fail";
    certificate.classList.add("hidden");
  }
});

studentNameInput.addEventListener("input", () => {
  const name = studentNameInput.value.trim();
  studentNameDisplay.textContent = name || "Learner";
});

downloadCoursePdfBtn.addEventListener("click", () => {
  downloadPdf("grounding-prompt-course-form.pdf", [
    "Grounding Prompt Training Course",
    "",
    "Steps to Ground a GPT:",
    "1. Define scope and boundaries.",
    "2. Provide trusted source material.",
    "3. Require evidence-based responses.",
    "4. Specify output format.",
    "5. Handle missing information explicitly.",
    "6. Review outputs and refine prompt.",
    "",
    "Knowledge test included in web form."
  ]);
});

downloadCertPdfBtn.addEventListener("click", () => {
  const learner = studentNameInput.value.trim() || "Learner";
  downloadPdf("grounding-course-certificate.pdf", [
    "Certificate of Completion",
    "",
    `Awarded to: ${learner}`,
    "For successfully passing the Grounding Prompt Training Course.",
    "",
    `Date: ${new Date().toISOString().slice(0, 10)}`
  ]);
});
