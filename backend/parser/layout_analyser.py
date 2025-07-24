import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from typing import List, Dict
import spacy
import json
import os
import io
import re

class PyMuPDFLayoutAnalyzer:
    def __init__(self, pdf_path: str, config_path: str = "../constants/config.json", lang="en"):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

        # Load spaCy language model
        if lang == "fr":
            self.nlp = spacy.load("fr_core_news_sm")
        else:
            self.nlp = spacy.load("en_core_web_sm")

        self.lang = lang
        self.ocr_lang = "eng+fra"  # for pytesseract

        # Load config
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
        
        with open(config_path, "r") as f:
            config = json.load(f)
            self.config = config  
            self.section_headers = [h.upper() for h in config.get("section_headers", [])]
            self.blacklist_headers = set(config.get("blacklist_headers", []))

    def extract_with_layout_analysis(self) -> str:
        """Main extraction loop with layout + OCR fallback"""
        full_text = ""
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            print(f"Processing page {page_num + 1}...")

            blocks = page.get_text("dict")
            structured_text = self._process_blocks(blocks)

            if not structured_text.strip():
                print("No text found, using OCR...")
                structured_text = self._extract_text_with_ocr(page)

            full_text += structured_text + "\n\n"

        return full_text.strip()

    def _extract_text_with_ocr(self, page) -> str:
        """Fallback OCR using pytesseract"""
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=self.ocr_lang)

        # Heuristic cleanup
        lines = text.splitlines()
        formatted = ""
        for line in lines:
            if self._is_likely_header(line):
                formatted += f"\n{line.strip().upper()}\n"
            elif line.strip():
                formatted += f"{line.strip()}\n"
        return formatted

    def _process_blocks(self, page_dict: Dict) -> str:
        """Sort blocks spatially and detect headers"""
        text_blocks = []
        for block in page_dict.get("blocks", []):
            if "lines" in block:
                block_text = ""
                font_sizes = []
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                        font_sizes.append(span["size"])
                    block_text += "\n"
                if block_text.strip():
                    text_blocks.append({
                        "text": block_text.strip(),
                        "bbox": block["bbox"],
                        "x0": block["bbox"][0],
                        "y0": block["bbox"][1],
                        "x1": block["bbox"][2],
                        "y1": block["bbox"][3],
                        "font_size": max(font_sizes) if font_sizes else 0,
                    })

        # Sort top-to-bottom, left-to-right (improves columns handling)
        text_blocks.sort(key=lambda b: (round(b["y0"] / 20), round(b["x0"] / 20)))

        formatted_text = ""
        for block in text_blocks:
            text = block["text"]
            if self._is_likely_header(text):
                formatted_text += f"\n{text.upper()}\n"
            else:
                formatted_text += f"{text}\n"
        return formatted_text

    def _is_likely_header(self, text: str) -> bool:
        """Heuristics to detect section headers (multi-language, capital letters, short phrases)"""
        clean = text.strip().upper()

        # Explicit match with known headers
        if any(header in clean for header in self.section_headers):
            return True

        # Common formatting rules
        if len(clean) < 50 and clean == text.strip() and clean.isupper():
            return True

        # Heading-like punctuation (optional)
        if re.match(r"^[A-Z\s\-]+:?$", clean):
            return True

        return False

    def get_text_blocks(self, raw_text: str) -> List[Dict]:
        """Extract blocks with font size and positions"""
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

    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()
