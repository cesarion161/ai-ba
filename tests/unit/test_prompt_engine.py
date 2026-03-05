from app.services.prompt_engine import prompt_engine


def test_render_web_search():
    result = prompt_engine.render(
        "market_research/web_search",
        business_idea="AI tutoring platform",
        target_audience="K-12 students",
        user_feedback=None,
    )
    assert "AI tutoring platform" in result
    assert "K-12 students" in result


def test_render_with_feedback():
    result = prompt_engine.render(
        "market_research/web_search",
        business_idea="SaaS",
        target_audience="SMBs",
        user_feedback="Include more data about pricing",
    )
    assert "Include more data about pricing" in result


def test_render_lean_canvas():
    result = prompt_engine.render(
        "market_research/lean_canvas",
        research_summary="Market is growing",
        competitor_analysis="3 main competitors",
        market_sizing="$10B TAM",
        user_answers="Product is a SaaS platform",
        user_feedback=None,
    )
    assert "Problem" in result
    assert "Solution" in result
