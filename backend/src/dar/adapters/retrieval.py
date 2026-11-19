from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

import chromadb
from rank_bm25 import BM25Plus

from dar.domain.models import Chunk

_WORD = re.compile(r"\w+")
_STOP = frozenset(
    "a an the of to in on at for and or is are was be with from by as it its this that what which who how "
    "do does me my you your i we they about near close any some there".split()
)
RRF_K = 60


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text) if w.lower() not in _STOP]


class Bm25Retriever:
    """Keyword retriever. Implements dar.domain.ports.Retriever."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._index = BM25Plus([_tokenize(f"{c.title} {c.section} {c.text}") or ["_"] for c in chunks])

    def search(self, query: str, k: int = 5, min_coverage: float = 0.0) -> list[Chunk]:
        """Chunks sharing query words. min_coverage = fraction of query words a chunk must contain."""
        terms = _tokenize(query)
        if not terms:
            return []
        scores = self._index.get_scores(terms)
        ranked = sorted(range(len(self._chunks)), key=lambda i: scores[i], reverse=True)

        def coverage(i: int) -> float:
            return sum(t in self._index.doc_freqs[i] for t in terms) / len(terms)

        hits = [i for i in ranked if coverage(i) > 0 and coverage(i) >= min_coverage]
        return [self._chunks[i] for i in hits[:k]]


def _open_collection(chunks: list[Chunk], index_dir: Path | None):
    """In memory by default. With index_dir the vectors persist and are reused unless the data changed."""
    config = {"hnsw": {"space": "cosine"}}
    fingerprint = hashlib.sha1("\n".join(f"{c.id}\t{c.text}" for c in chunks).encode()).hexdigest()
    if index_dir is None:
        client, name = chromadb.EphemeralClient(), f"chunks-{uuid.uuid4().hex}"
    else:
        client, name = chromadb.PersistentClient(path=str(index_dir)), "chunks"
        existing = next((c for c in client.list_collections() if c.name == name), None)
        if existing is not None:
            if (existing.metadata or {}).get("fingerprint") == fingerprint:
                return client.get_collection(name)
            client.delete_collection(name)
    collection = client.create_collection(name=name, configuration=config, metadata={"fingerprint": fingerprint})
    if chunks:
        collection.add(ids=[c.id for c in chunks], documents=[c.text for c in chunks])
    return collection


def _dense_ids(collection, count: int, query: str, pool: int, max_distance: float) -> list[str]:
    if not count:
        return []
    result = collection.query(query_texts=[query], n_results=min(pool, count))
    return [i for i, d in zip(result["ids"][0], result["distances"][0]) if d <= max_distance]


class DenseRetriever:
    """Vector-only retriever (Chroma). Implements dar.domain.ports.Retriever; used to compare against hybrid."""

    def __init__(self, chunks: list[Chunk], max_distance: float = 0.68, pool: int = 10,
                 index_dir: Path | None = None) -> None:
        self._by_id = {c.id: c for c in chunks}
        self._max_distance, self._pool = max_distance, pool
        self._collection = _open_collection(chunks, index_dir)

    def search(self, query: str, k: int = 5) -> list[Chunk]:
        ids = _dense_ids(self._collection, len(self._by_id), query, self._pool, self._max_distance)
        return [self._by_id[i] for i in ids[:k]]


class HybridRetriever:
    """BM25 keywords + Chroma vectors merged with Reciprocal Rank Fusion.

    A chunk is returned only if it is semantically close (cosine distance <= max_distance) or
    contains most of the query's words (min_coverage). Both floors are interim values measured on
    the real DarGlobal data (on-topic best distance 0.22-0.62, off-topic 0.71-0.86) and are
    calibrated on the golden set in ticket 18.
    """

    def __init__(self, chunks: list[Chunk], max_distance: float = 0.68, min_coverage: float = 0.75,
                 pool: int = 10, index_dir: Path | None = None) -> None:
        self._min_coverage = min_coverage
        self._by_id = {c.id: c for c in chunks}
        self._bm25 = Bm25Retriever(chunks)
        self._max_distance = max_distance
        self._pool = pool
        self._collection = _open_collection(chunks, index_dir)

    def search(self, query: str, k: int = 5) -> list[Chunk]:
        scores: dict[str, float] = {}
        for rank, chunk in enumerate(self._bm25.search(query, k=self._pool, min_coverage=self._min_coverage)):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (RRF_K + rank)
        dense = _dense_ids(self._collection, len(self._by_id), query, self._pool, self._max_distance)
        for rank, chunk_id in enumerate(dense):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        best_first = sorted(scores, key=lambda cid: scores[cid], reverse=True)
        return [self._by_id[cid] for cid in best_first[:k]]
