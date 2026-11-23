"""Compatibility imports for the shared report retrieval implementation."""
from pathlib import Path
import sys

SKILL_SCRIPTS = Path(__file__).resolve().parent / "skills" / "resume-assembler" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from resume_evidence import REFERENCES, WRITING_RULES, chunks, terms, cosine, prepare_context
