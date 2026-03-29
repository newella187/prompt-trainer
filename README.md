# ISO Prompt Builder (ISO 9001 / 14001 / 45001)

A small Python app that generates high-quality GPT prompts for:

- **Documentation questions**
- **Transcript analysis questions**
- **Clause-specific questions**

It supports ISO 9001, ISO 14001, and ISO 45001 and is designed to **adapt to standard updates** through a registry file.

## Why this app

Users often ask:

- “Give me a prompt to review this procedure against ISO 9001 clause 7.5.”
- “Give me a prompt to analyze this meeting transcript for ISO 45001 compliance issues.”
- “Give me a prompt by clause for ISO 14001 6.1.2.”

This app returns a ready-to-use prompt with strong constraints and output structure so GPT responses are more accurate and auditable.

## Features

- Prompt generation by:
  - `documentation`
  - `transcript`
  - `clause`
- Supports standards:
  - `iso9001`
  - `iso14001`
  - `iso45001`
- Uses a versioned registry (`standards_registry.json`) so updates to standards can be made without code changes.
- Includes a `refresh_registry` command to replace local registry data from an external JSON source.

## Quickstart

```bash
python3 app.py generate \
  --standard iso9001 \
  --mode documentation \
  --question "How do I assess control of documented information?" \
  --clause 7.5
```

## CLI usage

```bash
python3 app.py --help
```

Main options:

- `--standard`: `iso9001`, `iso14001`, or `iso45001`
- `--mode`: `documentation`, `transcript`, `clause`
- `--question`: user’s question
- `--clause`: optional clause key (e.g., `7.5`, `6.1.2`)
- `--registry`: optional path to registry JSON

## Updating standard versions

When ISO standards are revised, point to a new registry JSON:

```bash
python3 app.py refresh_registry \
  --source https://example.com/iso-registry.json \
  --registry standards_registry.json
```

The app reads `standard.edition`, `standard.published_date`, and clause descriptors directly from the registry.

## JSON schema (simplified)

```json
{
  "standards": {
    "iso9001": {
      "title": "ISO 9001",
      "edition": "2015",
      "published_date": "2015-09-15",
      "sources": ["https://www.iso.org/standard/..."],
      "clauses": {
        "7.5": "Documented information"
      }
    }
  }
}
```

## Notes

- The app **does not provide legal certification advice**.
- It generates robust prompts for use with GPT models.
- Always validate outputs against your certified management system requirements and latest official ISO publications.
