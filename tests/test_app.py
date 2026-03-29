import pathlib
import unittest

from app import PromptEngine, build_html_page


class PromptEngineTests(unittest.TestCase):
    def test_generate_documentation_prompt_contains_sections(self) -> None:
        engine = PromptEngine(pathlib.Path("standards_registry.json"))
        prompt = engine.build_prompt(
            standard_key="iso9001",
            mode="documentation",
            question="How do I evaluate document control for external providers?",
            clause="7.5",
        )

        self.assertIn("Interpretation of requirement", prompt)
        self.assertIn("Evidence expected by an auditor", prompt)
        self.assertIn("Target clause: 7.5", prompt)
        self.assertIn("ISO 9001", prompt)

    def test_unknown_standard_raises_value_error(self) -> None:
        engine = PromptEngine(pathlib.Path("standards_registry.json"))
        with self.assertRaises(ValueError):
            engine.build_prompt("iso9999", "documentation", "x")

    def test_build_html_page_includes_prompt_result(self) -> None:
        page = build_html_page(
            {
                "standard": "iso14001",
                "mode": "clause",
                "clause": "6.1.2",
                "question": "How to handle aspects?",
            },
            prompt="Generated prompt output",
        )

        self.assertIn("ISO Prompt Builder Web App", page)
        self.assertIn("Generated Prompt", page)
        self.assertIn("Generated prompt output", page)


if __name__ == "__main__":
    unittest.main()
