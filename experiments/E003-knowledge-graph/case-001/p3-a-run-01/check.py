"""Evaluate an E003 P3-A patch against the fixed pre-fix snapshot."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


FIXTURE = Path('examples/invalid/missing-acceptance.yaml')
REPAIRED_ACCEPTANCE = 'acceptance:\n  - 校验器可以读取补齐的验收条件。\n'
REQUIRED_DIAGNOSTIC = "'acceptance' is a required property"
COMMON_FIXTURES = ('dangling-reference.yaml', 'duplicate-key.yaml', 'relations-string.yaml')


def capture(root, args):
    try:
        result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return {'exit': None, 'stdout': '', 'stderr': 'Timeout after 45 seconds'}
    return {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def python(root, *args):
    return capture(root, [sys.executable, '-B', *args])


def invalid(root):
    result = python(root, 'scripts/validate_truth.py', 'examples/invalid')
    diagnostics = [line for line in result['stderr'].splitlines() if line.startswith('ERROR: ')]
    related = [line for line in diagnostics if str(FIXTURE) in line]
    unrelated = Counter(line for line in diagnostics if line not in related)
    return result, related, unrelated


def actual_test_count(result):
    match = re.search(r'Ran (\d+) tests?', result['stderr'])
    return int(match.group(1)) if match else 0


def check(baseline, patch):
    _, _, original_other = invalid(baseline)
    expected_other = Counter(line for line in original_other.elements()
                             if any(f'examples/invalid/{name}' in line for name in COMMON_FIXTURES))
    if len(expected_other) != len(COMMON_FIXTURES):
        raise ValueError('Baseline does not contain the three common independent diagnostics')
    with tempfile.TemporaryDirectory(prefix='e003-p3-check-') as temp:
        root = Path(temp) / 'snapshot'
        shutil.copytree(baseline, root)
        applied = capture(root, ['git', 'apply', '--whitespace=nowarn', str(patch)])
        if applied['exit'] != 0:
            return {'applied': False, 'apply_log': applied, 'passed': False}

        entire_suite = python(root, '-m', 'unittest', 'discover', '-s', 'tests', '-v')
        positive = python(root, 'scripts/validate_truth.py', 'examples/valid')
        regression = python(root, '-m', 'unittest', 'discover', '-s', 'tests', '-k', 'BatchDiagnosticsTests', '-v')
        original = (root / FIXTURE).read_text(encoding='utf-8')
        probes = {}
        for label, contents in (
            ('original', original),
            ('restored', original + REPAIRED_ACCEPTANCE),
            ('wrong_diagnostic', original.replace('origin: SRC-001', 'origin: SRC-998') + REPAIRED_ACCEPTANCE),
        ):
            (root / FIXTURE).write_text(contents, encoding='utf-8')
            tested = python(root, '-m', 'unittest', 'discover', '-s', 'tests', '-k', 'test_invalid', '-v')
            validate, related, other = invalid(root)
            probes[label] = {
                'test': tested,
                'tests_run': actual_test_count(tested),
                'validation_exit': validate['exit'],
                'related_diagnostics': related,
                'common_diagnostics_preserved': other >= expected_other,
            }

        start = probes['original']
        gates = {
            'normal_tests_and_valid_fixtures': (
                entire_suite['exit'] == 0 and actual_test_count(entire_suite) > 0 and positive['exit'] == 0
                and start['test']['exit'] == 0 and start['tests_run'] > 0 and start['validation_exit'] == 1
                and any(REQUIRED_DIAGNOSTIC in line for line in start['related_diagnostics'])
            ),
            'prior_batch_regressions': regression['exit'] == 0 and actual_test_count(regression) >= 5,
            'independent_diagnostics_preserved': all(p['common_diagnostics_preserved'] for p in probes.values()),
        }
        for label in ('restored', 'wrong_diagnostic'):
            row = probes[label]
            error = row['test']['stderr']
            gates[label] = (
                row['tests_run'] > 0 and row['test']['exit'] == 1
                and 'FAIL: test_invalid' in error and 'AssertionError' in error
                and ('missing-acceptance.yaml' in error or REQUIRED_DIAGNOSTIC in error)
                and not any(REQUIRED_DIAGNOSTIC in line for line in row['related_diagnostics'])
                and (label != 'wrong_diagnostic'
                     or any(line.endswith('missing origin SRC-998') for line in row['related_diagnostics']))
            )
        return {
            'applied': True, 'gates': gates, 'passed': all(gates.values()), 'probes': probes,
            'normal_suite': entire_suite, 'positive_validation': positive, 'batch_regression': regression,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('patch', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.baseline.resolve(), args.patch.resolve()), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
