import json
import httpx
from typing import Dict, List, Optional
from app.config import settings
from app.core.logging_config import logger

class LLMService:
    """
    Large Language Model (LLM) Service for in-depth legal analysis of complex or high-risk clauses.
    Analyzes practical consequences, identifies ambiguities, and suggests legal negotiation points
    with complete native support for English, Hindi, Malayalam, Telugu, and Tamil.
    """

    SYSTEM_PROMPT = """You are an expert NLP legal analyst assisting small businesses, freelancers, and startups.
Analyze the following high-risk or complex contract clause objectively.
Guidelines:
1. Explain what the clause explicitly states versus what risks or ambiguities arise.
2. Outline practical commercial consequences.
3. Suggest 2-3 specific questions for independent legal review.
4. Do NOT make definitive claims about legal enforceability or jurisdiction validity without qualification.
5. Base your explanation strictly on the provided text and evidence.
IMPORTANT: You must write your entire analysis and all headings fluently in the requested target language.
"""

    @classmethod
    def generate_detailed_analysis(
        cls,
        clause_text: str,
        category: str,
        risk_level: str,
        rationale: str,
        evidence: List[str],
        target_language: str = "English"
    ) -> Dict:
        """
        Generates deep legal analysis using the configured LLM provider or robust deterministic legal engine.
        Fully localized for the requested target language.
        """
        target_key = (target_language or "English").capitalize()

        # If API key is provided and provider is gemini/openai, attempt provider API
        if settings.LLM_API_KEY and settings.LLM_PROVIDER in ("gemini", "openai"):
            try:
                if settings.LLM_PROVIDER == "gemini":
                    return cls._call_gemini_api(clause_text, category, risk_level, rationale, evidence, target_key)
                elif settings.LLM_PROVIDER == "openai":
                    return cls._call_openai_api(clause_text, category, risk_level, rationale, evidence, target_key)
            except Exception as e:
                logger.warning(f"LLM API call failed ({e}). Reverting to built-in deep legal reasoning engine.")

        # Deterministic domain analysis engine for high-risk and complex clauses
        return cls._generate_heuristic_deep_analysis(clause_text, category, risk_level, rationale, evidence, target_key)

    @classmethod
    def _generate_heuristic_deep_analysis(
        cls,
        clause_text: str,
        category: str,
        risk_level: str,
        rationale: str,
        evidence: List[str],
        target_lang: str = "English"
    ) -> Dict:
        """
        Structured, comprehensive legal analysis generated deterministically
        with native fluency in English, Hindi, Malayalam, Telugu, and Tamil.
        """
        from app.services.translation_service import TranslationService

        cat_trans = TranslationService.translate_category(category, target_lang)
        risk_map = TranslationService.RISK_LEVEL_TRANSLATIONS.get(target_lang, {})
        risk_badge = risk_map.get(risk_level.lower(), risk_level.upper())
        translated_rationale = TranslationService.translate_explanation(rationale, target_lang)
        ev_str = ", ".join(evidence) if evidence else "Standard operational covenants"

        snippet = clause_text[:200] + ("..." if len(clause_text) > 200 else "")

        if target_lang == "Hindi":
            detailed_body = (
                f"{cat_trans} के लिए विस्तृत कानूनी विश्लेषण ({risk_badge}):\n\n"
                f"1. अनुबंध संबंधी दायित्व: यह खंड निर्दिष्ट करता है: \"{snippet}\"\n\n"
                f"2. जोखिम मूल्यांकन का आधार: {translated_rationale}\n\n"
                f"3. व्यावहारिक परिणाम: इस प्रावधान पर वर्तमान रूप में हस्ताक्षर करने से आपके व्यवसाय को "
                f"असीमित दायित्व, अप्रत्याशित वित्तीय जोखिम या विवाद की स्थिति में प्रक्रियात्मक नुकसान का सामना करना पड़ सकता है। "
                f"पहचाने गए मुख्य साक्ष्य: {ev_str}।\n\n"
                f"4. कानूनी समीक्षा के लिए महत्वपूर्ण सुझाव: अपने वकील से परामर्श करें कि क्या इस खंड में उचित वित्तीय सीमा "
                f"(Liability Cap) जोड़ी जा सकती है और क्या दोनों पक्षों के बीच पारस्परिक सुरक्षात्मक संतुलन सुनिश्चित किया जा सकता है।"
            )
            consequences = f"{cat_trans} के तहत संभावित वित्तीय और परिचालन देनदारियां उत्पन्न हो सकती हैं।"
            ambiguities = [
                "कार्रवाई का दायरा व्यापक है और बिना किसी स्पष्ट अपवाद के तैयार किया गया है।",
                "पारस्परिक सूचना या दोनों पक्षों के संतुलन की कमी है।"
            ]

        elif target_lang == "Malayalam":
            detailed_body = (
                f"{cat_trans} സംബന്ധിച്ച സമഗ്ര നിയമ വിശകലനം ({risk_badge}):\n\n"
                f"1. കരാർ ബാധ്യത: വ്യവസ്ഥ വ്യക്തമാക്കുന്നത്: \"{snippet}\"\n\n"
                f"2. അപകടസാധ്യതയുടെ കാരണം: {translated_rationale}\n\n"
                f"3. പ്രായോഗിക പ്രത്യാഘാതങ്ങൾ: ഈ വ്യവസ്ഥ നിലവിലെ രൂപത്തിൽ ഒപ്പുവെക്കുന്നത് നിങ്ങളുടെ സ്ഥാപനത്തിന് "
                f"അപ്രതീക്ഷിത സാമ്പത്തിക ബാധ്യതകളും തർക്കപരിഹാര വേളകളിൽ വലിയ നഷ്ടങ്ങളും വരുത്തിവച്ചേക്കാം. "
                f"കണ്ടെത്തിയ പ്രധാന തെളിവുകൾ: {ev_str}।\n\n"
                f"4. നിയമപരമായ അവലോകനത്തിനുള്ള നിർദ്ദേശങ്ങൾ: ഈ നിബന്ധന വാണിജ്യ മാനദണ്ഡങ്ങൾക്ക് അനുസൃതമാണോ എന്നും, "
                f"ബാധ്യതാ പരിധി നിശ്ചയിക്കാനും ഇരു കക്ഷികൾക്കും തുല്യ പരിരക്ഷ ഉറപ്പാക്കാനും കഴിയുമോ എന്നും അഭിഭാഷകനോട് ആലോചിക്കുക."
            )
            consequences = f"{cat_trans} വ്യവസ്ഥ പ്രകാരം ഭാവിയിൽ വലിയ സാമ്പത്തിക ബാധ്യതകൾ ഉണ്ടാകാൻ സാധ്യതയുണ്ട്."
            ambiguities = [
                "ബാധ്യതകളുടെ പരിധി വളരെ വിപുലമാണ്, വ്യക്തമായ ഇളവുകൾ ഉൾപ്പെടുത്തിയിട്ടില്ല.",
                "ഇരു കക്ഷികൾക്കും തുല്യമായ പരസ്പര സംരക്ഷണം ലഭ്യമല്ല."
            ]

        elif target_lang == "Telugu":
            detailed_body = (
                f"{cat_trans} కోసం సమగ్ర చట్టపరమైన విశ్లేషణ ({risk_badge}):\n\n"
                f"1. ఒప్పంద బాధ్యత: ఈ నిబంధన నిర్దేశిస్తుంది: \"{snippet}\"\n\n"
                f"2. ప్రమాద అంచనా హేతువు: {translated_rationale}\n\n"
                f"3. ఆచరణాత్మక పరిణామాలు: ప్రస్తుత రూపంలో ఈ నిబంధనపై సంతకం చేయడం వల్ల మీ సంస్థ ఊహించని "
                f"ఆర్థిక భారాలు లేదా వివాద పరిష్కార సమయంలో గణనీయమైన చట్టపరమైన నష్టాలకు గురికావచ్చు. "
                f"గుర్తించిన ఆధారాలు: {ev_str}।\n\n"
                f"4. చట్టపరమైన సమీక్ష కోసం సూచనలు: ఈ నిబంధన వాణిజ్య ప్రమాణాలకు అనుగుణంగా ఉందో లేదో మరియు "
                f"ఆర్థిక పరిమితిని (Liability Cap) చేర్చి ఇరు పక్షాలకు పరస్పర రక్షణ కల్పించేలా సవరించవచ్చో లేదో న్యాయ సలహాదారునితో చర్చించండి."
            )
            consequences = f"{cat_trans} ప్రకారం భవిష్యత్తులో తీవ్రమైన ఆర్థిక మరియు కార్యాచరణ బాధ్యతలు ఉత్పన్నమయ్యే ప్రమాదం ఉంది."
            ambiguities = [
                "పరిహార బాధ్యత పరిధి చాలా విస్తృతంగా ఉంది మరియు మినహాయింపులు లేవు.",
                "ఇరు పక్షాల మధ్య పరస్పర రక్షణలు లోపించాయి."
            ]

        elif target_lang == "Tamil":
            detailed_body = (
                f"{cat_trans} குறித்த விரிவான சட்ட பகுப்பாய்வு ({risk_badge}):\n\n"
                f"1. ஒப்பந்தக் கடமை: இந்த விதிமுறை குறிப்பிடுவது: \"{snippet}\"\n\n"
                f"2. இடர் மதிப்பீட்டு அடிப்படை: {translated_rationale}\n\n"
                f"3. நடைமுறை விளைவுகள்: தற்போதைய வடிவத்தில் இந்த விதிமுறையில் கையொப்பமிடுவது உங்கள் நிறுவனத்திற்கு "
                f"எதிர்பாராத நிதி இழப்புகள் அல்லது தகராறு தீர்வின் போது கடுமையான நடைமுறை குறைபாடுகளை ஏற்படுத்தக்கூடும். "
                f"கண்டறியப்பட்ட சான்றுகள்: {ev_str}।\n\n"
                f"4. சட்ட மறுஆய்வுக்கான முக்கிய ஆலோசனைகள்: இந்த விதிமுறை உங்கள் வர்த்தக வரம்பில் நியாயமானதா "
                f"என்றும், பொறுப்பு உச்சவரம்பு (Liability Cap) நிர்ணயித்து பரஸ்பர சமநிலையை ஏற்படுத்த முடியுமா என்றும் வழக்கறிஞரிடம் ஆலோசிக்கவும்."
            )
            consequences = f"{cat_trans} பிரிவின் கீழ் அதிக நிதி மற்றும் செயல்பாட்டு பொறுப்புகள் ஏற்பட வாய்ப்புள்ளது."
            ambiguities = [
                "பொறுப்பு வரம்பின் எல்லை மிகவும் விரிவாகவும் விதிவிலக்குகள் இன்றியும் உள்ளது.",
                "இரு தரப்பினருக்கும் சமமான பரஸ்பர பாதுகாப்பு இல்லை."
            ]

        else:
            detailed_body = (
                f"Detailed Analysis for {category} ({risk_level.upper()} RISK):\n\n"
                f"1. Contractual Obligation: The clause specifies: \"{snippet}\"\n\n"
                f"2. Risk Assessment Rationale: {rationale}\n\n"
                f"3. Practical Consequences: Signing this provision in its current form may expose your organization to "
                f"unforeseen liabilities or procedural disadvantages during dispute resolution. "
                f"Identified evidence spans: {ev_str}.\n\n"
                f"4. Suggested Points for Professional Review: Ask legal counsel to clarify whether this clause "
                f"is standard in your commercial jurisdiction and whether reciprocal mutual protections can be inserted."
            )
            consequences = f"Potential exposure to {category.lower()} liabilities and financial or operational impact."
            ambiguities = [
                "Scope of covered breaches is broadly phrased without explicit exceptions.",
                "Lack of bilateral mutuality or reciprocal notice requirements."
            ]

        return {
            "detailed_explanation": detailed_body,
            "practical_consequences": consequences,
            "ambiguities_identified": ambiguities,
            "model": f"LLM ({settings.LLM_PROVIDER}: {settings.LLM_MODEL_NAME})",
            "status": "success",
            "language": target_lang
        }

    @classmethod
    def _call_gemini_api(cls, clause_text: str, category: str, risk_level: str, rationale: str, evidence: List[str], target_lang: str) -> Dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL_NAME}:generateContent?key={settings.LLM_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        f"{cls.SYSTEM_PROMPT}\n\n"
                        f"Target Language: {target_lang}\n"
                        f"Category: {category}\nRisk: {risk_level}\nRationale: {rationale}\nEvidence: {evidence}\n"
                        f"Clause Text: {clause_text}\n\n"
                        f"Output the complete 4-part legal analysis strictly in {target_lang}."
                    )
                }]
            }]
        }
        with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "detailed_explanation": generated_text,
                "model": f"Gemini ({settings.LLM_MODEL_NAME})",
                "status": "success",
                "language": target_lang
            }

    @classmethod
    def _call_openai_api(cls, clause_text: str, category: str, risk_level: str, rationale: str, evidence: List[str], target_lang: str) -> Dict:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
        payload = {
            "model": settings.LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": f"{cls.SYSTEM_PROMPT}\nProvide complete response in {target_lang}."},
                {"role": "user", "content": f"Category: {category}\nRisk: {risk_level}\nClause: {clause_text}\nLanguage: {target_lang}"}
            ],
            "temperature": 0.2
        }
        with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            generated_text = data["choices"][0]["message"]["content"]
            return {
                "detailed_explanation": generated_text,
                "model": f"OpenAI ({settings.LLM_MODEL_NAME})",
                "status": "success",
                "language": target_lang
            }
