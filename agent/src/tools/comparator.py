"""Content comparison and scoring tool."""

from __future__ import annotations

import re
from typing import Any


class ComparatorTool:
    """Tool for comparing and scoring content candidates."""

    def __init__(self):
        """Initialize the comparator."""
        self._max_len = 50000  # Normalization cap

    def compute_signals(
        self, text: str, html: str, title: str = ""
    ) -> dict[str, float | int]:
        """
        Compute comparison signals for a content candidate.

        Args:
            text: Plain text content
            html: HTML content
            title: Page title for context

        Returns:
            Dictionary of computed signals
        """
        # Length signal (normalized)
        len_text = min(len(text), self._max_len)
        len_norm = len_text / self._max_len

        # Word count
        words = text.split()
        word_count = len(words)

        # Density: words per semantic block
        # Count headings, paragraphs, list items as blocks
        headings = len(re.findall(r"<h[1-6]", html, re.IGNORECASE))
        paragraphs = len(re.findall(r"<p>", html, re.IGNORECASE))
        lists = len(re.findall(r"<li>", html, re.IGNORECASE))
        blocks = max(headings + paragraphs + lists, 1)
        density = word_count / blocks

        # Structure richness
        structure_score = min(headings * 2 + lists, 50)

        # Link quality
        links = re.findall(r'href="([^"]+)"', html)
        absolute_links = sum(1 for link in links if link.startswith("http"))
        link_quality = absolute_links / max(len(links), 1) if links else 0

        # Freshness (look for date indicators)
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",
            r"\d{1,2}/\d{1,2}/\d{4}",
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",
        ]
        has_date = any(re.search(pattern, text[:500]) for pattern in date_patterns)
        freshness = 1.0 if has_date else 0.0

        return {
            "len_text": len_text,
            "len_norm": len_norm,
            "word_count": word_count,
            "density": min(density / 100, 1.0),  # Normalize to 0-1
            "structure": structure_score,
            "link_quality": link_quality,
            "freshness": freshness,
            "headings": headings,
            "lists": lists,
        }

    def semantic_overlap(self, text_a: str, text_b: str) -> float:
        """
        Compute semantic overlap using Jaccard similarity on word trigrams.

        Args:
            text_a: First text
            text_b: Second text

        Returns:
            Overlap score between 0 and 1
        """
        def get_trigrams(text: str) -> set[str]:
            """Extract word trigrams from text."""
            words = text.lower().split()
            trigrams = set()
            for i in range(len(words) - 2):
                trigrams.add(" ".join(words[i : i + 3]))
            return trigrams

        trigrams_a = get_trigrams(text_a)
        trigrams_b = get_trigrams(text_b)

        if not trigrams_a or not trigrams_b:
            return 0.0

        intersection = len(trigrams_a & trigrams_b)
        union = len(trigrams_a | trigrams_b)

        return intersection / union if union > 0 else 0.0

    def score_candidate(
        self, signals: dict[str, float | int], blocker_penalty: float = 0.0
    ) -> float:
        """
        Calculate weighted score for a candidate.

        Args:
            signals: Computed signals dictionary
            blocker_penalty: Penalty for detected blockers (0.0-1.0)

        Returns:
            Final score (0.0-1.0)
        """
        score = (
            0.35 * signals["len_norm"]
            + 0.20 * signals["density"]
            + 0.10 * min(signals["structure"] / 50, 1.0)
            + 0.10 * signals["freshness"]
            + 0.05 * signals["link_quality"]
        )

        # Apply blocker penalty
        score = max(score - blocker_penalty, 0.0)

        return min(score, 1.0)

    def compare_and_decide(
        self,
        readability_text: str,
        readability_html: str,
        trafilatura_text: str,
        trafilatura_html: str,
        title: str,
        blocker_flags: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """
        Compare two candidates and decide which is better.

        Args:
            readability_text: Text from extension's Readability
            readability_html: HTML from extension's Readability
            trafilatura_text: Text from agent's trafilatura
            trafilatura_html: HTML from agent's trafilatura
            title: Page title
            blocker_flags: Optional blocker flags for penalties

        Returns:
            Decision dictionary with chosen source and diagnostics
        """
        blocker_flags = blocker_flags or {}

        # Compute signals for both
        signals_r = self.compute_signals(readability_text, readability_html, title)
        signals_t = self.compute_signals(trafilatura_text, trafilatura_html, title)

        # Compute semantic overlap
        overlap = self.semantic_overlap(readability_text, trafilatura_text)

        # Add overlap to signals
        signals_r["overlap"] = overlap
        signals_t["overlap"] = overlap

        # Calculate blocker penalty for trafilatura
        blocker_penalty = 0.0
        if any(blocker_flags.values()):
            blocker_penalty = 0.3  # 30% penalty for blockers

        # Score both candidates
        score_r = self.score_candidate(signals_r, blocker_penalty=0.0)
        score_t = self.score_candidate(signals_t, blocker_penalty=blocker_penalty)

        # Decide: if difference < 5%, prefer Readability (user-visible)
        score_diff = abs(score_r - score_t)
        if score_diff < 0.05:
            chosen = "readability"
        else:
            chosen = "readability" if score_r > score_t else "trafilatura"

        return {
            "chosen": chosen,
            "score_readability": round(score_r, 3),
            "score_trafilatura": round(score_t, 3),
            "score_diff": round(score_diff, 3),
            "overlap": round(overlap, 3),
            "signals_readability": {
                "len": signals_r["len_text"],
                "density": round(signals_r["density"], 3),
                "overlap": round(overlap, 3),
            },
            "signals_trafilatura": {
                "len": signals_t["len_text"],
                "density": round(signals_t["density"], 3),
                "overlap": round(overlap, 3),
            },
            "blocker_penalty": blocker_penalty,
        }
