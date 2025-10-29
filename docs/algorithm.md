# Decision Algorithm & Scoring

This document contains the details of the scoring formula used to compare the browser-captured Readability extraction (A) vs the agent-side trafilatura extraction (B).

## Scoring signals
- length (normalized)
- content density (text/HTML)
- semantic overlap (similarity between A and B)
- structure richness (headings, lists, tables)
- freshness (date metadata)
- link quality (internal/external ratio)

## Weighted formula

score = 0.35*len + 0.20*density + 0.20*overlap + 0.10*structure + 0.10*freshness + 0.05*links - penalty(blockers)

Tie-breaking rule: if |score_A - score_B| < 0.05 prefer the browser-captured Readability result (A).

## Blocker penalties and thresholds
- If trafilatura extracts < 500 characters, an optional Playwright probe runs to detect login walls, paywalls, or CAPTCHAs. If blockers are detected, prefer A and add diagnostics.

--
*Moved from README: scoring formula and decision rules.*

## Decision algorithm (detailed)

When no redirect is detected, the agent computes a weighted score for each candidate (A = Readability, B = trafilatura) using the signals listed above. The formula is:

```
score = (
	0.35 * normalized_length +
	0.20 * content_density +
	0.20 * semantic_overlap +
	0.10 * structure_richness +
	0.10 * date_freshness +
	0.05 * link_quality
) - blocker_penalty
```

Rules:
- If |score_A - score_B| < 0.05 → prefer the browser-captured Readability (A).
- If both are long but differ greatly, prefer the browser capture and warn in diagnostics.

Blocker detection:
- If trafilatura extracts fewer than 500 characters, the agent may run a headless Playwright probe (30s cap) to detect login walls, paywalls or captchas. If blockers are found, prefer A.

