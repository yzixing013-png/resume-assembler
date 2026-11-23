"""Check the independently installed Skill and persistent-library behavior."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


class SkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installation = tempfile.TemporaryDirectory()
        source = Path(__file__).resolve().parents[1] / "skills" / "resume-assembler"
        cls.skill = Path(cls.installation.name) / "installed-skill"
        shutil.copytree(source, cls.skill, ignore=shutil.ignore_patterns("__pycache__"))
        cls.tool = cls.skill / "scripts" / "resume.py"

    @classmethod
    def tearDownClass(cls):
        cls.installation.cleanup()

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.root = Path(self.workspace.name)
        self.data = self.root / "personal data"

    def tearDown(self):
        self.workspace.cleanup()

    def run_tool(self, *arguments, success=True):
        result = subprocess.run(
            [sys.executable, str(self.tool), *arguments, "--data", str(self.data)],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return json.loads(result.stdout if success else result.stderr)

    def library(self):
        return json.loads((self.data / "library.json").read_text(encoding="utf-8"))

    def test_standalone_init_preserves_legacy_metadata_and_backs_up(self):
        self.run_tool("init")
        library = self.library()
        library["projects"] = [{"id": "old-project", "facts": [], "reports": [{"id": "old-report", "content": "original"}]}]
        library["custom_metadata"] = {"keep": True}
        (self.data / "library.json").write_text(json.dumps(library), encoding="utf-8")
        result = self.run_tool("init")
        self.assertEqual(self.library(), library)
        self.assertEqual(json.loads(Path(result["backup"]).read_text()), library)

    def test_reimport_preserves_source_identity_and_original_bytes(self):
        self.run_tool("init")
        report = self.root / "extracted.txt"
        original = b"\xef\xbb\xbfValidated 12 cases."
        report.write_bytes(original)
        first = self.run_tool("import", "--file", str(report))
        copied = self.root / "copy.txt"
        copied.write_bytes(original)
        second = self.run_tool("import", "--file", str(copied))
        self.assertTrue(second["reused"])
        self.assertEqual(first["source"]["id"], second["source"]["id"])
        self.assertEqual(len(self.library()["sources"]), 1)
        self.assertEqual((self.data / first["source"]["snapshot"]).read_bytes(), original)
        self.assertEqual((self.data / first["source"]["text_snapshot"]).read_text(), "Validated 12 cases.")

    def test_template_upload_is_separate_from_material_and_reuses_selection(self):
        self.run_tool("init")
        template = self.root / "template.zip"
        with zipfile.ZipFile(template, "w") as archive:
            archive.writestr("main.tex", r"\documentclass{article}\begin{document}{{CONTENT}}\end{document}")
        self.run_tool("import", "--file", str(template))
        result = self.run_tool("import", "--file", str(template), "--kind", "template")
        self.assertEqual(self.library()["template"], result["source"]["template_id"])
        self.assertEqual(len(self.library()["sources"]), 2)
        again = self.run_tool("import", "--file", str(template), "--kind", "template")
        self.assertTrue(again["reused"])
        self.assertEqual(len(self.library()["sources"]), 2)

    def test_failed_template_import_leaves_library_intact(self):
        self.run_tool("init")
        before = self.library()
        archive_path = self.root / "bad.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("../outside.tex", "bad")
        self.run_tool("import", "--file", str(archive_path), "--kind", "template", success=False)
        self.assertEqual(self.library(), before)
        self.assertEqual(list((self.data / "templates").iterdir()), [])

    def test_render_rejects_fabricated_numbers_before_compilation(self):
        self.run_tool("init")
        library = self.library()
        library["projects"] = [{"id": "p", "facts": [{"id": "f", "text": "Validated 12 cases."}]}]
        (self.data / "library.json").write_text(json.dumps(library), encoding="utf-8")
        assembly = self.root / "assembly.json"
        assembly.write_text(json.dumps({"selected": [{"id": "p", "bullets": [{"text": "Validated 99 cases.", "evidence": ["f"]}]}]}), encoding="utf-8")
        self.run_tool("render", "--assembly", str(assembly), success=False)
        self.assertEqual(list((self.data / "outputs").iterdir()), [])

    def test_images_are_archived_for_host_interpretation(self):
        self.run_tool("init")
        path = self.root / "certificate.png"
        path.write_bytes(b"image fixture")
        result = self.run_tool("import", "--file", str(path))
        self.assertIn("note", result["source"])
        self.assertTrue((self.data / result["source"]["snapshot"]).is_file())


if __name__ == "__main__":
    unittest.main()
