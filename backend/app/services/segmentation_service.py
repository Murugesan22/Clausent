import re
from typing import List, Dict, Optional
from app.core.logging_config import logger

class RawClause:
    def __init__(
        self,
        clause_number: int,
        clause_id_label: str,
        text: str,
        page_number: Optional[int] = 1,
        is_uncertain: bool = False
    ):
        self.clause_number = clause_number
        self.clause_id_label = clause_id_label
        self.text = text
        self.page_number = page_number
        self.is_uncertain = is_uncertain

class SegmentationService:
    """
    Legal-document clause segmentation service.
    Combines regex pattern recognition for legal numbering/headings with paragraph-based heuristics.
    """

    # Patterns matching standard legal clause headers:
    # 1. "1.", "1.1", "1.1.1", "(a)", "(i)", "1.01"
    # 2. "Clause 1", "Section 2", "Article IV", "Paragraph 5"
    # 3. Capitalized legal headings followed by a colon or newline
    CLAUSE_HEADER_REGEX = re.compile(
        r'(?:^|\n\n+)(?:'
        r'(?:(?:SECTION|Section|CLAUSE|Clause|ARTICLE|Article|PARAGRAPH|Paragraph)\s*(\d+|[IVXLCDM]+|[A-Z])(?:\.|\:|\s+[-–—]\s*|\s+))|'
        r'(?:(\d+(?:\.\d+)*)\.?(?:\s+[-–—]\s*|\s+))|'
        r'(?:\(([a-z0-9]+)\)\s+)|'
        r'(?:(?<=\n)([A-Z\s]{4,35})\:\s*)'
        r')',
        re.MULTILINE
    )

    @classmethod
    def segment_text(cls, text: str, page_texts: Optional[Dict[int, str]] = None) -> List[RawClause]:
        """
        Segments normalized contract text into individual clauses with stable numbering.
        """
        if not text or not text.strip():
            return []

        clauses: List[RawClause] = []
        
        # Split primarily by double line breaks (paragraphs) or clear numbered boundaries
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]

        current_clause_num = 1
        buffer_text = ""
        current_label = ""
        is_uncertain = False

        # Pattern to check if paragraph begins with clause-like identifier
        lead_pattern = re.compile(
            r'^(?:(?:SECTION|Section|CLAUSE|Clause|ARTICLE|Article)\s*(\d+|[IVXLCDM]+|[A-Z])[\.:\s-]*|(\d+(?:\.\d+)*)[\.:\s-]+|\(([a-z0-9]+)\)[\.:\s-]+|([A-Z\s]{3,30}:))',
            re.IGNORECASE
        )

        for p in paragraphs:
            match = lead_pattern.match(p)
            # If paragraph starts with a clear clause indicator and we already have accumulated text
            if match and buffer_text:
                clauses.append(
                    RawClause(
                        clause_number=current_clause_num,
                        clause_id_label=current_label or f"Clause {current_clause_num}",
                        text=buffer_text.strip(),
                        is_uncertain=is_uncertain
                    )
                )
                current_clause_num += 1
                buffer_text = p
                current_label = match.group(0).strip(" .:-\t")
                is_uncertain = False
            elif match and not buffer_text:
                buffer_text = p
                current_label = match.group(0).strip(" .:-\t")
            else:
                # If buffer is already long enough (> 150 chars) and this looks like a new paragraph
                if len(buffer_text) >= 180 and len(p) >= 40:
                    clauses.append(
                        RawClause(
                            clause_number=current_clause_num,
                            clause_id_label=current_label or f"Clause {current_clause_num}",
                            text=buffer_text.strip(),
                            is_uncertain=True  # Paragraph split without explicit numbered label
                        )
                    )
                    current_clause_num += 1
                    buffer_text = p
                    current_label = f"Clause {current_clause_num}"
                    is_uncertain = True
                else:
                    if buffer_text:
                        buffer_text += "\n" + p
                    else:
                        buffer_text = p
                        current_label = f"Clause {current_clause_num}"

        # Append remaining buffer
        if buffer_text:
            clauses.append(
                RawClause(
                    clause_number=current_clause_num,
                    clause_id_label=current_label or f"Clause {current_clause_num}",
                    text=buffer_text.strip(),
                    is_uncertain=is_uncertain
                )
            )

        # Fallback if no clauses segmented or single huge block: split by sentences or sub-paragraphs
        if len(clauses) <= 1 and len(text) > 400:
            logger.info("Single block detected. Performing sentence/sub-paragraph segmentation.")
            clauses = cls._fallback_sentence_split(text)

        # Assign page references if page_texts is provided
        if page_texts:
            for clause in clauses:
                for page_num, ptext in page_texts.items():
                    if clause.text[:50] in ptext:
                        clause.page_number = page_num
                        break

        logger.info(f"Segmented {len(clauses)} clauses from document.")
        return clauses

    @classmethod
    def _fallback_sentence_split(cls, text: str) -> List[RawClause]:
        # Split roughly every 2-3 sentences to provide digestible clauses
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
        result = []
        chunk = ""
        c_num = 1
        for s in sentences:
            chunk += (" " if chunk else "") + s
            if len(chunk) > 200:
                result.append(
                    RawClause(
                        clause_number=c_num,
                        clause_id_label=f"Provision {c_num}",
                        text=chunk.strip(),
                        is_uncertain=True
                    )
                )
                c_num += 1
                chunk = ""
        if chunk:
            result.append(
                RawClause(
                    clause_number=c_num,
                    clause_id_label=f"Provision {c_num}",
                    text=chunk.strip(),
                    is_uncertain=True
                )
            )
        return result
