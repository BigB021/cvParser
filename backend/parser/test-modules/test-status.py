import re
from typing import List, Optional, Tuple
import os
import json
import sys
import spacy
from rapidfuzz import process, fuzz
from langdetect import detect

# === Load config.json ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..','..','constants', 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# === Import layout analyzer ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer

# Load SpaCy models
nlp_en = spacy.load("en_core_web_md")
nlp_fr = spacy.load("fr_core_news_sm")

# === Define status & occupation mappings ===
NORMALIZED_STATUS_MAP = {
    # French
    "recherche de stage": "Looking for Internship",
    "recherche d'emploi": "Looking for Full-Time",
    "cherche un stage": "Looking for Internship",
    "disponible pour cdi": "Looking for CDI",
    "cherche un emploi": "Looking for Full-Time",
    "travail à temps partiel": "Looking for Part-Time",
    "stage professionnel": "Looking for Internship",
    "recherche d'une opportunité": "Looking for Opportunity",

    # English
    "looking for internship": "Looking for Internship",
    "seeking internship": "Looking for Internship",
    "available for full time": "Looking for Full-Time",
    "looking for job": "Looking for Full-Time",
    "seeking full time": "Looking for Full-Time",
    "available for part time": "Looking for Part-Time",
    "looking for part time": "Looking for Part-Time",
    "available for cdi": "Looking for CDI",
    "seeking opportunity": "Looking for Opportunity",
}

NORMALIZED_OCCUPATION_MAP = {
    # French
    "étudiant": "Student",
    "étudiant en informatique": "CS Student",
    "étudiant cycle ingénieur": "Engineering Student",
    "stagiaire": "Intern",
    "développeur junior": "Junior Developer",
    "jeune diplômé": "Graduate",
    "ingénieur data": "Data Engineer",
    "ingénieur intelligence artificielle": "AI Engineer",

    # English
    "student": "Student",
    "computer science student": "CS Student",
    "engineering student": "Engineering Student",
    "intern": "Intern",
    "junior developer": "Junior Developer",
    "fresh graduate": "Graduate",
    "trainee": "Intern",
    "data engineer": "Data Engineer",
    "ai engineer": "AI Engineer",
    "machine learning engineer": "ML Engineer",
}

STATUS_CANDIDATES = list(NORMALIZED_STATUS_MAP.keys())
OCCUPATION_CANDIDATES = list(NORMALIZED_OCCUPATION_MAP.keys())

# === Utility Functions ===
def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang if lang in ["fr", "en"] else "en"
    except:
        return "en"

def extract_candidate_phrases(text: str, lang: str) -> List[str]:
    nlp = nlp_fr if lang == "fr" else nlp_en
    doc = nlp(text)
    phrases = set()

    for np in doc.noun_chunks:
        phrase = np.text.strip().lower()
        if 4 < len(phrase) < 100:
            phrases.add(phrase)

    for sent in doc.sents:
        sent_text = sent.text.strip().lower()
        if any(kw in sent_text for kw in ["student", "étudiant", "intern", "stagiaire", "job", "emploi", "stage", "looking", "recherche", "available", "disponible", "engineer", "ingénieur"]):
            phrases.add(sent_text)

    return list(phrases)

def fuzzy_match(phrases: List[str], candidates: List[str], threshold: int = 70) -> Optional[str]:
    best_score = 0
    best_match = None
    for phrase in phrases:
        match, score, _ = process.extractOne(phrase, candidates, scorer=fuzz.token_sort_ratio)
        if score > best_score and score >= threshold:
            best_match = match
            best_score = score
    return best_match

def extract_status_and_occupation(text: str) -> Tuple[Optional[str], Optional[str]]:
    lang = detect_language(text)
    phrases = extract_candidate_phrases(text, lang)

    raw_status = fuzzy_match(phrases, STATUS_CANDIDATES)
    raw_occupation = fuzzy_match(phrases, OCCUPATION_CANDIDATES)

    status = NORMALIZED_STATUS_MAP.get(raw_status) if raw_status else None
    occupation = NORMALIZED_OCCUPATION_MAP.get(raw_occupation) if raw_occupation else None

    return status, occupation

# === Example Usage ===
if __name__ == '__main__':
    pdf_path = "tests/karim.pdf"
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    print("\n=== Formatted text ===")
    print(text)

    print("\n==================")
    status, occupation = extract_status_and_occupation(text)
    print(f"Extracted Status: {status}")
    print(f"Extracted Occupation: {occupation}")
