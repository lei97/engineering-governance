"""Rebuild the recorded Apollo graph and score it against the pinned Cookbook labels."""

import argparse
import json
from pathlib import Path
from statistics import mean

import networkx as nx


RUN = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def metrics(predicted, gold):
    hits = len(predicted & gold)
    precision = hits / len(predicted) if predicted else 0.0
    recall = hits / len(gold) if gold else 0.0
    f1 = 2 * hits / (len(predicted) + len(gold)) if predicted or gold else 0.0
    return dict(predicted=len(predicted), gold=len(gold), hits=hits,
                precision=precision, recall=recall, f1=f1)


def score(extracted, labels, aliases, resolved):
    def norm(name):
        name = name.strip().lower()
        return aliases.get(name, name)

    def triples(record):
        return {(norm(r['source']), r['predicate'].strip().lower(), norm(r['target']))
                for r in record['relations']}

    def endpoints(relations):
        return {(source, target) for source, _, target in relations}

    rows = {}
    for title, gold in labels.items():
        document = extracted[title]
        names = {norm(e['name']) for e in document['entities']}
        gold_names = {norm(e['name']) for e in gold['entities']}
        gold_triples = triples(gold)
        predicted = triples(document)
        control = {(source, 'predicate replaced for control', target)
                   for source, _, target in gold_triples}
        rows[title] = {
            'entity_names': metrics(names, gold_names),
            'relation_endpoints': metrics(endpoints(predicted), endpoints(gold_triples)),
            'literal_triples': metrics(predicted, gold_triples),
            'resolved_entity_recall': metrics(
                {norm(resolved.get(e['name'], e['name'])) for e in document['entities']},
                gold_names,
            )['recall'],
            'wrong_predicate_control': {
                'endpoint_f1': metrics(endpoints(control), endpoints(gold_triples))['f1'],
                'literal_triple_f1': metrics(control, gold_triples)['f1'],
            },
        }
    macro = {key: {m: mean(row[key][m] for row in rows.values())
                   for m in ('precision', 'recall', 'f1')}
             for key in ('entity_names', 'relation_endpoints', 'literal_triples')}
    return {'documents': rows, 'macro': macro}


def build_graph(extracted, clusters):
    graph = nx.MultiDiGraph()
    resolved = {}
    node_types = {}
    for entity_type, group in clusters.items():
        for cluster in group:
            canonical = cluster['canonical']
            node_types[canonical] = entity_type
            for alias in cluster['aliases']:
                if alias in resolved:
                    raise ValueError(f'Entity assigned twice: {alias}')
                resolved[alias] = canonical

    unresolved = set()
    dropped_edges = 0
    for title, doc in extracted.items():
        local_names = {e['name'] for e in doc['entities']}
        for entity in doc['entities']:
            name = entity['name']
            canonical = resolved.get(name)
            if canonical is None:
                unresolved.add(name)
                continue
            if canonical not in graph:
                graph.add_node(canonical, type=node_types[canonical],
                               description=entity['description'], source_docs=[], mentions=0)
            node = graph.nodes[canonical]
            node['source_docs'].append(title)
            node['mentions'] += 1
        for relation in doc['relations']:
            source, target = relation['source'], relation['target']
            if source not in local_names or target not in local_names:
                raise ValueError(f'Relation endpoint not extracted in {title}: {relation}')
            source, target = resolved.get(source), resolved.get(target)
            if source and target and source != target:
                graph.add_edge(source, target, predicate=relation['predicate'], source_doc=title)
            else:
                dropped_edges += 1

    for _, node in graph.nodes(data=True):
        node['source_docs'] = sorted(set(node['source_docs']))
    return graph, resolved, sorted(unresolved), dropped_edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cookbook_data', type=Path, help='directory with the pinned gold and alias JSON files')
    args = parser.parse_args()
    extracted = read_json(RUN / 'extraction.json')
    clusters = read_json(RUN / 'clusters.json')
    graph, resolved, unresolved, dropped = build_graph(extracted, clusters)
    results = {
        'document_count': len(extracted),
        'raw_entities': sum(len(doc['entities']) for doc in extracted.values()),
        'raw_relations': sum(len(doc['relations']) for doc in extracted.values()),
        'unresolved_names': unresolved,
        'dropped_edges': dropped,
        'node_count': graph.number_of_nodes(),
        'edge_count': graph.number_of_edges(),
        'weak_components': nx.number_weakly_connected_components(graph),
        'evaluation': score(extracted, read_json(args.cookbook_data / 'sample_triples.json'),
                            read_json(args.cookbook_data / 'alias_map.json'), resolved),
        'graph': nx.node_link_data(graph, edges='edges'),
    }
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
