"""End-to-end validation for Phase 7 (requires GROQ_API_KEY in .env)."""

import os

from llm_file_assistant import run_agent_loop

SEP = "-" * 60

# Query 1: Read all resumes
print(SEP)
print("Q1: Read all resumes in the resumes folder")
answer = run_agent_loop("Read all resumes in the resumes folder")
print(answer)
assert any(name in answer.lower() for name in ["john", "jane", "alice"]), (
    "Q1: expected candidate names in answer"
)

# Query 2: Find resumes mentioning Python
print(SEP)
print("Q2: Find resumes mentioning Python experience")
answer = run_agent_loop("Find resumes mentioning Python experience")
print(answer)
assert isinstance(answer, str) and len(answer) > 20, "Q2: answer too short"

# Query 3: Create a summary file
print(SEP)
print("Q3: Create a summary file for resume_john_doe.pdf")
answer = run_agent_loop("Create a summary file for resume_john_doe.pdf")
print(answer)
assert os.path.exists("output/summary_john_doe.txt"), (
    "Q3: expected output/summary_john_doe.txt to be created"
)
with open("output/summary_john_doe.txt", encoding="utf-8") as f:
    summary_content = f.read()
assert len(summary_content) > 50, "Q3: summary file looks too short"

print(SEP)
print("All end-to-end tests passed.")
