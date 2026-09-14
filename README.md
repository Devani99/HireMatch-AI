# AI Resume Screening and Candidate Matching Agent

A professional AI-powered recruitment screening tool built with Python and Streamlit. Recruiters upload a job description PDF and a candidate resume PDF. The application extracts the text, sends it to Google Gemini for structured analysis, and displays an evidence-based screening report in three simple steps.

---

### Live Demo Link - https://hirematch-ai-o3hgm6xxsywmagrgkypow2.streamlit.app/

---

## Features

- Three-step workflow: Upload Job Description PDF -> Upload Resume PDF -> Screening Report
- PDF text extraction using pypdf (text-based PDFs required)
- Evidence-based evaluation — AI only reports what is explicitly in the resume
- Transparent, deterministic scoring calculated in Python (not by the AI)
- Structured requirement match table with Strong Match / Partial Match / Not Found
- Key strengths, skill gaps, experience and education assessment
- Concise recruiter summary
- Downloadable plain-text report
- No protected characteristics evaluated (age, gender, religion, caste, etc.)
- Professional, minimal interface with no emojis or decorative symbols

---

## Technology Stack

| Component        | Technology                    |
|-----------------|-------------------------------|
| Interface        | Streamlit                     |
| AI Provider      | Google Gemini (gemini-3.5-flash-lite) |
| PDF Extraction   | pypdf                         |
| Data Validation  | Pydantic v2                   |
| Language         | Python 3.10+                  |
| Config           | python-dotenv                 |

---

## Installation

```bash
# 1. Clone the repository or navigate to the project folder
cd ai_resume_analyze

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Environment Variable Setup

```bash
# Copy the example file
copy .env.example .env    # Windows
# cp .env.example .env   # macOS / Linux

# Edit .env and add your Gemini API key
AI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

---

## How to Run

```bash
streamlit run app.py
```

The application opens at `http://localhost:8501` in your browser.

---

## Project Structure

```
ai_resume_analyze/
├── app.py              # Streamlit UI (step routing, rendering, CSS)
├── ai_service.py       # Google Gemini integration (isolated)
├── screening_service.py # Deterministic scoring + recommendation
├── pdf_service.py      # PDF validation and text extraction
├── models.py           # Pydantic v2 models for AI response validation
├── utils.py            # Input validation, text report generation
├── requirements.txt    # 6 dependencies
├── .env.example        # API key template
└── README.md           # This file
```

## PDF Upload Requirements

| Property              | Requirement              |
|-----------------------|--------------------------|
| Supported file type   | PDF only                 |
| Maximum file size     | 5 MB per file            |
| Job Description PDF   | Required (one file)      |
| Candidate Resume PDF  | Required (one file)      |
| Text-based PDFs       | Supported                |
| Scanned image PDFs    | Not supported (no OCR)   |
| Password-protected    | Not supported            |

The application extracts text from both uploaded PDFs using **pypdf** before sending the content to the AI screening service. If a PDF contains no extractable text (e.g., it is a scanned image), the upload will be rejected with a clear message. OCR is not implemented.

---

## Scoring Methodology

The match score is calculated entirely in Python using the following category weights:

| Category                         | Weight |
|----------------------------------|--------|
| Required Technical Skills         | 40%    |
| Relevant Professional Experience  | 25%    |
| Projects and Practical Experience | 15%    |
| Education                         | 10%    |
| Preferred Skills                  | 10%    |

**Per-requirement credit:**
- Strong Match → 100% credit for that requirement
- Partial Match → 50% credit for that requirement
- Not Found → 0% credit for that requirement

Each category score is normalized (0–100) before applying the weight. The final score is the weighted sum across all categories.

**Recommendation thresholds (applied by Python):**

| Score Range | Recommendation   |
|-------------|------------------|
| 80 – 100    | SHORTLIST        |
| 60 – 79     | REVIEW           |
| 0 – 59      | NOT RECOMMENDED  |

---

## AI Safety and Fairness Notes

- The AI is instructed never to invent skills, experience, education, certifications, employers, or achievements.
- If information is not present in the resume, requirements are classified as Not Found.
- Protected personal characteristics (age, gender, religion, caste, race, ethnicity, marital status, disability, political affiliation, etc.) are explicitly excluded from the evaluation.
- The final score and recommendation are computed deterministically by Python, not chosen by the AI.
- The recommendation is presented as recruiter decision support, not as an automatic hiring decision.

---

## Demo Test Case

**Job Role:** Data Scientist Intern

**Required Skills:** Python, SQL, Machine Learning, Statistics, Pandas, NumPy
**Preferred Skills:** Scikit-learn, Power BI, AWS
**Education:** Bachelor's degree in Computer Science, Data Science, AI, or related field
**Experience:** Internship or project experience in Data Science or Machine Learning

**Sample Candidate (Rahul Sharma):**
- Education: B.Tech in Computer Science
- Skills: Python, SQL, Pandas, NumPy, Scikit-learn, Machine Learning, Statistics, Power BI
- Projects: Customer Churn Prediction (Python, Scikit-learn), Sales Analysis Dashboard (Power BI)
- Experience: 6-month Data Science internship
- AWS: Basic knowledge

**Expected Outcome:** High match score (80+), SHORTLIST recommendation, AWS classified as Partial Match.
