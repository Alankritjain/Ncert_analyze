"""Text to chunk conversion for NCERT and PYQ text files."""

from __future__ import annotations

import json
import logging
import re
import hashlib
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class TextChunkBuilder:
    """Build paragraph-level chunks with exam-friendly metadata."""

    def __init__(self, raw_text_dir: Path, chunk_output_dir: Path) -> None:
        self.raw_text_dir = Path(raw_text_dir)
        self.chunk_output_dir = Path(chunk_output_dir)
        self.chunk_output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        paragraphs = [para.strip() for para in re.split(r"\n\s*\n", text) if para.strip()]
        clean_paragraphs: List[str] = []

        for para in paragraphs:
            para = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", para, flags=re.IGNORECASE)
            para = re.sub(r"\s+", " ", para).strip()
            # Heuristic split for oversized blocks when source has weak paragraph breaks.
            if len(para) > 1200:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                buffer = ""
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    candidate = f"{buffer} {sentence}".strip()
                    if len(candidate) > 700 and buffer:
                        clean_paragraphs.append(buffer)
                        buffer = sentence
                    else:
                        buffer = candidate
                if buffer:
                    clean_paragraphs.append(buffer)
            else:
                clean_paragraphs.append(para)

        return clean_paragraphs

    @staticmethod
    def _is_low_quality(text: str) -> bool:
        if not text or len(text) < 40:
            return True

        alpha_count = sum(ch.isalpha() for ch in text)
        alpha_ratio = alpha_count / max(1, len(text))
        if alpha_ratio < 0.45:
            return True

        tokens = [tok.lower() for tok in re.findall(r"[a-zA-Z0-9]+", text)]
        if len(tokens) < 8:
            return True

        unique_ratio = len(set(tokens)) / max(1, len(tokens))
        if unique_ratio < 0.3:
            return True

        token_freq: Dict[str, int] = {}
        for tok in tokens:
            token_freq[tok] = token_freq.get(tok, 0) + 1
        max_repeat = max(token_freq.values())
        if max_repeat / max(1, len(tokens)) > 0.2:
            return True

        return False

    @staticmethod
    def _chunk_id(source: str, file_name: str, file_key: str, paragraph_number: int) -> str:
        stem = Path(file_name).stem.lower()
        stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
        short_hash = hashlib.md5(file_key.encode("utf-8")).hexdigest()[:8]
        return f"{source}_{stem}_{short_hash}_p{paragraph_number:03d}"

    def build_chunks(self) -> List[Dict[str, object]]:
        manifest_path = self.raw_text_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found at {manifest_path}. Run scripts/pdf_to_text.py first."
            )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_map = {
            Path(str(entry.get("text_file", ""))).name.lower(): str(entry.get("type") or entry.get("source") or "ncert")
            for entry in manifest
            if entry.get("text_file")
        }

        text_files = sorted(self.raw_text_dir.rglob("*.txt"))
        logger.info("Found %d text files in %s", len(text_files), self.raw_text_dir)
        all_chunks: List[Dict[str, object]] = []

        for text_file in text_files:
            if not text_file.exists():
                logger.warning("Skipping missing text file: %s", text_file)
                continue

            raw_text = text_file.read_text(encoding="utf-8")
            paragraphs = self._split_paragraphs(raw_text)

            file_name = f"{text_file.stem}.pdf"
            source = source_map.get(text_file.name.lower(), "ncert")
            file_key = str(text_file.relative_to(self.raw_text_dir)).lower()

            file_chunks: List[Dict[str, object]] = []
            for idx, paragraph in enumerate(paragraphs, start=1):
                if not paragraph.strip():
                    continue
                if self._is_low_quality(paragraph):
                    continue
                file_chunks.append(
                    {
                        "chunk_id": self._chunk_id(source, file_name, file_key, idx),
                        "text": paragraph,
                        "source": source,
                        "file_name": file_name,
                        "paragraph_number": idx,
                    }
                )

            output_file = self.chunk_output_dir / f"{text_file.stem}_chunks.json"
            output_file.write_text(json.dumps(file_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info("Saved %d chunks to %s", len(file_chunks), output_file)

            all_chunks.extend(file_chunks)

        aggregate = self.chunk_output_dir / "all_chunks.json"
        aggregate.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved combined chunk file with %d chunks: %s", len(all_chunks), aggregate)
        return all_chunks
