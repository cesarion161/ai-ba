from app.core.llm_config import get_model_config


def test_all_node_types_have_config():
    expected = [
        "research",
        "calculate",
        "generate_document",
        "critic_review",
        "ask_user",
        "densify",
        "format_export",
    ]
    for task_type in expected:
        config = get_model_config(task_type)
        assert config.primary
        assert isinstance(config.fallbacks, list)
        assert config.temperature >= 0
        assert config.max_tokens > 0


def test_unknown_task_type_returns_default():
    config = get_model_config("nonexistent_task")
    assert config.primary == "claude-sonnet-4-20250514"


def test_calculate_low_temperature():
    config = get_model_config("calculate")
    assert config.temperature <= 0.2


def test_generate_document_high_tokens():
    config = get_model_config("generate_document")
    assert config.max_tokens >= 8192
