"""Embedding generation utilities for chunk JSON files."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate normalized embeddings from chunk payloads."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device=device)

    def generate(
        self,
        chunks_json_path: Path,
        embeddings_output_path: Path,
    ) -> Dict[str, object]:
        chunks_json_path = Path(chunks_json_path)
        embeddings_output_path = Path(embeddings_output_path)

        if not chunks_json_path.exists():
            raise FileNotFoundError(f"Chunk JSON not found: {chunks_json_path}")

        chunks: List[Dict[str, object]] = json.loads(chunks_json_path.read_text(encoding="utf-8"))
        if not chunks:
            raise ValueError(f"No chunks found in {chunks_json_path}")

        logger.info("Embedding input chunk count: %d", len(chunks))
        texts = [str(item["text"]) for item in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        records: List[Dict[str, object]] = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = {
                "source": chunk.get("source", "ncert"),
                "file_name": chunk.get("file_name", ""),
                "paragraph_number": int(chunk.get("paragraph_number", 0)),
            }
            records.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "metadata": metadata,
                    "embedding": embedding.tolist(),
                }
            )

        payload = {
            "pipeline_phase": "embedding_generation",
            "model": {
                "name": self.model_name,
                "embedding_dimension": int(self.model.get_sentence_embedding_dimension()),
                "device": self.device,
                "normalized": True,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "record_count": len(records),
            "records": records,
        }

        if payload["record_count"] <= 0:
            raise ValueError("Embedding generation produced zero records")

        embeddings_output_path.parent.mkdir(parents=True, exist_ok=True)
        embeddings_output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved %d embedding records to %s", len(records), embeddings_output_path)
        return payload
