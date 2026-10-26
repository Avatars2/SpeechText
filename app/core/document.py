from datetime import datetime
import logging
import os
from typing import Optional

# Suppress harmless fontTools font-subsetting warnings
logging.getLogger("fontTools").setLevel(logging.ERROR)
logging.getLogger("fontTools.subset").setLevel(logging.ERROR)

from fpdf import FPDF
from pypdf import PdfReader


class DocumentHandler:
    """
    Handles reading and exporting of PDF documents (.pdf) for STT and TTS workflows.
    """

    SYSTEM_INDIC_FONT = r"C:\Windows\Fonts\Nirmala.ttc"

    @classmethod
    def import_text_from_file(cls, file_path: str) -> str:
        """
        Extract text content exclusively from a .pdf file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return cls._read_pdf_file(file_path)
        else:
            raise ValueError(f"Unsupported format '{ext}'. Only PDF documents (.pdf) are supported.")

    @classmethod
    def export_to_pdf(cls, text: str, output_path: str, title: str = "SpeechText Document") -> str:
        """
        Generate a styled PDF document from text with complete Hindi, Gujarati,
        and English typography support.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        has_indic_font = False
        if os.path.exists(cls.SYSTEM_INDIC_FONT):
            try:
                pdf.add_font("IndicFont", "", cls.SYSTEM_INDIC_FONT)
                pdf.set_font("IndicFont", size=11)
                has_indic_font = True
            except Exception:
                has_indic_font = False

        if not has_indic_font:
            pdf.set_font("Helvetica", size=11)

        # Header bar
        pdf.set_fill_color(245, 247, 250)
        pdf.rect(0, 0, 210, 25, "F")

        # Header Title
        if has_indic_font:
            pdf.set_font("IndicFont", size=15)
        else:
            pdf.set_font("Helvetica", style="B", size=15)
        pdf.set_text_color(30, 41, 59)
        pdf.set_xy(15, 6)
        pdf.cell(0, 8, text=title, align="L")

        # Subtitle / Date
        if has_indic_font:
            pdf.set_font("IndicFont", size=9)
        else:
            pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(15, 14)
        date_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        pdf.cell(0, 6, text=f"Generated on {date_str} • SpeechText Converter", align="L")

        # Divider line
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, 26, 195, 26)

        # Main Text Content
        pdf.set_xy(15, 34)
        pdf.set_text_color(15, 23, 42)
        if has_indic_font:
            pdf.set_font("IndicFont", size=11)
        else:
            pdf.set_font("Helvetica", size=11)

        pdf.multi_cell(w=180, h=7, text=text, align="L")

        pdf.output(output_path)
        return output_path

    @classmethod
    def export_translation_pdf(
        cls,
        translated_text: str,
        target_lang: str,
        output_path: str,
    ) -> str:
        """
        Generate a styled PDF document containing exclusively the translated text.
        Does not include original text.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        has_indic_font = False
        if os.path.exists(cls.SYSTEM_INDIC_FONT):
            try:
                pdf.add_font("IndicFont", "", cls.SYSTEM_INDIC_FONT)
                has_indic_font = True
            except Exception:
                has_indic_font = False

        font_name = "IndicFont" if has_indic_font else "Helvetica"

        # Modern header
        pdf.set_fill_color(37, 99, 235)  # #2563EB primary brand blue
        pdf.rect(0, 0, 210, 26, "F")

        pdf.set_font(font_name, size=15)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 6)
        pdf.cell(0, 8, text=f"Translated Document ({target_lang})", align="L")

        pdf.set_font(font_name, size=9)
        pdf.set_text_color(220, 230, 255)
        pdf.set_xy(15, 14)
        date_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        pdf.cell(0, 6, text=f"Generated on {date_str} • Speech & Text Converter", align="L")

        # Divider line
        pdf.set_draw_color(226, 232, 240)
        pdf.line(15, 26, 195, 26)

        # Translated Text Content (Only translation, no original text)
        pdf.set_xy(15, 34)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font(font_name, size=11)
        pdf.multi_cell(w=180, h=7, text=translated_text or "(No translation)", align="L")

        pdf.output(output_path)
        return output_path

    @staticmethod
    def _read_pdf_file(file_path: str) -> str:
        """Extract text from all pages of a PDF document."""
        reader = PdfReader(file_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted.strip())

        full_text = "\n\n".join(text_parts).strip()
        if not full_text:
            raise ValueError("No readable text found in the selected PDF file.")
        return full_text
