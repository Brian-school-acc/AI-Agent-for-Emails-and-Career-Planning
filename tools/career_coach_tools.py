import json
import os
from typing import Annotated, List, Dict, Any, Optional
from pydantic import Field
from agent_framework import tool

# ==========================================
# TOOL 1: RESUME SKILL GAP ANALYZER
# ==========================================


@tool(
    name="analyze_resume_skill_gaps",
    description="Compares a student's current skills against a highly detailed, industry-mapped taxonomy to detect technical and soft skill gaps, providing a multi-tiered upskilling roadmap.",
    approval_mode="never_require",
)
def analyze_resume_skill_gaps(
    target_role: Annotated[
        str,
        Field(
            description="The job title or career path the student is targeting (e.g., 'Data Analyst', 'Software Engineer', 'Product Manager')."
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
    ROLE_TAXONOMY = {
        "data analyst": {
            "hard_skills": [
                "SQL",
                "Python",
                "R",
                "Tableau",
                "PowerBI",
                "Excel",
                "Statistics",
                "Data Cleaning",
            ],
            "soft_skills": [
                "Data Storytelling",
                "Stakeholder Communication",
                "Analytical Thinking",
            ],
            "certifications": [
                "Google Data Analytics Professional Certificate",
                "Microsoft Certified: Power BI Data Analyst Associate",
            ],
            "project_idea": "Build an end-to-end pipeline fetching public API data, cleaning it via Pandas, and charting it inside a public Tableau dashboard.",
        },
        "software engineer": {
            "hard_skills": [
                "Python",
                "Java",
                "JavaScript",
                "Git",
                "Data Structures",
                "Algorithms",
                "SQL",
                "Docker",
                "REST APIs",
                "Unit Testing",
            ],
            "soft_skills": [
                "Code Review Collaboration",
                "Agile Methodologies",
                "System Design",
            ],
            "certifications": [
                "AWS Certified Cloud Practitioner",
                "CKA: Certified Kubernetes Administrator",
            ],
            "project_idea": "Develop a microservices-based web application with full user auth, state persistence in PostgreSQL, deployed inside containerized Docker environments.",
        },
        "product manager": {
            "hard_skills": [
                "Product Roadmap",
                "User Research",
                "A/B Testing",
                "Agile",
                "Scrum",
                "Jira",
                "Market Analysis",
                "KPI Tracking",
            ],
            "soft_skills": [
                "Cross-functional Leadership",
                "Empathy",
                "Public Speaking",
                "Negotiation",
            ],
            "certifications": [
                "Certified Scrum Product Owner (CSPO)",
                "Pragmatic Institute Product Framework",
            ],
            "project_idea": "Draft a comprehensive Product Requirement Document (PRD) detailing a new featureset for an existing mobile app, including wireframes, user stories, and localized metrics.",
        },
        "marketing specialist": {
            "hard_skills": [
                "SEO",
                "Google Analytics",
                "Copywriting",
                "Content Strategy",
                "A/B Testing",
                "CRM",
                "Social Media Ads",
                "Email Marketing",
            ],
            "soft_skills": [
                "Creative Direction",
                "Campaign Execution",
                "Consumer Psychology",
            ],
            "certifications": [
                "Google Analytics 4 Certification",
                "HubSpot Inbound Marketing Certification",
            ],
            "project_idea": "Execute an end-to-end growth audit on a local small business, formulating an automated email nurturing sequence and a high-converting keyword target map.",
        },
    }

    # 2. Input Processing & Normalization
    normalized_target = target_role.strip().lower()
    student_skills_list = [
        s.strip().lower() for s in current_skills_csv.split(",") if s.strip()
    ]

    # Fallback to standard baseline profile if role is unrecognized
    matched_key = "data analyst"  # Default fallback
    for role_key in ROLE_TAXONOMY.keys():
        if role_key in normalized_target or normalized_target in role_key:
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
            "capstone_portfolio_project": taxonomy["project_idea"],
        },
    }

    return json.dumps(response_data, indent=4)


# ==========================================
# TOOL 2: INTERACTIVE INTERVIEW SCENARIO GENERATOR
# ==========================================


@tool(
    name="generate_mock_interview_scenario",
    description=("Generates an immersive, highly customized interview roleplay context including "
                 "explicit dynamic reviewer personas, localized technical criteria, and an evaluation rubric. "
                 "Make sure you generate an audio file for the simulation after this tool calling."),
    approval_mode="never_require",
)
def generate_mock_interview_scenario(
    industry: Annotated[
        str,
        Field(
            description="The domain or corporate environment (e.g., 'Tech', 'Finance', 'Healthcare', 'Consulting')."
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
    """
    # 1. Comprehensive Question & Persona Matrix
    INTERVIEW_MATRIX = {
        "tech": {
            "persona": "Marcus, Director of Engineering at an enterprise infrastructure company known for structural precision and robust code reviews.",
            "Internship": [
                "Can you walk me through a technical challenge you faced in a class project, and explain how you managed version control issues with your peers?",
                "Explain the practical difference between an array and a linked list, and when you would use one over the other.",
            ],
            "Entry-Level": [
                "Describe a time you had to debug a production issue or persistent error under tight parameters. What was your systematic process?",
                "How do you ensure your code is maintainable, well-tested, and optimized for scalability when collaborating in sprint cycles?",
            ],
            "Mid-Level": [
                "We are looking at migrating from a monolith to a distributed microservices framework. Walk me through how you isolate scopes and maintain data state consistency.",
                "Describe a time you encountered massive scope creep or technical friction from cross-functional teams. How did you align architectural requirements?",
            ],
        },
        "finance": {
            "persona": "Victoria Vance, Managing Director of Global Asset Management, focused heavily on rapid mathematical processing, quantitative rigor, and regulatory compliance.",
            "Internship": [
                "Why are you looking to break into this specific division of financial services, and how do you handle tracking shifting market variables daily?",
                "Walk me through how you construct a basic discounted cash flow (DCF) model or analyze a corporate balance sheet.",
            ],
            "Entry-Level": [
                "Describe an experience where you discovered an inconsistency or error within data sheets or financial reports. How did you resolve it?",
                "If given a tight deadline with multiple conflicting analytical deliverables, how do you prioritize tasks and manage stakeholder risk?",
            ],
            "Mid-Level": [
                "Walk me through a complex portfolio strategy or quantitative thesis you formulated, detailing your underlying risk mitigation parameters.",
                "Detail an instance where you had to pitch a high-stakes, controversial financial asset allocation strategy to a highly skeptical investment board.",
            ],
        },
    }

    # 2. Normalization & Selection Logic
    norm_industry = industry.strip().lower()
    matched_ind = (
        "tech" if "tech" in norm_industry or "soft" in norm_industry else "finance"
    )

    valid_levels = ["Internship", "Entry-Level", "Mid-Level"]
    matched_level = (
        experience_level if experience_level in valid_levels else "Entry-Level"
    )

    industry_data = INTERVIEW_MATRIX[matched_ind]
    question_pool = industry_data[matched_level]

    # 3. Constructing Structural Schemas & Rubrics
    scenario_payload = {
        "session_config": {
            "interviewer_persona": industry_data["persona"],
            "target_experience_tier": matched_level,
            "asserted_industry_domain": matched_ind.upper(),
        },
        "assessment_prompts": {
            "icebreaker_question": f"Welcome. To begin, please give me a brief overview of your background and explain why you're targeting our organization today.",
            "core_behavioral_question": question_pool[0],
            "domain_specific_question": question_pool[1],
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
    description=("Constructs a complex, multi-layered workplace conflict, systemic failure, or prioritization crisis "
                 "to evaluate a student's situational judgement and soft skills. "
                 "Make sure you generate an audio file for the simulation after this tool calling."),
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
