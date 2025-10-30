"""Tests for ComparatorTool."""

import pytest
from src.tools.comparator import ComparatorTool


@pytest.fixture
def comparator():
    """Create a ComparatorTool instance."""
    return ComparatorTool()


def test_compute_signals_basic(comparator):
    """Test basic signal computation."""
    text = "This is a sample article with some content. " * 20
    html = "<h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p><ul><li>Item</li></ul>"
    
    signals = comparator.compute_signals(text, html, "Sample Title")
    
    assert "len_text" in signals
    assert "density" in signals
    assert "structure" in signals
    assert signals["len_text"] > 0
    assert 0 <= signals["density"] <= 1.0


def test_semantic_overlap_identical(comparator):
    """Test semantic overlap with identical texts."""
    text = "The quick brown fox jumps over the lazy dog"
    overlap = comparator.semantic_overlap(text, text)
    
    assert overlap == 1.0


def test_semantic_overlap_different(comparator):
    """Test semantic overlap with completely different texts."""
    text_a = "Python programming language is great for data science"
    text_b = "The weather today is sunny and warm"
    
    overlap = comparator.semantic_overlap(text_a, text_b)
    
    assert overlap < 0.5


def test_semantic_overlap_similar(comparator):
    """Test semantic overlap with similar texts."""
    text_a = "Machine learning is a subset of artificial intelligence that enables computers to learn"
    text_b = "Machine learning enables computers to learn and is part of artificial intelligence"
    
    overlap = comparator.semantic_overlap(text_a, text_b)
    
    assert overlap > 0.3


def test_score_candidate_basic(comparator):
    """Test candidate scoring."""
    signals = {
        "len_norm": 0.8,
        "density": 0.6,
        "structure": 25,
        "freshness": 1.0,
        "link_quality": 0.7
    }
    
    score = comparator.score_candidate(signals, blocker_penalty=0.0)
    
    assert 0 <= score <= 1.0
    assert score > 0.5  # Should be reasonable score


def test_score_candidate_with_penalty(comparator):
    """Test candidate scoring with blocker penalty."""
    signals = {
        "len_norm": 0.8,
        "density": 0.6,
        "structure": 25,
        "freshness": 1.0,
        "link_quality": 0.7
    }
    
    score_no_penalty = comparator.score_candidate(signals, blocker_penalty=0.0)
    score_with_penalty = comparator.score_candidate(signals, blocker_penalty=0.3)
    
    assert score_with_penalty < score_no_penalty
    assert score_with_penalty >= 0  # Should not go negative


def test_compare_and_decide_prefer_readability_on_tie(comparator):
    """Test that readability is preferred when scores are tied."""
    text = "Sample article content " * 50
    html = "<article>" + "<p>Sample paragraph</p>" * 20 + "</article>"
    
    decision = comparator.compare_and_decide(
        extension_text=text,
        extension_html=html,
        trafilatura_text=text,  # Same content
        trafilatura_html=html,
        title="Test Article",
        blocker_flags={}
    )
    
    assert decision["chosen"] == "extension"
    assert "score_extension" in decision
    assert "score_trafilatura" in decision
    assert decision["score_diff"] < 0.05


def test_compare_and_decide_blocker_penalty(comparator):
    """Test that blocker flags penalize trafilatura."""
    readability_text = "Good article content " * 50
    trafilatura_text = "Good article content " * 50
    html = "<article>" + "<p>Paragraph</p>" * 20 + "</article>"
    
    blocker_flags = {
        "login_required": True,
        "paywall": False,
        "captcha": False
    }
    
    decision = comparator.compare_and_decide(
        extension_text=readability_text,
        extension_html=html,
        trafilatura_text=trafilatura_text,
        trafilatura_html=html,
        title="Test Article",
        blocker_flags=blocker_flags
    )
    
    # With blocker penalty, extension should be chosen
    assert decision["chosen"] == "extension"
    assert decision["blocker_penalty"] > 0


def test_compare_and_decide_better_content(comparator):
    """Test choosing candidate with objectively better content."""
    readability_text = "Short article"
    readability_html = "<p>Short</p>"
    
    trafilatura_text = "This is a much longer and more detailed article " * 100
    trafilatura_html = "<article>" + "<p>Detailed paragraph</p>" * 50 + "</article>"
    
    decision = comparator.compare_and_decide(
        extension_text=readability_text,
        extension_html=readability_html,
        trafilatura_text=trafilatura_text,
        trafilatura_html=trafilatura_html,
        title="Test Article",
        blocker_flags={}
    )
    
    # Trafilatura has much better content
    assert decision["chosen"] == "trafilatura"
    assert decision["score_trafilatura"] > decision["score_extension"]


def test_signals_structure_richness(comparator):
    """Test that structure richness is properly calculated."""
    html_rich = """
    <h1>Title</h1>
    <h2>Section 1</h2>
    <h3>Subsection</h3>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    <ol>
        <li>Step 1</li>
        <li>Step 2</li>
    </ol>
    """
    
    html_poor = "<p>Just plain text</p>"
    
    signals_rich = comparator.compute_signals("text content", html_rich, "Title")
    signals_poor = comparator.compute_signals("text content", html_poor, "Title")
    
    assert signals_rich["structure"] > signals_poor["structure"]
    assert signals_rich["headings"] > 0
    assert signals_rich["lists"] > 0
