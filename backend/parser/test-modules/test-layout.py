import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from typing import List, Dict, Optional
import spacy
import json
import os
import io
import re
from rapidfuzz import fuzz, process

class PyMuPDFLayoutAnalyzer:
    def __init__(self, pdf_path: str, config_path: str = "../constants/config.json", lang="en", fuzz_threshold=80):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

        # Load spaCy language model
        if lang == "fr":
            self.nlp = spacy.load("fr_core_news_sm")
        else:
            self.nlp = spacy.load("en_core_web_sm")

        self.lang = lang
        self.ocr_lang = "eng+fra"  # pytesseract langs
        self.fuzz_threshold = fuzz_threshold  # fuzzy matching threshold for headers

        # Load config
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
        
        with open(config_path, "r") as f:
            config = json.load(f)
            self.config = config
            self.section_headers = [h.upper() for h in config.get("section_headers", [])]
            self.blacklist_headers = set([h.upper() for h in config.get("blacklist_headers", [])])

    def extract_sections(self) -> Dict[str, str]:
        """
        Extract text from all pages, split by section headers using fuzzy matching.
        Returns dict {section_name: text}.
        """
        raw_text = ""
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            print(f"Processing page {page_num + 1}...")
            page_text = self._extract_page_text(page)
            raw_text += page_text + "\n\n"

        # Normalize lines and split to lines
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        # Detect section header line indices via fuzzy matching
        header_indices = []
        for i, line in enumerate(lines):
            matched_header = self._fuzzy_match_header(line)
            if matched_header:
                header_indices.append((i, matched_header))

        # If no headers found, return everything as "FULL_TEXT"
        if not header_indices:
            return {"FULL_TEXT": raw_text.strip()}

        # Extract sections between headers
        sections = {}
        for idx, (start_line, header) in enumerate(header_indices):
            end_line = header_indices[idx + 1][0] if idx + 1 < len(header_indices) else len(lines)
            section_text = "\n".join(lines[start_line + 1 : end_line]).strip()
            sections[header] = sections.get(header, "") + section_text + "\n"

        return sections

    def _extract_page_text(self, page) -> str:
        """
        Extract text for a single page by layout analysis,
        fallback on OCR if empty.
        """
        blocks = page.get_text("dict")
        text = self._process_blocks(blocks)
        if not text.strip():
            print("No text found by digital extraction, using OCR...")
            text = self._extract_text_with_ocr(page)
        return text

    def _process_blocks(self, page_dict: Dict) -> str:
        """
        Sort blocks spatially and detect headers,
        reconstruct text with clear headers in uppercase.
        """
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

        # Sort top-to-bottom, left-to-right for column support
        text_blocks.sort(key=lambda b: (round(b["y0"] / 20), round(b["x0"] / 20)))

        formatted_text = ""
        for block in text_blocks:
            text = block["text"]
            if self._is_likely_header(text):
                formatted_text += f"\n{text.upper()}\n"
            else:
                formatted_text += f"{text}\n"
        return formatted_text

    def _extract_text_with_ocr(self, page) -> str:
        """Fallback OCR extraction using pytesseract"""
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang=self.ocr_lang)

        # Format headers heuristically
        lines = text.splitlines()
        formatted = ""
        for line in lines:
            if self._is_likely_header(line):
                formatted += f"\n{line.strip().upper()}\n"
            elif line.strip():
                formatted += f"{line.strip()}\n"
        return formatted

    def _is_likely_header(self, text: str) -> bool:
        """
        Heuristics for detecting headers, same as before but using fuzzy matching optionally.
        """
        clean = text.strip().upper()

        # Exact or fuzzy match with known headers
        for header in self.section_headers:
            if header in clean:
                return True

        # Common header style: uppercase, short, punctuation
        if len(clean) < 50 and clean == text.strip() and clean.isupper():
            return True

        if re.match(r"^[A-Z\s\-]+:?$", clean):
            return True

        return False

    def _fuzzy_match_header(self, text: str) -> Optional[str]:
        """
        Fuzzy match text line to known section headers,
        return matched header or None.
        """
        clean = text.strip().upper()
        # Use rapidfuzz process.extractOne
        match, score, _ = process.extractOne(clean, self.section_headers, scorer=fuzz.partial_ratio)
        if score >= self.fuzz_threshold:
            return match
        return None

    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()
