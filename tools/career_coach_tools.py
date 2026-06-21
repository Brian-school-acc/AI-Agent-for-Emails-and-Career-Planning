import json
import os
import random
from typing import Annotated, List, Dict, Any, Optional
from pydantic import Field
from agent_framework import tool

# ==========================================
# TOOL 1: RESUME SKILL GAP ANALYZER
# ==========================================


@tool(
    name="analyze_resume_skill_gaps",
    description=(
        "Compares a student's current skills against a highly detailed, industry-mapped taxonomy "
        "to detect technical and soft skill gaps, providing a multi-tiered upskilling roadmap. "
        "Requires the targeted job role and a comma-separated list of the student's current skills."
    ),
    approval_mode="never_require",
)
def analyze_resume_skill_gaps(
    target_role: Annotated[
        str,
        Field(
            description="The job title or career path the student is targeting (e.g., 'Data Analyst', 'Software Engineer', 'Product Manager', 'UX Designer', 'Data Scientist')."
        ),
    ],
    current_skills_csv: Annotated[
        str,
        Field(
            description="A comma-separated string containing the student's existing skills, tools, or methodologies."
        ),
    ],
) -> str:
    """
    Analyzes skills gaps by running token-normalized matching against a rigorous, built-in matrix
    of common career tracks. It returns match metrics, classified gaps, and distinct action steps.
    """
    # 1. Normalized Industry Matrix
    #    Each role exposes hard_skills, soft_skills, certifications, and a POOL of project ideas
    #    so the recommended capstone varies between calls.
    ROLE_TAXONOMY = {
        "data analyst": {
            "aliases": ["data analytics", "business intelligence analyst", "bi analyst", "reporting analyst"],
            "hard_skills": [
                "SQL", "Python", "R", "Tableau", "PowerBI", "Excel",
                "Statistics", "Data Cleaning", "Data Visualization", "ETL",
            ],
            "soft_skills": [
                "Data Storytelling", "Stakeholder Communication", "Analytical Thinking", "Attention to Detail",
            ],
            "certifications": [
                "Google Data Analytics Professional Certificate",
                "Microsoft Certified: Power BI Data Analyst Associate",
                "Tableau Desktop Specialist",
            ],
            "project_ideas": [
                "Build an end-to-end pipeline fetching public API data, cleaning it via Pandas, and charting it inside a public Tableau dashboard.",
                "Analyze a public e-commerce dataset to surface churn drivers, then publish an interactive PowerBI report with cohort retention curves.",
                "Create a SQL-driven KPI dashboard for a fictional SaaS company, including week-over-week growth metrics and automated data-quality checks.",
            ],
        },
        "data scientist": {
            "aliases": ["machine learning engineer", "ml engineer", "ai engineer", "applied scientist"],
            "hard_skills": [
                "Python", "SQL", "Machine Learning", "Statistics", "Pandas",
                "Scikit-learn", "Deep Learning", "Feature Engineering",
                "Model Evaluation", "Experiment Design",
            ],
            "soft_skills": [
                "Hypothesis Framing", "Technical Communication", "Business Acumen", "Intellectual Curiosity",
            ],
            "certifications": [
                "TensorFlow Developer Certificate",
                "AWS Certified Machine Learning - Specialty",
                "DeepLearning.AI Machine Learning Specialization",
            ],
            "project_ideas": [
                "Train and deploy a churn-prediction model with a documented train/validation/test split and a SHAP-based interpretability report.",
                "Build a recommendation engine on an open dataset and benchmark collaborative filtering against a content-based baseline.",
                "Develop an end-to-end ML service: feature pipeline, model registry, and a FastAPI inference endpoint with monitoring.",
            ],
        },
        "software engineer": {
            "aliases": ["software developer", "backend engineer", "full stack developer", "swe", "web developer"],
            "hard_skills": [
                "Python", "Java", "JavaScript", "Git", "Data Structures",
                "Algorithms", "SQL", "Docker", "REST APIs", "Unit Testing",
                "CI/CD", "System Design",
            ],
            "soft_skills": [
                "Code Review Collaboration", "Agile Methodologies", "Technical Communication", "Ownership",
            ],
            "certifications": [
                "AWS Certified Cloud Practitioner",
                "CKA: Certified Kubernetes Administrator",
                "Oracle Certified Professional: Java SE",
            ],
            "project_ideas": [
                "Develop a microservices-based web application with full user auth, state persistence in PostgreSQL, deployed inside containerized Docker environments.",
                "Build a real-time chat app with WebSockets, message persistence, and a load test demonstrating it handles concurrent users.",
                "Create a CLI tool published to a package registry, complete with unit tests, CI pipeline, and semantic versioning.",
            ],
        },
        "product manager": {
            "aliases": ["product owner", "associate product manager", "apm", "pm"],
            "hard_skills": [
                "Product Roadmap", "User Research", "A/B Testing", "Agile",
                "Scrum", "Jira", "Market Analysis", "KPI Tracking", "Wireframing",
            ],
            "soft_skills": [
                "Cross-functional Leadership", "Empathy", "Public Speaking", "Negotiation", "Prioritization",
            ],
            "certifications": [
                "Certified Scrum Product Owner (CSPO)",
                "Pragmatic Institute Product Framework",
                "Google Project Management Professional Certificate",
            ],
            "project_ideas": [
                "Draft a comprehensive Product Requirement Document (PRD) detailing a new featureset for an existing mobile app, including wireframes, user stories, and localized metrics.",
                "Run a teardown of a popular app, identify a friction point, and propose a prioritized roadmap with an RICE-scored backlog.",
                "Design and document an A/B test for an onboarding flow, including hypothesis, success metrics, and a guardrail-metric plan.",
            ],
        },
        "marketing specialist": {
            "aliases": ["digital marketer", "growth marketer", "content marketer", "marketing analyst"],
            "hard_skills": [
                "SEO", "Google Analytics", "Copywriting", "Content Strategy",
                "A/B Testing", "CRM", "Social Media Ads", "Email Marketing", "Marketing Automation",
            ],
            "soft_skills": [
                "Creative Direction", "Campaign Execution", "Consumer Psychology", "Storytelling",
            ],
            "certifications": [
                "Google Analytics 4 Certification",
                "HubSpot Inbound Marketing Certification",
                "Meta Certified Digital Marketing Associate",
            ],
            "project_ideas": [
                "Execute an end-to-end growth audit on a local small business, formulating an automated email nurturing sequence and a high-converting keyword target map.",
                "Plan and document a multi-channel launch campaign with a content calendar, channel budget split, and projected CAC/LTV model.",
                "Build a landing page, run a simulated A/B test on two headlines, and report conversion lift with statistical significance.",
            ],
        },
        "ux designer": {
            "aliases": ["ui designer", "ux/ui designer", "product designer", "interaction designer"],
            "hard_skills": [
                "Figma", "Wireframing", "Prototyping", "User Research",
                "Usability Testing", "Design Systems", "Information Architecture",
                "Interaction Design", "Accessibility",
            ],
            "soft_skills": [
                "Empathy", "Design Critique", "Stakeholder Communication", "Storytelling",
            ],
            "certifications": [
                "Google UX Design Professional Certificate",
                "Nielsen Norman Group UX Certification",
                "Interaction Design Foundation Certification",
            ],
            "project_ideas": [
                "Run a full design sprint for a mobile feature: user interviews, low-to-high fidelity prototypes in Figma, and a moderated usability test report.",
                "Redesign a poorly-rated public service website and document the before/after with measurable accessibility improvements.",
                "Build a reusable component library / design system with documented tokens, states, and usage guidelines.",
            ],
        },
        "business analyst": {
            "aliases": ["systems analyst", "process analyst", "requirements analyst"],
            "hard_skills": [
                "SQL", "Excel", "Requirements Gathering", "Process Mapping",
                "Data Visualization", "BPMN", "Stakeholder Analysis", "Documentation",
            ],
            "soft_skills": [
                "Stakeholder Communication", "Analytical Thinking", "Facilitation", "Critical Thinking",
            ],
            "certifications": [
                "IIBA Entry Certificate in Business Analysis (ECBA)",
                "PMI Professional in Business Analysis (PMI-PBA)",
                "Six Sigma Green Belt",
            ],
            "project_ideas": [
                "Map an as-is vs. to-be business process for a fictional onboarding workflow, then quantify the projected efficiency gains.",
                "Write a full business requirements document (BRD) for a small internal tool, including use cases and acceptance criteria.",
                "Analyze an operational dataset to identify a bottleneck and present a cost/benefit recommendation deck.",
            ],
        },
        "cybersecurity analyst": {
            "aliases": ["security analyst", "soc analyst", "information security analyst", "infosec"],
            "hard_skills": [
                "Network Security", "SIEM", "Incident Response", "Linux",
                "Python", "Vulnerability Assessment", "Threat Modeling",
                "Cryptography", "Firewalls",
            ],
            "soft_skills": [
                "Risk Communication", "Attention to Detail", "Composure Under Pressure", "Documentation",
            ],
            "certifications": [
                "CompTIA Security+",
                "Certified Ethical Hacker (CEH)",
                "GIAC Security Essentials (GSEC)",
            ],
            "project_ideas": [
                "Build a home lab SIEM, ingest simulated attack logs, and write incident-response runbooks for three common alert types.",
                "Perform a documented vulnerability assessment of an intentionally-vulnerable VM and produce a prioritized remediation report.",
                "Create a threat model for a sample web application using STRIDE and propose mitigations for each identified risk.",
            ],
        },
    }

    # 2. Input Processing & Normalization
    normalized_target = target_role.strip().lower()
    student_skills_list = [
        s.strip().lower() for s in current_skills_csv.split(",") if s.strip()
    ]

    # Fallback to standard baseline profile if role is unrecognized
    matched_key = "data analyst"  # Default fallback
    for role_key, role_data in ROLE_TAXONOMY.items():
        candidates = [role_key] + role_data.get("aliases", [])
        if any(c in normalized_target or normalized_target in c for c in candidates):
            matched_key = role_key
            break

    taxonomy = ROLE_TAXONOMY[matched_key]
    all_required = taxonomy["hard_skills"] + taxonomy["soft_skills"]

    # 3. Gap Analysis Engine
    matched_skills = []
    missing_skills = []

    for skill in all_required:
        # Check for strict matches or partial substring matching
        if any(
            skill.lower() in student_skill or student_skill in skill.lower()
            for student_skill in student_skills_list
        ):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    # Calculate analytical match score
    total_skills_count = len(all_required)
    match_percentage = (
        round((len(matched_skills) / total_skills_count) * 100, 2)
        if total_skills_count > 0
        else 0.0
    )

    # 4. Formulate Actionable Roadmap Payload
    response_data = {
        "targeted_role_profile": matched_key.title(),
        "readiness_score": f"{match_percentage}%",
        "skills_audit": {
            "verified_matches": matched_skills,
            "identified_gaps": missing_skills,
        },
        "actionable_upskilling_roadmap": {
            "priority_technical_focus": [
                s for s in missing_skills if s in taxonomy["hard_skills"]
            ][:3],
            "recommended_certifications": taxonomy["certifications"],
            # Randomly surface one capstone so repeated calls feel fresh
            "capstone_portfolio_project": random.choice(taxonomy["project_ideas"]),
        },
    }

    return json.dumps(response_data, indent=4)


# ==========================================
# TOOL 2: INTERACTIVE INTERVIEW SCENARIO GENERATOR
# ==========================================


@tool(
    name="generate_mock_interview_scenario",
    description=(
        "Generates an immersive, highly customized interview roleplay context including explicit "
        "dynamic reviewer personas, localized technical criteria, and an evaluation rubric based "
        "on the specified industry and experience level. You MUST generate an audio file AND call "
        "the generate_image tool immediately after using this tool to create a realistic visual "
        "representation of the interviewer or environment for the user."
    ),
    approval_mode="never_require",
)
def generate_mock_interview_scenario(
    industry: Annotated[
        str,
        Field(
            description="The domain or corporate environment (e.g., 'Tech', 'Finance', 'Healthcare', 'Consulting', 'Marketing', 'Product')."
        ),
    ],
    experience_level: Annotated[
        str,
        Field(
            description="The candidate baseline tier: Choose from 'Internship', 'Entry-Level', or 'Mid-Level'."
        ),
    ] = "Entry-Level",
) -> str:
    """
    Constructs an interactive interview matrix designed to seed multi-turn agent conversations.
    Forces target evaluation models to track technical competence and behavioral frameworks.

    Each industry now exposes MULTIPLE personas and SEPARATE behavioral/domain question pools
    per level; questions are randomly sampled so repeated calls produce fresh interviews.
    """
    # 1. Comprehensive Question & Persona Matrix
    INTERVIEW_MATRIX = {
        "tech": {
            "aliases": ["software", "engineering", "it", "developer", "startup"],
            "personas": [
                "Marcus, Director of Engineering at an enterprise infrastructure company known for structural precision and robust code reviews.",
                "Priya, Staff Engineer at a fast-scaling fintech startup who values pragmatic trade-offs and shipping velocity.",
                "Kenji, Engineering Manager at a cloud platform team focused on reliability, observability, and on-call culture.",
            ],
            "Internship": {
                "behavioral": [
                    "Can you walk me through a technical challenge you faced in a class project, and explain how you managed version control issues with your peers?",
                    "Tell me about a time you had to learn an unfamiliar technology quickly. How did you approach it?",
                    "Describe a group project where responsibilities were unevenly split. What did you do?",
                ],
                "domain": [
                    "Explain the practical difference between an array and a linked list, and when you would use one over the other.",
                    "What happens, step by step, when you type a URL into a browser and hit enter?",
                    "How would you detect whether a linked list contains a cycle?",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Describe a time you had to debug a production issue or persistent error under tight parameters. What was your systematic process?",
                    "Tell me about a piece of feedback from a code review that changed how you write code.",
                    "Describe a time you disagreed with a teammate on a technical approach. How did it resolve?",
                ],
                "domain": [
                    "How do you ensure your code is maintainable, well-tested, and optimized for scalability when collaborating in sprint cycles?",
                    "Walk me through how you would design a URL shortener at a basic scale.",
                    "What is the difference between SQL and NoSQL, and when would you reach for each?",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Describe a time you encountered massive scope creep or technical friction from cross-functional teams. How did you align architectural requirements?",
                    "Tell me about a system you owned that failed in production. What was the post-mortem outcome?",
                    "Describe how you mentored a junior engineer through a difficult delivery.",
                ],
                "domain": [
                    "We are looking at migrating from a monolith to a distributed microservices framework. Walk me through how you isolate scopes and maintain data state consistency.",
                    "Design a rate limiter for a public API serving millions of requests per day.",
                    "How would you approach reducing p99 latency on a service that has gradually degraded over six months?",
                ],
            },
        },
        "finance": {
            "aliases": ["banking", "investment", "asset management", "fintech", "accounting"],
            "personas": [
                "Victoria Vance, Managing Director of Global Asset Management, focused heavily on rapid mathematical processing, quantitative rigor, and regulatory compliance.",
                "Daniel Osei, VP of Corporate Finance at a multinational, who probes for commercial awareness and clean financial reasoning.",
                "Mei Lin, Risk Director at an investment bank who stress-tests candidates on judgment under uncertainty.",
            ],
            "Internship": {
                "behavioral": [
                    "Why are you looking to break into this specific division of financial services, and how do you handle tracking shifting market variables daily?",
                    "Tell me about a time you spotted a small error in detailed numerical work. What did you do?",
                    "Which recent market event interested you, and what was your take on it?",
                ],
                "domain": [
                    "Walk me through how you construct a basic discounted cash flow (DCF) model or analyze a corporate balance sheet.",
                    "What are the three financial statements, and how do they connect?",
                    "If a company's net income is positive but cash flow is negative, what might be happening?",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Describe an experience where you discovered an inconsistency or error within data sheets or financial reports. How did you resolve it?",
                    "Tell me about a time you had to explain a complex number-heavy concept to a non-technical audience.",
                    "Describe a high-pressure deadline you managed across competing deliverables.",
                ],
                "domain": [
                    "If given a tight deadline with multiple conflicting analytical deliverables, how do you prioritize tasks and manage stakeholder risk?",
                    "How would you value a company that has no profits yet but is growing revenue rapidly?",
                    "Explain how a change in interest rates flows through to a bond's price.",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Detail an instance where you had to pitch a high-stakes, controversial financial asset allocation strategy to a highly skeptical investment board.",
                    "Tell me about a time your analysis led to a decision that turned out to be wrong. What did you learn?",
                    "Describe how you handled a client or stakeholder pushing for a position you believed was too risky.",
                ],
                "domain": [
                    "Walk me through a complex portfolio strategy or quantitative thesis you formulated, detailing your underlying risk mitigation parameters.",
                    "How would you hedge a portfolio that is heavily exposed to a single sector?",
                    "Talk me through how you would assess the credit risk of a mid-cap company seeking financing.",
                ],
            },
        },
        "healthcare": {
            "aliases": ["health", "medical", "clinical", "pharma", "biotech", "hospital"],
            "personas": [
                "Dr. Amara Okafor, Chief Medical Officer who weighs patient-safety reasoning above all else.",
                "Linda Park, Director of Clinical Operations focused on compliance, empathy, and process discipline.",
                "Dr. Rahul Mehta, Head of Health Informatics interested in data-driven care and ethics.",
            ],
            "Internship": {
                "behavioral": [
                    "Why are you drawn to a career in healthcare, and how do you handle emotionally demanding situations?",
                    "Tell me about a time you had to follow a strict protocol even when it was inconvenient.",
                    "Describe a situation where you supported someone who was distressed.",
                ],
                "domain": [
                    "How would you explain the importance of patient confidentiality to a new volunteer?",
                    "What does patient-centered care mean to you in practice?",
                    "Walk me through how you would prioritize tasks during a busy clinical shift.",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Describe a time you caught a potential safety issue. How did you escalate it?",
                    "Tell me about a moment you had to deliver difficult information with empathy.",
                    "Describe how you handled a disagreement with a colleague over patient care.",
                ],
                "domain": [
                    "How do you ensure accuracy when documenting sensitive patient or clinical data?",
                    "Explain how you would balance efficiency with thoroughness under heavy caseloads.",
                    "What steps would you take if you noticed a recurring process gap affecting patient outcomes?",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Describe a time you led a quality-improvement initiative across departments. What was the measurable outcome?",
                    "Tell me about navigating a conflict between operational targets and patient welfare.",
                    "Describe how you implemented a change that staff initially resisted.",
                ],
                "domain": [
                    "How would you design a workflow change to reduce patient wait times without compromising care quality?",
                    "Walk me through how you would evaluate adopting a new clinical technology or system.",
                    "How do you approach balancing regulatory compliance with frontline operational realities?",
                ],
            },
        },
        "consulting": {
            "aliases": ["strategy", "advisory", "management consulting"],
            "personas": [
                "Sophie Laurent, Engagement Manager at a top strategy firm who lives for structured, hypothesis-driven thinking.",
                "Andre Williams, Principal who pressure-tests candidates with ambiguous, open-ended business cases.",
                "Naoko Sato, Partner focused on client communication, executive presence, and crisp synthesis.",
            ],
            "Internship": {
                "behavioral": [
                    "Why consulting, and why now? Walk me through what excites you about client problem-solving.",
                    "Tell me about a time you had to quickly structure a messy, ambiguous problem.",
                    "Describe a moment you persuaded a group to adopt your point of view.",
                ],
                "domain": [
                    "A coffee chain's profits are falling. How would you structure your approach to diagnose why?",
                    "Estimate the number of electric vehicles sold in a mid-sized city per year.",
                    "How would you decide whether a retailer should launch its own delivery service?",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Tell me about a time you delivered a recommendation that a stakeholder initially rejected.",
                    "Describe how you handled an analysis where the data was incomplete or unreliable.",
                    "Describe a time you had to manage competing priorities across multiple workstreams.",
                ],
                "domain": [
                    "A client wants to cut costs by 15% without layoffs. How would you frame the levers available?",
                    "Walk me through how you would size the market for a new subscription product.",
                    "How would you assess whether two companies should merge?",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Describe leading a workstream where the client's executives disagreed with each other. How did you navigate it?",
                    "Tell me about a recommendation you made that had significant financial impact.",
                    "Describe a time you had to manage a junior team through a high-pressure deliverable.",
                ],
                "domain": [
                    "A profitable business unit is dragging down overall growth. How would you advise the board on its future?",
                    "Walk me through how you would structure a post-merger integration plan for two cultures in conflict.",
                    "How would you build a business case for entering a new geographic market?",
                ],
            },
        },
        "marketing": {
            "aliases": ["brand", "growth", "advertising", "communications", "digital marketing"],
            "personas": [
                "Tomas Rivera, VP of Growth at a consumer app obsessed with funnel metrics and experimentation.",
                "Hannah Cole, Brand Director who prizes storytelling, positioning, and creative judgment.",
                "Wei Chen, Head of Performance Marketing focused on CAC, ROAS, and analytical rigor.",
            ],
            "Internship": {
                "behavioral": [
                    "Why marketing, and which brand's recent campaign do you admire and why?",
                    "Tell me about a time you created content or messaging that resonated with an audience.",
                    "Describe a project where you had to work within a very limited budget.",
                ],
                "domain": [
                    "How would you measure whether a social media campaign was successful?",
                    "Walk me through the basic stages of a marketing funnel.",
                    "If a landing page had high traffic but low conversions, where would you start investigating?",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Describe a campaign that underperformed. How did you diagnose and respond?",
                    "Tell me about a time you used data to change a creative or messaging decision.",
                    "Describe how you handled conflicting feedback from multiple stakeholders on a creative asset.",
                ],
                "domain": [
                    "How would you design an A/B test for an email subject line, and how would you judge significance?",
                    "Walk me through how you would allocate a fixed budget across paid channels for a new product.",
                    "What metrics would you track to evaluate the health of an organic content strategy?",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Describe a time you owned a channel's full P&L and had to defend your spend to leadership.",
                    "Tell me about repositioning a product or brand that wasn't landing with its audience.",
                    "Describe how you scaled a campaign that was working without inflating acquisition costs.",
                ],
                "domain": [
                    "How would you build a multi-touch attribution model when channels overlap heavily?",
                    "Walk me through your strategy for reducing CAC by 20% while holding volume steady.",
                    "How would you structure a go-to-market plan for launching into a new customer segment?",
                ],
            },
        },
        "product": {
            "aliases": ["product management", "product owner", "pm"],
            "personas": [
                "Olivia Brandt, Group PM at a B2B SaaS company who drills into prioritization and trade-off reasoning.",
                "Raj Patel, Director of Product at a consumer platform focused on user empathy and metrics.",
                "Greta Nilsson, Head of Product who evaluates strategic thinking and cross-team influence.",
            ],
            "Internship": {
                "behavioral": [
                    "Why product management, and what product do you love and why?",
                    "Tell me about a time you gathered feedback from users to shape a decision.",
                    "Describe a group project where you had to align people with different goals.",
                ],
                "domain": [
                    "Pick an app you use daily. What one feature would you add, and how would you justify it?",
                    "How would you decide which of three feature requests to build first?",
                    "What metric would you use to know if a new feature is successful?",
                ],
            },
            "Entry-Level": {
                "behavioral": [
                    "Describe a time you had to say no to a stakeholder's feature request. How did you handle it?",
                    "Tell me about a feature you shipped that didn't perform as expected. What did you learn?",
                    "Describe how you resolved a conflict between engineering and design on scope.",
                ],
                "domain": [
                    "Walk me through how you would prioritize a backlog using a framework of your choice.",
                    "How would you design and measure an experiment to improve user onboarding?",
                    "A key engagement metric dropped 10% overnight. How do you investigate?",
                ],
            },
            "Mid-Level": {
                "behavioral": [
                    "Describe a product strategy you championed that required buy-in across multiple teams.",
                    "Tell me about a time you killed a feature or project. How did you make that call?",
                    "Describe how you led a team through an ambiguous, high-stakes launch.",
                ],
                "domain": [
                    "How would you define and defend a north-star metric for a two-sided marketplace?",
                    "Walk me through building a 12-month roadmap when leadership priorities keep shifting.",
                    "How would you approach pricing a new product tier with limited historical data?",
                ],
            },
        },
    }

    # 2. Normalization & Selection Logic
    norm_industry = industry.strip().lower()
    matched_ind = "tech"  # Default fallback
    for ind_key, ind_data in INTERVIEW_MATRIX.items():
        candidates = [ind_key] + ind_data.get("aliases", [])
        if any(c in norm_industry or norm_industry in c for c in candidates):
            matched_ind = ind_key
            break

    valid_levels = ["Internship", "Entry-Level", "Mid-Level"]
    matched_level = (
        experience_level if experience_level in valid_levels else "Entry-Level"
    )

    industry_data = INTERVIEW_MATRIX[matched_ind]
    level_pools = industry_data[matched_level]

    # 3. Randomized selection for variety across calls
    selected_persona = random.choice(industry_data["personas"])
    behavioral_q = random.choice(level_pools["behavioral"])
    domain_q = random.choice(level_pools["domain"])

    icebreaker_pool = [
        "Welcome. To begin, please give me a brief overview of your background and explain why you're targeting our organization today.",
        "Thanks for joining. Before we dive in, tell me a bit about yourself and what drew you to this role.",
        "Let's get started. Walk me through your journey so far and what you're hoping to do next.",
        "Good to meet you. Give me the short version of your story and why this opportunity stood out to you.",
    ]

    # 4. Constructing Structural Schemas & Rubrics
    scenario_payload = {
        "session_config": {
            "interviewer_persona": selected_persona,
            "target_experience_tier": matched_level,
            "asserted_industry_domain": matched_ind.upper(),
        },
        "assessment_prompts": {
            "icebreaker_question": random.choice(icebreaker_pool),
            "core_behavioral_question": behavioral_q,
            "domain_specific_question": domain_q,
        },
        "evaluation_rubric_standards": {
            "preferred_response_framework": "STAR Method (Situation, Task, Action, Result)",
            "key_performance_indicators": [
                "Technical Domain Competence",
                "Structured Problem Decomposition",
                "Composure and Communication Clarity",
                "Value Orientation and Metrics-Driven Outcomes",
            ],
        },
    }

    return json.dumps(scenario_payload, indent=4)


# ==========================================
# TOOL 3: SIMULATE WORKPLACE SCENARIO
# ==========================================


@tool(
    name="simulate_workplace",
    description=(
        "Constructs a complex, multi-layered workplace conflict, systemic failure, or prioritization "
        "crisis (configured via scenario type, department, and difficulty) to evaluate a student's "
        "situational judgement and soft skills. You MUST generate an audio file AND call the "
        "generate_image tool immediately after using this tool to visually illustrate the scenario "
        "and make the simulation feel immersive and realistic."
        "Afterwards, you MUST DISPLAY the image to the user in the UI"
    ),
    approval_mode="never_require",
)
def simulate_workplace(
    scenario_type: Annotated[
        str,
        Field(
            description="The primary engine catalyst: 'Scope Creep', 'Interpersonal Conflict', 'Missed Deadline', or 'Unclear Requirements'."
        ),
    ],
    department: Annotated[
        str,
        Field(
            description="The operational vertical: 'Engineering', 'Product Management', 'Corporate Marketing', or 'Operations'."
        ),
    ],
    difficulty: Annotated[
        str,
        Field(
            description="The escalation complexity tier: Choose either 'Entry-Level' or 'Managerial'."
        ),
    ] = "Entry-Level",
) -> str:
    """
    Generates structured workplace simulations with divergent operational options and localized downstream impacts.
    The Executive Agent uses this tool to walk students through interactive workplace branching paths.
    """
    # 1. Structural Branching Blueprint Database
    SCENARIO_DATABASE = {
        "scope creep": {
            "title": "The Infinite Horizon Sprint",
            "narrative": "Your cross-functional client team suddenly requests three un-scoped dashboard views 48 hours before the hard staging deployment freeze. Your primary engineer states it is impossible without generating massive technical debt.",
            "stakeholders": {
                "Elena (Account Director)": "Wants to keep the client happy at all costs to hit renewals.",
                "Dave (Lead Architect)": "Threatens to check out of the sprint if systemic code quality is compromised.",
            },
        },
        "interpersonal conflict": {
            "title": "Asymmetric Contribution Crisis",
            "narrative": "A core team member missed two consecutive standup deadlines, stalling the downstream dependency tasks assigned to you. When confronted privately, they became defensive, citing invisible structural blockages.",
            "stakeholders": {
                "Jordan (Peer Associate)": "Feels defensive and micromanaged by your operational follow-ups.",
                "Sarah (Department Lead)": "Only cares about clean deliverables by Friday and dislikes team friction.",
            },
        },
        "missed deadline": {
            "title": "The Staging Pipeline Breach",
            "narrative": "An automation script crashed over the weekend, corrupting the production-ready marketing assets template. The client launch occurs in exactly four hours, and your team is panicking without a dynamic fallback layout.",
            "stakeholders": {
                "Chloe (VP of Marketing)": "Demanding answers and real-time contingency execution immediate visibility.",
                "Sam (DevOps Support)": "Overwhelmed, trying to patch backend servers while lacking local data context.",
            },
        },
        "unclear requirements": {
            "title": "The Ambiguous Architecture Roadmap",
            "narrative": "The corporate steering committee provided a vague brief to optimize internal workflow metrics by 20% using arbitrary frameworks, but left out any underlying resource budgets or data infrastructure access.",
            "stakeholders": {
                "Robert (Executive Sponsor)": "Expects a comprehensive strategic proposal by tomorrow morning.",
                "Tina (Data Engineer)": "Refuses to start provisioning environments without a explicit data schema schema documentation.",
            },
        },
    }

    # 2. Validation Processing
    norm_type = scenario_type.strip().lower()
    matched_type = "scope creep"  # Default fallback logic
    for key in SCENARIO_DATABASE.keys():
        if key in norm_type or norm_type in key:
            matched_type = key
            break

    selected_scenario = SCENARIO_DATABASE[matched_type]

    # 3. Dynamic Vector Vector Calculations Based on Parameters
    is_managerial = difficulty.strip().lower() == "managerial"
    escalation_modifier = (
        "The steering committee is looking directly at you to mitigate department-wide organizational churn."
        if is_managerial
        else "As an individual contributor, your reputation for internal dependability is hanging in the balance."
    )

    # 4. Construct Operational Branch Options
    options = [
        {
            "vector_id": "OPTION_A",
            "action_strategy": "Escalate the bottleneck immediately to high-level leadership with a data-backed assessment.",
            "potential_downstream_risk": "May be perceived as a lack of self-management or direct conflict-resolution competence.",
        },
        {
            "vector_id": "OPTION_B",
            "action_strategy": "Convene an emergency cross-functional alignment sync to negotiate compromise metrics.",
            "potential_downstream_risk": "Consumes critical operational hours and may cause further scheduling slippage.",
        },
        {
            "vector_id": "OPTION_C",
            "action_strategy": "Absorb the pressure, work late hours to patch the issues manually, and document the gaps later.",
            "potential_downstream_risk": "Enforces unsustainable workplace burnout patterns and sets a high-debt precedent.",
        },
    ]

    # 5. Build Unified Simulation Schema Payload
    simulation_payload = {
        "simulation_metadata": {
            "scenario_name": selected_scenario["title"],
            "operational_vertical": department.upper(),
            "complexity_tier": difficulty,
            "escalation_modifier": escalation_modifier,
        },
        "core_dilemma": {
            "context_narrative": selected_scenario["narrative"],
            "active_stakeholders": selected_scenario["stakeholders"],
        },
        "branching_vectors": options,
        "evaluation_framework": {
            "competency_focus": [
                "De-escalation Capability",
                "Resource Prioritization",
                "Cross-Functional Collaboration",
            ],
            "prompt_for_student": "How do you navigate this crisis? Formulate your explicit message, email response, or structural action step.",
        },
    }

    return json.dumps(simulation_payload, indent=4)
