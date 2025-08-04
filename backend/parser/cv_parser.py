import sys
import os
import pprint

from parser.name_city_extraction import extract_name, extract_city
from parser.email_phone_extraction import extract_email, extract_phone_number
from parser.degree_extraction import extract_degrees
from parser.status_occupation_extraction import extract_occupation, extract_status
from parser.skills_experience_extraction import extract_skills, extract_experience_years

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from layout_analyser import PyMuPDFLayoutAnalyzer
from utils.helper import Helper
from models.resume import add_resume
helper = Helper()


def parse_pdf_to_data(pdf_path):
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

    status, status_confidence, status_matches = extract_status(text, language)
    occupation, occupation_level, occupation_confidence, occupation_matches = extract_occupation(text, language)


    resume_data = {
        "name": extract_name(text,analyzer),
        "email": extract_email(text),
        "phone": extract_phone_number(text),
        "city": extract_city(text,cities),
        "status": status.value,
        "degrees": extract_degrees(text),
        "occupation": occupation,
        "exp_years": extract_experience_years(experience_section),
        "skills": extract_skills(text, helper.skills, helper.skills_headers),
        "pdf_path": pdf_path,

    }

    #debugging
    print(f"======================================")
    print(f"Text extracted from PDF:")
    print(text)
    print(f"======================================")
    print(f"file:{pdf_path}")
    print(f"Name: {resume_data['name']}")
    print(f"Email: {resume_data['email']}")
    print(f"Phone: {resume_data['phone']}")
    print(f"City: {resume_data['city']}")
    print(f"Status: {status.value} (Confidence: {status_confidence})")
    print(f"Occupation: {occupation} (Level: {occupation_level}, Confidence: {occupation_confidence})")
    print(f"Degrees: {resume_data['degrees']}")
    print(f"Experience Years: {resume_data['exp_years']}")
    print(f"Skills: {resume_data['skills']}")

    return resume_data

# todo: implement error handling typshit and data verification ?
def process_and_store_resume(pdf_path):
    resume_data = parse_pdf_to_data(pdf_path)
    print(f"[Debug] adding {resume_data['name']} resume to db..")
    add_resume(resume_data)

    return resume_data


# Main execution (testing)
if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), ".." ,"pdfs", sys.argv[1]+ ".pdf" if len(sys.argv) > 1 else "youssef.pdf")
    resume_data = parse_pdf_to_data(pdf_path)
    
    process_and_store_resume(pdf_path)

    if (sys.argv[2] == "debug"):
        print(f"Debug mode enabled, printing resume data:")
        analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
        text = analyzer.extract_with_layout_analysis()
        print(text)
    print(f"======================================")
    pprint.pprint(resume_data)
    print(f"======================================")
