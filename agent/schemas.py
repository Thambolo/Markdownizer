"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ============================================
# Extension → Agent Request Models
# ============================================


class IframeInfo(BaseModel):
    """Information about iframes in the page."""

    src: str
    same_origin: bool = Field(alias="sameOrigin")


class CaptureStats(BaseModel):
    """Statistics about captured content."""

    char_count: int
    headings: int
    lists: int


class CaptureMeta(BaseModel):
    """Metadata about the capture process."""

    captured_at: str
    stats: CaptureStats
    iframe_info: list[IframeInfo] = []


class IngestRequest(BaseModel):
    """Request payload from browser extension.
    
    The extension sends its best extraction using priority:
    Schema.org > Semantic HTML > Readability.js fallback.
    """

    url: HttpUrl
    title: str
    html_extension: str  # Best extraction HTML from extension
    text_extension: str  # Best extraction text from extension
    meta: CaptureMeta


# ============================================
# Agent Internal Models
# ============================================


class ContentSignals(BaseModel):
    """Computed signals for content comparison."""

    len_text: int
    density: float
    overlap: float
    structure: int
    freshness: int
    links: float


class CandidateScore(BaseModel):
    """Score and signals for a content candidate."""

    source: Literal["extension", "trafilatura"]
    score: float
    signals: ContentSignals


class BlockerFlags(BaseModel):
    """Flags indicating access blockers."""

    login_required: bool = False
    paywall: bool = False
    captcha: bool = False
    cross_origin_iframe: bool = False
    content_too_thin: bool = False
    csp_blocked: bool = False


# ============================================
# Agent → Extension Response Models
# ============================================


class DiagnosticSignals(BaseModel):
    """Detailed signals for diagnostics."""

    len: int
    density: float
    overlap: float


class Diagnostics(BaseModel):
    """Diagnostic information about the comparison."""

    score_extension: float
    score_trafilatura: float
    signals: dict[str, DiagnosticSignals]
    redirect_detected: bool = False
    original_url: str | None = None
    final_url: str | None = None


class SuccessResponse(BaseModel):
    """Success response with Markdown content."""

    ok: Literal[True] = True
    chosen: Literal["extension", "trafilatura"]
    title: str
    url: str
    markdown: str
    diagnostics: Diagnostics


class ErrorResponse(BaseModel):
    """Error response when conversion fails."""

    ok: Literal[False] = False
    code: Literal[
        "content-mismatch",  # URL redirected to different page
        "login-required",
        "paywall",
        "captcha",
        "cross-origin-iframe",
        "content-too-thin",
        "csp-blocked",
        "fetch-failed",
        "extraction-failed",
    ]
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["ok", "degraded", "error"]
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
