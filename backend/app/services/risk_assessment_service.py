import re
from typing import Dict, List, Optional
from app.core.logging_config import logger

class RiskAssessmentResult:
    def __init__(
        self,
        risk_level: str,  # "low", "medium", "high"
        risk_score: float,
        rationale: str,
        evidence: List[str],
        suggested_action: str,
        suggested_questions: List[str],
        uncertainties: List[str],
        assessment_method: str
    ):
        self.risk_level = risk_level
        self.risk_score = risk_score
        self.rationale = rationale
        self.evidence = evidence
        self.suggested_action = suggested_action
        self.suggested_questions = suggested_questions
        self.uncertainties = uncertainties
        self.assessment_method = assessment_method

class RiskAssessmentService:
    """
    Independent Contract Risk Assessment Engine.
    Evaluates exposure, mutuality, uncapped damages, one-sided provisions,
    and restrictive covenants separately from categorization.
    Supports English as well as Indic multilingual contract indicators.
    """

    @classmethod
    def assess_risk(cls, clause_text: str, category: str) -> RiskAssessmentResult:
        text_lower = clause_text.lower()
        evidence: List[str] = []
        uncertainties: List[str] = [
            "Legal enforceability depends on applicable state/national contract statutes and commercial context."
        ]

        # -------------------------------------------------------------
        # 0. GLOBAL HIGH HAZARD OVERRIDES (Cross-Category Risk Invariants)
        # Even if misclassified or labeled General/Definitions, severe traps must be flagged!
        # -------------------------------------------------------------

        # Check for explicit uncapped / unlimited damage exposure
        if any(term in text_lower for term in [
            "in no event shall either party's liability be limited",
            "in no event shall contractor's liability be limited",
            "in no event shall vendor's liability be limited",
            "in no event shall provider's liability be limited",
            "unlimited liability",
            "without limitation as to amount",
            "no cap on liability",
            "liability shall not be limited",
            "fully liable for any and all",
            "fully liable for all",
            "under no circumstances shall",
            "வரம்பற்ற பொறுப்பு", "அசீமித பொறுப்பு", "असीमित दायित्व", "അപരിമിതമായ ബാധ്യത", "పరిమితి లేని బాధ్యత"
        ]) or ("liability" in text_lower and any(w in text_lower for w in ["unlimited", "not be limited", "no cap"])):
            evidence.append("Explicit removal of liability cap / unlimited damage exposure")
            return RiskAssessmentResult(
                risk_level="high",
                risk_score=94.0,
                rationale="This clause removes any cap on financial liability. You may be exposed to damages far exceeding the total contract value.",
                evidence=evidence,
                suggested_action="Negotiate a mutual aggregate liability cap (e.g., capped at total fees paid in preceding 12 months) and expressly exclude indirect/consequential damages.",
                suggested_questions=[
                    "What is our maximum financial exposure if an unintended breach or system outage occurs?",
                    "Can we insert a standard mutual liability cap tied to annual contract revenue?"
                ],
                uncertainties=uncertainties,
                assessment_method="Global Exposure Engine (Uncapped Liability Detection)"
            )

        # Check for punitive liquidated damages / forfeiture
        if any(term in text_lower for term in [
            "liquidated damages", "penalty of", "forfeiture of all fees", "forfeit all", "penalty fee"
        ]):
            evidence.append("Liquidated damages or punitive financial forfeiture provision")
            return RiskAssessmentResult(
                risk_level="high",
                risk_score=89.0,
                rationale="Imposes pre-agreed financial penalties or liquidated damages regardless of actual provable harm.",
                evidence=evidence,
                suggested_action="Replace liquidated damages with compensation strictly for direct actual damages proven in court.",
                suggested_questions=[
                    "Are the specified liquidated damages proportionate or legally deemed an unenforceable penalty?",
                    "Can we cap maximum liquidated damages to a small percentage of milestone fees?"
                ],
                uncertainties=uncertainties,
                assessment_method="Global Exposure Engine (Liquidated Damages)"
            )

        # Check for unilateral amendment rights without notice
        if any(term in text_lower for term in [
            "modify these terms at any time without notice",
            "amend this agreement at any time in its sole discretion",
            "reserves the right to change these terms without prior notice",
            "continued use constitutes acceptance of modifications"
        ]):
            evidence.append("Unilateral contract modification without prior written consent")
            return RiskAssessmentResult(
                risk_level="high",
                risk_score=87.0,
                rationale="Allows one party to unilaterally modify contract terms, pricing, or duties without requiring mutual written consent.",
                evidence=evidence,
                suggested_action="Require that any contract amendment or modification must be in writing and signed by authorized representatives of both parties.",
                suggested_questions=[
                    "Can the client alter service scopes, payment terms, or liability limits unilaterally?",
                    "Can we require 30 days advance written notice with a right to terminate if changes are unacceptable?"
                ],
                uncertainties=uncertainties,
                assessment_method="Global Exposure Engine (Unilateral Modification)"
            )

        # Check for total pre-existing IP assignment & moral rights waiver
        if any(term in text_lower for term in [
            "irrevocably waives all moral rights",
            "waives all moral rights",
            "assigns all preexisting intellectual property",
            "assigns all background intellectual property",
            "all inventions conceived during or outside"
        ]):
            evidence.append("Extensive IP forfeiture including background tools or irrevocable waiver of moral rights")
            return RiskAssessmentResult(
                risk_level="high",
                risk_score=88.0,
                rationale="Requires broad forfeiture of background proprietary tools or an irrevocable waiver of moral rights.",
                evidence=evidence,
                suggested_action="Retain ownership of all pre-existing tools, templates, and libraries, granting client only a perpetual non-exclusive license upon full payment.",
                suggested_questions=[
                    "Do we retain rights to our preexisting tools and reusable codebase?",
                    "Is IP assignment strictly conditioned upon receipt of full payment?"
                ],
                uncertainties=uncertainties,
                assessment_method="Global Exposure Engine (IP Forfeiture)"
            )

        # -------------------------------------------------------------
        # 1. LIMITATION OF LIABILITY
        # -------------------------------------------------------------
        if category in ("Limitation of Liability", "Liability"):
            # Check for uncapped exceptions (indemnity, confidentiality carveouts)
            has_uncapped_carveout = any(term in text_lower for term in [
                "shall not apply to", "except for indemnification", "excluding indemnification",
                "carve-out", "except with respect to", "notwithstanding anything to the contrary"
            ]) and any(term in text_lower for term in ["indemnif", "confidential", "intellectual property", "unlimited"])

            if has_uncapped_carveout:
                evidence.append("Liability cap contains major carve-outs leaving indemnification or other liabilities uncapped")
                return RiskAssessmentResult(
                    risk_level="high",
                    risk_score=86.0,
                    rationale="While a liability cap appears to exist, broad carve-outs (e.g. for indemnification or confidentiality) leave financial exposure uncapped.",
                    evidence=evidence,
                    suggested_action="Ensure that carve-outs are bilateral and capped at a realistic super-cap (e.g., 2x annual contract fees).",
                    suggested_questions=[
                        "What is our absolute maximum exposure under the uncapped carve-outs?",
                        "Can we negotiate a distinct super-cap for indemnification claims?"
                    ],
                    uncertainties=uncertainties,
                    assessment_method="Rule-Based Exposure Heuristics (Carve-out Analysis)"
                )

            # Check for bilateral capped liability
            has_cap = any(term in text_lower for term in [
                "aggregate liability", "total liability", "shall not exceed", "maximum liability", "capped at",
                "fees paid", "amount paid", "preceding 12 months", "preceding twelve months"
            ])

            if has_cap:
                return RiskAssessmentResult(
                    risk_level="low",
                    risk_score=25.0,
                    rationale="Liability is capped at defined financial thresholds (e.g. fees paid), which is standard commercial practice.",
                    evidence=["Defined aggregate liability threshold found with mutual application"],
                    suggested_action="Confirm that the specified liability cap aligns with your commercial insurance policy limits.",
                    suggested_questions=["Does the liability cap cover all deliverables or are there hidden exceptions?"],
                    uncertainties=uncertainties,
                    assessment_method="Rule-Based Exposure Heuristics (Capped Damages)"
                )
            else:
                return RiskAssessmentResult(
                    risk_level="medium",
                    risk_score=62.0,
                    rationale="Liability terms exist but lack an explicit financial monetary ceiling or create asymmetrical direct damage exposure.",
                    evidence=["Liability disclaimer present without explicit aggregate monetary cap"],
                    suggested_action="Insert an express aggregate cap limiting total liability to fees paid during the contract term.",
                    suggested_questions=["Are exclusions to the liability cap mutual between both parties?"],
                    uncertainties=uncertainties,
                    assessment_method="Rule-Based Exposure Heuristics"
                )

        # -------------------------------------------------------------
        # 2. INDEMNIFICATION
        # -------------------------------------------------------------
        if category in ("Indemnification", "Indemnity"):
            is_broad = any(term in text_lower for term in [
                "any and all", "arising out of or related to", "performance under this agreement",
                "hold harmless", "attorneys' fees", "attorney's fees", "losses, damages", "all claims"
            ])
            # Check unilateral actors
            is_unilateral = any(term in text_lower for term in [
                "contractor shall indemnify", "vendor shall indemnify", "consultant shall indemnify",
                "service provider shall indemnify", "provider shall indemnify", "you shall indemnify",
                "developer shall indemnify", "customer shall be indemnified", "client shall be indemnified",
                "party b shall indemnify", "licensee shall indemnify"
            ]) or (not "each party shall indemnify" in text_lower and not "mutual" in text_lower)

            has_fault_limitation = any(term in text_lower for term in [
                "solely caused by", "gross negligence and willful misconduct",
                "except to the extent caused by", "to the extent arising from provider's sole negligence"
            ])

            if is_broad and is_unilateral and not has_fault_limitation:
                evidence.append("Broad unilateral indemnity without requirement of direct fault or mutual reciprocity")
                return RiskAssessmentResult(
                    risk_level="high",
                    risk_score=90.0,
                    rationale="Broad unilateral indemnification obligates you to cover the other party's legal fees and third-party damages even if you were not solely at fault.",
                    evidence=evidence,
                    suggested_action="Limit indemnification strictly to third-party claims arising directly from your own material breach, gross negligence, or intentional misconduct.",
                    suggested_questions=[
                        "Does our commercial liability insurance cover contractual indemnity obligations of this scope?",
                        "Can we make the indemnification mutual or add a requirement of prompt written notice of claims?"
                    ],
                    uncertainties=uncertainties,
                    assessment_method="Indemnification Scope & Mutuality Framework"
                )
            else:
                return RiskAssessmentResult(
                    risk_level="medium",
                    risk_score=58.0,
                    rationale="Indemnification is present. While standard, indemnification obligations create potential third-party exposure and should be tied to insurance.",
                    evidence=["Indemnification clause with partial limitations or standard scope"],
                    suggested_action="Ensure indemnification covers only direct third-party intellectual property or bodily injury claims.",
                    suggested_questions=["Are legal defense costs subject to your prior written approval?"],
                    uncertainties=uncertainties,
                    assessment_method="Indemnification Scope Framework"
                )

        # -------------------------------------------------------------
        # 3. AUTOMATIC RENEWAL & TERM
        # -------------------------------------------------------------
        if category in ("Automatic Renewal", "Automatic Renewal & Term", "Term & Renewal"):
            # Extract notice window in days or months
            match_days = re.search(r'(\d+)\s+days', text_lower)
            match_word_days = re.search(r'(sixty|ninety|thirty|one hundred twenty)\s*(?:\(\d+\))?\s*days', text_lower)
            match_months = re.search(r'(\d+)\s+months?', text_lower)

            notice_days = 30
            if match_days:
                notice_days = int(match_days.group(1))
            elif match_word_days:
                w = match_word_days.group(1)
                notice_days = 60 if w == "sixty" else (90 if w == "ninety" else 30)
            elif match_months:
                notice_days = int(match_months.group(1)) * 30

            if notice_days >= 60:
                evidence.append(f"Notice requirement of {notice_days} days prior to expiration")
                return RiskAssessmentResult(
                    risk_level="high",
                    risk_score=88.0,
                    rationale=f"A long advance cancellation window ({notice_days} days) makes it easy to miss the cutoff and inadvertently get locked into another full contract term.",
                    evidence=evidence,
                    suggested_action=f"Negotiate the cancellation notice down to 30 days, or insert a requirement that the other party provide a written reminder notice 15 days before the cutoff.",
                    suggested_questions=[
                        "Can we eliminate automatic renewal in favor of an explicit written opt-in renewal?",
                        "What are the fees or penalties if we terminate after an inadvertent auto-renewal?"
                    ],
                    uncertainties=uncertainties,
                    assessment_method="Renewal Notice Window Assessment"
                )
            else:
                return RiskAssessmentResult(
                    risk_level="medium",
                    risk_score=50.0,
                    rationale="Agreement automatically renews with standard notice requirement.",
                    evidence=[f"Notice requirement of {notice_days} days"],
                    suggested_action="Set calendar alerts 45 days prior to contract expiration.",
                    suggested_questions=["What is the procedure and email address for sending valid non-renewal notice?"],
                    uncertainties=uncertainties,
                    assessment_method="Renewal Notice Window Assessment"
                )

        # -------------------------------------------------------------
        # 4. TERMINATION & CANCELLATION
        # -------------------------------------------------------------
        if category in ("Termination", "Termination & Cancellation", "Termination for Convenience"):
            match_days = re.search(r'(\d+)\s+days?', text_lower)
            notice_days = int(match_days.group(1)) if match_days else 30

            is_immediate = any(term in text_lower for term in [
                "immediate", "without cause", "sole discretion", "without notice", "terminate at any time"
            ])
            is_short_convenience = ("convenience" in text_lower or "without cause" in text_lower or "at any time" in text_lower) and notice_days <= 15

            if is_immediate:
                evidence.append("Immediate termination without cause or notice period")
                return RiskAssessmentResult(
                    risk_level="high",
                    risk_score=87.0,
                    rationale="The other party can terminate immediately without cause, offering no operational transition period or revenue stability.",
                    evidence=evidence,
                    suggested_action="Require at least 30 days advance written notice for any termination without cause.",
                    suggested_questions=[
                        "Can termination without cause be removed or made mutual with 30-60 days notice?",
                        "Is compensation guaranteed for all work completed up to the date of termination?"
                    ],
                    uncertainties=uncertainties,
                    assessment_method="Termination Notice Assessment (Immediate Termination)"
                )
            elif is_short_convenience:
                evidence.append(f"Termination for convenience on only {notice_days} days notice")
                return RiskAssessmentResult(
                    risk_level="high" if notice_days <= 7 else "medium",
                    risk_score=85.0 if notice_days <= 7 else 75.0,
                    rationale=f"The other party can walk away with only {notice_days} days of notice, giving you minimal time to plan transition or recover invested resources.",
                    evidence=evidence,
                    suggested_action="Negotiate at least 30 to 60 days notice for termination for convenience, plus guaranteed payment for all work completed to date.",
                    suggested_questions=["What compensation is guaranteed for work completed if early termination occurs?"],
                    uncertainties=uncertainties,
                    assessment_method="Termination Notice Assessment"
                )
            else:
                return RiskAssessmentResult(
                    risk_level="low",
                    risk_score=28.0,
                    rationale="Standard termination clause requiring cause or standard advance written notice.",
                    evidence=["Notice period is commercially customary (30+ days)"],
                    suggested_action="Confirm that termination triggers orderly handover and prompt payment of outstanding invoices.",
                    suggested_questions=["What happens to confidential data and work product upon termination?"],
                    uncertainties=uncertainties,
                    assessment_method="Termination Notice Assessment"
                )

        # -------------------------------------------------------------
        # 5. NON-COMPETE & RESTRICTIVE COVENANTS
        # -------------------------------------------------------------
        if category in ("Non-Compete", "Non-Compete & Restrictive Covenants"):
            # Check years vs months
            match_years = re.search(r'(\d+)\s+years?', text_lower)
            match_months = re.search(r'(\d+)\s+months?', text_lower)
            match_word_years = re.search(r'(one|two|three)\s*(?:\(\d+\))?\s*years?', text_lower)

            months = 12
            if match_years:
                months = int(match_years.group(1)) * 12
            elif match_word_years:
                w = match_word_years.group(1)
                months = 24 if w == "two" else (36 if w == "three" else 12)
            elif match_months:
                months = int(match_months.group(1))

            is_high = months > 12 or any(term in text_lower for term in ["worldwide", "any territory", "direct or indirect"])
            evidence.append(f"Restrictive covenant duration of {months} months")
            return RiskAssessmentResult(
                risk_level="high" if is_high else "medium",
                risk_score=91.0 if is_high else 76.0,
                rationale=f"Restricts you from providing similar commercial services to competitors for {months} months, which directly curtails your commercial livelihood.",
                evidence=evidence,
                suggested_action="Narrow the definition of 'direct competitor', restrict duration to maximum 6-12 months, and limit scope only to clients you personally served.",
                suggested_questions=[
                    "Is this non-compete enforceable under your state or national labor laws?",
                    "Can we replace the non-compete with a customer non-solicitation clause?"
                ],
                uncertainties=uncertainties,
                assessment_method="Restrictive Covenant Scope Assessment"
            )

        # -------------------------------------------------------------
        # 6. INTELLECTUAL PROPERTY RIGHTS
        # -------------------------------------------------------------
        if category in ("Intellectual Property", "Intellectual Property Rights"):
            has_tool_forfeiture = any(term in text_lower for term in [
                "assigns all right, title, and interest", "pre-existing", "preexisting", "moral rights", "work made for hire"
            ])
            if has_tool_forfeiture:
                evidence.append("Broad transfer of deliverable IP and potential background tools")
                return RiskAssessmentResult(
                    risk_level="medium",
                    risk_score=68.0,
                    rationale="Transfers full ownership of deliverables. Verify that pre-existing code, tools, and proprietary methodologies are expressly carved out.",
                    evidence=evidence,
                    suggested_action="Specify that background IP remains your property, granting client a license upon payment.",
                    suggested_questions=["Does the client own background utilities or only custom end-deliverables?"],
                    uncertainties=uncertainties,
                    assessment_method="Intellectual Property Assessment"
                )

        # -------------------------------------------------------------
        # 7. GOVERNING LAW & DISPUTE RESOLUTION
        # -------------------------------------------------------------
        if category in ("Governing Law and Dispute Resolution", "Governing Law", "Dispute Resolution"):
            evidence.append("Binding arbitration and predetermined governing venue")
            return RiskAssessmentResult(
                risk_level="medium",
                risk_score=72.0,
                rationale="Specifies binding arbitration in a designated venue, waiving rights to a local court trial and potentially increasing administrative legal costs.",
                evidence=evidence,
                suggested_action="Check whether the specified jurisdiction and arbitration forum are financially and geographically feasible.",
                suggested_questions=[
                    "What are the estimated filing fees and administrative costs for arbitration in this designated venue?",
                    "Can we agree that disputes under a certain monetary threshold can be handled via virtual mediation?"
                ],
                uncertainties=uncertainties,
                assessment_method="Jurisdiction & Dispute Forum Assessment"
            )

        # -------------------------------------------------------------
        # 8. WARRANTY DISCLAIMER
        # -------------------------------------------------------------
        if category in ("Warranty Disclaimer", "Warranty"):
            evidence.append("Full 'as is' disclaimer disclaiming implied merchantability and fitness warranties")
            return RiskAssessmentResult(
                risk_level="medium",
                risk_score=65.0,
                rationale="The provider disclaims all warranties 'as is', leaving you with little recourse if deliverables fail to perform.",
                evidence=evidence,
                suggested_action="Request an express warranty confirming deliverables will substantially conform to project specifications for at least 30-90 days.",
                suggested_questions=["What remedy or refund is provided if delivered work fails acceptance testing?"],
                uncertainties=uncertainties,
                assessment_method="Warranty & Recourse Assessment"
            )

        # -------------------------------------------------------------
        # 9. ROUTINE / STANDARD PROVISIONS
        # -------------------------------------------------------------
        return RiskAssessmentResult(
            risk_level="low",
            risk_score=20.0,
            rationale="Standard commercial provision without punitive, unilateral, or disproportionate liability risks.",
            evidence=["Routine commercial terms with mutual application"],
            suggested_action="Standard clause. Ensure all operational timelines match internal workflows.",
            suggested_questions=["Are there any specific operational preconditions attached to this obligation?"],
            uncertainties=uncertainties,
            assessment_method="Standard Commercial Baseline Assessment"
        )
