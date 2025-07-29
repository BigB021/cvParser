import sys
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from typing import List, Dict, Tuple
import io
import re
import os


class RobustPDFTextExtractor:
    def __init__(self, pdf_path: str, lang="en+fr", dpi=300):
        """
        Initialize the PDF text extractor
        
        Args:
            pdf_path: Path to the PDF file
            lang: Language for OCR ("en", "fr", or "en+fr")
            dpi: DPI for OCR rendering (higher = better quality, slower)
        """
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.dpi = dpi
        
        # OCR language mapping
        ocr_lang_map = {
            "en": "eng",
            "fr": "fra", 
            "en+fr": "eng+fra"
        }
        self.ocr_lang = ocr_lang_map.get(lang, "eng+fra")
        
        # Layout analysis parameters
        self.line_height_threshold = 5  # pixels
        self.column_gap_threshold = 50  # pixels
        self.paragraph_gap_threshold = 15  # pixels

    def extract_text(self) -> str:
        """
        Main extraction method that returns formatted text string
        Automatically detects if PDF is digital or scanned
        """
        full_text = ""
        
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            
            # Try digital extraction first
            page_text = self._extract_digital_text(page)
            
            # If no meaningful text found, use OCR
            if not self._has_meaningful_text(page_text):
                print(f"Page {page_num + 1}: Using OCR (scanned or image-based)")
                page_text = self._extract_with_ocr(page)
            else:
                print(f"Page {page_num + 1}: Digital text extraction")
            
            # Add page separator for multi-page documents
            if page_num > 0:
                full_text += "\n" + "="*80 + f" PAGE {page_num + 1} " + "="*80 + "\n\n"
            
            full_text += page_text
        
        return self._post_process_text(full_text)

    def _extract_digital_text(self, page) -> str:
        """
        Extract text from digital PDF with layout preservation
        """
        # Get text blocks with detailed positioning
        blocks = page.get_text("dict")
        text_elements = self._parse_text_blocks(blocks)
        
        if not text_elements:
            return ""
        
        # Sort elements by position (top-to-bottom, left-to-right)
        text_elements.sort(key=lambda x: (round(x['y0'] / self.line_height_threshold), 
                                        round(x['x0'] / self.column_gap_threshold)))
        
        # Group into columns and lines
        formatted_text = self._reconstruct_layout(text_elements)
        
        return formatted_text

    def _parse_text_blocks(self, page_dict: Dict) -> List[Dict]:
        """
        Parse PyMuPDF text blocks into structured elements
        """
        text_elements = []
        
        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                line_text = ""
                font_sizes = []
                font_flags = []
                
                for span in line["spans"]:
                    text = span["text"]
                    if text.strip():  # Only process non-empty spans
                        line_text += text
                        font_sizes.append(span.get("size", 12))
                        font_flags.append(span.get("flags", 0))
                
                if line_text.strip():
                    text_elements.append({
                        'text': line_text,
                        'x0': line["bbox"][0],
                        'y0': line["bbox"][1], 
                        'x1': line["bbox"][2],
                        'y1': line["bbox"][3],
                        'font_size': max(font_sizes) if font_sizes else 12,
                        'is_bold': any(flag & 2**4 for flag in font_flags),  # Bold flag
                        'width': line["bbox"][2] - line["bbox"][0],
                        'height': line["bbox"][3] - line["bbox"][1]
                    })
        
        return text_elements

    def _reconstruct_layout(self, elements: List[Dict]) -> str:
        """
        Reconstruct text layout preserving spacing, columns, and paragraphs
        """
        if not elements:
            return ""
        
        formatted_lines = []
        current_y = elements[0]['y0']
        current_line_elements = []
        
        for element in elements:
            # Check if we're on a new line
            if abs(element['y0'] - current_y) > self.line_height_threshold:
                # Process current line
                if current_line_elements:
                    line_text = self._merge_line_elements(current_line_elements)
                    formatted_lines.append({
                        'text': line_text,
                        'y': current_y,
                        'gap_after': 0
                    })
                
                # Start new line
                current_line_elements = [element]
                current_y = element['y0']
            else:
                current_line_elements.append(element)
        
        # Don't forget the last line
        if current_line_elements:
            line_text = self._merge_line_elements(current_line_elements)
            formatted_lines.append({
                'text': line_text,
                'y': current_y,
                'gap_after': 0
            })
        
        # Calculate gaps between lines for paragraph detection
        for i in range(len(formatted_lines) - 1):
            gap = formatted_lines[i + 1]['y'] - formatted_lines[i]['y']
            formatted_lines[i]['gap_after'] = gap
        
        # Build final text with proper spacing
        result = ""
        for i, line in enumerate(formatted_lines):
            result += line['text']
            
            # Add appropriate line breaks based on gaps
            if i < len(formatted_lines) - 1:
                if line['gap_after'] > self.paragraph_gap_threshold:
                    result += "\n\n"  # Paragraph break
                else:
                    result += "\n"   # Regular line break
        
        return result

    def _merge_line_elements(self, elements: List[Dict]) -> str:
        """
        Merge elements on the same line, preserving horizontal spacing
        """
        if not elements:
            return ""
        
        # Sort by x position
        elements.sort(key=lambda x: x['x0'])
        
        merged_text = ""
        prev_x1 = None
        
        for element in elements:
            text = element['text']
            
            # Add spacing between elements if there's a gap
            if prev_x1 is not None:
                gap = element['x0'] - prev_x1
                if gap > self.column_gap_threshold:
                    # Large gap - likely different columns
                    merged_text += "    "  # Tab-like spacing
                elif gap > 10:  # Smaller gap - add spaces
                    num_spaces = min(max(1, int(gap / 6)), 8)  # Reasonable spacing
                    merged_text += " " * num_spaces
                elif not merged_text.endswith(" ") and not text.startswith(" "):
                    merged_text += " "  # Ensure word separation
            
            merged_text += text
            prev_x1 = element['x1']
        
        return merged_text

    def _extract_with_ocr(self, page) -> str:
        """
        Extract text using OCR with layout preservation
        """
        # Render page at high DPI for better OCR accuracy
        pix = page.get_pixmap(dpi=self.dpi)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Use pytesseract with layout preservation
        try:
            # Get text with bounding boxes for layout reconstruction
            data = pytesseract.image_to_data(img, lang=self.ocr_lang, output_type=pytesseract.Output.DICT)
            
            # Reconstruct text with layout
            ocr_text = self._reconstruct_ocr_layout(data)
            
            if not ocr_text.strip():
                # Fallback to simple text extraction
                ocr_text = pytesseract.image_to_string(img, lang=self.ocr_lang)
                
        except Exception as e:
            print(f"OCR error: {e}")
            # Final fallback
            ocr_text = pytesseract.image_to_string(img, lang=self.ocr_lang)
        
        return ocr_text

    def _reconstruct_ocr_layout(self, data: Dict) -> str:
        """
        Reconstruct layout from pytesseract output data
        """
        lines = {}
        
        # Group words by line
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 30:  # Filter low confidence
                text = data['text'][i].strip()
                if text:
                    top = data['top'][i]
                    left = data['left'][i]
                    
                    # Group by approximate line (allowing some variance)
                    line_key = round(top / 10) * 10
                    
                    if line_key not in lines:
                        lines[line_key] = []
                    
                    lines[line_key].append({
                        'text': text,
                        'left': left,
                        'top': top
                    })
        
        # Sort lines by vertical position
        sorted_lines = sorted(lines.items())
        
        result = ""
        prev_line_top = None
        
        for line_top, words in sorted_lines:
            # Sort words by horizontal position
            words.sort(key=lambda w: w['left'])
            
            # Add paragraph breaks for large vertical gaps
            if prev_line_top is not None and line_top - prev_line_top > 30:
                result += "\n\n"
            elif result:
                result += "\n"
            
            # Merge words with appropriate spacing
            line_text = ""
            prev_right = None
            
            for word in words:
                if prev_right is not None:
                    gap = word['left'] - prev_right
                    if gap > 50:  # Large gap - likely different column
                        line_text += "    "
                    elif gap > 15:  # Medium gap
                        line_text += "  "
                    elif not line_text.endswith(" "):
                        line_text += " "
                
                line_text += word['text']
                prev_right = word['left'] + len(word['text']) * 8  # Approximate width
            
            result += line_text
            prev_line_top = line_top
        
        return result

    def _has_meaningful_text(self, text: str) -> bool:
        """
        Check if extracted text is meaningful (not just artifacts)
        """
        if not text or len(text.strip()) < 10:
            return False
        
        # Check for reasonable ratio of alphanumeric characters
        alphanumeric = sum(c.isalnum() for c in text)
        total_chars = len(text.replace(' ', '').replace('\n', ''))
        
        if total_chars == 0:
            return False
        
        ratio = alphanumeric / total_chars
        return ratio > 0.6  # At least 60% should be meaningful characters

    def _post_process_text(self, text: str) -> str:
        """
        Clean up and normalize the extracted text
        """
        # Remove excessive whitespace while preserving structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean up line but preserve intentional spacing
            cleaned = re.sub(r'[ \t]+', ' ', line.strip())
            cleaned_lines.append(cleaned)
        
        # Remove excessive empty lines (max 2 consecutive)
        result = []
        empty_count = 0
        
        for line in cleaned_lines:
            if not line:
                empty_count += 1
                if empty_count <= 2:
                    result.append(line)
            else:
                empty_count = 0
                result.append(line)
        
        # Join and final cleanup
        final_text = '\n'.join(result)
        
        # Remove any remaining problematic characters but preserve structure
        final_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', final_text)
        
        return final_text.strip()

    def get_document_info(self) -> Dict:
        """
        Get basic document information
        """
        return {
            'page_count': len(self.doc),
            'file_path': self.pdf_path,
            'file_size': os.path.getsize(self.pdf_path) if os.path.exists(self.pdf_path) else 0
        }

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'doc') and self.doc:
            self.doc.close()



# Usage example
def main():
    """Example usage"""
    # Initialize extractor
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..", "pdfs", sys.argv[1] + ".pdf" if len(sys.argv) > 1 else "youssef.pdf"))

    extractor = RobustPDFTextExtractor(pdf_path, lang="en+fr", dpi=300)
    
    # Extract text
    extracted_text = extractor.extract_text()
    
    # Print or save the result
    print("Extracted Text:")
    print("=" * 80)
    print(extracted_text)
    
    # Get document info
    info = extractor.get_document_info()
    print(f"\nDocument Info: {info}")
    
    # Save to file if needed
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(extracted_text)


if __name__ == "__main__":
    main()