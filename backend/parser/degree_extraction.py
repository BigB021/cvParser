import re
from unidecode import unidecode
from rapidfuzz import fuzz,process
import sys
import os

# === Import layout analyzer and hlper classes ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper

helper = Helper()

FIELDS = [
    "informatique", "computer science", "gestion", "management",
    "sciences économiques", "économie", "mathematics", "mathématiques",
    "marketing", "finance", "droit", "law", "comptabilité", "accounting",
    "logistique", "supply chain", "big data", "data science", "AI", 
    "réseaux", "networking", "cybersécurité", "cybersecurity", "ingénierie",
    "génie logiciel", "software engineering", "biologie", "physique",
    "chimie", "mécanique", "électrique", "electrical", "civil engineering"
]


def extract_clean_field(text, degree_match):
    text = helper.normalize_text(text)
    best_match = None
    best_score = 0

    # Recherche les expressions types "en gestion", "in management", etc.
    patterns = [
        rf'{re.escape(degree_match)}\s+(?:en|in|de|of)\s+([a-z\s,&-]+)',
        r"(?:d[ée]plom[ée]|formation|degree|master|bachelor|license|licence|cycle)\s+(?:en|in|de|of)\s+([a-z\s,&-]+)",
        r"(?:en|in|de|of)\s+([a-z\s,&-]{4,})"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for raw_field in matches:
            field = helper.clean_field_name(raw_field)
            match, score,_ = process.extractOne(field, FIELDS, scorer=fuzz.token_sort_ratio)
            if score > best_score and score > 70:
                best_match, best_score = match, score

    return best_match.title() if best_match else None




def extract_year_range(text):
    if not text:
        return None
    patterns = [
        r'(20\d{2})\s*[-–—]\s*(20\d{2}|présent|en cours|current|present|currently)',
        r'\b(20\d{2})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_institution(lines, index, window=2):
    keywords = helper.config.get("institutions", [])
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

def extract_degrees(text, debug=False):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = []
    seen_degrees = set()
    aliases_dict = helper.config.get("degree_aliases", {})

    for idx, line in enumerate(lines):
        if len(line) < 5:
            continue

        norm_line = helper.normalize_text(line)
        if any(skip in norm_line for skip in ['email', 'phone', 'linkedin', 'github', 'skills', 'projects', 'languages']):
            continue

        if not helper.is_education_section(lines, idx):
            continue

        best_match = None
        best_score = 0

        for degree, aliases in aliases_dict.items():
            for alias in aliases:
                score = fuzz.token_set_ratio(norm_line, helper.normalize_text(alias))
                if score > 85 and score > best_score:
                    if helper.normalize_text(alias) in norm_line or fuzz.partial_ratio(norm_line, helper.normalize_text(alias)) > 90:
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

    # Filter invalid fields like "project", etc.
    valid_results = []
    for result in results:
        if result['field'] and any(word in result['field'].lower() for word in ['project', 'algorithm', 'visualization', 'tool']):
            continue
        valid_results.append(result)

    # Return detailed results if debug is enabled
    if debug:
        return valid_results

    # Otherwise, return simplified formatted strings
    simplified = []
    for res in valid_results:
        degree = res["degree"]
        field = res["field"]
        institution = res["institution"]

        parts = [degree]
        if field:
            parts.append(f"in {field}")
        if institution:
            parts.append(f"at {institution}")

        simplified.append(" ".join(parts))

    return simplified


# Main execution (testing)
if __name__ == "__main__":
    pdf_path = "tests/youssef.pdf"
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    print(f"file:{pdf_path}")
    print("\n=== Formatted text ===")
    print(text)
    print("\n=== Degrees ===")
    results = extract_degrees(text)
    for result in results:
        print(f"Degree: {result['degree']}, Field: {result['field']}, Year: {result['year_range']}")
