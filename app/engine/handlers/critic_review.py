from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway

logger = structlog.get_logger()

# Branch-specific review criteria and system messages
_REVIEW_CONFIGS: dict[str, dict[str, str]] = {
    "technical_architecture": {
        "system": (
            "You are a principal software architect reviewing a technical architecture "
            "document. You have 15+ years of experience building production systems. "
            "You are thorough, skeptical, and focused on operational realities."
        ),
        "criteria": """\
## Evaluation Criteria for Architecture Document

1. **Specificity**: Does it name exact services, tools, libraries,
and configurations — or hand-wave with vague suggestions?
2. **Trade-off analysis**: Does every major decision include
alternatives and trade-offs? Or are choices unjustified?
3. **Failure modes**: Does it address what happens when things break?
Retries, circuit breakers, failover, graceful degradation?
4. **Cost awareness**: Are there cost estimates?
Does it distinguish $50/mo vs $5000/mo choices?
5. **Scalability realism**: Does it identify bottlenecks
and how to address them at 10x and 100x scale?
6. **Diagrams**: Are there Mermaid diagrams for architecture,
data flow, and ER? Are they detailed or superficial?
7. **Security**: Auth, encryption, secrets management,
compliance — all addressed?
8. **Operational readiness**: CI/CD, monitoring, logging,
alerting, runbooks — would an ops team know what to do?
9. **Data architecture**: Database choices justified?
Schema design? Caching strategy? Event patterns?
10. **Patterns**: Are relevant patterns (circuit breaker, saga,
CQRS, bulkhead) discussed with justification?
11. **Completeness**: Could an engineering team start
implementation from this document alone?
12. **Implementation readiness**: Are API endpoints specified?
Data models defined? Service boundaries clear?""",
    },
    "execution_planning": {
        "system": (
            "You are a senior technical program manager reviewing an execution plan. "
            "You focus on realistic timelines, proper risk assessment, and actionable sprint plans."
        ),
        "criteria": """\
## Evaluation Criteria for Execution Plan

1. **Realistic timelines**: Are effort estimates grounded in reality? Are there buffers?
2. **Dependencies**: Are cross-team and technical dependencies mapped?
3. **Risk register**: Are risks specific (not generic) with real mitigation strategies?
4. **Sprint planning**: Are the first sprints detailed enough to start immediately?
5. **Budget breakdown**: Is it granular enough for financial planning?
6. **Launch criteria**: Are MVP and launch criteria specific and measurable?
7. **Team structure**: Are roles and hiring needs realistic?""",
    },
    "product_strategy": {
        "system": (
            "You are a senior product strategist reviewing a product roadmap. "
            "You focus on prioritization clarity, competitive positioning, and measurable outcomes."
        ),
        "criteria": """\
## Evaluation Criteria for Product Roadmap

1. **Prioritization**: Are features clearly prioritized with rationale?
2. **Market fit**: Does it address real user needs supported by research?
3. **Monetization**: Is the revenue model realistic and well-justified?
4. **Metrics**: Are success metrics specific and measurable (not vanity metrics)?
5. **Technical feasibility**: Are dependencies on technical work identified?
6. **Competitive advantage**: Does it articulate clear differentiation?""",
    },
    "market_research": {
        "system": (
            "You are a senior business strategist and feasibility analyst reviewing "
            "a market research or feasibility document. You focus on evidence quality, "
            "assumption validity, and honest assessment of risks."
        ),
        "criteria": """\
## Evaluation Criteria for Market Research / Feasibility Document

1. **Evidence quality**: Are claims grounded in research data
or are they assumptions stated as facts?
2. **Market sizing rigor**: Are TAM/SAM/SOM calculations
specific with stated methodology, or vague claims?
3. **Competitor coverage**: Are real competitors identified
with specific strengths/weaknesses?
4. **Feasibility honesty**: Does the assessment flag real risks
and RED/AMBER ratings, or is everything green?
5. **Unit economics**: Are CAC, LTV, payback period calculated with stated assumptions?
6. **Assumptions visibility**: Are key assumptions explicitly listed with validation methods?
7. **Go/no-go clarity**: Is the recommendation clear and actionable with specific conditions?""",
    },
    "business_requirements": {
        "system": (
            "You are a senior business analyst reviewing a Business Requirements Document, "
            "Business Rules Catalog, and Business Process Model. You focus on completeness, "
            "testability, and traceability of requirements."
        ),
        "criteria": """\
## Evaluation Criteria for Business Requirements Package

1. **Measurability**: Does every requirement have a measurable
outcome? "User-friendly" is not a requirement.
2. **Traceability**: Do requirements trace to business
objectives? Can you follow goal to requirement?
3. **Business rules completeness**: Are rules specific and
unambiguous? Do they cover failure cases, not just happy paths?
4. **Process coverage**: Are current/future-state processes
documented? Are exception flows identified?
5. **Service blueprint**: Does the process model connect
frontstage UX to backstage systems?
6. **Constraints and assumptions**: Are constraints and
dependencies explicitly stated — not hidden?
7. **Scope boundaries**: Is it clear what is in-scope and out-of-scope, and why?
8. **Operational coverage**: Are support, admin, billing, and
incident processes documented — not just product features?
9. **Testability**: Could a QA team write test cases from these
requirements without asking questions?
10. **Consistency**: Do the BRD, business rules, and process
model align — or do they contradict each other?""",
    },
    "delivery": {
        "system": (
            "You are a senior delivery architect reviewing API contracts, data models, "
            "QA strategy, and traceability documentation. You focus on implementation "
            "readiness, specification precision, and coverage completeness."
        ),
        "criteria": """\
## Evaluation Criteria for Delivery Documentation

1. **API completeness**: Are all endpoints defined with
request/response schemas, error codes, and auth?
2. **Data model precision**: Are entities defined with field
types, constraints, PII classification, and retention?
3. **Test coverage mapping**: Does the QA strategy map test
scenarios to specific requirements and business rules?
4. **Traceability**: Can you trace from business objective
to requirement to feature to story to test case?
5. **Performance targets**: Are performance test scenarios
specific with target numbers (latency, throughput)?
6. **Security testing**: Does QA go beyond "run a scanner"
to include specific attack scenarios?
7. **Gap identification**: Does the traceability matrix
honestly identify coverage gaps?
8. **Implementation readiness**: Could two independent teams
build compatible systems from these specs?""",
    },
}

_DEFAULT_REVIEW = {
    "system": "You are a meticulous business document reviewer.",
    "criteria": """\
## Evaluation Criteria

1. Completeness: Are all required sections present?
2. Accuracy: Are claims supported by data?
3. Clarity: Is the document clear and well-structured?
4. Actionability: Does it provide actionable insights?
5. Consistency: Are there any contradictions?""",
}


@register_handler(NodeType.CRITIC_REVIEW)
class CriticReviewHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        max_cycles = config.get("max_cycles", 2)
        branch = config.get("branch", "default")

        # Get the document to review from upstream
        document = ""
        for key, data in input_data.items():
            if isinstance(data, dict) and "document" in data:
                document = data["document"]
                break

        if not document:
            return {
                "verdict": "fail",
                "feedback": "No document provided for review.",
                "score": 0,
            }

        review_config = _REVIEW_CONFIGS.get(branch, _DEFAULT_REVIEW)

        prompt = f"""Review the following document critically and thoroughly.

## Document to Review
{document}

{review_config["criteria"]}

Provide:
- A verdict: "pass" (score >= 7) or "fail" (score < 7)
- A score from 1-10 with justification
- Specific, actionable feedback on what to improve (not vague suggestions)
- A summary of strengths
- Missing sections or topics that should be covered

Format your response as structured analysis.
"""

        messages = [
            {"role": "system", "content": review_config["system"]},
            {"role": "user", "content": prompt},
        ]

        review = await llm_gateway.complete(messages, task_type="critic_review")

        # Parse verdict from review (simple heuristic)
        verdict = "pass" if "pass" in review.lower()[:200] else "fail"
        score_estimate = 7.0 if verdict == "pass" else 4.0

        return {
            "verdict": verdict,
            "feedback": review,
            "score": score_estimate,
            "max_cycles": max_cycles,
        }
