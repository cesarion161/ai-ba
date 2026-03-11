"""Full analysis composite template — combines all branches with cross-branch dependencies.

Flow:
  Phase 1: Market Research — intake → research → lean canvas → feasibility assessment
  Phase 2: Business Requirements — BRD questions → business rules + process model → BRD
  Phase 3: Product Strategy — product questions → feature/pricing research → roadmap
  Phase 4: UX & Requirements — UX questions → UX research → user stories
  Phase 5: Technical Architecture — tech questions → research → architecture
  Phase 6: Execution Planning — execution questions → cost estimation → execution plan
  Phase 7: Delivery — QA strategy → traceability matrix
  Phase 8: Densification — role-specific dense references
  Phase 9: Export — ZIP archive
"""

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.models.workflow_node import NodeType

# Common dependency lists used by multiple nodes
_ALL_CRITIC_NODES = [
    "lean_canvas_critic",
    "feasibility_critic",
    "brd_critic",
    "product_roadmap_critic",
    "user_stories_critic",
    "architecture_critic",
    "execution_plan_critic",
]

FULL_ANALYSIS = WorkflowTemplate(
    key="full_analysis",
    label="Full Business Analysis",
    nodes=[
        # ===================================================================
        # PHASE 1: Market Research & Viability
        # ===================================================================
        NodeTemplate(
            slug="intake_questions",
            label="Discovery & Intake Questions",
            branch="market_research",
            node_type=NodeType.ASK_USER,
            requires_approval=False,
            config={
                "questions": [
                    "Describe your product or service idea in detail. What does it do?",
                    "What problem does it solve? How painful is it today?",
                    "Who is your target customer? (Role, company size, industry)",
                    "What alternatives or competitors exist today?",
                    "Why now? What market or technology shift makes this timely?",
                    "What is your expected pricing model and price range?",
                    "What constraints exist? (Budget, timeline, regulations, team)",
                    "What would make this project fail? (Top 3 risks you're most worried about)",
                ]
            },
        ),
        NodeTemplate(
            slug="web_search",
            label="Market & Industry Research",
            branch="market_research",
            node_type=NodeType.RESEARCH,
            depends_on=["intake_questions"],
            config={"tool": "tavily", "max_results": 10},
        ),
        NodeTemplate(
            slug="competitor_analysis",
            label="Competitor Analysis",
            branch="market_research",
            node_type=NodeType.RESEARCH,
            depends_on=["intake_questions"],
            config={"tool": "tavily", "focus": "competitors"},
        ),
        NodeTemplate(
            slug="market_sizing",
            label="Market Sizing (TAM/SAM/SOM)",
            branch="market_research",
            node_type=NodeType.CALCULATE,
            depends_on=["web_search"],
            config={"calculation": "tam_sam_som"},
        ),
        NodeTemplate(
            slug="lean_canvas",
            label="Lean Canvas",
            branch="market_research",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["web_search", "competitor_analysis", "market_sizing"],
            config={"template": "lean_canvas", "branch": "market_research"},
        ),
        NodeTemplate(
            slug="lean_canvas_critic",
            label="Lean Canvas Review",
            branch="market_research",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["lean_canvas"],
            config={"max_cycles": 2, "branch": "market_research"},
        ),
        # --- Feasibility Assessment (gates further investment) ---
        NodeTemplate(
            slug="feasibility_assessment",
            label="Feasibility Assessment",
            branch="market_research",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["lean_canvas_critic"],
            config={"template": "feasibility", "branch": "market_research"},
        ),
        NodeTemplate(
            slug="feasibility_critic",
            label="Feasibility Review",
            branch="market_research",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["feasibility_assessment"],
            config={"max_cycles": 2, "branch": "market_research"},
        ),
        # ===================================================================
        # PHASE 2: Business Requirements
        # ===================================================================
        NodeTemplate(
            slug="brd_questions",
            label="Business Requirements Questions",
            branch="business_requirements",
            node_type=NodeType.ASK_USER,
            depends_on=["feasibility_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "Describe the key business processes to support or automate.",
                    "What business rules govern your domain? (e.g., approvals, pricing)",
                    "What compliance or regulatory requirements apply?",
                    "Who are the key user roles and what actions can each role perform?",
                    "What are the critical data entities in your business?",
                ]
            },
        ),
        # Business rules and process model run in parallel
        NodeTemplate(
            slug="business_rules",
            label="Business Rules Catalog",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions"],
            config={"template": "business_rules", "branch": "business_requirements"},
        ),
        NodeTemplate(
            slug="process_model",
            label="Business Process Model",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions"],
            config={"template": "process_model", "branch": "business_requirements"},
        ),
        # BRD synthesizes business rules and process model
        NodeTemplate(
            slug="brd",
            label="Business Requirements Document",
            branch="business_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["brd_questions", "business_rules", "process_model"],
            config={"template": "brd", "branch": "business_requirements"},
        ),
        NodeTemplate(
            slug="brd_critic",
            label="Business Requirements Review",
            branch="business_requirements",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["brd"],
            config={"max_cycles": 2, "branch": "business_requirements"},
        ),
        # ===================================================================
        # PHASE 3: Product Strategy (depends on BRD)
        # ===================================================================
        NodeTemplate(
            slug="product_questions",
            label="Product Strategy Questions",
            branch="product_strategy",
            node_type=NodeType.ASK_USER,
            depends_on=["brd_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What are the core features of your product? List the top 5-10 capabilities.",
                    "What is your monetization strategy? (subscription, freemium, etc.)",
                    "What is your product's key differentiator?",
                    "What does the user's 'aha moment' look like? When do they first get value?",
                    "What distribution channels will you use to reach customers?",
                ]
            },
        ),
        NodeTemplate(
            slug="feature_research",
            label="Feature Landscape Research",
            branch="product_strategy",
            node_type=NodeType.RESEARCH,
            depends_on=["product_questions"],
            config={"tool": "tavily", "focus": "features"},
        ),
        NodeTemplate(
            slug="pricing_research",
            label="Pricing Model Research",
            branch="product_strategy",
            node_type=NodeType.RESEARCH,
            depends_on=["product_questions"],
            config={"tool": "tavily", "focus": "pricing"},
        ),
        NodeTemplate(
            slug="product_roadmap",
            label="Product Roadmap",
            branch="product_strategy",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["feature_research", "pricing_research"],
            config={"template": "product_roadmap", "branch": "product_strategy"},
        ),
        NodeTemplate(
            slug="product_roadmap_critic",
            label="Product Roadmap Review",
            branch="product_strategy",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["product_roadmap"],
            config={"max_cycles": 2, "branch": "product_strategy"},
        ),
        # ===================================================================
        # PHASE 4: UX & Requirements (depends on BRD, parallel with product)
        # ===================================================================
        NodeTemplate(
            slug="ux_questions",
            label="UX & Requirements Questions",
            branch="ux_requirements",
            node_type=NodeType.ASK_USER,
            depends_on=["brd_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "Describe your primary user personas. (Role, goals, frustrations)",
                    "What are the 3-5 critical user journeys? Walk through each step-by-step.",
                    "What platforms must be supported? (Web, iOS, Android, desktop app, API-only)",
                    "What accessibility requirements apply? (WCAG level, etc.)",
                    "What does a successful first-time user experience look like?",
                ]
            },
        ),
        NodeTemplate(
            slug="ux_research",
            label="UX Best Practices Research",
            branch="ux_requirements",
            node_type=NodeType.RESEARCH,
            depends_on=["ux_questions"],
            config={"tool": "tavily", "focus": "ux_patterns"},
        ),
        NodeTemplate(
            slug="user_stories",
            label="User Stories Document",
            branch="ux_requirements",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["ux_research"],
            config={"template": "user_stories", "branch": "ux_requirements"},
        ),
        NodeTemplate(
            slug="user_stories_critic",
            label="User Stories Review",
            branch="ux_requirements",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["user_stories"],
            config={"max_cycles": 2},
        ),
        # ===================================================================
        # PHASE 5: Technical Architecture
        # ===================================================================
        NodeTemplate(
            slug="tech_questions",
            label="Technical Architecture Questions",
            branch="technical_architecture",
            node_type=NodeType.ASK_USER,
            depends_on=["product_roadmap_critic", "user_stories_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What is your team's technical expertise?",
                    "What are your scalability requirements? (Users at launch, 6mo, 1yr)",
                    "What external systems or APIs must be integrated?",
                    "What are your availability/uptime requirements? (99.9%? 99.99%?)",
                    "Are there data residency or compliance constraints?",
                ]
            },
        ),
        NodeTemplate(
            slug="tech_stack_research",
            label="Tech Stack Research",
            branch="technical_architecture",
            node_type=NodeType.RESEARCH,
            depends_on=["tech_questions"],
            config={"tool": "tavily", "focus": "technology"},
        ),
        NodeTemplate(
            slug="architecture_doc",
            label="Architecture Document",
            branch="technical_architecture",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["tech_stack_research"],
            config={"template": "architecture", "branch": "technical_architecture"},
        ),
        NodeTemplate(
            slug="architecture_critic",
            label="Architecture Review",
            branch="technical_architecture",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["architecture_doc"],
            config={"max_cycles": 2, "branch": "technical_architecture"},
        ),
        # --- Detailed Technical Specs (derived from architecture) ---
        NodeTemplate(
            slug="api_contracts",
            label="API & Event Contract Specification",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["architecture_critic", "user_stories_critic"],
            config={"template": "api_contracts", "branch": "delivery"},
        ),
        NodeTemplate(
            slug="data_model_spec",
            label="Data Model Specification",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["architecture_critic", "brd_critic"],
            config={"template": "data_model", "branch": "delivery"},
        ),
        # ===================================================================
        # PHASE 6: Execution Planning
        # ===================================================================
        NodeTemplate(
            slug="execution_questions",
            label="Execution Planning Questions",
            branch="execution_planning",
            node_type=NodeType.ASK_USER,
            depends_on=["architecture_critic"],
            requires_approval=False,
            config={
                "questions": [
                    "What is your team size and composition? (Engineers, designers, PMs)",
                    "What is your total budget for the build phase?",
                    "What is your target launch date or timeline constraint?",
                    "Do you have existing infrastructure or CI/CD?",
                    "What is your risk tolerance? (Aggressive vs conservative)",
                ]
            },
        ),
        NodeTemplate(
            slug="cost_estimation",
            label="Cost Estimation",
            branch="execution_planning",
            node_type=NodeType.CALCULATE,
            depends_on=["execution_questions"],
            config={"calculation": "cost_estimation"},
        ),
        NodeTemplate(
            slug="execution_plan",
            label="Execution Plan Document",
            branch="execution_planning",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["cost_estimation"],
            config={"template": "execution_plan", "branch": "execution_planning"},
        ),
        NodeTemplate(
            slug="execution_plan_critic",
            label="Execution Plan Review",
            branch="execution_planning",
            node_type=NodeType.CRITIC_REVIEW,
            depends_on=["execution_plan"],
            config={"max_cycles": 2, "branch": "execution_planning"},
        ),
        # ===================================================================
        # PHASE 7: Delivery — QA Strategy & Traceability
        # ===================================================================
        NodeTemplate(
            slug="qa_strategy",
            label="QA & Test Strategy",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=["execution_plan_critic", "user_stories_critic", "architecture_critic"],
            config={"template": "qa_strategy", "branch": "delivery"},
        ),
        NodeTemplate(
            slug="traceability_matrix",
            label="Traceability Matrix",
            branch="delivery",
            node_type=NodeType.GENERATE_DOCUMENT,
            depends_on=[
                "lean_canvas_critic",
                "brd_critic",
                "product_roadmap_critic",
                "user_stories_critic",
                "architecture_critic",
                "execution_plan_critic",
                "qa_strategy",
            ],
            config={"template": "traceability_matrix", "branch": "delivery"},
        ),
        # --- Product Backlog (structured JSON + markdown) ---
        NodeTemplate(
            slug="product_backlog",
            label="Product Backlog",
            branch="delivery",
            node_type=NodeType.GENERATE_BACKLOG,
            depends_on=[
                "user_stories_critic",
                "execution_plan_critic",
                "traceability_matrix",
                "product_roadmap_critic",
            ],
            config={"template": "backlog", "branch": "delivery"},
        ),
        # ===================================================================
        # PHASE 8: Densification
        # ===================================================================
        NodeTemplate(
            slug="densify_developer",
            label="Densify for Developer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                *_ALL_CRITIC_NODES,
                "api_contracts",
                "data_model_spec",
                "qa_strategy",
                "traceability_matrix",
                "product_backlog",
            ],
            config={"role": "developer"},
        ),
        NodeTemplate(
            slug="densify_designer",
            label="Densify for Designer",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                *_ALL_CRITIC_NODES,
                "traceability_matrix",
                "product_backlog",
            ],
            config={"role": "designer"},
        ),
        NodeTemplate(
            slug="densify_pm",
            label="Densify for Product Manager",
            branch="densification",
            node_type=NodeType.DENSIFY,
            depends_on=[
                *_ALL_CRITIC_NODES,
                "qa_strategy",
                "traceability_matrix",
                "product_backlog",
            ],
            config={"role": "product_manager"},
        ),
        # ===================================================================
        # PHASE 9: Export
        # ===================================================================
        NodeTemplate(
            slug="format_export",
            label="Format & Export Archive",
            branch="export",
            node_type=NodeType.FORMAT_EXPORT,
            depends_on=["densify_developer", "densify_designer", "densify_pm"],
            requires_approval=False,
            config={"format": "zip"},
        ),
    ],
)
