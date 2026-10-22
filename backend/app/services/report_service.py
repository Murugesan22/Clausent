import os
import csv
import io
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from app.config import settings
from app.core.exceptions import ReportGenerationError
from app.core.logging_config import logger
from app.services.translation_service import TranslationService

class ReportService:
    """
    Report generation service supporting PDF generation (via ReportLab),
    JSON structured export, and CSV tabular export.
    Supports complete, end-to-end localization in English, Tamil, Hindi, Malayalam, and Telugu.
    """

    @classmethod
    def generate_pdf_report(cls, analysis_data: Dict, language: Optional[str] = None) -> Path:
        """
        Generates a professional PDF report styled with Clausent's legal paper palette.
        Supports complete target language translation (English, Tamil, Hindi, Malayalam, Telugu)
        and renders Indic scripts natively via system TrueType fonts.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Target language resolution
            target_lang = language or analysis_data.get("target_language") or "English"
            is_indic = target_lang.lower() != "english"

            if is_indic:
                analysis_data = TranslationService.translate_analysis_data(analysis_data, target_lang)

            ui_labels = TranslationService.get_ui_labels(target_lang)

            # Register Unicode Indic TrueType font (Nirmala UI on Windows, Arial fallback)
            font_regular = 'Helvetica'
            font_bold = 'Helvetica-Bold'
            font_oblique = 'Helvetica-Oblique'

            nirmala_path = "C:/Windows/Fonts/Nirmala.ttc"
            arial_path = "C:/Windows/Fonts/arial.ttf"

            if os.path.exists(nirmala_path):
                try:
                    pdfmetrics.registerFont(TTFont('Nirmala', nirmala_path, subfontIndex=0))
                    pdfmetrics.registerFont(TTFont('Nirmala-Bold', nirmala_path, subfontIndex=1))
                    font_regular = 'Nirmala'
                    font_bold = 'Nirmala-Bold'
                    font_oblique = 'Nirmala'
                    logger.info("Registered Nirmala TrueType font for Indic PDF rendering.")
                except Exception as fe:
                    logger.warning(f"Could not register Nirmala font: {fe}")

            if font_regular == 'Helvetica' and os.path.exists(arial_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arial', arial_path))
                    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                    font_regular = 'Arial'
                    font_bold = 'Arial-Bold'
                    font_oblique = 'Arial'
                except Exception:
                    pass

            raw_doc_name = analysis_data.get("filename", "Contract")
            safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(raw_doc_name).stem)[:30]
            report_filename = f"Clausent_Report_{safe_name}_{target_lang}.pdf"
            report_path = settings.REPORT_DIR / report_filename

            doc = SimpleDocTemplate(
                str(report_path),
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            # Palette matching CLAUSENT editorial legal UI
            c_ink = colors.HexColor("#1F2340")
            c_ink_soft = colors.HexColor("#565C7D")
            c_paper_panel = colors.HexColor("#E4DCC8")
            c_accent = colors.HexColor("#6E2C3C")
            c_high = colors.HexColor("#A63A34")
            c_med = colors.HexColor("#93641F")
            c_low = colors.HexColor("#3E6B5C")

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontName=font_bold,
                fontSize=20,
                leading=24,
                textColor=c_ink
            )
            subtitle_style = ParagraphStyle(
                'DocSubtitle',
                parent=styles['Normal'],
                fontName=font_regular,
                fontSize=11,
                leading=15,
                textColor=c_ink_soft
            )
            h2_style = ParagraphStyle(
                'SectionH2',
                parent=styles['Heading2'],
                fontName=font_bold,
                fontSize=12.5,
                leading=16,
                textColor=c_accent,
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontName=font_regular,
                fontSize=9.5,
                leading=13.5,
                textColor=c_ink
            )
            table_cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontName=font_regular,
                fontSize=9,
                leading=12.5,
                textColor=c_ink
            )
            table_hdr_style = ParagraphStyle(
                'TableHdr',
                parent=styles['Normal'],
                fontName=font_bold,
                fontSize=9.5,
                leading=13,
                textColor=colors.white
            )
            clause_text_style = ParagraphStyle(
                'ClauseText',
                parent=styles['Normal'],
                fontName=font_oblique,
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#333333")
            )
            clause_trans_style = ParagraphStyle(
                'ClauseTransText',
                parent=styles['Normal'],
                fontName=font_regular,
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#1A365D")
            )
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontName=font_oblique,
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#666666"),
                alignment=1
            )

            elements = []

            # 1. Header / Masthead
            elements.append(Paragraph("CLAUSENT", title_style))
            elements.append(Paragraph(f"{ui_labels.get('title_suffix', 'AI Contract Risk Report')} [{target_lang}]", subtitle_style))
            elements.append(Spacer(1, 8))
            elements.append(HRFlowable(width="100%", thickness=1.5, color=c_ink, spaceAfter=12))

            # 2. Contract Metadata Table
            doc_label = ui_labels.get("doc", "Document")
            gen_label = ui_labels.get("generated", "Generated")
            det_label = ui_labels.get("detected_lang", "Detected Language")
            tgt_label = ui_labels.get("target_lang", "Target Language")
            tot_label = ui_labels.get("total_clauses", "Total Clauses")
            score_label = ui_labels.get("overall_score", "Overall Risk Score")

            risk_level_str = analysis_data.get("overall_risk_level_display") or analysis_data.get("overall_risk_level", "LOW").upper()

            meta_data = [
                [
                    Paragraph(f"<b>{doc_label}:</b> " + str(analysis_data.get("filename", "Contract")), body_style),
                    Paragraph(f"<b>{gen_label}:</b> " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), body_style)
                ],
                [
                    Paragraph(f"<b>{det_label}:</b> " + str(analysis_data.get("detected_language", "English")), body_style),
                    Paragraph(f"<b>{tgt_label}:</b> " + str(target_lang), body_style)
                ],
                [
                    Paragraph(f"<b>{tot_label}:</b> {analysis_data.get('total_clauses', 0)}", body_style),
                    Paragraph(f"<b>{score_label}:</b> <font color='{c_high.hexval()}'><b>{analysis_data.get('overall_risk_score', 0)}/100 ({risk_level_str})</b></font>", body_style)
                ]
            ]
            meta_table = Table(meta_data, colWidths=[265, 265])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_paper_panel),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#C7BCA0")),
                ('FONTNAME', (0, 0), (-1, -1), font_regular),
            ]))
            elements.append(meta_table)
            elements.append(Spacer(1, 10))

            # 3. Executive Summary
            elements.append(Paragraph(ui_labels.get("summary_hdr", "EXECUTIVE SUMMARY"), h2_style))
            exec_summary_text = analysis_data.get("executive_summary", "Contract analysis complete.")
            elements.append(Paragraph(exec_summary_text, body_style))

            if analysis_data.get("suggested_review_areas"):
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>{ui_labels.get('lbl_action', 'Suggested Action')}:</b> {analysis_data.get('suggested_review_areas')}", body_style))

            elements.append(Spacer(1, 10))

            # 4. Risk Breakdown Statistics Table
            risk_labels = TranslationService.RISK_LEVEL_TRANSLATIONS.get(target_lang.capitalize(), {
                "high": "HIGH RISK", "medium": "MEDIUM RISK", "low": "LOW RISK"
            })

            stats_data = [
                [
                    Paragraph(f"<b>{ui_labels.get('col_risk', 'Risk Level')}</b>", table_hdr_style),
                    Paragraph(f"<b>{ui_labels.get('col_count', 'Count')}</b>", table_hdr_style),
                    Paragraph(f"<b>{ui_labels.get('col_status', 'Status Assessment')}</b>", table_hdr_style)
                ],
                [
                    Paragraph(f"<font color='{c_high.hexval()}'><b>{risk_labels.get('high', 'HIGH RISK')}</b></font>", table_cell_style),
                    Paragraph(str(analysis_data.get("high_risk_count", 0)), table_cell_style),
                    Paragraph(ui_labels.get("high_status", "Requires immediate review and negotiation"), table_cell_style)
                ],
                [
                    Paragraph(f"<font color='{c_med.hexval()}'><b>{risk_labels.get('medium', 'MEDIUM RISK')}</b></font>", table_cell_style),
                    Paragraph(str(analysis_data.get("medium_risk_count", 0)), table_cell_style),
                    Paragraph(ui_labels.get("med_status", "Examine operational and legal exposure"), table_cell_style)
                ],
                [
                    Paragraph(f"<font color='{c_low.hexval()}'><b>{risk_labels.get('low', 'LOW RISK')}</b></font>", table_cell_style),
                    Paragraph(str(analysis_data.get("low_risk_count", 0)), table_cell_style),
                    Paragraph(ui_labels.get("low_status", "Commercially standard contractual terms"), table_cell_style)
                ],
            ]
            stats_table = Table(stats_data, colWidths=[130, 70, 330])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), c_ink),
                ('FONTNAME', (0, 0), (-1, -1), font_regular),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#C7BCA0")),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 12))

            # 5. Detailed Clause Breakdown
            elements.append(Paragraph(ui_labels.get("clauses_hdr", "DETAILED CLAUSE FINDINGS"), h2_style))

            clauses = analysis_data.get("clauses", [])
            for c in clauses:
                risk = (c.get("risk_level") or c.get("risk") or "low").lower()
                r_color = c_high if risk == "high" else (c_med if risk == "medium" else c_low)

                cat_name = c.get("category_display") or c.get("category", "General")
                r_display = c.get("risk_level_display") or risk_labels.get(risk, risk.upper())
                c_num = c.get("clause_number") or c.get("id") or 1

                clause_header = f"<b>{c.get('clause_id_label', f'Clause {c_num}')} — {cat_name}</b> [<font color='{r_color.hexval()}'><b>{r_display}</b></font>]"
                elements.append(Paragraph(clause_header, body_style))

                # Original text excerpt
                orig = c.get("original_text") or c.get("text") or ""
                if len(orig) > 350:
                    orig = orig[:340] + "..."
                elements.append(Paragraph(f"<b>{ui_labels.get('lbl_orig', 'Original Text')}:</b> &ldquo;{orig}&rdquo;", clause_text_style))

                # If translated text exists and differs from original, show it
                trans_clause = c.get("translated_text")
                if trans_clause and trans_clause.strip() and trans_clause != orig and is_indic:
                    if len(trans_clause) > 350:
                        trans_clause = trans_clause[:340] + "..."
                    elements.append(Paragraph(f"<b>{ui_labels.get('lbl_trans', 'Translation')}:</b> &ldquo;{trans_clause}&rdquo;", clause_trans_style))

                # Plain-Language SLM explanation
                slm_exp = c.get("slm_explanation") or c.get("explain") or ""
                if slm_exp:
                    elements.append(Paragraph(f"<b>{ui_labels.get('lbl_explain', 'Explanation')}:</b> {slm_exp}", body_style))

                # Risk Rationale
                why = c.get("risk_rationale") or c.get("why") or ""
                if why:
                    elements.append(Paragraph(f"<b>{ui_labels.get('lbl_why', 'Why it was flagged')}:</b> {why}", body_style))

                # Action
                act = c.get("suggested_action") or c.get("action") or ""
                if act:
                    elements.append(Paragraph(f"<b>{ui_labels.get('lbl_action', 'Suggested Action')}:</b> {act}", body_style))

                # Suggested review questions
                questions = c.get("suggested_questions")
                if questions and isinstance(questions, list) and len(questions) > 0:
                    q_text = "<br/>• ".join(questions)
                    elements.append(Paragraph(f"<b>{ui_labels.get('lbl_review_points', 'Questions for Legal Review')}:</b><br/>• {q_text}", body_style))

                elements.append(Spacer(1, 8))

            # 6. Disclaimer
            elements.append(Spacer(1, 14))
            elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#C7BCA0"), spaceAfter=8))
            elements.append(Paragraph(ui_labels.get("disclaimer", "DISCLAIMER: CLAUSENT provides automated AI-assisted contract analysis for informational and educational purposes only."), disclaimer_style))

            doc.build(elements)
            logger.info(f"Generated PDF report at {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}", exc_info=True)
            raise ReportGenerationError(f"Error generating PDF report: {str(e)}")

    @classmethod
    def generate_json_export(cls, analysis_data: Dict) -> str:
        """Exports analysis in structured JSON format."""
        return json.dumps({
            "export_type": "CLAUSENT_CONTRACT_ANALYSIS",
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data": analysis_data
        }, indent=2)

    @classmethod
    def generate_csv_export(cls, clauses: List[Dict]) -> str:
        """Exports clause analysis in CSV format."""
        output = io.StringIO()
        fieldnames = [
            "clause_number", "clause_label", "category", "risk_level",
            "risk_score", "explanation", "risk_rationale", "suggested_action", "original_text"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for c in clauses:
            writer.writerow({
                "clause_number": c.get("clause_number", ""),
                "clause_label": c.get("clause_id_label", ""),
                "category": c.get("category", ""),
                "risk_level": c.get("risk_level", ""),
                "risk_score": c.get("risk_score", 0),
                "explanation": c.get("slm_explanation") or c.get("explain", ""),
                "risk_rationale": c.get("risk_rationale") or c.get("why", ""),
                "suggested_action": c.get("suggested_action") or c.get("action", ""),
                "original_text": (c.get("original_text") or c.get("text", "")).replace("\n", " ")
            })

        return output.getvalue()
