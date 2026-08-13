from app.seo.rules import SEORulesEngine
from app.seo.score import calculate_page_score


def test_missing_title_rule():
    page_data = {
        "title": "",
        "meta_description": "Valid Meta Description",
        "h1": "Valid H1",
        "canonical": "https://example.com",
        "missing_alt_count": 0,
        "word_count": 500,
        "status_code": 200
    }
    issues = SEORulesEngine.evaluate_page(page_data)
    issue_types = [i["issue_type"] for i in issues]
    assert "Missing Title" in issue_types


def test_title_too_long_rule():
    page_data = {
        "title": "A" * 70,
        "meta_description": "Valid Meta Description",
        "h1": "Valid H1",
        "canonical": "https://example.com",
        "missing_alt_count": 0,
        "word_count": 500,
        "status_code": 200
    }
    issues = SEORulesEngine.evaluate_page(page_data)
    issue_types = [i["issue_type"] for i in issues]
    assert "Title Too Long" in issue_types


def test_perfect_page_score():
    page_data = {
        "title": "Optimal SEO Service & Pricing Guide Title Tag",
        "meta_description": "Optimal meta description providing valuable service pricing insights and features.",
        "h1": "Main H1 Heading",
        "canonical": "https://example.com/page",
        "missing_alt_count": 0,
        "word_count": 500,
        "status_code": 200
    }
    issues = SEORulesEngine.evaluate_page(page_data)
    score = calculate_page_score(issues)
    assert len(issues) == 0
    assert score == 100
