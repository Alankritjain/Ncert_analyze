"""ChromaDB indexing and retrieval helpers for semantic search."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaIndexer:
    """Index embeddings and run vector search against persistent ChromaDB."""

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str = "ncert_chemistry",
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_collection(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:  # pylint: disable=broad-except
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_embeddings(self, embeddings_json_path: Path, batch_size: int = 128) -> int:
        payload = json.loads(Path(embeddings_json_path).read_text(encoding="utf-8"))
        records: List[Dict[str, Any]] = payload.get("records", [])
        total = 0

        for idx in range(0, len(records), batch_size):
            batch = records[idx : idx + batch_size]
            ids = [row["chunk_id"] for row in batch]
            docs = [row["text"] for row in batch]
            embs = [row["embedding"] for row in batch]
            metas = [
                {
                    "source": str(row["metadata"].get("source", "ncert")),
                    "file_name": str(row["metadata"].get("file_name", "")),
                    "paragraph_number": int(row["metadata"].get("paragraph_number", 0)),
                }
                for row in batch
            ]
            self.collection.upsert(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
            total += len(batch)

        logger.info("Indexed %d records into collection '%s'", total, self.collection_name)
        logger.info("Collection '%s' total records now: %d", self.collection_name, self.collection.count())
        return total

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances", "embeddings"],
        )
