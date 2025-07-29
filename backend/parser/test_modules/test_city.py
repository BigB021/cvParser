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

def extract_city_from_text(text: str, city_list: List[str], score_threshold: int = 90) -> Optional[str]:
    norm_text = helper.normalize_text(text)
    words = norm_text.split()
    candidates = set()

    for i in range(len(words)):
        unigram = words[i].strip(",.;:()")
        if len(unigram) >= 3:
            candidates.add(unigram)
        if i + 1 < len(words):
            bigram = f"{words[i]} {words[i+1]}".strip(",.;:()")
            if len(bigram) >= 3:
                candidates.add(bigram)

    norm_city_map = {helper.normalize_text(city): city for city in city_list}

    best_match = None
    best_score = 0

    for candidate in candidates:
        match = process.extractOne(candidate, norm_city_map.keys(), score_cutoff=score_threshold)
        if match:
            matched_norm_city, score = match[0], match[1]
            if score > best_score:
                best_score = score
                best_match = norm_city_map[matched_norm_city]

    return best_match

def extract_city(full_text: str, city_list: List[str]) -> Optional[str]:
    # Define relevant section headers and blacklist headers
    section_headers = ["PROFILE", "PROFIL", "CONTACT", "COORDONNÉES"]
    # Use the blacklist headers as next section names to stop extracting early
    blacklist_headers = [
        "EDUCATION", "FORMATION", "EXPERIENCE", "EXPÉRIENCE", "PROJECTS", "PROJETS", "SKILLS",
        "COMPÉTENCES", "LANGUAGES", "LANGUES", "VOLUNTEERING", "BÉNÉVOLAT"
    ]

    # Extract relevant section text for city search
    section_text = helper.extract_section(full_text, section_headers, blacklist_headers)
    print(f"[DEBUG] Extracted section for city search: {section_text}")
    city = extract_city_from_text(section_text, city_list)

    if city:
        return city
    else:
        # fallback: search entire text if nothing found
        return extract_city_from_text(full_text, city_list)


