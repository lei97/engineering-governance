#!/usr/bin/env python3
"""Validate restricted engineering YAML records."""
import argparse
import json
import stat
import sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PREFIX = dict(requirement='REQ', source='SRC', contract='CON', artifact='ART', test='TEST', observation='OBS')
TARGETS = dict(refined_by={'REQ','CON'}, implemented_by={'ART'}, verified_by={'TEST'}, derived_from=set(PREFIX.values()))

class Loader(yaml.BaseLoader):
    pass

def mapping(loader, node):
    result = {}
    for k, v in node.value:
        if not isinstance(k, yaml.ScalarNode):
            raise ValueError('complex mapping keys forbidden')
        key = loader.construct_object(k)
        if key in result:
            raise ValueError(f'duplicate mapping key: {key}')
        result[key] = loader.construct_object(v)
    return result
Loader.add_constructor('tag:yaml.org,2002:map', mapping)

def load_restricted(path):
    source = path.read_text(encoding='utf-8-sig')
    events = list(yaml.parse(source))
    for event in events:
        if isinstance(event, yaml.events.AliasEvent):
            raise ValueError('YAML aliases forbidden')
        if isinstance(event, (yaml.events.ScalarEvent, yaml.events.SequenceStartEvent, yaml.events.MappingStartEvent)):
            if event.anchor is not None:
                raise ValueError('YAML anchors forbidden')
            if event.tag is not None:
                raise ValueError('explicit YAML tags forbidden')
    if sum(isinstance(e, yaml.events.DocumentStartEvent) for e in events) != 1:
        raise ValueError('expected exactly one YAML document')
    data = yaml.load(source, Loader=Loader)
    if not isinstance(data, dict):
        raise ValueError('top-level mapping required')
    return data

def validate_path(directory):
    schema = json.loads((ROOT/'schemas/knowledge.schema.json').read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema)
    files = sorted(directory.rglob('*.yaml'))
    count = len(files)
    errors = []
    for path in sorted(directory.rglob('*.yml')):
        if not path.name.endswith('.yml'):
            continue
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                continue
        except OSError:
            # The suffix remains reportable even if the entry cannot be inspected.
            pass
        errors.append(f'{path}: unsupported .yml file extension; use .yaml')
    records = []
    kind_by_id = {}
    for path in files:
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                count -= 1
                continue
            record = load_restricted(path)
        except OSError as exc:
            errors.append(f'{path}: cannot read YAML file: {exc.strerror or exc}')
            continue
        except (ValueError, yaml.YAMLError, UnicodeError) as exc:
            errors.append(f'{path}: {exc}')
            continue
        for err in validator.iter_errors(record):
            errors.append(f'{path} [{"/".join(map(str,err.path)) or "root"}]: {err.message}')
        records.append((path, record))
        ident = record.get('id')
        if not isinstance(ident, str):
            continue
        kind = record.get('kind')
        if not isinstance(kind, str) or kind not in PREFIX:
            # The ID still resolves even when the kind cannot be checked.
            kind = None
        if ident in kind_by_id:
            errors.append(f'{path}: duplicate id {ident}')
        else:
            kind_by_id[ident] = kind
        if kind is not None and not ident.startswith(PREFIX[kind] + '-'):
            errors.append(f'{path}: mismatched id and kind')
    for path, record in records:
        ident = record.get('id')
        origin = record.get('origin')
        if isinstance(origin, str):
            if origin == ident:
                errors.append(f'{path}: self origin')
            elif origin not in kind_by_id:
                errors.append(f'{path}: missing origin {origin}')
            elif kind_by_id[origin] not in (None, 'source'):
                errors.append(f'{path}: origin must be source')
        relations = record.get('relations')
        if not isinstance(relations, dict):
            continue
        for rel, targets in relations.items():
            if rel not in TARGETS or not isinstance(targets, list):
                continue
            for target in targets:
                if not isinstance(target, str):
                    continue
                if target == ident:
                    errors.append(f'{path}: self reference')
                elif target not in kind_by_id:
                    errors.append(f'{path}: missing relation target {target}')
                elif target.split('-')[0] not in TARGETS[rel]:
                    errors.append(f'{path}: invalid {rel} target {target}')
    if not count and not errors:
        errors.append('no .yaml files found')
    return errors, count

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error('expected existing directory')
    errors, count = validate_path(args.directory)
    for error in errors:
        print('ERROR:', error, file=sys.stderr)
    print(f'{"FAIL" if errors else "PASS"}: {count} YAML records; {len(errors)} errors')
    return int(bool(errors))

if __name__ == '__main__':
    sys.exit(main())
