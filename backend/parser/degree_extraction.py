import re
import sys
import os
from rapidfuzz import fuzz, process
from unidecode import unidecode

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper

helper = Helper()

FIELDS = helper.config.get("fields", [])


FIELD_ALIASES = helper.config.get("field_aliases", {})

def extract_clean_field(text, degree_match):
    text = helper.normalize_text(text)
    all_phrases = []

    patterns = [
        rf'{re.escape(degree_match)}\s+(?:en|in|de|of)?\s*([a-z\s,&-]+)',  
        r"(?:en|in|de|of)\s+([a-z\s,&-]{4,})",                           
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        all_phrases.extend(matches)

    # Add fallback: check entire text for presence of field terms
    for known_field in FIELDS:
        if known_field.lower() in text:
            all_phrases.append(known_field)

    best_match = None
    best_score = 0

    for phrase in all_phrases:
        cleaned = helper.clean_field_name(phrase)
        match, score, _ = process.extractOne(cleaned, FIELDS, scorer=fuzz.token_sort_ratio)
        if score > best_score and score > 70:
            best_match = match
            best_score = score

    return best_match.title() if best_match else None


def extract_year_range(text: str) -> str | None:
    if not text:
        return None
    patterns = [
        r'(20\d{2})\s*[-–—]\s*(20\d{2}|présent|en cours|current|present)',
        r'\b(20\d{2})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None

def extract_institution(lines: list[str], idx: int, window: int = 2) -> str | None:
    patterns = [
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+University|School|Faculty|Institute)',
        rf"({'|'.join(helper.config.get('institutions', []))})[^\n]*"
    ]
    for offset in range(-window, window + 1):
        i = idx + offset
        if 0 <= i < len(lines):
            line = lines[i].strip()
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and len(match.group()) > 6:
                    return match.group().strip()
    return None

def match_degrees_in_line(line: str) -> tuple[str, int]:
    norm_line = helper.normalize_text(line)
    best_match, best_score = None, 0
    for degree, aliases in helper.config.get("degree_aliases", {}).items():
        for alias in aliases:
            score = fuzz.token_set_ratio(norm_line, helper.normalize_text(alias))
            if score > 85 and score > best_score:
                if helper.normalize_text(alias) in norm_line or fuzz.partial_ratio(norm_line, helper.normalize_text(alias)) > 90:
                    best_match, best_score = degree, score
    return best_match, best_score

def scan_resume(lines: list[str], restrict_to_edu=True) -> list[dict]:
    results = []
    seen = set()
    for idx, line in enumerate(lines):
        if len(line) < 5:
            continue
        norm_line = helper.normalize_text(line)
        if any(x in norm_line for x in ['email', 'phone', 'linkedin', 'github', 'skills', 'projects', 'languages']):
            continue
        if restrict_to_edu and not helper.is_education_section(lines, idx):
            continue
        degree, score = match_degrees_in_line(line)
        if degree and score >= 85:
            context = ' '.join(lines[max(0, idx-2):min(len(lines), idx+3)])
            field = extract_clean_field(context, degree.lower())
            year = extract_year_range(context)
            institution = extract_institution(lines, idx)
            signature = (degree, field, year)
            if signature not in seen:
                seen.add(signature)
                results.append({
                    "degree": degree,
                    "field": field,
                    "institution": institution,
                    "year_range": year,
                    "source": line.strip(),
                    "confidence": score
                })
    return results

def extract_degrees(text: str, debug=False) -> list:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = scan_resume(lines, restrict_to_edu=True)

    if not results:
        results = scan_resume(lines, restrict_to_edu=False)

    if not results:
        for idx, line in enumerate(lines):
            norm_line = helper.normalize_text(line)
            if any(kw in norm_line for kw in helper.config.get("degree_keywords", [])):
                for degree, aliases in helper.config.get("degree_aliases", {}).items():
                    if any(alias in norm_line for alias in aliases):
                        field = extract_clean_field(line, degree)
                        year = extract_year_range(line)
                        institution = extract_institution(lines, idx)
                        signature = (degree, field, year)
                        if signature not in results:
                            results.append({
                                "degree": degree,
                                "field": field,
                                "institution": institution,
                                "year_range": year,
                                "source": line.strip(),
                                "confidence": 70
                            })

    final_results = [
        r for r in results
        if not (r['field'] and any(k in r['field'].lower() for k in ['project', 'tool', 'algorithm']))
    ]

    if debug:
        return final_results

    return [
        f"{r['degree']}" +
        (f" in {r['field']}" if r['field'] else '') +
        (f" at {r['institution']}" if r['institution'] else '')
        for r in final_results
    ]


if __name__ == "__main__":
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "youssef"
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "pdfs", f"{pdf_name}.pdf")
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    raw_text = analyzer.extract_with_layout_analysis()

    print(f"\n=== File: {pdf_path} ===\n")
    print("=== Extracted Text ===\n", raw_text)
    print("\n=== Degrees Extracted ===")
    degrees = extract_degrees(raw_text, debug=True)

    if degrees and isinstance(degrees[0], dict):
        for d in degrees:
            print(f"- Degree: {d['degree']}, Field: {d['field']}, Year: {d['year_range']}, Institution: {d['institution']}")
    else:
        for d in degrees:
            print(f"- {d}")
