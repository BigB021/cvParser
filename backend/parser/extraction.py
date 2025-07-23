import sys
import os
import datetime
import fitz  # PyMuPDF
import re
from typing import List, Dict, Optional
import spacy
import json
from rapidfuzz import process,fuzz
from rapidfuzz.fuzz import token_set_ratio, partial_ratio

from unidecode import unidecode
from collections import defaultdict
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from layout_analyser import PyMuPDFLayoutAnalyzer
from models.resume import add_resume, get_all_resumes, delete_resume, get_resume_by_id

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..','constants', 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)


def extract_candidate_name(text: str, analyzer: PyMuPDFLayoutAnalyzer) -> Optional[str]:
    blocks = analyzer.get_text_blocks(text)
    blocks = sorted(blocks, key=lambda b: (-b.get("font_size", 0), b["y0"]))
    top_blocks = [b["text"] for b in blocks[:8] if b["text"]]

    # 1. Try SpaCy NER on both original and title-cased text
    for block_text in top_blocks:
        for variant in (block_text, block_text.title()):
            doc = analyzer.nlp(variant)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name = _clean_name(ent.text)
                    if name:
                        return name

    # 2. Heuristic: first line with 2+ uppercase words (likely name in uppercase)
    for block_text in top_blocks:
        words = block_text.strip().split()
        uppercase_words = [w for w in words if w.isupper() and len(w) > 1]
        if len(uppercase_words) >= 2:
            probable_name = " ".join(words)
            if block_text.strip().upper() not in analyzer.blacklist_headers:
                return _clean_name(probable_name)

    # 3. Heuristic: first non-header line before keywords like "etudiant", "contact"
    keywords = ["etudiant", "student", "contact", "email", "tel", "phone"]
    for block_text in top_blocks:
        line_lower = block_text.lower()
        if any(kw in line_lower for kw in keywords):
            continue
        if any(char.isdigit() for char in block_text):
            continue
        if block_text.strip().upper() in analyzer.blacklist_headers:
            continue
        words = block_text.strip().split()
        if 1 <= len(words) <= 6:
            return _clean_name(block_text.strip())

    # 4. Regex fallback: allow uppercase names
    regex_patterns = [
        r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3}',         # Title case
        r'^[A-Z]{2,}(?:\s[A-Z]{2,}){1,3}',             # Uppercase (e.g. NIZAR KOURTI)
    ]
    for pattern in regex_patterns:
        name_match = re.search(pattern, text, re.MULTILINE)
        if name_match:
            return _clean_name(name_match.group().strip())

    print("\n[WARNING] Candidate name could not be extracted.")
    print("--- DEBUG: Top blocks ---")
    for b in top_blocks:
        print(f"> {b}")
    return None



def _clean_name(name: str) -> str:
    """
    Removes job titles or other known keywords that don't belong in names.
    """
    tokens = name.strip().split()
    cleaned = []
    for token in tokens:
        if token.lower() in CONFIG.get("job_titles",[]):
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



from typing import Dict

def extract_job_title(text: str, canonical_job_titles: Dict[str, list], threshold: int = 80) -> str:
    best_match = ("", 0)
    lines = text.lower().splitlines()

    # Filter out short or unrelated lines (e.g. "english", "skills", "bachelor")
    filtered_lines = [line.strip() for line in lines if len(line.strip()) > 8 and any(c.isalpha() for c in line)]

    for title, phrases in canonical_job_titles.items():
        for phrase in phrases:
            for line in filtered_lines:
                score = fuzz.token_set_ratio(phrase.lower(), line)
                if score > best_match[1]:
                    best_match = (title, score)

    return best_match[0] if best_match[1] >= threshold else ""


################################# probably needs to be put in a separate module ##############################################

# === Helpers ===
def normalize_text(text):
    if not text:
        return ""
    text = unidecode(text.lower().strip())
    text = re.sub(r'\s+', ' ', text)
    return text

def is_education_section(lines, index, window=3):
    education_indicators = CONFIG.get("education_headers", [])
    start = max(0, index - window)
    end = min(len(lines), index + window)
    context = ' '.join(lines[start:end]).lower()
    return any(indicator in context for indicator in education_indicators)

def extract_clean_field(text, degree_match):
    text = normalize_text(text)
    valid_fields = CONFIG.get("skills", [])  # Assuming fields overlap with skills for now

    patterns = [
        rf'{re.escape(degree_match)}\s+(?:en|in|de|of)\s+([a-z\s,&-]+?)(?:\s|$|\n|\.|\()',
        r'(?:en|in|de|of)\s+([a-z\s,&-]+?)(?:\s|$|\n|\.|\()',
        r"cycle\s+d[\'']ingenieurs?\s+([a-z\s,&-]+?)(?:\s|$|\n|\.|\()'"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            field = match.strip()
            for valid_field in valid_fields:
                if fuzz.partial_ratio(field, valid_field) > 70:
                    return clean_field_name(field)
    return None

def clean_field_name(field):
    field = field.strip()
    noise_patterns = [
        r'\b(?:degree|diploma|programme|program|formation|cycle|year|annee)\b',
        r'\([^)]*\)',
        r'\s+',
    ]
    for pattern in noise_patterns:
        field = re.sub(pattern, ' ', field, flags=re.IGNORECASE)

    field = ' '.join(field.split())
    return field.title() if len(field) > 2 else None

def extract_year_range(text):
    if not text:
        return None
    patterns = [
        r'(20\d{2})\s*[-–—]\s*(20\d{2}|present|currently|current)',
        r'(20\d{2})\s*[-–—]\s*(20\d{2})',
        r'\b(20\d{2})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def extract_institution(lines, index, window=2):
    keywords = CONFIG.get("institutions", [])
    patterns = [
        rf"({'|'.join(keywords)})\s+[a-z\s]+",
        r'[A-Z][a-z]+\s+(?:University|School|Institute|Faculty)'
    ]

    for offset in range(-window, window + 1):
        i = index + offset
        if 0 <= i < len(lines):
            line = lines[i].strip()
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and len(match.group()) > 8:
                    return match.group().strip()
    return None

def extract_degrees(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = []
    seen_degrees = set()
    aliases_dict = CONFIG.get("degree_aliases", {})

    for idx, line in enumerate(lines):
        if len(line) < 5:
            continue

        norm_line = normalize_text(line)
        if any(skip in norm_line for skip in ['email', 'phone', 'linkedin', 'github', 'skills', 'projects', 'languages']):
            continue

        if not is_education_section(lines, idx):
            continue

        best_match = None
        best_score = 0

        for degree, aliases in aliases_dict.items():
            for alias in aliases:
                score = fuzz.token_set_ratio(norm_line, normalize_text(alias))
                if score > 85 and score > best_score:
                    if normalize_text(alias) in norm_line or fuzz.partial_ratio(norm_line, normalize_text(alias)) > 90:
                        best_match = degree
                        best_score = score

        if best_match:
            context_lines = lines[max(0, idx - 2):min(len(lines), idx + 3)]
            context = ' '.join(context_lines)
            field = extract_clean_field(context, best_match.lower())
            year_range = extract_year_range(context)
            institution = extract_institution(lines, idx)

            signature = (best_match, field, year_range)
            if signature not in seen_degrees and best_score >= 85:
                seen_degrees.add(signature)
                degree_data = {
                    "degree": best_match,
                    "field": field,
                    "institution": institution,
                    "year_range": year_range,
                    "source": line.strip(),
                    "confidence": best_score
                }
                results.append(degree_data)

    valid_results = []
    for result in results:
        if result['field'] and any(word in result['field'].lower() for word in ['project', 'algorithm', 'visualization', 'tool']):
            continue
        valid_results.append(result)

    return valid_results

################################################################################################

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

def extract_skills(text: str, known_skills: List[str], section_headers: List[str], threshold=80) -> List[str]:
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
    jobs = extract_job_title(text, CONFIG.get("canonical_job_titles",{}))
    degrees = extract_degrees(text)

    CITIES = [city.lower() for city in CONFIG["cities"]]
    city = extract_city(text, CITIES)    
        # Extract text
    text = analyzer.extract_with_layout_analysis()

    # Extract only the experience-related section
    experience_section = extract_section(
        text,
        section_names=CONFIG.get("experience", []),
        next_section_names=CONFIG.get("next_section", [])
    )

    # Then extract experience years ONLY from this section
    exp_years = extract_experience_years(experience_section)
    skills = extract_skills(text, CONFIG.get("skills", []), CONFIG.get("skills_headers", []))

    status = extract_status_nlp(text, CONFIG.get("cutoff_words", []))



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
        pdf_path = "tests/test-ocr.pdf"
        result = process_pdf_with_pymupdf(pdf_path)

        degrees_dict = result['degrees']

        print("File name: ",pdf_path)
        
        print("\n=== FORMATTED TEXT ===")
        print(result['text'])
        
        print("=== STRUCTURED EXTRACTION RESULTS ===")
        print(f"**Candidate Name: {result['candidate_name']}")
        print(f"**Email: {result['email']}")
        print(f"**Phone: {result['phone_number']}")
        print(f"**City: {result['city']}")
        print(f"**job_titles: {result['job_titles']}")
        print(f"**experience: {result['experience']} years")
        print(f"**skills: {result['skills']}")
        print(f"**Status: {result['status']}")
        print("**Degrees:")
        for d in degrees_dict:
            print(f"  - {d['degree']} in {d['field']} ({d['year_range']})")

        
        resume_data = {
            "name": result['candidate_name'],
            "email": result['email'],
            "phone": result['phone_number'],
            "occupation": result['job_titles'],
            "exp_years": result['experience'],
            "city": result['city'],
            "status": result['status'],
            "pdf_path": pdf_path,
            "degrees": [
                {"type": d["degree"], "subject": d["field"]}
                for d in degrees_dict
            ],
            "skills": result['skills']
        }


        add_resume(resume_data)
  

        
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()