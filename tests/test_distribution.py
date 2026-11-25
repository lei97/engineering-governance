from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_distribution.py"


class DistributionTests(unittest.TestCase):
    def build(self, variant, destination):
        return subprocess.run(
            [sys.executable, str(BUILDER), variant, str(destination)],
            cwd=destination.parent,
            capture_output=True,
            text=True,
        )

    def test_light_contains_installable_skill_and_references(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "light.zip"
            result = self.build("light", destination)
            self.assertEqual(result.returncode, 0, result.stderr)

            with ZipFile(destination) as bundle:
                skill = "skills/engineering-governance"
                expected = {"LICENSE", "docs/install.md", f"{skill}/SKILL.md"}
                expected.update(
                    f"{skill}/references/{name}.md"
                    for name in (
                        "standard", "creative", "learning", "reverse", "repair",
                        "governance-summary",
                    )
                )
                self.assertEqual(set(bundle.namelist()), expected)

    def test_full_validates_external_project(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            destination = workspace / "full.zip"
            result = self.build("full", destination)
            self.assertEqual(result.returncode, 0, result.stderr)

            governance = workspace / "governance bundle"
            with ZipFile(destination) as bundle:
                self.assertIn("specifications/change-protocol.md", bundle.namelist())
                self.assertIn("requirements.txt", bundle.namelist())
                schema = "schemas/knowledge.schema.json"
                self.assertEqual(bundle.read(schema), (ROOT / schema).read_bytes())
                bundle.extractall(governance)

            project = workspace / "external project"
            shutil.copytree(ROOT / "examples/valid", project / "truth")
            result = subprocess.run(
                [sys.executable, str(governance / "scripts/validate_truth.py"), "truth"],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS: 5 YAML records; 0 errors", result.stdout)

    def test_build_preserves_existing_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "existing.zip"
            destination.write_bytes(b"existing content")

            result = self.build("full", destination)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(destination.read_bytes(), b"existing content")
