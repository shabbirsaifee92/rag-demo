import pytesseract
from PIL import Image
import pandas as pd
import io
import fitz  # PyMuPDF
import docx2txt
import re
from typing import List, Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentPreprocessor:
    def __init__(self):
        self.supported_formats = {
            'pdf': self._process_pdf,
            'docx': self._process_docx,
            'png': self._process_image,
            'jpg': self._process_image,
            'jpeg': self._process_image
        }

    def process_document(self, file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Process document and extract content including tables and annotations."""
        file_ext = filename.split('.')[-1].lower()

        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")

        return self.supported_formats[file_ext](file_content)

    def _process_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        """Process PDF files, extracting text, tables, and annotations."""
        chunks = []
        doc = fitz.open(stream=content, filetype="pdf")

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text
            text = page.get_text()

            # Extract tables
            tables = self._extract_tables_from_pdf_page(page)

            # Extract annotations
            annotations = self._extract_annotations(page)

            # Process text content
            text_chunks = self._chunk_text(text)
            for chunk in text_chunks:
                chunks.append({
                    'content': chunk,
                    'type': 'text',
                    'page': page_num + 1,
                    'metadata': {'source_type': 'text'}
                })

            # Add tables
            for table in tables:
                chunks.append({
                    'content': table,
                    'type': 'table',
                    'page': page_num + 1,
                    'metadata': {'source_type': 'table'}
                })

            # Add annotations
            for annotation in annotations:
                chunks.append({
                    'content': annotation,
                    'type': 'annotation',
                    'page': page_num + 1,
                    'metadata': {'source_type': 'annotation'}
                })

        return chunks

    def _process_docx(self, content: bytes) -> List[Dict[str, Any]]:
        """Process DOCX files, extracting text and tables."""
        text = docx2txt.process(io.BytesIO(content))
        chunks = []

        # Extract tables using regex patterns
        table_pattern = r'\|.*\|'
        tables = re.findall(table_pattern, text, re.MULTILINE)

        # Remove tables from text
        clean_text = re.sub(table_pattern, '', text, flags=re.MULTILINE)

        # Process main text
        text_chunks = self._chunk_text(clean_text)
        for chunk in text_chunks:
            chunks.append({
                'content': chunk,
                'type': 'text',
                'page': 1,  # DOCX doesn't have pages
                'metadata': {'source_type': 'text'}
            })

        # Process tables
        for table in tables:
            chunks.append({
                'content': table,
                'type': 'table',
                'page': 1,
                'metadata': {'source_type': 'table'}
            })

        return chunks

    def _process_image(self, content: bytes) -> List[Dict[str, Any]]:
        """Process images using OCR."""
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image)

        chunks = []
        text_chunks = self._chunk_text(text)

        for chunk in text_chunks:
            chunks.append({
                'content': chunk,
                'type': 'text',
                'page': 1,
                'metadata': {
                    'source_type': 'ocr',
                    'confidence': self._calculate_ocr_confidence(chunk)
                }
            })

        return chunks

    def _extract_tables_from_pdf_page(self, page) -> List[str]:
        """Extract tables from PDF page."""
        tables = []
        # Find table-like structures using layout analysis
        blocks = page.get_text("blocks")
        for block in blocks:
            if self._is_table_block(block):
                table_text = self._format_table_block(block)
                tables.append(table_text)
        return tables

    def _extract_annotations(self, page) -> List[str]:
        """Extract annotations from PDF page."""
        annotations = []
        for annot in page.annots():
            if annot.info.get('content'):
                annotations.append(annot.info['content'])
        return annotations

    def _is_table_block(self, block) -> bool:
        """Detect if a block represents a table."""
        # Simple heuristic: check for multiple vertical bars or tabs
        text = block[4]
        return '|' in text or '\t' in text or text.count('  ') > 3

    def _format_table_block(self, block) -> str:
        """Format table block into a string representation."""
        return block[4].replace('\n', ' ').strip()

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # Adjust chunk boundaries to not split words
            if end < text_length:
                last_space = chunk.rfind(' ')
                if last_space != -1:
                    end = start + last_space
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def _calculate_ocr_confidence(self, text: str) -> float:
        """Calculate confidence score for OCR text."""
        # Simple heuristic based on text characteristics
        words = text.split()
        if not words:
            return 0.0

        # Check for common OCR errors
        error_patterns = [
            r'\d[a-zA-Z]',  # Mixed digits and letters
            r'[^a-zA-Z0-9\s\.,;:\'\"!?\-()]',  # Unusual characters
            r'\s{3,}'  # Multiple spaces
        ]

        error_count = sum(1 for pattern in error_patterns for _ in re.finditer(pattern, text))
        confidence = max(0.0, min(1.0, 1.0 - (error_count / len(words))))

        return confidence
