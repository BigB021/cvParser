import spacy
from spacy.matcher import PhraseMatcher
import re
import json
from pathlib import Path
from typing import Tuple
import numpy as np
import os
import sys

# === Import layout analyzer ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..','..','constants', 'config.json')
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

nlp = spacy.load("en_core_web_md")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Use all canonical_job_titles values for matcher patterns
phrase_patterns = []
for titles in CONFIG["canonical_job_titles"].values():
    phrase_patterns.extend([nlp.make_doc(title) for title in titles])
matcher.add("OCCUPATION", phrase_patterns)

# Prototypes for status detection
STATUS_PROTOTYPES = {
    "student": [
        "i am a student", "currently studying", "pursuing a degree",
        "final year student", "enrolled in a university"
    ],
    "fresh_graduate": [
        "recent graduate", "just graduated", "bachelor's degree completed",
        "i have recently finished my degree"
    ],
    "intern": [
        "looking for an internship", "seeking internship",
        "internship position", "available for internship"
    ],
    "professional": [
        "working as", "i am a professional", "experience in", "currently employed"
    ]
}

class ExtractionResult:
    def __init__(self, occupation: str, level: str, status: str, confidence: float):
        self.occupation = occupation
        self.level = level
        self.status = status
        self.confidence = round(confidence, 3)

    def to_dict(self):
        return {
            "occupation": self.occupation,
            "level": self.level,
            "status": self.status,
            "confidence": self.confidence,
        }

class StatusOccupationExtractor:
    def __init__(self):
        self.config = CONFIG

    def clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    def get_header(self, text: str) -> str:
        header = text[:500]
        return self.clean_text(header)

    def detect_status_semantic(self, doc: spacy.tokens.Doc) -> Tuple[str, float]:
        best_status = "unknown"
        best_score = 0.0
        for label, phrases in STATUS_PROTOTYPES.items():
            for phrase in phrases:
                sim = nlp(phrase).similarity(doc)
                if sim > best_score:
                    best_status = label
                    best_score = sim
        return best_status, best_score

    def extract_occupation(self, doc: spacy.tokens.Doc) -> Tuple[str, str, float]:
        matches = matcher(doc)
        if matches:
            best_span = max([doc[start:end] for _, start, end in matches], key=lambda span: len(span.text))
            occupation = best_span.text.lower()
            conf = 1.0
        else:
            best_title = None
            best_score = 0.0
            doc_vector = doc.vector
            for canonical, titles in self.config["canonical_job_titles"].items():
                for title in titles:
                    title_vector = nlp(title).vector
                    sim = np.dot(title_vector, doc_vector) / (np.linalg.norm(title_vector) * np.linalg.norm(doc_vector) + 1e-8)
                    if sim > best_score:
                        best_score = sim
                        best_title = canonical
            occupation = best_title if best_score > 0.7 else "unknown"
            conf = best_score

        level = "Unknown"
        for lvl, keywords in self.config.get("education_levels", {}).items():
            if any(k.lower() in doc.text.lower() for k in keywords):
                level = lvl.capitalize()
                break

        return occupation, level, conf

    def parse_cv(self, text: str) -> ExtractionResult:
        header_text = self.get_header(text)
        doc = nlp(header_text)

        status, status_conf = self.detect_status_semantic(doc)
        occupation, level, occ_conf = self.extract_occupation(doc)

        confidence = round((status_conf + occ_conf) / 2, 3)
        return ExtractionResult(occupation, level, status, confidence)

# Test
if __name__ == "__main__":
    file = 'tests/oumaima.pdf'
    text = PyMuPDFLayoutAnalyzer(file).extract_with_layout_analysis()
    print("======= Text ======")
    print(text)
    print("===================")

    extractor = StatusOccupationExtractor()
    res = extractor.parse_cv(text)
    print(res.to_dict())
    print(f"Status: {res.status}")
    print(f"Occupation: {res.occupation}")
    print(f"Occupation level: {res.level}")
    print(f"Confidence score: {res.confidence}")
