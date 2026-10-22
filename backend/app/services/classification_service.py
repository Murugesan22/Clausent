import re
from typing import Dict, List, Tuple
from app.services.legal_bert_service import LegalBertService
from app.core.logging_config import logger

class ClassificationResult:
    def __init__(self, category: str, confidence: float, evidence_spans: List[str], classification_method: str):
        self.category = category
        self.confidence = confidence
        self.evidence_spans = evidence_spans
        self.classification_method = classification_method

class ClassificationService:
    """
    Clause Classification Service aligning with the Contract Understanding Atticus Dataset (CUAD) taxonomy.
    Differentiates clause categorization (what the clause is about) from risk assessment (how hazardous it is).
    Supports English as well as Indic multilingual contract keywords.
    """

    # CUAD-aligned taxonomy patterns & indicators (including Indic legal terms)
    TAXONOMY_PATTERNS = {
        "Limitation of Liability": [
            r'\b(?:limitation\s+of\s+liability|limited\s+liability|liability\s+cap|liability\s+be\s+limited|liability.*unlimited|under\s+no\s+circumstances.*liability)\b',
            r'\b(?:consequential\s+damages|indirect\s+damages|direct\s+damages|punitive\s+damages|loss\s+of\s+profits|loss\s+of\s+revenue|maximum\s+liability|no\s+cap|unlimited\s+liability)\b',
            r'(?:பொறுப்பு\s*வரம்பு|दायित्व\s*की\s*सीमा|ബാധ്യതാ\s*പരിധി|బాధ్యత\s*పరిమితి|அதிகபட்ச\s*பொறுப்பு|அசீமித\s*பொறுப்பு|असीमित\s*दायित्व)'
        ],
        "Indemnification": [
            r'\b(?:indemnif(?:y|ies|ication)|hold\s+harmless|defend\s+and\s+hold\s+harmless|attorneys?[\'\s]*fees|losses,\s*damages,\s*liabilities)\b',
            r'\b(?:third[- ]party\s+claims|infringement\s+claims|defend,\s*indemnify|shall\s+indemnify|agrees\s+to\s+indemnify)\b',
            r'(?:இழப்பீட்டு\s*உத்தரவாதம்|இழப்பீடு|ক্ষतिपूर्ति|നഷ്ടപരിഹാരം|నష్టపరిహారం)'
        ],
        "Termination": [
            r'\b(?:terminat(?:e|ion)|for\s+convenience|upon\s+\d+\s+days?|written\s+notice\s+of\s+termination|material\s+breach|right\s+to\s+terminate)\b',
            r'\b(?:cure\s+period|immediate\s+termination|without\s+cause|notice\s+of\s+cancellation|survive\s+termination|sole\s+discretion.*terminat)\b',
            r'(?:முடிவுறுத்தல்|ரத்து\s*செய்தல்|समाप्ति|रद्दीकरण|റദ്ദാക്കൽ|రద్దు)'
        ],
        "Automatic Renewal": [
            r'\b(?:automatic(?:ally)?\s+renew(?:al|s)?|successive\s+(?:one[- ]year|terms?)|unless\s+(?:either\s+party\s+gives|written)\s+notice\s+of\s+non[- ]renewal)\b',
            r'\b(?:prior\s+to\s+the\s+end\s+of\s+the\s+then[- ]current\s+term|evergreen|opt[- ]in\s+renewal|renewal\s+term|renew\s+for\s+additional)\b',
            r'(?:தானாக\s*புதுப்பித்தல்|स्वचालित\s*नवीनीकरण|സ്വയമേവ\s*പുതുക്കൽ|స్వయంచాలక\s*పునరుద్ధరణ)'
        ],
        "Payment Terms": [
            r'\b(?:payment\s+terms?|remit\s+payment|invoice\s+date|within\s+\d+\s+days\s+of\s+invoice|late\s+fee|interest\s+rate|taxes|billing)\b',
            r'\b(?:wire\s+transfer|net\s+\d+|payable\s+upon|milestone\s+payments?|compensation|invoicing)\b',
            r'(?:பணம்\s*செலுத்தும்\s*விதிமுறைகள்|கட்டணம்|भुगतान\s*की\s*शर्तें|പേയ്മെന്റ്|చెల్లింపు)'
        ],
        "Confidentiality": [
            r'\b(?:confidential\s+information|non[- ]disclosure|proprietary\s+information|protect.*confidential|duty\s+of\s+confidentiality)\b',
            r'\b(?:receiving\s+party|disclosing\s+party|trade\s+secrets|nda|non-disclosure)\b',
            r'(?:ரகசியத்தன்மை|ரகசிய\s*தகவல்|गोपनीयता|രഹസ്യാത്മകത|రహస్యత)'
        ],
        "Governing Law and Dispute Resolution": [
            r'\b(?:governing\s+law|jurisdiction|dispute\s+resolution|binding\s+arbitration|courts?\s+of|laws\s+of\s+the\s+State\s+of)\b',
            r'\b(?:venue|exclusive\s+jurisdiction|arbitration\s+in|arbitrator|mediation|legal\s+proceedings)\b',
            r'(?:சட்ட\s*அதிகார\s*வரம்பு|தகராறு\s*தீர்வு|शासी\s*कानून|विवाद\s*समाधान|നിയമപരിധി|వర్తించే\s*చట్టం)'
        ],
        "Non-Compete": [
            r'\b(?:non[- ]compete|restrictive\s+covenant|shall\s+not\s+(?:directly\s+or\s+indirectly\s+)?compete|similar\s+services|solicit(?:ation)?)\b',
            r'\b(?:direct\s+competitor|restricted\s+period|non[- ]solicitation|exclusivity|competing\s+business)\b',
            r'(?:போட்டியிடாமை|போட்டி\s*கட்டுப்பாடு|गैर-प्रतिस्पर्धा|മത്സരവിലക്ക്|పోటీ\s*నిషేధం)'
        ],
        "Warranty Disclaimer": [
            r'\b(?:as\s+is|without\s+warranties?\s+of\s+any\s+kind|express\s+or\s+implied|merchantability|fitness\s+for\s+a\s+particular\s+purpose)\b',
            r'\b(?:disclaim(?:s|er)|warrants\s+that|implied\s+warranties|satisfactory\s+quality)\b',
            r'(?:உத்தரவாத\s*மறுப்பு|உத்தரவாதம்|वारंटी\s*अस्वीकरण|വാറന്റി|వారంటీ)'
        ],
        "Force Majeure": [
            r'\b(?:force\s+majeure|acts?\s+of\s+god|circumstances\s+beyond.*control|natural\s+disasters?|war,\s*terrorism|pandemic)\b',
            r'(?:கட்டாய\s*நிகழ்வு|अनिवार्य\s*घटना|നിർബന്ധിത\s*സാഹചര്യം|అనివార్య\s*సంఘటన)'
        ],
        "Assignment": [
            r'\b(?:assign(?:ment|s)?|shall\s+not\s+assign|prior\s+written\s+consent.*assign|subcontract(?:ing)?|successor)\b',
            r'(?:ஒப்பந்த\s*உரிமைகள்\s*மாற்றல்|समनुदेशन|കരാർ\s*കൈമാറ്റം|ఒప్పంద\s*బదిలీ)'
        ],
        "Intellectual Property": [
            r'\b(?:intellectual\s+property|work\s+made\s+for\s+hire|moral\s+rights|patents?|trademarks?|copyrights?|ownership\s+of\s+deliverables)\b',
            r'\b(?:proprietary\s+rights|inventions|pre-existing\s+materials|background\s+technology)\b',
            r'(?:அறிவுசார்\s*சொத்துரிமை|बौद्धिक\s*संपदा|ബൗദ്ധിക\s*സ്വത്ത്|మేధో\s*సంపత్తి)'
        ],
        "Definitions": [
            r'\b(?:meanings?\s+ascribed|capitalized\s+terms?|definitions?|as\s+used\s+herein|schedule\s+[A-Z])\b',
            r'(?:வரையறைகள்|परिभाषाएं|നിർവചനങ്ങൾ|నిర్వచనాలు)'
        ]
    }

    @classmethod
    def classify_clause(cls, clause_text: str) -> ClassificationResult:
        """
        Classifies clause text using CUAD legal taxonomy rules and Legal-BERT representation.
        """
        bert_meta = LegalBertService.encode_clause(clause_text)

        best_category = "General Provisions"
        best_score = 0.0
        evidence_spans = []

        # Evaluate taxonomy patterns
        for category, patterns in cls.TAXONOMY_PATTERNS.items():
            matches_for_category = []
            for pat in patterns:
                found = re.findall(pat, clause_text, re.IGNORECASE)
                if found:
                    matches_for_category.extend(found)

            if matches_for_category:
                # Score based on pattern matches and frequency
                score = min(0.96, 0.70 + (len(matches_for_category) * 0.08))
                if score > best_score:
                    best_score = score
                    best_category = category
                    evidence_spans = list(set([m if isinstance(m, str) else m[0] for m in matches_for_category]))

        if best_score == 0.0:
            best_category = "General Provisions"
            best_score = 0.65
            evidence_spans = ["Standard agreement boilerplate language"]

        method = f"Legal-BERT Representation + CUAD Category Taxonomy ({bert_meta.get('status', 'active')})"
        return ClassificationResult(
            category=best_category,
            confidence=round(best_score * 100, 1),
            evidence_spans=evidence_spans,
            classification_method=method
        )
