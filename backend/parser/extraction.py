import sys
import os
import datetime
import fitz  # PyMuPDF
import re
from typing import List, Dict, Optional
import spacy
import json
from rapidfuzz import process,fuzz
from unidecode import unidecode
from collections import defaultdict
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from layout_analyser import PyMuPDFLayoutAnalyzer
from models.resume import add_resume




def extract_candidate_name(text: str, analyzer: PyMuPDFLayoutAnalyzer) -> Optional[str]:
    """
    Extracts the candidate's name from the resume text using a combination of
    NER, font-size, regex, and heuristic fallbacks.
    """
    # Get sorted top blocks (by font size then vertical position)
    blocks = analyzer.get_text_blocks(text)
    blocks = sorted(blocks, key=lambda b: (-b.get("font_size", 0), b["y0"]))
    top_blocks = [b["text"] for b in blocks[:8] if b["text"]]
    # First try: SpaCy NER on top blocks
    for block_text in top_blocks:
        doc = analyzer.nlp(block_text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = _clean_name(ent.text,analyzer)
                if name:
                    return name
    # Second try: Heuristic rule – title case words in a line (exclude known headers)
    for block_text in top_blocks:
        if any(char.isdigit() for char in block_text):
            continue
        if block_text.strip().upper() in analyzer.blacklist_headers:
            continue
        words = block_text.strip().split()
        if 1 <= len(words) <= 6:
            probable_name = " ".join([w for w in words if w[0].isupper()])
            if 1 <= len(probable_name.split()) <= 4:
                return _clean_name(probable_name,analyzer)
    # Third try: Regex fallback for proper names at beginning
    name_match = re.search(r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3}', text)
    if name_match:
        return _clean_name(name_match.group().strip(),analyzer)
    # Logging for debugging
    print("\n[WARNING] Candidate name could not be extracted.")
    print("--- DEBUG: Top blocks ---")
    for b in top_blocks:
        print(f"> {b}")
    return None


def _clean_name(name: str, analyzer: PyMuPDFLayoutAnalyzer) -> str:
    """
    Removes job titles or other known keywords that don't belong in names.
    """
    tokens = name.strip().split()
    cleaned = []
    for token in tokens:
        if token.lower() in analyzer.job_titles:
            break
        cleaned.append(token)
    return " ".join(cleaned)


def extract_email_from_text(text: str) -> Optional[str]:
    """Extract email using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_phone_number_from_text(text: str) -> Optional[str]:
    """Extract Moroccan phone numbers using regex"""
    patterns = [
        r'\+212[\s-]*(?:\(0\)[\s-]*)?(?:6|7)[\d\s()-]{8,}',
        r'(?:06|07)[\d\s()-]{8,}',
        r'212[\s-]*(?:6|7)[\d\s()-]{8,}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0].replace(' ', '').replace('-', '').replace('(0)', '').replace('(', '').replace(')', '')
            return phone
    return None

def extract_city(text: str, city_list: List[str], score_threshold: int = 88) -> Optional[str]:
    """Extract Moroccan city from text using strict fuzzy matching."""
    text = text.lower()
    words = text.split()
    candidates = set()
    # Add unigrams and bigrams (up to 2-word city names like 'el jadida')
    for i in range(len(words)):
        unigram = words[i]
        bigram = f"{words[i]} {words[i+1]}" if i+1 < len(words) else ""
        candidates.update([unigram.strip(",.;:()"), bigram.strip(",.;:()")])

    # Filter short/meaningless candidates
    candidates = {c for c in candidates if len(c) >= 3}

    best_match = None
    best_score = 0

    for candidate in candidates:
        match = process.extractOne(candidate, city_list)
        if match:
            city_name, score = match[0],match[1]
            if score > best_score and score >= score_threshold:
                best_match = city_name
                best_score = score

    return best_match


def extract_job_titles(text: str, job_list: List[str], threshold=85) -> List[str]:
    """
    Extract candidate's occupation using fuzzy matching
    """
    found = set()
    for line in text.lower().splitlines():
        match = process.extractOne(line, job_list)
        if match and match[1] > threshold:
            found.add(match[0])
    return list(found)


# Degree extraction still ass: duplicated enteries and inaccurate dates
def extract_degrees(text: str, degree_keywords: List[str], threshold: int = 85) -> List[Dict[str, Optional[str]]]:
    """
    Extracts degrees with field and year information using buffered line context.
    """
    section_text = extract_section(
        text,
        section_names=["education", "academic background"],
        next_section_names=["skills", "projects", "experience", "certifications", "languages"]
    )

    lines = normalize_lines(section_text.splitlines())
    degree_pattern = '|'.join([re.escape(d.lower()) for d in degree_keywords])
    year_pattern = r'(20|19)\d{2}(?:\s*[-–—to]{1,3}\s*(20|19)?\d{2}|)'
    
    results = []
    seen = set()

    for idx, line in enumerate(lines):
        line_lower = unidecode(line.lower())
        if not re.search(degree_pattern, line_lower):
            continue

        degree_match = process.extractOne(line_lower, degree_keywords, scorer=fuzz.token_set_ratio)
        if not degree_match or degree_match[1] < threshold:
            continue

        degree_name = degree_match[0].title()

        # Try to find field of study in the same or nearby lines
        context_lines = ' '.join(lines[max(0, idx-1): idx+2]).strip()
        field_match = re.search(r'\b(?:in|of|en)\s+([a-zA-Z\s]{3,50})', context_lines)
        field = field_match.group(1).strip().title() if field_match else None

        # Extract year or year range
        year_match = re.search(year_pattern, context_lines)
        year_range = year_match.group(0) if year_match else None

        entry_key = f"{degree_name}|{field}|{year_range}"
        if entry_key not in seen:
            results.append({
                "degree": degree_name,
                "field": field,
                "year_range": year_range,
                "source": line.strip()
            })
            seen.add(entry_key)

    return results



# helper function
def normalize_lines(lines: List[str]) -> List[str]:
    """
    Normalizes lines to merge broken lines that belong together
    """
    normalized = []
    buffer = ""
    for line in lines:
        stripped = line.strip()
        if stripped:
            if buffer:
                buffer += " " + stripped
            else:
                buffer = stripped
        else:
            if buffer:
                normalized.append(buffer)
                buffer = ""
    if buffer:
        normalized.append(buffer)
    return normalized


def extract_section(text: str, section_names: List[str], next_section_names: List[str]) -> str:
    """
    Extracts a section of the resume between a section header and the next header.
    """
    lines = text.splitlines()
    section_lines = []
    is_in_section = False

    for line in lines:
        line_clean = line.strip().lower()
        if any(header in line_clean for header in section_names):
            is_in_section = True
            continue
        if is_in_section and any(header in line_clean for header in next_section_names):
            break
        if is_in_section:
            section_lines.append(line)

    return "\n".join(section_lines).strip()


def extract_experience_years(text: str, debug: bool = True) -> int:
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

def extract_skills(text: str, known_skills: List[str], section_headers: List[str], threshold=85) -> List[str]:
    """Extract skills from text using fuzzy matching within the skills section."""
    skills_found = set()
    
    # First: try to extract only the skills section
    skills_section = extract_section(
        text,
        section_names=section_headers,
        next_section_names=["experience", "education", "projects", "languages", "certifications"]
    )

    # Fallback to full text if section not found
    source_text = skills_section if skills_section else text

    lines = source_text.lower().splitlines()
    
    for line in lines:
        # Try multiple matches in each line
        for skill in known_skills:
            score = fuzz.partial_ratio(skill.lower(), line)
            if score >= threshold:
                skills_found.add(skill)

    return sorted(skills_found)


def clean_status_text(status: str, cutoff_words:str) -> str:
    """
    Extracts candidate's current status
    """
    import re
    if not status:
        return None
    status = status.strip()
    status = re.sub(r'\s+', ' ', status)  # Normalize spaces

    # Cut off trailing incomplete fragments at conjunctions or commas
    #cutoff_words = [' and ', ' but ', ' however ', ' moreover ', ' whereas ', ' also ']
    for w in cutoff_words:
        idx = status.lower().find(w)
        if idx > 20:  # avoid cutting too early, only cut if phrase is longer than 20 chars
            status = status[:idx].strip()
            break

    # Remove trailing punctuation like comma, semicolon, dash
    status = re.sub(r'[,;:\-\s]+$', '', status)

    # Optionally truncate to ~150 chars max
    if len(status) > 150:
        status = status[:150].rstrip() + "..."

    return status



def extract_status_nlp(text: str, cutoff_words) -> Optional[str]:
    """
    Extract candidate status with improved regex matching and cleanup.
    """

    text_lower = text.lower()

    # Extract profile and education sections (fall back to full text)
    profile_section = extract_section(text_lower, ["profile", "summary", "about me"], ["experience", "education", "skills"])
    education_section = extract_section(text_lower, ["education", "academic background"], ["experience", "skills", "projects"])

    search_sections = [profile_section, education_section, text_lower]

    status_keywords = r"(?:currently|presently|enrolled|pursuing|studying|ongoing|candidate|apprentice|graduate|student|engineer)"
    degree_keywords = r"(?:master|bachelor|phd|licence|degree|engineering)"

    combined_pattern = re.compile(
        rf"((?:\S+\s+){{0,5}}{status_keywords}(?:\s+\S+){{0,5}}{degree_keywords}(?:\s+\S+){{0,5}})",
        re.IGNORECASE
    )



    # Search for combined status + degree phrase first
    for section in search_sections:
        if not section:
            continue
        matches = combined_pattern.findall(section)
        if matches:
            # Clean and return the shortest meaningful match
            cleaned = [clean_status_text(m,cutoff_words) for m in matches if m]
            cleaned = [c for c in cleaned if c]
            if cleaned:
                # Return shortest cleaned phrase (likely most precise)
                return min(cleaned, key=len)

    # Fallback: only status keywords phrase
    status_only_pattern = re.compile(
        rf"((?:\S+\s+){{0,20}}{status_keywords}(?:\s+\S+){{0,20}})",
        re.IGNORECASE
    )
    for section in search_sections:
        if not section:
            continue
        matches = status_only_pattern.findall(section)
        if matches:
            cleaned = [clean_status_text(m,cutoff_words) for m in matches if m]
            cleaned = [c for c in cleaned if c]
            if cleaned:
                return min(cleaned, key=len)

    return None




def process_pdf_with_pymupdf(pdf_path: str) -> Dict:
    """Process PDF with PyMuPDF layout analysis"""
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    
    # Extract text with layout analysis
    text = analyzer.extract_with_layout_analysis()
    
    # Extract structured information
    candidate_name = extract_candidate_name(text, analyzer)
    email = extract_email_from_text(text)
    phone = extract_phone_number_from_text(text)
    jobs = extract_job_titles(text, analyzer.job_titles)
    degrees = extract_degrees(text,analyzer.degrees)

    city = extract_city(text, analyzer.cities)    
        # Extract text
    text = analyzer.extract_with_layout_analysis()

    # Extract only the experience-related section
    experience_section = extract_section(
        text,
        section_names=analyzer.experience,
        next_section_names=analyzer.next_section
    )

    # Then extract experience years ONLY from this section
    exp_years = extract_experience_years(experience_section)
    skills = extract_skills(text, analyzer.config.get("skills", []), analyzer.config.get("skills_headers", []))

    status = extract_status_nlp(text, analyzer.config.get("cutoff_words", []))



    return {
        'text': text,
        'candidate_name': candidate_name,
        'email': email,
        'phone_number': phone,
        'city': city,
        "job_titles": jobs,
        "degrees": degrees,
        "experience": exp_years,
        "skills": skills,
        "status": status,

    }


# Main execution (testing module)
if __name__ == "__main__":
    try:
        pdf_path = "tests/khalid.pdf"
        result = process_pdf_with_pymupdf(pdf_path)
        
        print("=== STRUCTURED EXTRACTION RESULTS ===")
        print(f"**Candidate Name: {result['candidate_name']}")
        print(f"**Email: {result['email']}")
        print(f"**Phone: {result['phone_number']}")
        print(f"**City: {result['city']}")
        print(f"**job_titles: {result['job_titles']}")
        print(f"**degrees: {result['degrees']}")
        print(f"**experience: {result['experience']} years")
        print(f"**skills: {result['skills']}")
        print(f"**Status: {result['status']}")

        occupation = ''
        for job in result['job_titles']:
            occupation += job + " "
        print(occupation)
        sample_resume = {
            "name": result['candidate_name'],
            "email": result['email'],
            "phone": result['phone_number'],
            "occupation": occupation,
            "exp_years": result['experience'],
            "city": result['city'],
            "status": result['status'],
            "pdf_path": pdf_path,
            "degrees": [
                {"type": "Master", "subject": "Data Science"},
                {"type": "Bachelor", "subject": "Computer Science"}
            ],
            "skills": result['skills']
        }

        add_resume(sample_resume)

  

        # print("\n=== FORMATTED TEXT ===")
        # print(result['text'])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()