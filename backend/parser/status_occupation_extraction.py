import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import asdict, dataclass
from enum import Enum
import sys
import os
# === Import layout analyzer ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper

helper = Helper()
CONFIG = helper.config
        
status_patterns = helper.status_patterns
occupation_patterns = helper.occupation_patterns
education_levels = helper.education_levels
language_indicators = helper.language_indicators




class StatusType(Enum):
    INTERNSHIP = "looking_for_internship"
    FULL_TIME = "looking_for_full_time"
    PART_TIME = "looking_for_part_time"
    CURRENTLY_EMPLOYED = "currently_employed"
    STUDENT = "student"
    UNEMPLOYED = "unemployed"
    UNKNOWN = "unknown"

class OccupationLevel(Enum):
    STUDENT = "student"
    JUNIOR = "junior"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    UNKNOWN = "unknown"

@dataclass
class ExtractionResult:
    occupation: str
    occupation_level: OccupationLevel
    status: StatusType
    confidence_score: float
    raw_matches: Dict[str, List[str]]


def extract_status( text: str, language: str) -> Tuple[StatusType, float, List[str]]:
    """Extract employment status from text"""
    matches = {}
    confidence_scores = {}
    
    for status_key, patterns in status_patterns.items():
        try:
            status_type = StatusType(status_key)
        except ValueError:
            continue
            
        if language in patterns:
            status_matches = []
            for pattern in patterns[language]:
                found = re.findall(pattern, text, re.IGNORECASE)
                status_matches.extend(found)
            
            if status_matches:
                matches[status_type] = status_matches
                # Calculate confidence based on number and specificity of matches
                confidence_scores[status_type] = len(status_matches) * 0.3
    
    if not matches:
        return StatusType.UNKNOWN, 0.0, []
    
    # Determine the most likely status
    best_status = max(confidence_scores, key=confidence_scores.get)
    confidence = min(confidence_scores[best_status], 1.0)
    
    return best_status, confidence, matches.get(best_status, [])
def extract_occupation( text: str, language: str) -> Tuple[str, OccupationLevel, float, Dict[str, List[str]]]:
    """Extract occupation and level from text"""
    occupation_matches = {}
    occupation_scores = {}
    
    for occupation, config in occupation_patterns.items():
        if language in config['patterns']:
            matches = []
            for pattern in config['patterns'][language]:
                found = re.findall(pattern, text, re.IGNORECASE)
                matches.extend(found)
            
            if matches:
                occupation_matches[occupation] = matches
                occupation_scores[occupation] = len(matches)
    
    if not occupation_matches:
        return "unknown", OccupationLevel.UNKNOWN, 0.0, {}
    
    # Find best matching occupation
    best_occupation = max(occupation_scores, key=occupation_scores.get)
    
    # Determine level for the best occupation
    level = _extract_level(text, best_occupation)
    
    confidence = min(occupation_scores[best_occupation] * 0.4, 1.0)
    
    return best_occupation, level, confidence, occupation_matches
def _extract_level( text: str, occupation: str) -> OccupationLevel:
    """Extract the level/seniority for a given occupation"""
    if occupation not in occupation_patterns:
        return OccupationLevel.UNKNOWN
    
    levels_config = occupation_patterns[occupation].get('levels', {})
    
    for level_name, patterns in levels_config.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                try:
                    return OccupationLevel(level_name)
                except ValueError:
                    continue
    
    # Default level based on education indicators
    for level_name, patterns in education_levels.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                if level_name in ['bachelor', 'master']:
                    return OccupationLevel.STUDENT
    
    return OccupationLevel.UNKNOWN

def parce_status_and_occupation( cv_text: str) -> ExtractionResult:
    """Main parsing function"""
    # Preprocess text
    processed_text = helper.preprocess_text(cv_text)
    
    # Detect language
    language = helper.detect_language(processed_text)
    
    # Extract status
    status, status_confidence, status_matches = extract_status(processed_text, language)
    
    # Extract occupation
    occupation, occupation_level, occupation_confidence, occupation_matches = extract_occupation(processed_text, language)
    
    # Calculate overall confidence
    overall_confidence = (status_confidence + occupation_confidence) / 2
    
    return ExtractionResult(
        occupation=occupation,
        occupation_level=occupation_level,
        status=status,
        confidence_score=overall_confidence,
        raw_matches={
            'status_matches': status_matches,
            'occupation_matches': occupation_matches
        }
    )



# Example usage and testing
def test_parser():
    file = 'pdfs/karim.pdf'
    text = PyMuPDFLayoutAnalyzer(file).extract_with_layout_analysis()
    res = parce_status_and_occupation(text)


    print("===================")
    print(f"Status: {res.status}")
    print(f"Occupation: {res.occupation}")
    print(f"Occupation level: {res.occupation_level}")
    print(f"Confidence score: {res.confidence_score}")

 
if __name__ == '__main__':
    test_parser()