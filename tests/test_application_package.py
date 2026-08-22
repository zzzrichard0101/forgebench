import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ApplicationPackageTests(unittest.TestCase):
    def test_application_materials_preserve_the_negative_result(self) -> None:
        description = (
            ROOT / "docs/application-project-description.md"
        ).read_text(encoding="utf-8")
        demo = (ROOT / "demo/5-minute-demo.md").read_text(encoding="utf-8")
        for text in (description, demo):
            self.assertIn("0/30", text)
            self.assertIn("hard-safety", text)
            self.assertNotIn("improved held-out reliability", text)

    def test_one_page_pdf_is_present_and_linked(self) -> None:
        pdf = ROOT / "output/pdf/forgebench-one-page-portfolio.pdf"
        self.assertTrue(pdf.read_bytes().startswith(b"%PDF-"))
        self.assertGreater(pdf.stat().st_size, 20_000)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("output/pdf/forgebench-one-page-portfolio.pdf", readme)
        self.assertIn("demo/5-minute-demo.md", readme)


if __name__ == "__main__":
    unittest.main()
