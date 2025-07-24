import re
import sys
import os
import json
from unidecode import unidecode
from typing import List


# === Load config.json ===
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..','..','constants', 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# === Import layout analyzer ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer


class Helper:
    def __init__(self):
        self.config = CONFIG
        self.status_patterns = self.config.get('status_patterns', {})
        self.occupation_patterns = self.config.get('occupation_patterns', {})
        self.education_levels = self.config.get('education_levels', {})        
        self.language_indicators = self.config.get('language_indicators', {})
        self.cities = self.config.get('cities', [])
        self.skills = self.config.get('skills', [])
        self.skills_headers = self.config.get('skills_headers', [])
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better matching"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep accents
        text = re.sub(r'[^\w\s\u00C0-\u017F]', ' ', text)
        return text.strip()
    
    
    def normalize_text(self, text):
        if not text:
            return ""
        text = unidecode(text.lower().strip())
        text = re.sub(r'\s+', ' ', text)
        return text
    

    def detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        french_indicators = self.language_indicators.get('french', [])
        english_indicators = self.language_indicators.get('english', [])

        french_count = sum(1 for word in french_indicators if word in text.lower())
        english_count = sum(1 for word in english_indicators if word in text.lower())
        return 'french' if french_count > english_count else 'english'
    
    
    def is_education_section(self, lines, index, window=3):
        education_indicators = self.config.get("education_headers", [])
        start = max(0, index - window)
        end = min(len(lines), index + window)
        context = ' '.join(lines[start:end]).lower()
        return any(indicator in context for indicator in education_indicators)
    
    def clean_field_name(self,field):
        noise_patterns = [
            r'\b(?:degree|diploma|programme|program|formation|cycle|year|annee|niveau)\b',
            r'\([^)]*\)',  # remove (xx)
            r'[^\w\s-]',   # remove punctuation
            r'\s{2,}',     # collapse multiple spaces
        ]
        field = field.lower()
        for pattern in noise_patterns:
            field = re.sub(pattern, ' ', field, flags=re.IGNORECASE)

        field = ' '.join(field.split())  # Remove extra spaces
        return field.strip()
    
    def extract_section(self,text: str, section_names: List[str], next_section_names: List[str]) -> str:
        lines = text.splitlines()
        section_lines = []
        is_in_section = False

        for line in lines:
            line_clean = line.strip().lower()
            if any(header in line_clean for header in section_names):
                #print(f"[DEBUG] Found start of section at: {line}")
                is_in_section = True
                continue
            if is_in_section and any(header in line_clean for header in next_section_names):
                #print(f"[DEBUG] Found end of section at: {line}")
                break
            if is_in_section:
                section_lines.append(line)

        #print(f"[DEBUG] Extracted section content:\n{section_lines[:5]}...") 
        return "\n".join(section_lines).strip()


