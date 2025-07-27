import sys
import os
import re
from typing import Optional
from rapidfuzz import process
from typing import List


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.helper import Helper
from layout_analyser import PyMuPDFLayoutAnalyzer

helper = Helper()
def extract_email(text: str) -> Optional[str]:
    """Extract email using regex"""
    text = re.sub(r'\s*@\s*', '@', text)  # removes spaces around @

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_phone_number(text: str) -> Optional[str]:
    """Extract Moroccan phone numbers using regex"""
    patterns = [
        r'\+212[\s-]*(?:\(0\)[\s-]*)?(?:6|7)[\d\s()/.-]{6,}',
        r'(?:06|07)[\d\s()-]{8,}',
        r'212[\s-]*(?:6|7)[\d\s()-]{8,}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0]
            phone = re.sub(r'\s+|[-().]', '', phone)  # Remove whitespace, dashes, dots, parentheses
            phone = phone.replace('\n', '').strip('.').strip()

            return phone
    return None



# Main execution (testing)
if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), ".." ,"pdfs", sys.argv[1]+ ".pdf" if len(sys.argv) > 1 else "youssef.pdf")
    analyzer = PyMuPDFLayoutAnalyzer(pdf_path)
    text = analyzer.extract_with_layout_analysis()
    # print(text)
    print(f"file:{pdf_path}")
    phone = extract_phone_number(text)
    email = extract_email(text)
    print(f"Phone: {phone} ")
    print(f"Email: {email} ")