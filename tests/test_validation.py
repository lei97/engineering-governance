import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_truth import validate_path, load_restricted
ROOT = Path(__file__).resolve().parents[1]

class ValidationTests(unittest.TestCase):
    def test_valid(self):
        errors, count = validate_path(ROOT/'examples/valid')
        self.assertEqual(errors, [])
        self.assertEqual(count, 5)

    def test_invalid(self):
        errors, count = validate_path(ROOT/'examples/invalid')
        self.assertEqual(count, 5)
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


class BatchDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.batch = Path(temp.name)
        shutil.copytree(ROOT / 'examples/valid', self.batch, dirs_exist_ok=True)
        self.unrelated = self.batch / 'later' / 'REQ-004.yaml'
        self.unrelated.parent.mkdir()
        shutil.copyfile(ROOT / 'examples/invalid/dangling-reference.yaml', self.unrelated)

    def update_record(self, filename, **fields):
        path = self.batch / filename
        record = load_restricted(path)
        record.update(fields)
        path.write_text(yaml.safe_dump(record, allow_unicode=True), encoding='utf-8')
        return path

    def assert_batch_diagnostics(self, path, field, *additional):
        errors, _ = validate_path(self.batch)
        field_errors = [error for error in errors if error.startswith(f'{path} [{field}]: ')]
        self.assertEqual(len(field_errors), 1, errors)
        self.assertCountEqual(errors, [
            field_errors[0],
            f'{self.unrelated}: missing origin SRC-999',
            *additional,
        ])

    def test_kind_list_on_referenced_source(self):
        path = self.update_record('SRC-001.yaml', kind=['source'])
        self.assert_batch_diagnostics(path, 'kind')

    def test_relations_string(self):
        path = self.batch / 'TEST-002.yaml'
        shutil.copyfile(ROOT / 'examples/invalid/relations-string.yaml', path)
        self.assert_batch_diagnostics(path, 'relations')

    def test_relations_list_preserves_origin_check(self):
        path = self.update_record('REQ-001.yaml', relations=['verified_by'], origin='SRC-998')
        self.assert_batch_diagnostics(path, 'relations', f'{path}: missing origin SRC-998')

    def test_origin_list_preserves_relation_check(self):
        path = self.update_record(
            'REQ-001.yaml', origin=['SRC-001'], relations={'verified_by': ['TEST-999']}
        )
        self.assert_batch_diagnostics(path, 'origin', f'{path}: missing relation target TEST-999')

    def test_id_mapping_preserves_outgoing_checks(self):
        path = self.update_record('SRC-002.yaml', id={'value': 'SRC-002'}, origin='SRC-998')
        self.assert_batch_diagnostics(path, 'id', f'{path}: missing origin SRC-998')


if __name__=='__main__': unittest.main()
