from __future__ import annotations

import random
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


RANDOM_STATE = 42
MIN_PARAGRAPH_CHARS = 100
VALID_DOMAINS = {"claude", "hackerrank", "visa"}


class Retriever:
    def __init__(self, data_root: Path | str | None = None) -> None:
        random.seed(RANDOM_STATE)

        self.data_root = Path(data_root) if data_root is not None else Path(__file__).resolve().parents[1] / "data"
        self.chunks: list[dict[str, str]] = self._load_chunks()

        self._vectorizer = TfidfVectorizer()
        texts = [chunk["text"] for chunk in self.chunks]
        self._matrix = self._vectorizer.fit_transform(texts) if texts else None

    def _infer_domain(self, file_path: Path) -> str | None:
        parts = [part.lower() for part in file_path.parts]
        for domain in VALID_DOMAINS:
            if domain in parts:
                return domain
        return None

    def _chunk_text(self, text: str) -> list[str]:
        paragraphs = re.split(r"\n\s*\n+", text)
        return [p.strip() for p in paragraphs if len(p.strip()) >= MIN_PARAGRAPH_CHARS]

    def _load_chunks(self) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        for md_path in sorted(self.data_root.rglob("*.md")):
            domain = self._infer_domain(md_path)
            if domain is None:
                continue

            text = md_path.read_text(encoding="utf-8", errors="ignore")
            for paragraph in self._chunk_text(text):
                chunks.append(
                    {
                        "text": paragraph,
                        "source_file": str(md_path),
                        "domain": domain,
                    }
                )
        return chunks

    def retrieve(self, query: str, domain: str | None, top_k: int = 8) -> list[dict[str, str | float]]:
        if not query or self._matrix is None:
            return []

        indices = list(range(len(self.chunks)))
        if domain is not None:
            normalized_domain = domain.lower().strip()
            indices = [i for i, chunk in enumerate(self.chunks) if chunk["domain"] == normalized_domain]

        if not indices:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix[indices]).ravel()

        # Map global index -> score for easy lookup
        score_by_index = {idx: float(score) for idx, score in zip(indices, scores)}

        ranked_pairs = sorted(zip(indices, scores), key=lambda pair: pair[1], reverse=True)

        results: list[dict[str, str | float]] = []

        # Special boost: for Claude troubleshooting queries, prepend troubleshooting chunks
        query_lower = query.lower()
        boosted_indices: list[int] = []
        try:
            if domain is not None and domain.lower().strip() == 'claude':
                trigger_phrases = ['stopped working', 'not working', 'all requests failing']
                if any(phrase in query_lower for phrase in trigger_phrases):
                    # Find chunks coming from the troubleshooting folder for Claude
                    for i, chunk in enumerate(self.chunks):
                        path_norm = chunk['source_file'].replace('\\', '/').lower()
                        if '/data/claude/claude/troubleshooting/' in path_norm or 'data/claude/claude/troubleshooting/' in path_norm:
                            if i in score_by_index:
                                boosted_indices.append(i)
                    # Sort boosted indices by score desc
                    boosted_indices = sorted(boosted_indices, key=lambda idx: score_by_index.get(idx, 0.0), reverse=True)
        except Exception:
            boosted_indices = []

        seen_sources = set()

        # Add boosted results first (if any)
        for idx in boosted_indices:
            chunk = self.chunks[idx]
            src = chunk['source_file']
            if src in seen_sources:
                continue
            seen_sources.add(src)
            results.append({
                'text': chunk['text'],
                'source_file': src,
                'score': float(score_by_index.get(idx, 0.0)),
            })

        # Then add the rest of ranked pairs (skipping any already added)
        for idx, score in ranked_pairs:
            chunk = self.chunks[idx]
            src = chunk['source_file']
            if src in seen_sources:
                continue
            seen_sources.add(src)
            results.append({
                'text': chunk['text'],
                'source_file': src,
                'score': float(score),
            })

        # Return top_k results after boosting
        return results[:top_k]
