"""
app.py
------
AI Resume Screening and Candidate Matching Agent
Streamlit application entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import logging

import streamlit as st
from dotenv import load_dotenv

from ai_service import run_screening_analysis
from models import Recommendation, ScreeningResult, ScoreBreakdown
from pdf_service import (
    MAX_FILE_SIZE_LABEL,
    PdfExtractionResult,
    extract_pdf_text,
    format_file_info,
    validate_pdf_upload,
)
from screening_service import parse_and_score
from utils import generate_text_report, generate_pdf_report

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Resume Screening and Candidate Matching Agent",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — professional, minimal, no decorative elements
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ---- Global ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Page background */
    .stApp {
        background-color: #F4F5F7;
    }

    /* Remove default Streamlit padding at top */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 860px;
    }

    /* ---- Application header ---- */
    .app-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .app-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.95rem;
        color: #6B7280;
        margin-bottom: 0;
    }

    /* ---- Step indicator ---- */
    .step-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin-bottom: 2rem;
        padding: 0;
    }
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        min-width: 140px;
    }
    .step-number {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        border: 2px solid #D1D5DB;
        background-color: #F4F5F7;
        color: #9CA3AF;
        margin-bottom: 0.4rem;
        transition: all 0.2s ease;
    }
    .step-number.active {
        border-color: #1E3A5F;
        background-color: #1E3A5F;
        color: #FFFFFF;
    }
    .step-number.completed {
        border-color: #1E3A5F;
        background-color: #1E3A5F;
        color: #FFFFFF;
    }
    .step-label {
        font-size: 0.78rem;
        font-weight: 500;
        color: #9CA3AF;
        text-align: center;
    }
    .step-label.active {
        color: #1E3A5F;
        font-weight: 600;
    }
    .step-label.completed {
        color: #1E3A5F;
    }
    .step-connector {
        flex: 1;
        height: 2px;
        background-color: #D1D5DB;
        margin-bottom: 1.4rem;
        max-width: 80px;
    }
    .step-connector.completed {
        background-color: #1E3A5F;
    }

    /* ---- Content card ---- */
    .content-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }

    /* ---- Section headings ---- */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }
    .section-description {
        font-size: 0.875rem;
        color: #6B7280;
        margin-bottom: 1.2rem;
    }

    /* ---- Step progress label ---- */
    .step-progress-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* ---- Character counter ---- */
    .char-count {
        font-size: 0.78rem;
        color: #9CA3AF;
        text-align: right;
        margin-top: 0.25rem;
    }

    /* ---- Score display ---- */
    .score-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 1.75rem 2rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .score-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .score-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        line-height: 1;
    }
    .score-max {
        font-size: 1rem;
        font-weight: 400;
        color: #6B7280;
    }

    /* Score progress bar */
    .score-bar-track {
        background: #E5E7EB;
        border-radius: 4px;
        height: 8px;
        width: 100%;
        margin-top: 0.5rem;
    }
    .score-bar-fill {
        height: 8px;
        border-radius: 4px;
        background-color: #1E3A5F;
        transition: width 0.4s ease;
    }

    /* ---- Recommendation badge ---- */
    .recommendation-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .rec-shortlist {
        background-color: #DCFCE7;
        color: #14532D;
        border: 1px solid #BBF7D0;
    }
    .rec-review {
        background-color: #FEF9C3;
        color: #713F12;
        border: 1px solid #FDE68A;
    }
    .rec-not-recommended {
        background-color: #FEE2E2;
        color: #7F1D1D;
        border: 1px solid #FECACA;
    }

    /* ---- Match status badges ---- */
    .match-strong {
        color: #14532D;
        background: #DCFCE7;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .match-partial {
        color: #713F12;
        background: #FEF9C3;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .match-not-found {
        color: #7F1D1D;
        background: #FEE2E2;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        white-space: nowrap;
    }

    /* ---- Evidence pair ---- */
    .evidence-item {
        border-left: 3px solid #1E3A5F;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        background: #F8FAFC;
        border-radius: 0 4px 4px 0;
    }
    .evidence-req {
        font-size: 0.82rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.2rem;
    }
    .evidence-text {
        font-size: 0.82rem;
        color: #4B5563;
        margin-bottom: 0;
    }

    /* ---- Assessment grid ---- */
    .assess-row {
        display: grid;
        grid-template-columns: 160px 1fr;
        gap: 0.5rem 1rem;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
    }
    .assess-label {
        font-weight: 600;
        color: #374151;
    }
    .assess-value {
        color: #4B5563;
    }

    /* ---- Divider ---- */
    .section-divider {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 1.5rem 0;
    }

    /* ---- Disclaimer ---- */
    .disclaimer-text {
        font-size: 0.78rem;
        color: #6B7280;
        padding: 0.6rem 0.75rem;
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 4px;
        margin-top: 0.5rem;
    }

    /* ---- Loading card ---- */
    .loading-card {
        text-align: center;
        padding: 2.5rem 1rem;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        font-size: 0.95rem;
        color: #374151;
        font-weight: 500;
    }

    /* ---- Error card ---- */
    .error-card {
        padding: 1rem 1.25rem;
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 6px;
        color: #7F1D1D;
        font-size: 0.875rem;
        font-weight: 500;
    }

    /* ---- Streamlit tweaks ---- */
    /* File uploader styling */
    div[data-testid="stFileUploader"] {
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        background: #FFFFFF;
        padding: 0.25rem;
    }
    div[data-testid="stFileUploader"]:focus-within {
        border-color: #1E3A5F;
        box-shadow: 0 0 0 3px rgba(30,58,95,0.08);
    }

    /* File info card */
    .file-info-card {
        background: #F8FAFC;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-top: 0.75rem;
        font-size: 0.85rem;
    }
    .file-info-row {
        display: grid;
        grid-template-columns: 120px 1fr;
        gap: 0.2rem 0.75rem;
        margin-bottom: 0.1rem;
    }
    .file-info-label {
        font-weight: 600;
        color: #374151;
    }
    .file-info-value {
        color: #4B5563;
        word-break: break-all;
    }
    .file-status-ready {
        color: #14532D;
        font-weight: 600;
    }
    .upload-hint {
        font-size: 0.78rem;
        color: #6B7280;
        margin-top: 0.4rem;
    }

    .stButton > button {
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #1E3A5F;
        border: 1px solid #1E3A5F;
        color: #FFFFFF;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #163050;
        border-color: #163050;
    }

    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF;
        border: 1px solid #D1D5DB;
        color: #374151;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #F9FAFB;
        border-color: #9CA3AF;
        color: #111827;
    }

    /* Download button — Streamlit renders this as stDownloadButton, not stButton */
    div[data-testid="stDownloadButton"] > button {
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        width: 100%;
        background-color: #1E3A5F;
        border: 1px solid #1E3A5F;
        color: #FFFFFF !important;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #163050 !important;
        border-color: #163050 !important;
        color: #FFFFFF !important;
    }

    /* Hide Streamlit header, footer, menu */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        overflow: hidden;
    }

    /* Score breakdown table */
    .breakdown-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
        margin-top: 0.75rem;
    }
    .breakdown-table th {
        text-align: left;
        padding: 0.5rem 0.75rem;
        background: #F9FAFB;
        border-bottom: 1px solid #E5E7EB;
        font-weight: 600;
        color: #374151;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .breakdown-table td {
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid #F3F4F6;
        color: #4B5563;
        vertical-align: top;
    }
    .breakdown-table tr:last-child td {
        border-bottom: none;
        font-weight: 600;
        color: #111827;
        background: #F8FAFC;
    }

    /* Responsive */
    @media (max-width: 640px) {
        .step-indicator { flex-direction: column; gap: 0.25rem; }
        .step-connector { display: none; }
        .step-item { min-width: unset; }
        .block-container { padding: 1.5rem 1rem; }
        .app-title { font-size: 1.25rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    defaults = {
        "step": 1,
        # Extracted text strings passed to AI
        "job_description": "",          # extracted text from JD PDF
        "candidate_resume": "",          # extracted text from resume PDF
        # PDF file metadata (display only, not persisted across reruns)
        "jd_pdf_name": "",
        "jd_pdf_size": "",
        "resume_pdf_name": "",
        "resume_pdf_size": "",
        # Results
        "screening_result": None,       # ScreeningResult | None
        "score_breakdown": None,        # ScoreBreakdown | None
        "text_report": None,            # str | None
        "error": None,                  # str | None
        "retry": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# ---------------------------------------------------------------------------
# Helper renderers
# ---------------------------------------------------------------------------

def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
            <div class="app-title">AI Resume Screening and Candidate Matching Agent</div>
            <div class="app-subtitle">
                Compare a candidate resume with job requirements and generate an evidence based screening report.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_indicator(current_step: int) -> None:
    steps = ["Job Description", "Candidate Resume", "Screening Result"]
    html_parts: list[str] = ['<div class="step-indicator">']

    for i, label in enumerate(steps, start=1):
        if i < current_step:
            number_class = "completed"
            label_class = "completed"
        elif i == current_step:
            number_class = "active"
            label_class = "active"
        else:
            number_class = ""
            label_class = ""

        html_parts.append(f"""
        <div class="step-item">
            <div class="step-number {number_class}">{i}</div>
            <div class="step-label {label_class}">{label}</div>
        </div>
        """)

        if i < len(steps):
            connector_class = "completed" if i < current_step else ""
            html_parts.append(f'<div class="step-connector {connector_class}"></div>')

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_error(message: str) -> None:
    st.markdown(
        f'<div class="error-card">{message}</div>',
        unsafe_allow_html=True,
    )


def recommendation_badge_html(rec: Recommendation) -> str:
    css_class = {
        Recommendation.SHORTLIST: "rec-shortlist",
        Recommendation.REVIEW: "rec-review",
        Recommendation.NOT_RECOMMENDED: "rec-not-recommended",
    }.get(rec, "")
    return f'<span class="recommendation-badge {css_class}">{rec.value}</span>'


def status_badge_html(status: str) -> str:
    css_class = {
        "Strong Match": "match-strong",
        "Partial Match": "match-partial",
        "Not Found": "match-not-found",
    }.get(status, "")
    return f'<span class="{css_class}">{status}</span>'


def _file_info_html(info: dict) -> str:
    """Build an HTML file-info card from a file metadata dict."""
    rows = []
    for label, value in info.items():
        extra_class = " file-status-ready" if label == "Status" else ""
        rows.append(
            '<div class="file-info-row">'
            f'<div class="file-info-label">{label}</div>'
            f'<div class="file-info-value{extra_class}">{value}</div>'
            "</div>"
        )
    return '<div class="file-info-card">' + "".join(rows) + "</div>"


# ---------------------------------------------------------------------------
# Step 1 — Job Description
# ---------------------------------------------------------------------------

def render_step1() -> None:
    st.markdown(
        '<div class="step-progress-label">Step 1 of 3 &mdash; Job Description</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-title">Job Description</div>
        <div class="section-description">
            Upload the job description as a PDF file.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="upload-hint">PDF files only &nbsp;|&nbsp; Maximum file size: {MAX_FILE_SIZE_LABEL}</div>',
        unsafe_allow_html=True,
    )

    jd_file = st.file_uploader(
        label="Upload Job Description",
        type=["pdf"],
        accept_multiple_files=False,
        key="jd_uploader",
        help=f"PDF files only. Maximum size: {MAX_FILE_SIZE_LABEL}.",
    )

    # Show file info card if a file is selected
    if jd_file is not None:
        validation_error = validate_pdf_upload(jd_file)
        if validation_error:
            render_error(validation_error)
        else:
            info = format_file_info(jd_file)
            st.markdown(_file_info_html(info), unsafe_allow_html=True)

    # Validation error banner
    if st.session_state.error == "jd_no_file":
        render_error("Please upload the job description PDF before continuing.")
    elif st.session_state.error == "jd_pdf_error":
        render_error(st.session_state.get("error_detail", "The uploaded file could not be read. Please upload a valid PDF."))

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    if st.button("Continue", type="primary", use_container_width=False):
        if jd_file is None:
            st.session_state.error = "jd_no_file"
            st.rerun()
        else:
            validation_error = validate_pdf_upload(jd_file)
            if validation_error:
                st.session_state.error = "jd_pdf_error"
                st.session_state["error_detail"] = validation_error
                st.rerun()
            else:
                extraction: PdfExtractionResult = extract_pdf_text(jd_file)
                if not extraction.success:
                    st.session_state.error = "jd_pdf_error"
                    st.session_state["error_detail"] = extraction.error
                    st.rerun()
                else:
                    st.session_state.job_description = extraction.text
                    st.session_state.jd_pdf_name = jd_file.name
                    info = format_file_info(jd_file)
                    st.session_state.jd_pdf_size = info["File size"]
                    st.session_state.error = None
                    st.session_state["error_detail"] = ""
                    st.session_state.step = 2
                    st.rerun()


# ---------------------------------------------------------------------------
# Step 2 — Candidate Resume
# ---------------------------------------------------------------------------

def render_step2() -> None:
    st.markdown(
        '<div class="step-progress-label">Step 2 of 3 &mdash; Candidate Resume</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="section-title">Candidate Resume</div>
        <div class="section-description">
            Upload the candidate resume as a PDF file.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show which JD was accepted (carried forward from Step 1)
    if st.session_state.jd_pdf_name:
        st.markdown(
            f'<div class="upload-hint">Job description loaded: '
            f'<strong>{st.session_state.jd_pdf_name}</strong> '
            f'({st.session_state.jd_pdf_size})</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="upload-hint">PDF files only &nbsp;|&nbsp; Maximum file size: {MAX_FILE_SIZE_LABEL}</div>',
        unsafe_allow_html=True,
    )

    resume_file = st.file_uploader(
        label="Upload Candidate Resume",
        type=["pdf"],
        accept_multiple_files=False,
        key="resume_uploader",
        help=f"PDF files only. Maximum size: {MAX_FILE_SIZE_LABEL}.",
    )

    # Show file info card if a file is selected
    if resume_file is not None:
        validation_error = validate_pdf_upload(resume_file)
        if validation_error:
            render_error(validation_error)
        else:
            info = format_file_info(resume_file)
            st.markdown(_file_info_html(info), unsafe_allow_html=True)

    # Validation and AI failure error banners
    if st.session_state.error == "resume_no_file":
        render_error("Please upload the candidate resume PDF before screening.")
    elif st.session_state.error == "resume_pdf_error":
        render_error(st.session_state.get("error_detail", "The uploaded file could not be read. Please upload a valid PDF."))
    elif st.session_state.error == "ai_failure":
        render_error("The screening could not be completed. Please try again.")

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    col_back, col_screen = st.columns([1, 3])

    with col_back:
        if st.button("Back", type="secondary", use_container_width=True):
            st.session_state.error = None
            st.session_state.step = 1
            st.rerun()

    with col_screen:
        if st.button("Screen Candidate", type="primary", use_container_width=True):
            if resume_file is None:
                st.session_state.error = "resume_no_file"
                st.rerun()
            else:
                validation_error = validate_pdf_upload(resume_file)
                if validation_error:
                    st.session_state.error = "resume_pdf_error"
                    st.session_state["error_detail"] = validation_error
                    st.rerun()
                else:
                    extraction: PdfExtractionResult = extract_pdf_text(resume_file)
                    if not extraction.success:
                        st.session_state.error = "resume_pdf_error"
                        st.session_state["error_detail"] = extraction.error
                        st.rerun()
                    else:
                        st.session_state.candidate_resume = extraction.text
                        st.session_state.resume_pdf_name = resume_file.name
                        info = format_file_info(resume_file)
                        st.session_state.resume_pdf_size = info["File size"]
                        st.session_state.error = None
                        st.session_state["error_detail"] = ""
                        run_screening(extraction.text)


def run_screening(resume_text: str) -> None:
    """Invoke AI analysis and compute scores. Called from Step 2."""
    with st.spinner("Analyzing candidate profile"):
        try:
            raw = run_screening_analysis(
                job_description=st.session_state.job_description,
                candidate_resume=resume_text,
            )
            result, score_breakdown = parse_and_score(raw)
            text_report = generate_text_report(
                result=result,
                score_breakdown=score_breakdown,
                job_description=st.session_state.job_description,
                candidate_resume=resume_text,
            )

            st.session_state.screening_result = result
            st.session_state.score_breakdown = score_breakdown
            st.session_state.text_report = text_report
            st.session_state.error = None
            st.session_state.step = 3
            st.rerun()

        except RuntimeError as exc:
            logger.error("Screening failed: %s", exc)
            st.session_state.error = "ai_failure"
            st.rerun()
        except Exception as exc:
            logger.exception("Unexpected error during screening: %s", exc)
            st.session_state.error = "ai_failure"
            st.rerun()


# ---------------------------------------------------------------------------
# Step 3 — Screening Result
# ---------------------------------------------------------------------------

def render_step3() -> None:
    result: ScreeningResult = st.session_state.screening_result
    score_breakdown: ScoreBreakdown = st.session_state.score_breakdown

    if result is None or score_breakdown is None:
        render_error("No screening result available. Please start a new screening.")
        if st.button("Start New Screening", type="primary"):
            reset_session()
        return

    st.markdown(
        '<div class="step-progress-label">Step 3 of 3 — Screening Result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-title">Candidate Screening Report</div>',
        unsafe_allow_html=True,
    )

    # ---- Score and Recommendation ----
    score = score_breakdown.final_score
    bar_width = int(score)

    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-label">Overall Match Score</div>
            <div class="score-value">{score:.0f} <span class="score-max">out of 100</span></div>
            <div class="score-bar-track">
                <div class="score-bar-fill" style="width:{bar_width}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rec_html = recommendation_badge_html(result.recommendation)
    st.markdown(
        f"""
        <div style="margin-bottom:0.5rem;">
            <span style="font-size:0.8rem;font-weight:600;color:#6B7280;
                         text-transform:uppercase;letter-spacing:0.05em;
                         margin-right:0.75rem;">Recommendation</span>
            {rec_html}
        </div>
        <div class="disclaimer-text">
            This recommendation is intended to support recruiter review and is not an automatic hiring decision.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Score Breakdown ----
    with st.expander("Score Breakdown", expanded=False):
        breakdown_rows = [
            ("Required Technical Skills", "40%", f"{score_breakdown.required_skills_score:.1f}"),
            ("Relevant Professional Experience", "25%", f"{score_breakdown.experience_score:.1f}"),
            ("Education", "10%", f"{score_breakdown.education_score:.1f}"),
            ("Projects and Practical Experience", "15%", f"{score_breakdown.projects_score:.1f}"),
            ("Preferred Skills", "10%", f"{score_breakdown.preferred_skills_score:.1f}"),
        ]
        rows_html = "".join(
            f"<tr><td>{cat}</td><td>{weight}</td><td><strong>{score_val}</strong></td></tr>"
            for cat, weight, score_val in breakdown_rows
        )
        st.markdown(
            f"""
            <table class="breakdown-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Weight</th>
                        <th>Category Score (0-100)</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                    <tr>
                        <td>Final Weighted Score</td>
                        <td>100%</td>
                        <td>{score:.1f}</td>
                    </tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ---- Requirement Match Table ----
    st.markdown('<div class="section-title">Requirement Match</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)

    if result.requirement_matches:
        import pandas as pd

        rows = []
        for match in result.requirement_matches:
            rows.append(
                {
                    "Requirement": match.requirement,
                    "Category": match.category.value,
                    "Match Status": match.status.value,
                    "Evidence": match.evidence,
                }
            )
        df = pd.DataFrame(rows)

        def color_status(val: str) -> str:
            colors = {
                "Strong Match": "background-color:#DCFCE7;color:#14532D;font-weight:600;",
                "Partial Match": "background-color:#FEF9C3;color:#713F12;font-weight:600;",
                "Not Found": "background-color:#FEE2E2;color:#7F1D1D;font-weight:600;",
            }
            return colors.get(val, "")

        styled = df.style.map(color_status, subset=["Match Status"])
        st.dataframe(styled, width="stretch", hide_index=True)
    else:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.875rem;">No requirement match data available.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ---- Key Strengths ----
    st.markdown('<div class="section-title">Key Strengths</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    for strength in result.key_strengths:
        st.markdown(
            f'<p style="font-size:0.875rem;color:#374151;margin:0.3rem 0;padding-left:0.75rem;'
            f'border-left:2px solid #1E3A5F;">- {strength}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Skill Gaps ----
    st.markdown('<div class="section-title">Skill Gaps</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    if result.skill_gaps:
        for gap in result.skill_gaps:
            st.markdown(
                f'<p style="font-size:0.875rem;color:#374151;margin:0.3rem 0;padding-left:0.75rem;'
                f'border-left:2px solid #D1D5DB;">- {gap}</p>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.875rem;">No significant skill gaps identified.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Experience Assessment ----
    st.markdown('<div class="section-title">Experience Assessment</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    exp = result.experience_assessment
    st.markdown(
        f"""
        <div class="assess-row"><div class="assess-label">Required Experience</div><div class="assess-value">{exp.required_experience}</div></div>
        <div class="assess-row"><div class="assess-label">Candidate Experience</div><div class="assess-value">{exp.candidate_experience}</div></div>
        <div class="assess-row"><div class="assess-label">Assessment</div><div class="assess-value">{exp.assessment}</div></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Education and Certification Assessment ----
    st.markdown(
        '<div class="section-title">Education and Certification Assessment</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    edu = result.education_assessment
    cert_row = (
        f'<div class="assess-row"><div class="assess-label">Certifications</div>'
        f'<div class="assess-value">{edu.certifications}</div></div>'
        if edu.certifications
        else ""
    )
    st.markdown(
        f"""
        <div class="assess-row"><div class="assess-label">Required Education</div><div class="assess-value">{edu.required_education}</div></div>
        <div class="assess-row"><div class="assess-label">Candidate Education</div><div class="assess-value">{edu.candidate_education}</div></div>
        {cert_row}
        <div class="assess-row"><div class="assess-label">Assessment</div><div class="assess-value">{edu.assessment}</div></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Projects and Practical Experience ----
    st.markdown(
        '<div class="section-title">Projects and Practical Experience</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    if result.projects_assessment:
        for project in result.projects_assessment:
            st.markdown(
                f'<p style="font-size:0.875rem;color:#374151;margin:0.4rem 0;">{project}</p>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.875rem;">No relevant projects identified in the resume.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Potential Concerns ----
    st.markdown('<div class="section-title">Potential Concerns</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    if result.potential_concerns:
        for concern in result.potential_concerns:
            st.markdown(
                f'<p style="font-size:0.875rem;color:#374151;margin:0.3rem 0;">{concern}</p>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.875rem;">No significant concerns identified.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Recruiter Summary ----
    st.markdown('<div class="section-title">Recruiter Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.875rem;color:#374151;line-height:1.7;margin-top:0.5rem;">'
        f'{result.recruiter_summary}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Evidence from Resume ----
    st.markdown('<div class="section-title">Evidence from Resume</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    if result.evidence_from_resume:
        for item in result.evidence_from_resume:
            badge = status_badge_html(item.status.value)
            st.markdown(
                f"""
                <div class="evidence-item">
                    <div class="evidence-req">{item.requirement} &nbsp; {badge}</div>
                    <div class="evidence-text">{item.evidence}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.875rem;">No evidence pairs available.</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ---- Final Recommendation ----
    st.markdown('<div class="section-title">Final Recommendation</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:0.75rem;'></div>", unsafe_allow_html=True)
    rec_html = recommendation_badge_html(result.recommendation)
    st.markdown(
        f"""
        {rec_html}
        <p style="font-size:0.875rem;color:#374151;margin-top:0.75rem;line-height:1.6;">
            {result.recommendation_explanation}
        </p>
        <div class="disclaimer-text">
            This recommendation is intended to support recruiter review and is not an automatic hiring decision.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)

    # ---- Action Buttons ----
    col_new, col_download = st.columns([1, 1])

    with col_new:
        if st.button("Start New Screening", type="secondary", use_container_width=True):
            reset_session()

    with col_download:
        pdf_bytes = generate_pdf_report(
            result=result,
            score_breakdown=score_breakdown,
        )
        st.download_button(
            label="Download Report",
            data=pdf_bytes,
            file_name="candidate_screening_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)

    # Copy report (displays in expander so user can select-all and copy)
    with st.expander("View Full Report Text (for copying)"):
        text_report = st.session_state.text_report or ""
        st.code(text_report, language=None)


# ---------------------------------------------------------------------------
# Session reset
# ---------------------------------------------------------------------------

def reset_session() -> None:
    keys_to_clear = [
        "step",
        "job_description",
        "candidate_resume",
        "jd_pdf_name",
        "jd_pdf_size",
        "resume_pdf_name",
        "resume_pdf_size",
        "screening_result",
        "score_breakdown",
        "text_report",
        "error",
        "error_detail",
        "retry",
        # Clear Streamlit file uploader widget state so new files can be selected
        "jd_uploader",
        "resume_uploader",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ---------------------------------------------------------------------------
# Main rendering router
# ---------------------------------------------------------------------------

def main() -> None:
    render_header()
    render_step_indicator(st.session_state.step)

    st.markdown('<div class="content-card">', unsafe_allow_html=True)

    if st.session_state.step == 1:
        render_step1()
    elif st.session_state.step == 2:
        render_step2()
    elif st.session_state.step == 3:
        render_step3()
    else:
        render_error("An unexpected error occurred. Please start a new screening.")
        if st.button("Start New Screening", type="primary"):
            reset_session()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
