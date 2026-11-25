import os
import re
from typing import Optional


class DocumentParserService:
    """Robust document parser extracting clean plain text from PDF and DOCX files.
    
    Supports PyMuPDF (fitz) with automated pypdf fallback for PDFs,
    and python-docx for DOCX files.
    """

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extract text from PDF using PyMuPDF (fitz) or pypdf."""
        text_chunks = []
        
        # 1. Try PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page in doc:
                text = page.get_text()
                if text:
                    text_chunks.append(text)
            doc.close()
            if text_chunks:
                return DocumentParserService._clean_extracted_text("\n".join(text_chunks))
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARN] fitz extraction encountered an issue: {e}, falling back to pypdf.")

        # 2. Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_chunks.append(text)
            if text_chunks:
                return DocumentParserService._clean_extracted_text("\n".join(text_chunks))
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARN] pypdf extraction encountered an issue: {e}")

        # 3. Fallback to pure python binary/regex text extraction
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                # Extract text strings between parentheses or streams
                extracted = re.findall(rb"\((.*?)\)", content)
                decoded = " ".join([c.decode("utf-8", errors="ignore") for c in extracted if len(c) > 3])
                if len(decoded.strip()) > 50:
                    return DocumentParserService._clean_extracted_text(decoded)
        except Exception as e:
            print(f"[ERROR] Direct binary PDF parse error: {e}")

        raise ValueError("Could not extract readable text from PDF. Please ensure file is not password-protected or scanned without text.")

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """Extract text from DOCX using python-docx with zip/xml fallback."""
        text_chunks = []
        
        # 1. Try python-docx
        try:
            import docx
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_chunks.append(para.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text_chunks.append(" | ".join(row_text))
            if text_chunks:
                return DocumentParserService._clean_extracted_text("\n".join(text_chunks))
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARN] python-docx extraction issue: {e}, attempting zipfile fallback.")

        # 2. Pure Python zipfile + XML fallback for DOCX
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                # Word XML namespace
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for node in tree.iterfind(".//w:p", ns):
                    texts = [t.text for t in node.iterfind(".//w:t", ns) if t.text]
                    if texts:
                        text_chunks.append("".join(texts))
            if text_chunks:
                return DocumentParserService._clean_extracted_text("\n".join(text_chunks))
        except Exception as e:
            print(f"[ERROR] DOCX fallback extraction failed: {e}")

        raise ValueError("Could not extract readable text from DOCX document.")

    @staticmethod
    def parse_document(file_path: str, file_type: str) -> str:
        """Unified document parser dispatcher."""
        norm_type = file_type.lower().replace(".", "").strip()
        if norm_type == "pdf":
            return DocumentParserService.extract_text_from_pdf(file_path)
        elif norm_type in ("docx", "doc"):
            return DocumentParserService.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format '{file_type}'. Supported formats: .pdf, .docx")

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Normalize line breaks, remove extraneous whitespace, and clean artifacts."""
        # Replace non-breaking spaces and control chars
        text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Collapse multiple inline spaces
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


document_parser = DocumentParserService()
