import fitz
import pytesseract
from PIL import Image
from typing import List, Dict
import spacy
import json
import os
import io

class PyMuPDFLayoutAnalyzer:
    def __init__(self, pdf_path: str, config_path: str = "../constants/config.json"):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.nlp = spacy.load("en_core_web_sm")

        # Load configuration
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
        
        with open(config_path, "r") as f:
            config = json.load(f)
            self.config = config  
            self.section_headers = config.get("section_headers", [])
            self.blacklist_headers = set(config.get("blacklist_headers", []))
            # self.job_titles = config.get("job_titles", [])
            # self.cities = [city.lower() for city in config["cities"]]
            # self.degrees = config.get("degree_aliases", {})
            # self.experience = config.get("experience", [])
            # self.next_section = config.get("next_section", [])
            # self.skills = config.get("skills", [])
            # self.skills_headers = config.get("skills_headers", [])
            # self.education = config.get("education_headers", [])
            # self.institutions = config.get("institutions", [])

    def extract_with_layout_analysis(self) -> str:
        """Extract text with layout analysis and fallback to OCR if necessary."""
        full_text = ""
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            print(f"Processing page {page_num + 1}")

            # Try layout extraction
            blocks = page.get_text("dict")
            structured_text = self._process_blocks(blocks)

            # If no real text found, use OCR
            if not structured_text.strip():
                print("Fallback to OCR for this page.")
                structured_text = self._extract_text_with_ocr(page)

            full_text += structured_text + "\n\n"
        return full_text.strip()

    def _extract_text_with_ocr(self, page) -> str:
        """Convert page to image and apply OCR for text extraction"""
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang='eng')

        # Basic cleanup & section formatting
        lines = text.splitlines()
        formatted = ""
        for line in lines:
            if self._is_likely_header(line):
                formatted += f"\n{line.upper()}\n"
            elif line.strip():
                formatted += f"{line}\n"
        return formatted

    def _process_blocks(self, page_dict: Dict) -> str:
        """Process text blocks and maintain layout structure"""
        text_blocks = []
        for block in page_dict.get("blocks", []):
            if "lines" in block:
                block_text = ""
                block_bbox = block["bbox"]
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        line_text += span["text"]
                    if line_text.strip():
                        block_text += line_text + "\n"
                if block_text.strip():
                    text_blocks.append({
                        "text": block_text.strip(),
                        "bbox": block_bbox,
                        "x0": block_bbox[0],
                        "y0": block_bbox[1],
                        "x1": block_bbox[2],
                        "y1": block_bbox[3]
                    })

        text_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
        formatted_text = ""
        for block in text_blocks:
            text = block["text"]
            if self._is_likely_header(text):
                formatted_text += f"\n{text.upper()}\n"
            else:
                formatted_text += f"{text}\n"
        return formatted_text

    def get_text_blocks(self, raw_text: str) -> List[Dict]:
        """Extract font and layout information (useful for name detection etc.)"""
        blocks_with_fonts = []
        for page in self.doc:
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if "lines" in block:
                    block_text = ""
                    font_sizes = []
                    for line in block["lines"]:
                        for span in line["spans"]:
                            block_text += span["text"] + " "
                            font_sizes.append(span["size"])
                    if block_text.strip():
                        blocks_with_fonts.append({
                            "text": block_text.strip(),
                            "y0": block["bbox"][1],
                            "x0": block["bbox"][0],
                            "font_size": max(font_sizes) if font_sizes else 0,
                        })
        return blocks_with_fonts

    def _is_likely_header(self, text: str) -> bool:
        """Determine if text is likely a header/title"""
        text_upper = text.upper().strip()
        if any(header in text_upper for header in self.section_headers):
            return True
        if len(text.strip()) < 50 and text.isupper():
            return True
        return False

    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()
