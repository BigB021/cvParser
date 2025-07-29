import sys
import os
import re
from typing import Optional
from rapidfuzz import process
from typing import List

from unidecode import unidecode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from parser.utils.helper import Helper
from layout_analyser import PyMuPDFLayoutAnalyzer

helper = Helper()

def extract_name(text: str, analyzer: PyMuPDFLayoutAnalyzer) -> Optional[str]:
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
        if token.lower() in helper.config.get("job_titles",[]):
            break
        cleaned.append(token)
    return " ".join(cleaned)

def extract_city(text: str, city_list: List[str], score_threshold: int = 88) -> Optional[str]:
    """Extract Moroccan city from text with fuzzy matching ignoring accents and minor typos."""
    norm_text = unidecode(text.lower())
    words = norm_text.split()
    candidates = set()
    
    # unigram + bigram (2-words city names)
    for i in range(len(words)):
        unigram = words[i].strip(",.;:()")
        if unigram:
            candidates.add(unigram)
        if i + 1 < len(words):
            bigram = f"{words[i]} {words[i+1]}".strip(",.;:()")
            if bigram:
                candidates.add(bigram)
    
    # filter short candidates
    candidates = {c for c in candidates if len(c) >= 3}

    # Create mapping normalized_city -> original city (to recover accented name)
    norm_city_map = {unidecode(city.lower()): city for city in city_list}

    best_match = None
    best_score = 0

    for candidate in candidates:
        # rapidfuzz extractOne compares against keys (norm_city_map keys)
        match = process.extractOne(candidate, norm_city_map.keys())
        if match:
            matched_norm_city, score = match[0], match[1]
            if score > best_score and score >= score_threshold:
                best_score = score
                best_match = norm_city_map[matched_norm_city]  # return original accented city

    return best_match



# Main execution (testing)
if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), ".." ,"pdfs", sys.argv[1]+ ".pdf" if len(sys.argv) > 1 else "youssef.pdf")
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    print(f"file:{pdf_path}")
    #print("\n=== Formatted text ===")
    #print(text)

    name = extract_name(text, analyzer)
    CITIES = [city.lower() for city in  helper.cities]
    city = extract_city(text, CITIES)    
    print(f"Name: {name}")
    print(f"City: {city}")