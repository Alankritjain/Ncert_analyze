"""PYQ-to-NCERT retrieval engine with cross-encoder reranking and debug diagnostics."""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from src.pipeline.chroma_db import ChromaIndexer

logger = logging.getLogger(__name__)


@dataclass
class RankedChunk:
    """Internal ranked NCERT candidate for selected PYQ."""

    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    vector: List[float]
    vector_score: float
    rerank_score: float
    keyword_score: float = 0.0
    hybrid_score: float = 0.0


class IntelligentQueryEngine:
    """Retrieve NCERT paragraphs that best explain a selected CBSE PYQ."""

    def __init__(
        self,
        chroma_dir: Path,
        collection_name: str = "ncert_chemistry",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        chunks_path: Path = Path("output/chunks/all_chunks.json"),
        device: str = "cpu",
    ) -> None:
        self.embedder = SentenceTransformer(embedding_model, device=device)
        self.reranker = CrossEncoder(reranker_model, device=device)
        self.indexer = ChromaIndexer(persist_dir=chroma_dir, collection_name=collection_name)
        self.chunks_path = Path(chunks_path)
        self.min_pyq_score = 0.05

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        arr1 = np.array(vec1, dtype=float)
        arr2 = np.array(vec2, dtype=float)
        denom = np.linalg.norm(arr1) * np.linalg.norm(arr2)
        if math.isclose(float(denom), 0.0):
            return 0.0
        return float(np.dot(arr1, arr2) / denom)

    @staticmethod
    def _token_set(text: str) -> set[str]:
        return {tok for tok in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(tok) > 2}

    @staticmethod
    def _minmax_normalize(values: List[float]) -> List[float]:
        if not values:
            return []
        minimum = min(values)
        maximum = max(values)
        if math.isclose(minimum, maximum):
            return [1.0 for _ in values]
        return [(v - minimum) / (maximum - minimum) for v in values]

    def _mcq_keyword_set(self, text: str) -> set[str]:
        stop = {
            "which", "what", "when", "where", "how", "why", "none", "both",
            "following", "correct", "incorrect", "statement", "statements", "option",
            "choose", "mark", "true", "false", "most", "least", "among", "from",
            "with", "that", "this", "these", "those", "there", "their", "each",
        }
        return {tok for tok in self._token_set(text) if tok not in stop}

    def _prepare_query_text(self, text: str) -> str:
        """Normalize MCQ text so retrieval focuses on the stem and key option concepts."""
        cleaned = " ".join((text or "").replace("\r", " ").replace("\n", " ").split())
        if not cleaned:
            return ""

        cleaned = re.sub(r"^\s*(?:Q(?:uestion)?\s*)?\d+\s*[:.)-]\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Split likely option pattern: A) ... B) ... C) ... D) ...
        option_chunks = re.split(r"\s+[A-D][\).:]\s+", cleaned)
        if len(option_chunks) <= 1:
            return cleaned

        stem = option_chunks[0].strip()
        options_text = " ".join(option_chunks[1:])
        option_terms = sorted(self._mcq_keyword_set(options_text), key=lambda t: (-len(t), t))
        option_hint = " ".join(option_terms[:12])

        if option_hint:
            return f"{stem}. option concepts: {option_hint}"
        return stem

    def _adds_new_information(self, first_text: str, second_text: str) -> bool:
        tokens_a = self._token_set(first_text)
        tokens_b = self._token_set(second_text)
        if not tokens_a or not tokens_b:
            return True
        overlap = len(tokens_a.intersection(tokens_b)) / max(1, len(tokens_a.union(tokens_b)))
        return overlap < 0.65

    def _covers_additional_query_concept(self, query: str, first_text: str, second_text: str) -> bool:
        stop = {
            "what",
            "which",
            "when",
            "where",
            "how",
            "why",
            "define",
            "explain",
            "state",
            "write",
            "about",
            "from",
            "with",
            "that",
            "this",
            "for",
            "into",
            "their",
            "there",
        }
        query_terms = {t for t in self._token_set(query) if t not in stop}
        if not query_terms:
            return True

        first_terms = self._token_set(first_text)
        second_terms = self._token_set(second_text)

        covered_by_first = query_terms.intersection(first_terms)
        covered_by_second = query_terms.intersection(second_terms)
        additional = covered_by_second - covered_by_first
        return len(additional) > 0

    def get_pyq_list(self, limit: int = 250) -> List[Dict[str, str]]:
        if not self.chunks_path.exists():
            return []

        rows = json.loads(self.chunks_path.read_text(encoding="utf-8"))
        pyqs = [row for row in rows if str(row.get("source", "")).lower() == "pyq"]

        result: List[Dict[str, str]] = []
        for row in pyqs[:limit]:
            result.append(
                {
                    "pyq_id": str(row.get("chunk_id", "")),
                    "text": str(row.get("text", "")),
                    "file_name": str(row.get("file_name", "")),
                    "paragraph_number": str(row.get("paragraph_number", "")),
                }
            )
        return result

    def _get_pyq_by_id(self, pyq_id: str) -> Dict[str, str]:
        for item in self.get_pyq_list(limit=10000):
            if item["pyq_id"] == pyq_id:
                return item
        raise ValueError(f"PYQ id not found: {pyq_id}")

    def _to_ranked_chunks(self, raw_results: Dict[str, Any], query_text: str) -> List[RankedChunk]:
        ids = raw_results.get("ids", [[]])[0]
        docs = raw_results.get("documents", [[]])[0]
        metas = raw_results.get("metadatas", [[]])[0]
        dists = raw_results.get("distances", [[]])[0]
        embs = raw_results.get("embeddings", [[]])[0]

        if not ids:
            return []

        rerank_scores = self.reranker.predict([[query_text, doc] for doc in docs])
        query_terms = self._mcq_keyword_set(query_text)

        vector_scores: List[float] = []
        rerank_scores_list: List[float] = []
        keyword_scores: List[float] = []

        for idx in range(len(ids)):
            vector_scores.append(1 - float(dists[idx]) if idx < len(dists) else 0.0)
            rerank_scores_list.append(float(rerank_scores[idx]))
            doc_terms = self._mcq_keyword_set(docs[idx])
            if query_terms and doc_terms:
                overlap = len(query_terms.intersection(doc_terms)) / max(1, len(query_terms))
            else:
                overlap = 0.0
            keyword_scores.append(float(overlap))

        rerank_norm = self._minmax_normalize(rerank_scores_list)
        vector_norm = self._minmax_normalize(vector_scores)

        ranked: List[RankedChunk] = []
        for idx, chunk_id in enumerate(ids):
            hybrid_score = (0.65 * rerank_norm[idx]) + (0.25 * vector_norm[idx]) + (0.10 * keyword_scores[idx])
            ranked.append(
                RankedChunk(
                    chunk_id=chunk_id,
                    text=docs[idx],
                    metadata=metas[idx] if idx < len(metas) else {},
                    vector=embs[idx] if idx < len(embs) else [],
                    vector_score=vector_scores[idx],
                    rerank_score=rerank_scores_list[idx],
                    keyword_score=keyword_scores[idx],
                    hybrid_score=float(hybrid_score),
                )
            )

        ranked.sort(key=lambda row: row.hybrid_score, reverse=True)
        return ranked

    def query_from_pyq(self, pyq_id: Optional[str] = None, pyq_text: Optional[str] = None, top_k: int = 10) -> Dict[str, Any]:
        if pyq_id:
            selected_pyq = self._get_pyq_by_id(pyq_id)
            query_text = selected_pyq["text"].strip()
        else:
            if not pyq_text or not pyq_text.strip():
                raise ValueError("Either pyq_id or pyq_text must be provided")
            query_text = pyq_text.strip()
            selected_pyq = {
                "pyq_id": "ad_hoc_pyq",
                "text": query_text,
                "file_name": "manual_input",
                "paragraph_number": "",
            }

        query_text = self._prepare_query_text(query_text)

        query_embedding = self.embedder.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()

        raw_results = self.indexer.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata={"source": "ncert"},
        )
        ranked = self._to_ranked_chunks(raw_results=raw_results, query_text=query_text)

        if not ranked:
            return {
                "selected_pyq": selected_pyq,
                "best_matching_ncert_paragraph": None,
                "second_supporting_paragraph": None,
                "debug": {
                    "top_cross_encoder_scores": [],
                    "second_paragraph_status": "discarded_no_candidates",
                    "retrieved_files": [],
                },
            }

        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else None

        second_status = "not_available"
        second_payload = None

        if second is not None:
            if second.hybrid_score < 0.75 * best.hybrid_score:
                second_status = "discarded_score_ratio"
            elif not self._adds_new_information(best.text, second.text):
                second_status = "discarded_redundant_content"
            elif len(best.vector) > 0 and len(second.vector) > 0 and self._cosine_similarity(best.vector, second.vector) > 0.85:
                second_status = "discarded_redundancy_similarity"
            elif not self._covers_additional_query_concept(query_text, best.text, second.text):
                second_status = "discarded_no_additional_concept"
            else:
                second_status = "selected"
                second_payload = {
                    "chunk_id": second.chunk_id,
                    "text": second.text,
                    "score": second.hybrid_score,
                    "metadata": second.metadata,
                }

        response = {
            "selected_pyq": selected_pyq,
            "best_matching_ncert_paragraph": {
                "chunk_id": best.chunk_id,
                "text": best.text,
                "score": best.hybrid_score,
                "metadata": best.metadata,
            },
            "second_supporting_paragraph": second_payload,
            "debug": {
                "top_cross_encoder_scores": [
                    {
                        "chunk_id": row.chunk_id,
                        "score": row.hybrid_score,
                        "cross_score": row.rerank_score,
                        "keyword_score": row.keyword_score,
                        "vector_score": row.vector_score,
                        "file_name": str(row.metadata.get("file_name", "")),
                        "paragraph_number": row.metadata.get("paragraph_number", ""),
                    }
                    for row in ranked[:5]
                ],
                "second_paragraph_status": second_status,
                "retrieved_files": sorted({str(row.metadata.get("file_name", "")) for row in ranked[:5]}),
            },
        }
        return response
