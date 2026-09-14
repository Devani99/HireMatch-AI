"""
models.py
---------
Pydantic data models for structured AI response validation.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MatchStatus(str, Enum):
    STRONG_MATCH = "Strong Match"
    PARTIAL_MATCH = "Partial Match"
    NOT_FOUND = "Not Found"


class RequirementCategory(str, Enum):
    REQUIRED_SKILL = "Required Skill"
    PREFERRED_SKILL = "Preferred Skill"
    EXPERIENCE = "Experience"
    EDUCATION = "Education"
    CERTIFICATION = "Certification"
    PROJECT_EXPERIENCE = "Project Experience"
    RESPONSIBILITY = "Responsibility"


class Recommendation(str, Enum):
    SHORTLIST = "SHORTLIST"
    REVIEW = "REVIEW"
    NOT_RECOMMENDED = "NOT RECOMMENDED"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class RequirementMatch(BaseModel):
    requirement: str = Field(..., description="The specific job requirement being evaluated")
    category: RequirementCategory = Field(..., description="Category of the requirement")
    status: MatchStatus = Field(..., description="Match status based on resume evidence")
    evidence: str = Field(..., description="Concise evidence from the resume, or 'Not found in resume'")


class ExperienceAssessment(BaseModel):
    required_experience: str = Field(..., description="Experience required by the job description")
    candidate_experience: str = Field(..., description="Experience found in the candidate resume")
    assessment: str = Field(..., description="Concise objective assessment")


class EducationAssessment(BaseModel):
    required_education: str = Field(..., description="Education required by the job description")
    candidate_education: str = Field(..., description="Education found in the candidate resume")
    certifications: Optional[str] = Field(None, description="Relevant certifications found")
    assessment: str = Field(..., description="Concise objective assessment")


# ---------------------------------------------------------------------------
# Main screening result model
# ---------------------------------------------------------------------------

class ScreeningResult(BaseModel):
    """
    Validated structured output from the AI screening analysis.
    Score and recommendation are computed by Python, not the AI.
    """

    # --- Requirement matches (AI-produced) ---
    requirement_matches: List[RequirementMatch] = Field(
        ...,
        description="List of every evaluated requirement with match status and evidence"
    )

    # --- Narrative sections (AI-produced) ---
    key_strengths: List[str] = Field(
        ...,
        min_length=1,
        description="Three to five concise candidate strengths relevant to the role"
    )
    skill_gaps: List[str] = Field(
        ...,
        description="Important skills or qualifications missing or only partially demonstrated"
    )
    experience_assessment: ExperienceAssessment
    education_assessment: EducationAssessment
    projects_assessment: List[str] = Field(
        ...,
        description="Relevant projects and practical experience found in the resume"
    )
    potential_concerns: List[str] = Field(
        ...,
        description="Job-relevant gaps or concerns based only on job-related evidence"
    )
    recruiter_summary: str = Field(
        ...,
        description="80-120 word professional summary explaining overall suitability"
    )
    evidence_from_resume: List[RequirementMatch] = Field(
        ...,
        description="Key requirement-evidence pairs drawn directly from the resume"
    )

    # --- Computed by Python (set after AI response is parsed) ---
    match_score: Optional[float] = Field(None, ge=0, le=100)
    recommendation: Optional[Recommendation] = None
    recommendation_explanation: Optional[str] = None


# ---------------------------------------------------------------------------
# Score breakdown model
# ---------------------------------------------------------------------------

class ScoreBreakdown(BaseModel):
    required_skills_score: float = Field(..., ge=0, le=100, description="Score for required technical skills (weight 40%)")
    experience_score: float = Field(..., ge=0, le=100, description="Score for relevant experience (weight 25%)")
    education_score: float = Field(..., ge=0, le=100, description="Score for education (weight 10%)")
    projects_score: float = Field(..., ge=0, le=100, description="Score for projects and practical experience (weight 15%)")
    preferred_skills_score: float = Field(..., ge=0, le=100, description="Score for preferred skills (weight 10%)")
    final_score: float = Field(..., ge=0, le=100, description="Weighted final score")

    @classmethod
    def weights(cls) -> dict:
        return {
            "required_skills_score": 0.40,
            "experience_score": 0.25,
            "education_score": 0.10,
            "projects_score": 0.15,
            "preferred_skills_score": 0.10,
        }
