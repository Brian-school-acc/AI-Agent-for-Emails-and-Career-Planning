
import json
from agent_framework import tool
from random import choice

@tool(
    name="analyze_resume_skill_gaps",
    description="Compares a student's resume against a target job description or industry standard to identify missing skills.",
    approval_mode="never_require",
)
def analyze_resume_skill_gaps(target_role: str, current_skills_csv: str) -> str:
    """
    Analyze skill gaps for a specific career path.
    Args:
        target_role: The job title the student wants (e.g., 'Data Analyst').
        current_skills_csv: A comma-separated list of the student's current skills.
    """
    # Mock analysis response
    return json.dumps(
        {
            "role": target_role,
            "matched_skills": ["Python", "Communication"],
            "missing_skills": ["SQL", "Tableau", "Agile Methodologies"],
            "recommendation": "Consider taking a beginner SQL course or building a small Tableau dashboard project.",
        }
    )


@tool(
    name="generate_mock_interview_scenario",
    description="Generates a customized, interactive mock interview scenario complete with a persona and behavioral questions.",
    approval_mode="never_require",
)
def generate_mock_interview_scenario(
    industry: str, experience_level: str = "Internship"
) -> str:
    """
    Setup a mock interview roleplay environment.
    Args:
        industry: The field of work (e.g., 'Finance', 'Tech', 'Marketing').
        experience_level: 'Internship', 'Entry-Level', or 'Mid-Level'.
    """
    questions = [
        "Tell me about a time you had to adapt to a sudden change in a project.",
        f"Why are you interested in pursuing {industry}?",
        "Describe a time you worked with a difficult team member.",
    ]
    return json.dumps(
        {
            "interviewer_persona": f"Senior Manager in {industry}",
            "scenario_context": f"You are interviewing for an {experience_level} position.",
            "starting_question": choice(questions),
        }
    )
