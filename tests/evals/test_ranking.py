"""Search ranking benchmark on fictional names: hit@1 and hit@5, before/after."""

import json
import unicodedata
from pathlib import Path

from eu_reg_mcp.register import search_entries

HERE = Path(__file__).parent
SNAPSHOT = json.loads((HERE / "ranking_snapshot.json").read_text(encoding="utf-8"))
QUERIES = json.loads((HERE / "ranking_queries.json").read_text(encoding="utf-8"))


def _fold(text):
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


def baseline_ids(query):
    """The search before ranking: substring or exact LEI, register order."""
    needle = _fold(query)
    return [
        entry["entry_id"]
        for entry in SNAPSHOT["registers"][0]["entries"]
        if needle in _fold(entry["entity_name"]) or needle == _fold(entry["lei"])
    ]


def ranked_ids(query):
    """Real matches only: `results`, never `similar_names`."""
    return [hit["entry_id"] for hit in search_entries(SNAPSHOT, query)["results"]]


def similar_ids(query):
    """Suggestions labelled "not a match", for zero-match queries."""
    return [hit["entry_id"] for hit in search_entries(SNAPSHOT, query)["similar_names"]]


def hit_rate(ids_for, k, cases=None):
    cases = QUERIES if cases is None else cases
    hits = sum(
        any(i in case["expected"] for i in ids_for(case["query"])[:k]) for case in cases
    )
    return hits / len(cases)


def test_benchmark_size():
    assert len(QUERIES) >= 20


def test_ranking_beats_baseline_on_real_matches():
    # Ranking only reorders literal matches, so hit@5 cannot rise; hit@1 does.
    before = (hit_rate(baseline_ids, 1), hit_rate(baseline_ids, 5))
    after = (hit_rate(ranked_ids, 1), hit_rate(ranked_ids, 5))
    print(f"real-match hit@1 {before[0]:.2f} -> {after[0]:.2f}", end="; ")
    print(f"hit@5 {before[1]:.2f} -> {after[1]:.2f}")
    assert after[0] > before[0]
    assert after[1] >= before[1]
    matched = [case for case in QUERIES if ranked_ids(case["query"])]
    assert hit_rate(ranked_ids, 1, matched) == 1.0


def test_similar_names_recall_on_zero_match_queries():
    # Reported apart from hit@k: these suggestions are not matches (rule 2).
    zero = [case for case in QUERIES if not ranked_ids(case["query"])]
    recall = hit_rate(similar_ids, 1, zero)
    print(f"similar_names recall@1 {recall:.2f} on {len(zero)} zero-match queries")
    assert zero and recall >= 0.9


def test_exact_lei_and_exact_name_rank_first():
    lei = search_entries(SNAPSHOT, "529900EXAMPLE0000022")["results"][0]
    assert lei["match"] == {"score": 1.0, "basis": "exact_lei"}
    name = search_entries(SNAPSHOT, "kestrel coin foundation")["results"][0]
    assert name["match"]["basis"] == "exact_name"


def test_similar_names_only_without_matches_and_never_for_leis():
    assert search_entries(SNAPSHOT, "orbit")["similar_names"] == []
    assert search_entries(SNAPSHOT, "529900EXAMPLE9999999")["similar_names"] == []
    similar = search_entries(SNAPSHOT, "kestral coin")["similar_names"]
    assert 0 < len(similar) <= 5
    assert all(item["label"] == "not a match" for item in similar)
    assert all(0.8 <= item["similarity"] <= 1 for item in similar)


def test_whole_words_outrank_partial_word_prefix():
    snapshot = {
        "snapshot_date": "2026-10-19",
        "registers": [
            {
                "slug": "other-wp",
                "fetched": True,
                "entries": [
                    {"entry_id": "p", "entity_name": "Tokenise Example GmbH"},
                    {"entry_id": "w", "entity_name": "Example Token AG"},
                ],
            }
        ],
    }
    ids = [hit["entry_id"] for hit in search_entries(snapshot, "token")["results"]]
    assert ids == ["w", "p"]


def test_nonsense_has_no_similar_names():
    assert search_entries(SNAPSHOT, "xyzzy plugh")["similar_names"] == []
