import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_truth import validate_path, load_restricted
ROOT = Path(__file__).resolve().parents[1]

class ValidationTests(unittest.TestCase):
    def test_valid(self):
        errors, count = validate_path(ROOT/'examples/valid')
        self.assertEqual(errors, [])
        self.assertEqual(count, 4)

    def test_invalid(self):
        errors, count = validate_path(ROOT/'examples/invalid')
        self.assertEqual(count, 4)
        for term in ('duplicate mapping key', 'anchors forbidden', 'missing origin', 'acceptance'):
            self.assertTrue(any(term in e for e in errors), (term, errors))

    def test_reject_alias(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.yaml';p.write_text('a: &x hello\nb: *x\n')
            with self.assertRaisesRegex(ValueError,'anchors|aliases'):
                load_restricted(p)

    def test_reject_tags(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.yaml';p.write_text('a: !!str hello\n')
            with self.assertRaisesRegex(ValueError,'tags'):
                load_restricted(p)

    def test_reject_multiple_docs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.yaml';p.write_text('a: hello\n---\na: world\n')
            with self.assertRaisesRegex(ValueError,'exactly one'):
                load_restricted(p)

if __name__=='__main__': unittest.main()
