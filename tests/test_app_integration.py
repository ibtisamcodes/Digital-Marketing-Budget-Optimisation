"""
Test Suite for Master Application Integration.
Verifies clean imports, page registry integrity, and callable page renderers for all 13 pages.
"""

import pytest

def test_app_imports_and_page_registry():
    import app
    assert hasattr(app, 'PAGES')
    assert len(app.PAGES) == 13, f"Expected 13 pages, found {len(app.PAGES)}"
    
    expected_pages = [
        "1. Executive Overview",
        "2. YouTube Comment Analytics",
        "3. YouTube Sentiment Analysis",
        "4. YouTube Engagement Insights",
        "5. Advertising Analytics",
        "6. Audience Insights",
        "7. Big Data Processing Lab",
        "8. Advertising Budget Optimizer",
        "9. Dataset Management",
        "10. Database Explorer",
        "11. Unified Marketing Insights",
        "12. Reports and Exports",
        "13. Analytics Assistant"
    ]
    for p_name in expected_pages:
        assert p_name in app.PAGES, f"Missing page: {p_name}"
        assert callable(app.PAGES[p_name]), f"Page renderer for {p_name} is not callable."

def test_page_modules_direct_import():
    from src.ui.page_01_overview import render_page_overview
    from src.ui.page_02_youtube_analytics import render_page_youtube_analytics
    from src.ui.page_03_youtube_sentiment import render_page_youtube_sentiment
    from src.ui.page_04_youtube_engagement import render_page_youtube_engagement
    from src.ui.page_05_advertising_analytics import render_page_advertising_analytics
    from src.ui.page_06_audience_insights import render_page_audience_insights
    from src.ui.page_07_bigdata_lab import render_page_bigdata_lab
    from src.ui.page_08_budget_optimizer import render_page_budget_optimizer
    from src.ui.page_09_dataset_management import render_page_dataset_management
    from src.ui.page_10_database_explorer import render_page_database_explorer
    from src.ui.page_11_unified_insights import render_page_unified_insights
    from src.ui.page_12_reports import render_page_reports
    from src.ui.page_13_assistant import render_page_assistant

    assert render_page_overview is not None
    assert render_page_assistant is not None

