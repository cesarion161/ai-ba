from app.engine.templates.base import WorkflowTemplate
from app.engine.templates.densification import DENSIFICATION
from app.engine.templates.execution_planning import EXECUTION_PLANNING
from app.engine.templates.export import EXPORT
from app.engine.templates.full_analysis import FULL_ANALYSIS
from app.engine.templates.market_research import MARKET_RESEARCH
from app.engine.templates.product_strategy import PRODUCT_STRATEGY
from app.engine.templates.technical_architecture import TECHNICAL_ARCHITECTURE
from app.engine.templates.ux_requirements import UX_REQUIREMENTS

TEMPLATE_REGISTRY: dict[str, WorkflowTemplate] = {
    MARKET_RESEARCH.key: MARKET_RESEARCH,
    PRODUCT_STRATEGY.key: PRODUCT_STRATEGY,
    UX_REQUIREMENTS.key: UX_REQUIREMENTS,
    TECHNICAL_ARCHITECTURE.key: TECHNICAL_ARCHITECTURE,
    EXECUTION_PLANNING.key: EXECUTION_PLANNING,
    DENSIFICATION.key: DENSIFICATION,
    EXPORT.key: EXPORT,
    FULL_ANALYSIS.key: FULL_ANALYSIS,
}


def get_template(key: str) -> WorkflowTemplate:
    if key not in TEMPLATE_REGISTRY:
        raise KeyError(f"Unknown template: {key}. Available: {list(TEMPLATE_REGISTRY.keys())}")
    return TEMPLATE_REGISTRY[key]
