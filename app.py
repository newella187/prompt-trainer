#!/usr/bin/env python3
"""ISO prompt builder CLI + web app.

Generates high-accuracy prompts for ISO 9001/14001/45001 questions
in documentation, transcript, or clause mode.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_REGISTRY = pathlib.Path(__file__).with_name("standards_registry.json")


@dataclass
class StandardProfile:
    key: str
    title: str
    edition: str
    published_date: str
    sources: list[str]
    clauses: dict[str, str]


class PromptEngine:
    def __init__(self, registry_path: pathlib.Path = DEFAULT_REGISTRY) -> None:
        self.registry_path = registry_path
        self._registry = self._load_registry()

    def _load_registry(self) -> dict:
        with self.registry_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if "standards" not in data:
            raise ValueError("Registry is missing 'standards' root key")

        return data

    def get_standard(self, key: str) -> StandardProfile:
        standards = self._registry["standards"]
        if key not in standards:
            valid = ", ".join(sorted(standards.keys()))
            raise ValueError(f"Unknown standard '{key}'. Valid: {valid}")

        record = standards[key]
        return StandardProfile(
            key=key,
            title=record["title"],
            edition=record["edition"],
            published_date=record["published_date"],
            sources=record.get("sources", []),
            clauses=record.get("clauses", {}),
        )

    def build_prompt(
        self,
        standard_key: str,
        mode: str,
        question: str,
        clause: str | None = None,
    ) -> str:
        standard = self.get_standard(standard_key)

        clause_context = ""
        if clause:
            clause_name = standard.clauses.get(clause, "(clause descriptor not in registry)")
            clause_context = f"Target clause: {clause} — {clause_name}"

        task_focus = {
            "documentation": (
                "Evaluate, draft, or improve management system documentation "
                "for conformity evidence."
            ),
            "transcript": (
                "Analyze transcript content (interviews, meetings, audits) "
                "for conformity signals, nonconformity risks, and missing evidence."
            ),
            "clause": (
                "Provide a clause-level interpretation and implementation guidance "
                "with objective evidence expectations."
            ),
        }

        if mode not in task_focus:
            valid_modes = ", ".join(sorted(task_focus))
            raise ValueError(f"Unknown mode '{mode}'. Valid: {valid_modes}")

        sources_text = "\n".join(f"- {s}" for s in standard.sources) or "- (No source URL provided)"

        prompt = textwrap.dedent(
            f"""
            You are a senior ISO management systems expert supporting compliance preparation.

            Standard profile:
            - Standard: {standard.title}
            - Edition: {standard.edition}
            - Published date: {standard.published_date}
            - Scope mode: {mode}
            {f"- {clause_context}" if clause_context else "- Target clause: (not specified)"}

            Priority task:
            {task_focus[mode]}

            User question:
            {question}

            Instructions:
            1) Give an answer strictly aligned to the selected ISO standard and clause intent.
            2) If the user input lacks key context, ask up to 5 focused clarification questions first.
            3) Produce output in these sections:
               - Interpretation of requirement
               - Evidence expected by an auditor
               - Common nonconformities / risk patterns
               - Step-by-step implementation actions
               - Example wording/templates (documentation or transcript follow-up)
               - Verification checklist
            4) Distinguish clearly between mandatory requirement language and best-practice suggestions.
            5) If there may be a newer edition/amendment than the profile, state that explicitly and include a "Delta-check list" for what to verify.
            6) Keep language precise, auditable, and free of unsupported assumptions.

            Reference links for version verification:
            {sources_text}
            """
        ).strip()

        return prompt


def refresh_registry(source: str, destination: pathlib.Path) -> None:
    with urllib.request.urlopen(source, timeout=20) as response:
        content = response.read().decode("utf-8")

    data = json.loads(content)
    if "standards" not in data:
        raise ValueError("Downloaded registry is missing 'standards'")

    destination.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _selected(value: str, selected_value: str) -> str:
    return " selected" if value == selected_value else ""


def build_html_page(form_values: dict[str, str], prompt: str | None = None, error: str | None = None) -> str:
    standard = form_values.get("standard", "iso9001")
    mode = form_values.get("mode", "documentation")
    clause = form_values.get("clause", "")
    question = form_values.get("question", "")

    prompt_block = ""
    if prompt:
        prompt_block = (
            "<h2>Generated Prompt</h2>"
            f"<pre>{html.escape(prompt)}</pre>"
        )

    error_block = f"<p class='error'>{html.escape(error)}</p>" if error else ""

    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>ISO Prompt Builder</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem auto; max-width: 1000px; padding: 0 1rem; }}
    form {{ display: grid; gap: 0.75rem; }}
    label {{ font-weight: 700; }}
    input, select, textarea, button {{ font-size: 1rem; padding: 0.5rem; }}
    textarea {{ min-height: 120px; }}
    pre {{ background: #111827; color: #f3f4f6; padding: 1rem; overflow: auto; white-space: pre-wrap; }}
    .help {{ color: #374151; margin-top: 0; }}
    .error {{ color: #b91c1c; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>ISO Prompt Builder Web App</h1>
  <p class='help'>Generate GPT prompts for ISO 9001 / 14001 / 45001 documentation, transcript, or clause-specific requests.</p>
  {error_block}
  <form method='post' action='/'>
    <label for='standard'>Standard</label>
    <select id='standard' name='standard'>
      <option value='iso9001'{_selected('iso9001', standard)}>ISO 9001</option>
      <option value='iso14001'{_selected('iso14001', standard)}>ISO 14001</option>
      <option value='iso45001'{_selected('iso45001', standard)}>ISO 45001</option>
    </select>

    <label for='mode'>Mode</label>
    <select id='mode' name='mode'>
      <option value='documentation'{_selected('documentation', mode)}>Documentation</option>
      <option value='transcript'{_selected('transcript', mode)}>Transcript</option>
      <option value='clause'{_selected('clause', mode)}>By Clause</option>
    </select>

    <label for='clause'>Clause (optional)</label>
    <input id='clause' name='clause' value='{html.escape(clause)}' placeholder='e.g., 7.5 or 6.1.2'>

    <label for='question'>Question</label>
    <textarea id='question' name='question' required placeholder='Describe what prompt you need...'>{html.escape(question)}</textarea>

    <button type='submit'>Generate Prompt</button>
  </form>

  {prompt_block}
</body>
</html>
"""


class PromptWebHandler(BaseHTTPRequestHandler):
    engine: PromptEngine

    def _send_html(self, content: str, status: int = 200) -> None:
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self._send_html("<h1>Not found</h1>", status=404)
            return

        page = build_html_page({})
        self._send_html(page)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/":
            self._send_html("<h1>Not found</h1>", status=404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        data = urllib.parse.parse_qs(body)

        form_values = {
            "standard": data.get("standard", ["iso9001"])[0],
            "mode": data.get("mode", ["documentation"])[0],
            "clause": data.get("clause", [""])[0],
            "question": data.get("question", [""])[0],
        }

        try:
            prompt = self.engine.build_prompt(
                standard_key=form_values["standard"],
                mode=form_values["mode"],
                question=form_values["question"],
                clause=form_values["clause"] or None,
            )
            page = build_html_page(form_values, prompt=prompt)
            self._send_html(page)
        except ValueError as exc:
            page = build_html_page(form_values, error=str(exc))
            self._send_html(page, status=400)


def run_web_app(host: str, port: int, registry: pathlib.Path) -> None:
    handler = type("ConfiguredPromptWebHandler", (PromptWebHandler,), {})
    handler.engine = PromptEngine(registry)

    with ThreadingHTTPServer((host, port), handler) as server:
        print(f"ISO Prompt Builder web app running on http://{host}:{port}")
        server.serve_forever()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ISO prompt builder")
    sub = parser.add_subparsers(dest="command")

    generate = sub.add_parser("generate", help="Generate a prompt")
    generate.add_argument("--standard", required=True, choices=["iso9001", "iso14001", "iso45001"])
    generate.add_argument("--mode", required=True, choices=["documentation", "transcript", "clause"])
    generate.add_argument("--question", required=True)
    generate.add_argument("--clause", required=False)
    generate.add_argument("--registry", default=str(DEFAULT_REGISTRY))

    refresh = sub.add_parser("refresh_registry", help="Refresh standards registry from URL")
    refresh.add_argument("--source", required=True)
    refresh.add_argument("--registry", default=str(DEFAULT_REGISTRY))

    web = sub.add_parser("web", help="Run web app")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)
    web.add_argument("--registry", default=str(DEFAULT_REGISTRY))

    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()

    if args.command == "generate":
        engine = PromptEngine(pathlib.Path(args.registry))
        result = engine.build_prompt(
            standard_key=args.standard,
            mode=args.mode,
            question=args.question,
            clause=args.clause,
        )
        print(result)
        return 0

    if args.command == "refresh_registry":
        refresh_registry(args.source, pathlib.Path(args.registry))
        print(f"Updated registry: {args.registry}")
        return 0

    if args.command == "web":
        run_web_app(args.host, args.port, pathlib.Path(args.registry))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
