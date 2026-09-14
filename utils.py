"""
utils.py
--------
Utility functions: input validation, plain-text report generation,
and general helper methods.
"""

from __future__ import annotations

from datetime import datetime
from models import Recommendation, ScreeningResult, ScoreBreakdown

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MIN_INPUT_LENGTH = 50  # Minimum characters considered meaningful content


def validate_job_description(text: str) -> str | None:
    """
    Validate the job description input.
    Returns an error message string, or None if the input is valid.
    """
    if not text or len(text.strip()) < MIN_INPUT_LENGTH:
        return "Please enter a valid job description before continuing."
    return None


def validate_resume(text: str) -> str | None:
    """
    Validate the candidate resume input.
    Returns an error message string, or None if the input is valid.
    """
    if not text or len(text.strip()) < MIN_INPUT_LENGTH:
        return "Please enter a valid candidate resume before screening."
    return None


# ---------------------------------------------------------------------------
# Text report generation
# ---------------------------------------------------------------------------

def _recommendation_label(rec: Recommendation) -> str:
    return rec.value


def _score_bar(score: float, width: int = 40) -> str:
    """Create a simple ASCII progress bar for the score."""
    filled = int(round(score / 100 * width))
    return f"[{'#' * filled}{'-' * (width - filled)}] {score:.1f}/100"


def generate_text_report(
    result: ScreeningResult,
    score_breakdown: ScoreBreakdown,
    job_description: str,
    candidate_resume: str,
) -> str:
    """
    Generate a complete plain-text recruiter report suitable for
    copying to clipboard or downloading as a .txt file.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []

    def section(title: str) -> None:
        lines.append("")
        lines.append("=" * 60)
        lines.append(title.upper())
        lines.append("=" * 60)

    def subsection(title: str) -> None:
        lines.append("")
        lines.append(f"--- {title} ---")

    # Header
    lines.append("=" * 60)
    lines.append("AI RESUME SCREENING AND CANDIDATE MATCHING AGENT")
    lines.append("Candidate Screening Report")
    lines.append(f"Generated: {now}")
    lines.append("=" * 60)

    # Score and recommendation
    section("Overall Match Score")
    lines.append(f"  {score_breakdown.final_score:.1f} out of 100")
    lines.append(f"  {_score_bar(score_breakdown.final_score)}")
    lines.append("")
    lines.append(f"  Recommendation: {_recommendation_label(result.recommendation)}")
    lines.append("")
    lines.append(
        "  This recommendation is intended to support recruiter review "
        "and is not an automatic hiring decision."
    )

    # Score breakdown
    section("Score Breakdown")
    lines.append(f"  Required Technical Skills (40%): {score_breakdown.required_skills_score:.1f}/100")
    lines.append(f"  Relevant Experience       (25%): {score_breakdown.experience_score:.1f}/100")
    lines.append(f"  Education                 (10%): {score_breakdown.education_score:.1f}/100")
    lines.append(f"  Projects / Practical Exp  (15%): {score_breakdown.projects_score:.1f}/100")
    lines.append(f"  Preferred Skills          (10%): {score_breakdown.preferred_skills_score:.1f}/100")
    lines.append(f"  ------------------------------------------")
    lines.append(f"  Final Weighted Score           : {score_breakdown.final_score:.1f}/100")

    # Requirement match table
    section("Requirement Match")
    header = f"  {'Requirement':<30} {'Category':<22} {'Status':<16} Evidence"
    lines.append(header)
    lines.append("  " + "-" * 100)
    for match in result.requirement_matches:
        req = match.requirement[:28]
        cat = match.category.value[:20]
        status = match.status.value[:14]
        evidence = match.evidence
        lines.append(f"  {req:<30} {cat:<22} {status:<16} {evidence}")

    # Key strengths
    section("Key Strengths")
    for strength in result.key_strengths:
        lines.append(f"  - {strength}")

    # Skill gaps
    section("Skill Gaps")
    for gap in result.skill_gaps:
        lines.append(f"  - {gap}")

    # Experience assessment
    section("Experience Assessment")
    exp = result.experience_assessment
    lines.append(f"  Required Experience  : {exp.required_experience}")
    lines.append(f"  Candidate Experience : {exp.candidate_experience}")
    lines.append(f"  Assessment           : {exp.assessment}")

    # Education and certification assessment
    section("Education and Certification Assessment")
    edu = result.education_assessment
    lines.append(f"  Required Education  : {edu.required_education}")
    lines.append(f"  Candidate Education : {edu.candidate_education}")
    if edu.certifications:
        lines.append(f"  Certifications      : {edu.certifications}")
    lines.append(f"  Assessment          : {edu.assessment}")

    # Projects
    section("Projects and Practical Experience")
    for project in result.projects_assessment:
        lines.append(f"  - {project}")

    # Potential concerns
    section("Potential Concerns")
    if result.potential_concerns:
        for concern in result.potential_concerns:
            lines.append(f"  - {concern}")
    else:
        lines.append("  No significant concerns identified.")

    # Evidence from resume
    section("Evidence from Resume")
    for item in result.evidence_from_resume:
        lines.append(f"  Requirement : {item.requirement}")
        lines.append(f"  Status      : {item.status.value}")
        lines.append(f"  Evidence    : {item.evidence}")
        lines.append("")

    # Recruiter summary
    section("Recruiter Summary")
    lines.append(f"  {result.recruiter_summary}")

    # Final recommendation
    section("Final Recommendation")
    lines.append(f"  Recommendation : {_recommendation_label(result.recommendation)}")
    lines.append(f"  Explanation    : {result.recommendation_explanation}")
    lines.append("")
    lines.append(
        "  This recommendation is intended to support recruiter review "
        "and is not an automatic hiring decision."
    )

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def get_status_color(status: str) -> str:
    """
    Map a match status string to a display CSS color hex for Streamlit.
    """
    mapping = {
        "Strong Match": "#1a6e3c",
        "Partial Match": "#7a5c00",
        "Not Found": "#8b1a1a",
    }
    return mapping.get(status, "#333333")


# ---------------------------------------------------------------------------
# PDF report generation
# ---------------------------------------------------------------------------

def generate_pdf_report(
    result: ScreeningResult,
    score_breakdown: ScoreBreakdown,
) -> bytes:
    """
    Generate a structured PDF screening report using fpdf2.

    Returns:
        PDF file content as bytes, ready to be served as a download.
    """
    from fpdf import FPDF

    # ---- Helpers ----
    def _safe(text: str) -> str:
        """Strip characters outside Latin-1 to keep fpdf2 happy."""
        return text.encode("latin-1", errors="replace").decode("latin-1")

    def _rec_label(rec: Recommendation) -> str:
        return rec.value if rec else "N/A"

    # ---- PDF setup ----
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(left=18, top=18, right=18)

    PAGE_W = pdf.w - 36  # usable width

    # ---- Document title ----
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(PAGE_W, 8, _safe("AI Resume Screening and Candidate Matching Agent"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(PAGE_W, 6, _safe("Candidate Screening Report"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(PAGE_W, 6, _safe(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    def section_heading(title: str) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(241, 243, 247)
        pdf.cell(PAGE_W, 7, _safe(title.upper()), ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.ln(1)

    def body_text(text: str, indent: float = 0) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(18 + indent)
        pdf.multi_cell(PAGE_W - indent, 5.5, _safe(text))

    def label_value(label: str, value: str) -> None:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(18)
        pdf.cell(42, 5.5, _safe(label + ":"), ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(PAGE_W - 42, 5.5, _safe(value))

    def bullet(text: str) -> None:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(22)
        pdf.multi_cell(PAGE_W - 4, 5.5, _safe("- " + text))

    # ---- Score and Recommendation ----
    section_heading("Overall Match Score")
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(PAGE_W, 12,
             _safe(f"{score_breakdown.final_score:.0f} / 100"),
             ln=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(PAGE_W, 7,
             _safe(f"Recommendation:  {_rec_label(result.recommendation)}"),
             ln=True, align="C")
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(PAGE_W, 5,
                   _safe("This recommendation is intended to support recruiter review "
                         "and is not an automatic hiring decision."), align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ---- Score Breakdown ----
    section_heading("Score Breakdown")
    rows = [
        ("Required Technical Skills", "40%", f"{score_breakdown.required_skills_score:.1f}"),
        ("Relevant Professional Experience", "25%", f"{score_breakdown.experience_score:.1f}"),
        ("Education", "10%", f"{score_breakdown.education_score:.1f}"),
        ("Projects and Practical Experience", "15%", f"{score_breakdown.projects_score:.1f}"),
        ("Preferred Skills", "10%", f"{score_breakdown.preferred_skills_score:.1f}"),
        ("Final Weighted Score", "100%", f"{score_breakdown.final_score:.1f}"),
    ]
    col_w = [PAGE_W * 0.55, PAGE_W * 0.15, PAGE_W * 0.30]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(249, 250, 251)
    for header, cw in zip(["Category", "Weight", "Score (0-100)"], col_w):
        pdf.cell(cw, 6, _safe(header), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i, (cat, wt, sc) in enumerate(rows):
        if i == len(rows) - 1:
            pdf.set_font("Helvetica", "B", 9)
        for val, cw in zip([cat, wt, sc], col_w):
            pdf.cell(cw, 5.5, _safe(val), border=1)
        pdf.ln()
    pdf.ln(3)

    # ---- Requirement Match ----
    section_heading("Requirement Match")
    col_w2 = [PAGE_W * 0.28, PAGE_W * 0.20, PAGE_W * 0.18, PAGE_W * 0.34]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(249, 250, 251)
    for header, cw in zip(["Requirement", "Category", "Status", "Evidence"], col_w2):
        pdf.cell(cw, 6, _safe(header), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for match in result.requirement_matches:
        # Track Y before row to draw multi-line cells properly
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        vals = [
            match.requirement,
            match.category.value,
            match.status.value,
            match.evidence,
        ]
        # Calculate max height needed
        max_lines = 1
        for val, cw in zip(vals, col_w2):
            n = max(1, len(val) // max(1, int(cw / 2.5)) + 1)
            max_lines = max(max_lines, n)
        row_h = max(5.5, max_lines * 4.5)
        for val, cw in zip(vals, col_w2):
            pdf.set_xy(x_start, y_start)
            pdf.multi_cell(cw, row_h / max(1, max_lines),
                           _safe(val[:120] + ("..." if len(val) > 120 else "")),
                           border=1)
            x_start += cw
        pdf.set_xy(18, y_start + row_h)
    pdf.ln(3)

    # ---- Key Strengths ----
    section_heading("Key Strengths")
    for s in result.key_strengths:
        bullet(s)
    pdf.ln(2)

    # ---- Skill Gaps ----
    section_heading("Skill Gaps")
    if result.skill_gaps:
        for g in result.skill_gaps:
            bullet(g)
    else:
        body_text("No significant skill gaps identified.")
    pdf.ln(2)

    # ---- Experience Assessment ----
    section_heading("Experience Assessment")
    exp = result.experience_assessment
    label_value("Required", exp.required_experience)
    label_value("Candidate", exp.candidate_experience)
    label_value("Assessment", exp.assessment)
    pdf.ln(2)

    # ---- Education and Certification Assessment ----
    section_heading("Education and Certification Assessment")
    edu = result.education_assessment
    label_value("Required", edu.required_education)
    label_value("Candidate", edu.candidate_education)
    if edu.certifications:
        label_value("Certifications", edu.certifications)
    label_value("Assessment", edu.assessment)
    pdf.ln(2)

    # ---- Projects and Practical Experience ----
    section_heading("Projects and Practical Experience")
    if result.projects_assessment:
        for p in result.projects_assessment:
            bullet(p)
    else:
        body_text("No relevant projects identified.")
    pdf.ln(2)

    # ---- Potential Concerns ----
    section_heading("Potential Concerns")
    if result.potential_concerns:
        for c in result.potential_concerns:
            bullet(c)
    else:
        body_text("No significant concerns identified.")
    pdf.ln(2)

    # ---- Evidence from Resume ----
    section_heading("Evidence from Resume")
    for item in result.evidence_from_resume:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(18)
        pdf.cell(PAGE_W, 5, _safe(f"{item.requirement}  [{item.status.value}]"), ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(22)
        pdf.multi_cell(PAGE_W - 4, 5, _safe(item.evidence))
        pdf.ln(1)
    pdf.ln(2)

    # ---- Recruiter Summary ----
    section_heading("Recruiter Summary")
    body_text(result.recruiter_summary)
    pdf.ln(2)

    # ---- Final Recommendation ----
    section_heading("Final Recommendation")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(PAGE_W, 7, _safe(f"Recommendation: {_rec_label(result.recommendation)}"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(PAGE_W, 5.5, _safe(result.recommendation_explanation or ""))
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(PAGE_W, 4.5,
                   _safe("This recommendation is intended to support recruiter review "
                         "and is not an automatic hiring decision."))
    pdf.set_text_color(0, 0, 0)

    return bytes(pdf.output())

