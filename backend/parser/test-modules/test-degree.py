import re
import json
from unidecode import unidecode
from rapidfuzz import fuzz
import sys
import os

# === Load config.json ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..','..','constants', 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# === Import layout analyzer ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer

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

def extract_degrees_precise(text):
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

# === TESTING ===
if __name__ == "__main__":
    pdf_path = "tests/khalid.pdf"
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    print(f"file:{pdf_path}")
    print("\n=== Formatted text ===")
    print(text)
    print("\n=== Degrees ===")
    results = extract_degrees_precise(text)
    for result in results:
        print(f"Degree: {result['degree']}, Field: {result['field']}, Year: {result['year_range']}")
