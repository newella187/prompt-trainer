#!/usr/bin/env python3
"""ISO prompt builder CLI.

Generates high-accuracy prompts for ISO 9001/14001/45001 questions
in documentation, transcript, or clause mode.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import textwrap
import urllib.request
from dataclasses import dataclass

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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
