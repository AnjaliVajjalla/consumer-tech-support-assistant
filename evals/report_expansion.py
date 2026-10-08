"""Export reproducible retrieval results and misses without generation API calls."""

import json
from pathlib import Path

from evals.eval_retrieval import GOLDEN_SET, METHODS
from src.retrieve import load_chunks_with_embeddings


def main():
    chunks = load_chunks_with_embeddings()
    report = {"questions": len(GOLDEN_SET), "documents": len({c['doc_id'] for c in chunks}),
              "chunks": len(chunks), "hybrid_alpha": 0.95, "methods": {}}
    for name, method in METHODS.items():
        cases = []
        for case in GOLDEN_SET:
            results = method(case['question'], chunks, top_k=3)
            rank = next((i for i, result in enumerate(results, 1)
                         if result['doc_id'] == case['expected_doc_id']), None)
            cases.append({**case, "rank": rank, "retrieved_doc_ids": [r['doc_id'] for r in results]})
        report['methods'][name] = {
            "hit_rate@3": round(sum(c['rank'] is not None for c in cases) / len(cases), 4),
            "mrr@3": round(sum(1 / c['rank'] if c['rank'] else 0 for c in cases) / len(cases), 4),
            "cases": cases,
        }
        print(name, {k: v for k, v in report['methods'][name].items() if k != 'cases'}, flush=True)
    output = Path(__file__).resolve().parents[1] / 'docs' / 'evaluation-results.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {output}')


if __name__ == '__main__':
    main()
