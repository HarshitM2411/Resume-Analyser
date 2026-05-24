"""One-time helper to create sample PDF and DOCX resumes for Phase 0."""

from pathlib import Path

RESUMES_DIR = Path(__file__).resolve().parent.parent / "resumes"

JOHN_DOE_TEXT = """John Doe
Software Engineer
john.doe@email.com | (555) 123-4567

SUMMARY
Full-stack software engineer with 6+ years of experience building scalable
web applications and APIs. Strong Python expertise across backend services,
data pipelines, and automation.

EXPERIENCE
Senior Software Engineer | TechCorp Inc. | 2020 - Present
- Built REST APIs in Python (FastAPI) serving 2M+ daily requests
- Led migration of legacy monolith to microservices on AWS
- Mentored 3 junior developers on Python best practices and code review

Software Engineer | StartupXYZ | 2018 - 2020
- Developed Django web applications and PostgreSQL data models
- Implemented CI/CD pipelines with GitHub Actions

EDUCATION
B.S. Computer Science, MIT

SKILLS
Python, JavaScript, FastAPI, Django, PostgreSQL, Docker, AWS, Git
"""

JANE_SMITH_TEXT = """Jane Smith
Product Manager
jane.smith@email.com | (555) 987-6543

SUMMARY
Product manager with 7 years of experience shipping B2B SaaS products.
Skilled at translating customer needs into roadmaps and cross-functional delivery.

EXPERIENCE
Senior Product Manager | CloudFlow | 2021 - Present
- Owned roadmap for analytics dashboard used by 500+ enterprise clients
- Increased user retention by 18% through feature prioritization and UX research

Product Manager | DataWorks | 2018 - 2021
- Launched integrations platform connecting 20+ third-party tools
- Partnered with engineering on agile delivery and sprint planning

EDUCATION
MBA, Wharton School | B.A. Economics, UCLA

SKILLS
Product strategy, roadmapping, Jira, SQL, user research, stakeholder management
"""


def create_docx(path: Path) -> None:
    from docx import Document

    doc = Document()
    for paragraph in JANE_SMITH_TEXT.strip().split("\n"):
        doc.add_paragraph(paragraph)
    doc.save(path)


def create_pdf(path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError:
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
        from fpdf import FPDF

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    for line in JOHN_DOE_TEXT.strip().split("\n"):
        if not line.strip():
            pdf.ln(4)
            continue
        pdf.multi_cell(effective_width, 6, line)
    pdf.output(str(path))


def main() -> None:
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    create_docx(RESUMES_DIR / "resume_jane_smith.docx")
    create_pdf(RESUMES_DIR / "resume_john_doe.pdf")
    print(f"Created sample resumes in {RESUMES_DIR}")


if __name__ == "__main__":
    main()
