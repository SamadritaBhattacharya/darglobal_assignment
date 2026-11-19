"""The three retrievers side by side: why hybrid is used. Observed by which pages each one returns."""
import json
import pathlib

import pytest

from dar.adapters.retrieval import Bm25Retriever, DenseRetriever, HybridRetriever
from dar.domain.models import Chunk

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_realestate.json"


@pytest.fixture(scope="module")
def retrievers():
    chunks = [Chunk(**r) for r in json.loads(CORPUS.read_text(encoding="utf-8"))]
    return {
        "bm25": Bm25Retriever(chunks),
        "dense": DenseRetriever(chunks, max_distance=9.0),
        "hybrid": HybridRetriever(chunks, max_distance=9.0, min_coverage=0.0),
    }


def ids(retriever, query, k=3):
    return [c.id for c in retriever.search(query, k=k)]


def test_keyword_search_finds_exact_names_but_not_paraphrases(retrievers):
    assert ids(retrievers["bm25"], "Marlow Plaza")[0] == "re-marlow"
    assert "re-garden" not in ids(retrievers["bm25"], "good place to raise kids")  # shares no words with the page


def test_vector_search_finds_paraphrases(retrievers):
    assert "re-garden" in ids(retrievers["dense"], "good place to raise kids")


def test_hybrid_gets_both_the_exact_name_and_the_paraphrase(retrievers):
    assert ids(retrievers["hybrid"], "Marlow Plaza")[0] == "re-marlow"
    assert "re-garden" in ids(retrievers["hybrid"], "good place to raise kids")
