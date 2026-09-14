"""
ai_service.py
-------------
Isolated AI communication layer.
Sends job description and candidate resume to Google Gemini and returns
a raw parsed dict for downstream validation.

All AI provider interaction is confined to this module so that the
provider can be swapped without touching application logic.

Uses the current google-genai SDK (google.genai).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

# Ensure google-genai (new SDK) is preferred over google-generativeai (old SDK).
# Both packages share the 'google' namespace, which can cause import conflicts.
# Importing via importlib with explicit package path avoids the collision.
try:
    import importlib
    _genai_spec = importlib.util.find_spec("google.genai")
    if _genai_spec is None:
        raise ImportError("google-genai package not found")
    import google.genai as genai  # new SDK: pip install google-genai
except Exception as _e:
    raise ImportError(
        "Could not import google-genai. "
        "Please run: pip install google-genai>=1.0.0"
    ) from _e

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AI_API_KEY: str = os.getenv("AI_API_KEY", "")
AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an AI Resume Screening and Candidate Matching Assistant designed to support professional recruiters.

Your task is to objectively compare a candidate resume against a provided job description and produce a structured evidence based assessment.

First analyze the job description.
Extract required technical skills.
Extract preferred technical skills.
Extract required experience.
Extract preferred experience.
Extract education requirements.
Extract relevant certifications.
Extract important responsibilities.

Then analyze the candidate resume.
Extract technical skills.
Extract professional experience.
Extract internships.
Extract relevant projects.
Extract education.
Extract certifications.
Extract relevant achievements.

Compare the candidate evidence with the job requirements.
For every important requirement assign exactly one status.
Strong Match
Partial Match
Not Found

Use Strong Match only when the resume provides clear evidence that the candidate satisfies the requirement.
Use Partial Match when the resume provides some related evidence but does not fully demonstrate the requirement.
Use Not Found when the resume does not provide sufficient evidence.

Only use information explicitly supported by the resume.
Never invent skills.
Never invent experience.
Never invent employers.
Never invent job titles.
Never invent education.
Never invent certifications.
Never invent project results.
Never invent achievements.
Never invent numerical metrics.
If information is unavailable, classify it as Not Found.

Do not evaluate protected or non job related characteristics.
Ignore age, gender, religion, caste, race, ethnicity, marital status, photograph, physical appearance, disability, political affiliation, and similar personal characteristics.
Evaluate only job relevant evidence.

Return concise evidence for every important match decision.
Keep evidence factual and based on resume content.
Identify key strengths.
Identify important skill gaps.
Identify experience gaps.
Identify relevant education.
Identify relevant projects.
Identify potential concerns based only on job related information.
Generate a concise recruiter summary of approximately 80 to 120 words.

Do not calculate or include a final match score in your response.
Do not make the final hiring recommendation.
Maintain a neutral, professional, concise, and objective tone.
Do not use emojis.
Do not use decorative symbols.

Return ONLY valid JSON matching this exact structure (no markdown, no code fences, just raw JSON):

{
  "requirement_matches": [
    {
      "requirement": "string - the specific requirement",
      "category": "Required Skill | Preferred Skill | Experience | Education | Certification | Project Experience | Responsibility",
      "status": "Strong Match | Partial Match | Not Found",
      "evidence": "string - factual evidence from resume, or 'Not found in resume'"
    }
  ],
  "key_strengths": ["string", "string", "string"],
  "skill_gaps": ["string", "string"],
  "experience_assessment": {
    "required_experience": "string",
    "candidate_experience": "string",
    "assessment": "string"
  },
  "education_assessment": {
    "required_education": "string",
    "candidate_education": "string",
    "certifications": "string or null",
    "assessment": "string"
  },
  "projects_assessment": ["string", "string"],
  "potential_concerns": ["string"],
  "recruiter_summary": "string - 80 to 120 word professional summary",
  "evidence_from_resume": [
    {
      "requirement": "string",
      "category": "Required Skill",
      "status": "Strong Match | Partial Match | Not Found",
      "evidence": "string - direct evidence from the resume"
    }
  ]
}"""

# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------

def _build_user_prompt(job_description: str, candidate_resume: str) -> str:
    return (
        f"Job Description:\n{job_description.strip()}\n\n"
        f"Candidate Resume:\n{candidate_resume.strip()}\n\n"
        "Analyze the candidate resume against the job description and return the structured JSON assessment."
    )


# ---------------------------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> str:
    """
    Strip markdown code fences if the model wraps JSON in them,
    then return the cleaned JSON string.
    """
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_screening_analysis(job_description: str, candidate_resume: str) -> dict[str, Any]:
    """
    Send the job description and resume to the Gemini AI model and return the
    parsed response as a Python dict.

    Raises:
        RuntimeError: If the AI request fails or the response cannot be parsed.
    """
    if not AI_API_KEY:
        raise RuntimeError(
            "AI_API_KEY is not configured. "
            "Please set it in your .env file."
        )

    user_prompt = _build_user_prompt(job_description, candidate_resume)

    try:
        client = genai.Client(api_key=AI_API_KEY)

        response = client.models.generate_content(
            model=AI_MODEL,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        raw_text: str = response.text
        logger.debug("Raw AI response received (length=%d)", len(raw_text))

    except Exception as exc:
        logger.exception("AI API call failed: %s", exc)
        raise RuntimeError("The AI service did not respond. Please try again.") from exc

    # --- Parse JSON ---
    try:
        cleaned = _extract_json(raw_text)
        result: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse AI JSON response: %s\nRaw: %s", exc, raw_text[:500])
        raise RuntimeError(
            "The AI returned an unexpected response format. Please try again."
        ) from exc

    return result
