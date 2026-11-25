import errno
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_truth import validate_path, load_restricted
ROOT = Path(__file__).resolve().parents[1]
SUFFIX_EXAMPLES = ROOT / 'examples/file-suffix'

INVALID_DIAGNOSTICS = {
    '00-support/SRC-001.yaml': [],
    'alias.yaml': ['YAML aliases forbidden'],
    'anchor.yaml': ['YAML anchors forbidden'],
    'complex-mapping-key.yaml': ['complex mapping keys forbidden'],
    'dangling-reference.yaml': ['missing origin SRC-999'],
    'duplicate-id.yaml': ['duplicate id SRC-001'],
    'duplicate-key.yaml': ['duplicate mapping key: id'],
    'explicit-tag.yaml': ['explicit YAML tags forbidden'],
    'invalid-relation-target.yaml': ['invalid verified_by target SRC-001'],
    'mismatched-id-kind.yaml': ['mismatched id and kind'],
    'missing-acceptance.yaml': ["[root]: 'acceptance' is a required property"],
    'missing-relation-target.yaml': ['missing relation target TEST-999'],
    'multiple-documents.yaml': ['expected exactly one YAML document'],
    'origin-not-source.yaml': ['origin must be source'],
    'relation-self.yaml': ['self reference'],
    'relations-string.yaml': ["[relations]: 'REQ-001' is not of type 'object'"],
    'self-origin.yaml': ['self origin'],
    'top-level-sequence.yaml': ['top-level mapping required'],
}


class ValidationTests(unittest.TestCase):
    def test_valid(self):
        errors, count = validate_path(ROOT/'examples/valid')
        self.assertEqual(errors, [])
        self.assertEqual(count, 5)

    def test_invalid(self):
        self.assert_invalid_examples(ROOT / 'examples/invalid')

    def assert_invalid_examples(self, directory):
        files = [path.relative_to(directory).as_posix() for path in directory.rglob('*.yaml')]
        self.assertCountEqual(files, INVALID_DIAGNOSTICS.keys())
        errors, count = validate_path(directory)
        self.assertEqual(count, len(files))
        for filename, expected in INVALID_DIAGNOSTICS.items():
            path = str(directory / filename)
            prefixes = (f'{path}: ', f'{path} [')
            diagnostics = [
                error[len(path):].removeprefix(': ').removeprefix(' ')
                for error in errors if error.startswith(prefixes)
            ]
            self.assertEqual(diagnostics, expected, filename)
        self.assertEqual(len(errors), sum(map(len, INVALID_DIAGNOSTICS.values())), errors)

    def test_repaired_acceptance_fails_negative_assertion(self):
        with tempfile.TemporaryDirectory() as temp:
            examples = Path(temp) / 'invalid'
            shutil.copytree(ROOT / 'examples/invalid', examples)
            path = examples / 'missing-acceptance.yaml'
            record = load_restricted(path)
            record['acceptance'] = ['校验器可以读取补齐的验收条件。']
            path.write_text(yaml.safe_dump(record, allow_unicode=True), encoding='utf-8')

            with self.assertRaisesRegex(self.failureException, "'acceptance' is a required property"):
                self.assert_invalid_examples(examples)

            record['origin'] = 'SRC-998'
            path.write_text(yaml.safe_dump(record, allow_unicode=True), encoding='utf-8')

            with self.assertRaisesRegex(self.failureException, 'missing origin SRC-998'):
                self.assert_invalid_examples(examples)


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


class InputDiscoveryTests(unittest.TestCase):
    def run_validator(self, directory):
        return subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts/validate_truth.py'), str(directory)],
            capture_output=True, text=True, check=False,
        )

    def test_record_suffix_directories_are_scanned_as_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            nested = batch / 'records.yml' / 'nested.yaml'
            shutil.copytree(SUFFIX_EXAMPLES / 'valid', nested)
            shutil.copyfile(
                SUFFIX_EXAMPLES / 'valid/SRC-999.yaml', nested / 'ignored.YML'
            )
            result = self.run_validator(batch)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'PASS: 1 YAML records; 0 errors')
        self.assertEqual(result.stderr, '')

    def test_mixed_batch_reports_each_unsupported_file_and_validates_yaml(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            shutil.copytree(SUFFIX_EXAMPLES / 'invalid', batch, dirs_exist_ok=True)
            rejected = batch / 'nested' / 'SRC-999.yml'
            rejected_invalid_content = batch / 'invalid-content.yml'
            rejected_invalid_content.write_text('[', encoding='utf-8')
            shutil.copyfile(ROOT / 'examples/valid/SRC-001.yaml', batch / 'SRC-001.yaml')
            dependent = batch / 'REQ-004.yaml'
            shutil.copyfile(ROOT / 'examples/invalid/dangling-reference.yaml', dependent)
            result = self.run_validator(batch)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.strip(), 'FAIL: 2 YAML records; 3 errors')
        self.assertCountEqual(result.stderr.splitlines(), [
            f'ERROR: {rejected}: unsupported .yml file extension; use .yaml',
            f'ERROR: {rejected_invalid_content}: unsupported .yml file extension; use .yaml',
            f'ERROR: {dependent}: missing origin SRC-999',
        ])

    def test_only_unsupported_suffix_reports_the_path(self):
        batch = SUFFIX_EXAMPLES / 'invalid'
        rejected = batch / 'nested' / 'SRC-999.yml'
        result = self.run_validator(batch)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.strip(), 'FAIL: 0 YAML records; 1 errors')
        self.assertEqual(
            result.stderr.strip(), f'ERROR: {rejected}: unsupported .yml file extension; use .yaml'
        )

    def test_reports_unsupported_file_when_metadata_is_inaccessible(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            shutil.copytree(SUFFIX_EXAMPLES / 'invalid', batch, dirs_exist_ok=True)
            rejected = batch / 'nested' / 'SRC-999.yml'
            dependent = batch / 'REQ-004.yaml'
            shutil.copyfile(ROOT / 'examples/invalid/dangling-reference.yaml', dependent)
            stat_path = Path.stat

            def stat_record(path, *args, **kwargs):
                if path == rejected:
                    raise PermissionError(errno.EACCES, 'Permission denied', path)
                return stat_path(path, *args, **kwargs)

            with patch.object(Path, 'stat', stat_record):
                errors, count = validate_path(batch)

        self.assertEqual(count, 1)
        self.assertCountEqual(errors, [
            f'{rejected}: unsupported .yml file extension; use .yaml',
            f'{dependent}: missing origin SRC-999',
        ])

    def test_unreadable_record_preserves_later_file_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            shutil.copytree(SUFFIX_EXAMPLES / 'valid', batch, dirs_exist_ok=True)
            unreadable = batch / 'SRC-999.yaml'
            dependent = batch / 'later' / 'REQ-004.yaml'
            dependent.parent.mkdir()
            shutil.copyfile(ROOT / 'examples/invalid/dangling-reference.yaml', dependent)
            read_text = Path.read_text

            def read_record(path, *args, **kwargs):
                if path == unreadable:
                    raise PermissionError(errno.EACCES, 'Permission denied', path)
                return read_text(path, *args, **kwargs)

            with patch.object(Path, 'read_text', read_record):
                errors, count = validate_path(batch)

        self.assertEqual(count, 2)
        self.assertCountEqual(errors, [
            f'{unreadable}: cannot read YAML file: Permission denied',
            f'{dependent}: missing origin SRC-999',
        ])


if __name__=='__main__': unittest.main()
