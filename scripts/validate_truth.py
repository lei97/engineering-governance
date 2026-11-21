#!/usr/bin/env python3
"""Validate restricted engineering YAML records."""
import argparse
import json
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
    errors, records = [], {}
    if not files:
        return ['no .yaml files found'], 0
    for path in files:
        try:
            record = load_restricted(path)
        except (ValueError, yaml.YAMLError, UnicodeError) as exc:
            errors.append(f'{path}: {exc}')
            continue
        for err in validator.iter_errors(record):
            errors.append(f'{path} [{"/".join(map(str,err.path)) or "root"}]: {err.message}')
        ident = record.get('id')
        kind = record.get('kind')
        if not isinstance(ident, str):
            continue
        if ident in records:
            errors.append(f'{path}: duplicate id {ident}')
        else:
            records[ident] = (path, record)
        if kind in PREFIX and not ident.startswith(PREFIX[kind]+'-'):
            errors.append(f'{path}: mismatched id and kind')
    for ident, (path, record) in records.items():
        origin = record.get('origin')
        if isinstance(origin, str):
            if origin == ident:
                errors.append(f'{path}: self origin')
            elif origin not in records:
                errors.append(f'{path}: missing origin {origin}')
            elif records[origin][1].get('kind') != 'source':
                errors.append(f'{path}: origin must be source')
        for rel, targets in (record.get('relations') or {}).items():
            if rel not in TARGETS or not isinstance(targets, list):
                continue
            for target in targets:
                if not isinstance(target, str):
                    continue
                if target == ident:
                    errors.append(f'{path}: self reference')
                elif target not in records:
                    errors.append(f'{path}: missing relation target {target}')
                elif target.split('-')[0] not in TARGETS[rel]:
                    errors.append(f'{path}: invalid {rel} target {target}')
    return errors, len(files)

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
