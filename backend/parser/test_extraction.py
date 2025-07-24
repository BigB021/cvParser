import sys
import os
import pprint

from name_city_extraction import extract_name, extract_city
from email_phone_extraction import extract_email, extract_phone_number
from degree_extraction import extract_degrees
from status_occupation_extraction import extract_occupation,extract_status
from skills_experience_extraction import extract_skills, extract_experience_years

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper

helper = Helper()

# Main execution (testing)
if __name__ == "__main__":
    pdf_path = "tests/youssef.pdf"
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    # Preprocess text
    processed_text = helper.preprocess_text(text)
    language = helper.detect_language(processed_text)
    cities = [city.lower() for city in  helper.cities]

    experience_section = helper.extract_section(
        text,
        section_names=helper.config.get("experience", []),
        next_section_names=helper.config.get("next_section", [])
    )

    education_section = helper.extract_section(
        text,
        section_names=helper.config.get("education_headers", []),
        next_section_names=helper.config.get("next_section", [])
    )

    status_tuple = extract_status(text, language)

    # Detect language
    resume_data = {
        "name": extract_name(text,analyzer),
        "email": extract_email(text),
        "phone": extract_phone_number(text),
        "city": extract_city(text,cities),
        "status": {status_tuple[0].value},
        "degrees": extract_degrees(text),
        "occupation": extract_occupation(text,language),
        "exp_years": extract_experience_years(experience_section),
        "skills": extract_skills(text, helper.skills, helper.skills_headers)

    }

    #print(f"text: {text}")
    print(f"======================================")
    pprint.pprint(resume_data)
    print(f"======================================")
    print(f"education section : {education_section}")
