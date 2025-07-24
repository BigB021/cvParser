
import sys
import os
import re
import datetime
from rapidfuzz import fuzz
from typing import List

# === Import layout analyzer and hlper classes ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper

helper = Helper()


import re
from rapidfuzz import fuzz, process
from typing import List, Set
import unicodedata


def normalize_token(token: str) -> str:
    """Clean, lowercase and normalize accents for consistent comparison"""
    token = token.strip().lower()
    token = unicodedata.normalize('NFKD', token)
    token = ''.join([c for c in token if not unicodedata.combining(c)])
    return token


def extract_skills(text: str, known_skills: List[str], section_headers: List[str], threshold=85) -> List[str]:
    skills_found: Set[str] = set()
    normalized_skills = {normalize_token(skill): skill for skill in known_skills}

    # First, attempt to extract a specific 'skills' section
    skills_section = helper.extract_section(
        text,
        section_names=section_headers,
        next_section_names=helper.config.get("next_section", [])
    )

    source_text = skills_section if skills_section else text
    lines = source_text.lower().splitlines()

    for line in lines:
        line = normalize_token(line)
        tokens = re.split(r'[:,•·\-\|;/]', line)
        for token in tokens:
            token = normalize_token(token)

            # Try fuzzy matching against normalized known skills
            match = process.extractOne(token, normalized_skills.keys(), score_cutoff=threshold)
            if match:
                original_skill = normalized_skills[match[0]]
                skills_found.add(original_skill)

    return sorted(skills_found)


def extract_experience_years(text: str, debug: bool = False) -> int:
    """
    Extract years of experience from resume text.
    Returns the highest number of years found, or 0 if none found.
    Logs detailed info if debug=True.
    """
    patterns = [
        r'(\d+)\s+years? of experience',
        r'over\s+(\d+)\s+years',
        r'since\s+(20\d{2}|19\d{2})',
        r'(\d{4})\s*[-–—]\s*(\d{4}|present|now|current)',
        r'(\d+)\+?\s+years',  # e.g. "5+ years"
        r'experience of (\d+) years',
    ]
    current_year = datetime.datetime.now().year
    extracted_years = []

    text_lower = text.lower()
    if debug:
        print("[DEBUG] Starting experience years extraction...")

    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            if debug:
                print(f"[DEBUG] Pattern '{pattern}' found matches: {matches}")
            for match in matches:
                try:
                    if isinstance(match, tuple):
                        # Pattern with start and end years, e.g. "2017 - 2022"
                        start = int(match[0])
                        end_str = match[1]
                        if end_str.isdigit():
                            end = int(end_str)
                        elif end_str in ('present', 'now', 'current'):
                            end = current_year
                        else:
                            end = current_year
                        years_exp = end - start
                        if years_exp > 0:
                            extracted_years.append(years_exp)
                            if debug:
                                print(f"[DEBUG] Extracted {years_exp} years from range {start} - {end}")
                    else:
                        # Single number like "5 years"
                        years_exp = int(match)
                        if years_exp > 0:
                            extracted_years.append(years_exp)
                            if debug:
                                print(f"[DEBUG] Extracted {years_exp} years from single value")
                except Exception as e:
                    if debug:
                        print(f"[WARNING] Failed to parse experience from match {match}: {e}")
                    continue

    if extracted_years:
        max_years = max(extracted_years)
        if debug:
            print(f"[DEBUG] Maximum years of experience extracted: {max_years}")
        return max_years

    if debug:
        print("[DEBUG] No experience years found, returning 0")
    return 0


# Main execution (testing)
if __name__ == "__main__":
    pdf_path = "tests/youssef.pdf"
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    print(f"file:{pdf_path}")
     # Extract only the experience-related section
    experience_section = helper.extract_section(
        text,
        section_names=helper.config.get("experience", []),
        next_section_names=helper.config.get("next_section", [])
    )

    # Then extract experience years ONLY from this section
    exp_years = extract_experience_years(experience_section)
    skills = extract_skills(text, helper.skills, helper.skills_headers)
    print(f"Text: {text}")
    print(f"Skills: {skills}")
    print(f"Experience years: {exp_years}")
