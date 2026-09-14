"""
screening_service.py
--------------------
Deterministic scoring and recommendation logic.

The AI returns structured match data. Python computes the final numeric
score and recommendation — these are never delegated to the AI.
"""

from __future__ import annotations

import logging
from typing import Any

from models import (
    MatchStatus,
    Recommendation,
    RequirementCategory,
    ScreeningResult,
    ScoreBreakdown,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Credit per match status (proportion of full credit for that requirement)
STATUS_CREDIT = {
    MatchStatus.STRONG_MATCH: 1.0,
    MatchStatus.PARTIAL_MATCH: 0.5,
    MatchStatus.NOT_FOUND: 0.0,
}

# Map categories to score buckets
CATEGORY_BUCKET_MAP: dict[RequirementCategory, str] = {
    RequirementCategory.REQUIRED_SKILL: "required_skills",
    RequirementCategory.PREFERRED_SKILL: "preferred_skills",
    RequirementCategory.EXPERIENCE: "experience",
    RequirementCategory.EDUCATION: "education",
    RequirementCategory.CERTIFICATION: "education",        # certifications count toward education bucket
    RequirementCategory.PROJECT_EXPERIENCE: "projects",
    RequirementCategory.RESPONSIBILITY: "required_skills", # responsibilities assessed as skill overlap
}

# Weights (must sum to 1.0)
WEIGHTS = {
    "required_skills": 0.40,
    "experience": 0.25,
    "education": 0.10,
    "projects": 0.15,
    "preferred_skills": 0.10,
}


# ---------------------------------------------------------------------------
# Core scoring logic
# ---------------------------------------------------------------------------

def calculate_category_score(credits: list[float]) -> float:
    """
    Given a list of per-requirement credit values (0.0, 0.5, or 1.0),
    return a normalized 0-100 score for that category.
    Returns 0 if there are no requirements in the category.
    """
    if not credits:
        return 0.0
    return (sum(credits) / len(credits)) * 100.0


def calculate_weighted_score(breakdown: dict[str, list[float]]) -> ScoreBreakdown:
    """
    Compute category scores and the final weighted score.

    Args:
        breakdown: dict mapping bucket names to lists of credit values.

    Returns:
        ScoreBreakdown with per-category scores and final weighted score.
    """
    required_skills_score = calculate_category_score(breakdown.get("required_skills", []))
    experience_score = calculate_category_score(breakdown.get("experience", []))
    education_score = calculate_category_score(breakdown.get("education", []))
    projects_score = calculate_category_score(breakdown.get("projects", []))
    preferred_skills_score = calculate_category_score(breakdown.get("preferred_skills", []))

    final_score = (
        required_skills_score * WEIGHTS["required_skills"]
        + experience_score * WEIGHTS["experience"]
        + education_score * WEIGHTS["education"]
        + projects_score * WEIGHTS["projects"]
        + preferred_skills_score * WEIGHTS["preferred_skills"]
    )

    return ScoreBreakdown(
        required_skills_score=round(required_skills_score, 1),
        experience_score=round(experience_score, 1),
        education_score=round(education_score, 1),
        projects_score=round(projects_score, 1),
        preferred_skills_score=round(preferred_skills_score, 1),
        final_score=round(final_score, 1),
    )


def determine_recommendation(score: float) -> tuple[Recommendation, str]:
    """
    Apply score thresholds to derive the recommendation and explanation.

    Returns:
        (Recommendation enum, explanation string)
    """
    if score >= 80:
        return (
            Recommendation.SHORTLIST,
            (
                "The candidate demonstrates strong alignment with the key requirements of this role. "
                "The evidence in the resume supports progression to the next stage of the recruitment process."
            ),
        )
    elif score >= 60:
        return (
            Recommendation.REVIEW,
            (
                "The candidate meets several core requirements but has identifiable gaps in one or more areas. "
                "A recruiter review is recommended to assess whether these gaps are acceptable for this role."
            ),
        )
    else:
        return (
            Recommendation.NOT_RECOMMENDED,
            (
                "The candidate does not meet a sufficient number of the key requirements for this role "
                "based on the available resume evidence. Further review is at the recruiter's discretion."
            ),
        )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def compute_scores_and_recommendation(result: ScreeningResult) -> tuple[ScoreBreakdown, Recommendation, str]:
    """
    Given a parsed ScreeningResult (before score and recommendation are set),
    compute the score breakdown and recommendation.

    Returns:
        (ScoreBreakdown, Recommendation, explanation_string)
    """
    # Build per-bucket credit lists from requirement_matches
    breakdown: dict[str, list[float]] = {k: [] for k in WEIGHTS}

    for match in result.requirement_matches:
        bucket = CATEGORY_BUCKET_MAP.get(match.category, "required_skills")
        credit = STATUS_CREDIT.get(match.status, 0.0)
        breakdown[bucket].append(credit)

    score_breakdown = calculate_weighted_score(breakdown)
    recommendation, explanation = determine_recommendation(score_breakdown.final_score)

    return score_breakdown, recommendation, explanation


def parse_and_score(raw_dict: dict[str, Any]) -> tuple[ScreeningResult, ScoreBreakdown]:
    """
    Validate the raw AI response dict, compute scores, attach them to the
    ScreeningResult model, and return both.

    Raises:
        ValueError: If the AI response cannot be validated against the model.
    """
    try:
        result = ScreeningResult.model_validate(raw_dict)
    except Exception as exc:
        logger.exception("AI response validation failed: %s", exc)
        raise ValueError(
            "The AI returned a response that could not be validated. Please try again."
        ) from exc

    score_breakdown, recommendation, explanation = compute_scores_and_recommendation(result)

    # Attach computed values
    result.match_score = score_breakdown.final_score
    result.recommendation = recommendation
    result.recommendation_explanation = explanation

    return result, score_breakdown
