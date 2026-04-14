"""PDF to text extraction utilities for NCERT and PYQ documents."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List

import fitz

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Extract cleaned text from PDF files and persist text artifacts."""

    def __init__(self, media_dir: Path, raw_text_dir: Path) -> None:
        self.media_dir = Path(media_dir)
        self.raw_text_dir = Path(raw_text_dir)
        self.raw_text_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _clean_page_text(text: str) -> str:
        text = text.replace("\u00a0", " ")
        text = re.sub(r"[ \t]+", " ", text)

        lines = [line.strip() for line in text.splitlines()]
        merged: List[str] = []

        for line in lines:
            if not line:
                merged.append("")
                continue

            if merged and merged[-1] and not merged[-1].endswith((".", "?", "!", ":", ";")):
                merged[-1] = f"{merged[-1]} {line}".strip()
            else:
                merged.append(line)

        cleaned = "\n".join(merged)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @staticmethod
    def _dedupe_adjacent_words(text: str) -> str:
        # Collapse repeated adjacent tokens, e.g., "electrolysis electrolysis".
        return re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)

    @staticmethod
    def _remove_repeated_page_markers(page_texts: List[str]) -> List[str]:
        line_counts: Dict[str, int] = {}

        for page in page_texts:
            lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
            candidates = lines[:2] + lines[-2:]
            for line in candidates:
                if len(line) <= 90:
                    key = line.lower()
                    line_counts[key] = line_counts.get(key, 0) + 1

        repeated = {line for line, count in line_counts.items() if count >= 3}
        if not repeated:
            return page_texts

        cleaned_pages: List[str] = []
        for page in page_texts:
            filtered = [
                ln
                for ln in page.splitlines()
                if not ln.strip() or ln.strip().lower() not in repeated
            ]
            cleaned_pages.append("\n".join(filtered))

        return cleaned_pages

    @staticmethod
    def _source_from_path(pdf_path: Path) -> str:
        lower_parts = {part.lower() for part in pdf_path.parts}
        if "pyqs" in lower_parts or "pyq_chem" in lower_parts:
            return "pyq"
        return "ncert"

    def _txt_output_path(self, pdf_path: Path) -> Path:
        source = self._source_from_path(pdf_path)
        stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", pdf_path.stem)
        if source == "pyq":
            return self.raw_text_dir / "pyqs" / f"{stem}.txt"
        return self.raw_text_dir / f"{stem}.txt"

    def extract_all(self) -> List[Dict[str, str]]:
        if not self.media_dir.exists():
            raise FileNotFoundError(f"Media directory not found: {self.media_dir}")

        manifest: List[Dict[str, str]] = []
        pdf_files = sorted(self.media_dir.rglob("*.pdf"))

        logger.info("Found %d PDF files under %s", len(pdf_files), self.media_dir)

        for pdf_file in pdf_files:
            source = self._source_from_path(pdf_file)
            output_path = self._txt_output_path(pdf_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with fitz.open(pdf_file) as doc:
                    pages = [self._clean_page_text(page.get_text("text")) for page in doc]
                pages = self._remove_repeated_page_markers(pages)
                pages = [self._dedupe_adjacent_words(page) for page in pages]
                full_text = "\n\n".join(part for part in pages if part).strip()
                output_path.write_text(full_text, encoding="utf-8")
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to extract text from %s: %s", pdf_file, exc)
                continue

            manifest.append(
                {
                    "file": pdf_file.name,
                    "type": source,
                    "source": source,
                    "pdf_file": str(pdf_file),
                    "text_file": str(output_path),
                    "file_name": pdf_file.name,
                }
            )
            logger.info("Extracted %s -> %s", pdf_file.name, output_path)

        manifest_path = self.raw_text_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved extraction manifest with %d records: %s", len(manifest), manifest_path)
        return manifest
