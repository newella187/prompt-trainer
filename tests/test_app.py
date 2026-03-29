import pathlib
import unittest

from app import PromptEngine


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


if __name__ == "__main__":
    unittest.main()
