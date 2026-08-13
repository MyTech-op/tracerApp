from typing import List, Dict, Any


def calculate_page_score(issues: List[Dict[str, Any]]) -> int:
    """
    Deducts points from baseline score 100 based on severity of detected issues:
    - Critical issue: -15 pts
    - Warning issue: -8 pts
    - Info issue: -3 pts
    Score is bounded between 0 and 100.
    """
    score = 100
    for issue in issues:
        severity = issue.get("severity", "warning")
        if severity == "critical":
            score -= 15
        elif severity == "warning":
            score -= 8
        elif severity == "info":
            score -= 3
    return max(0, min(100, score))
