import React, { useState, useEffect, useRef, useMemo } from "react";
import * as api from "./services/api";
import { LOGO_SRC } from "./assets/logo";

const CLAUSES = [
  { id: 1, type: "Definitions", risk: "low", text: "Capitalized terms used in this Agreement shall have the meanings ascribed to them in Schedule A.", explain: "Standard boilerplate that just points to defined terms elsewhere in the contract.", why: "No obligations or exposure are created by this clause.", action: "No action needed.", conf: 97, evidence: ["Capitalized terms defined in Schedule A"], questions: ["Are all schedules attached?"], uncertainties: ["Subject to referenced schedules"] },
  { id: 2, type: "Payment Terms", risk: "low", text: "Client shall remit payment within thirty (30) days of invoice date via wire transfer or ACH.", explain: "A standard 30-day payment window, common across service agreements.", why: "The timeline and payment method are both reasonable and typical.", action: "No action needed.", conf: 95, evidence: ["30-day payment timeline"], questions: ["What are late fee terms?"], uncertainties: ["Banking transfer fee allocation"] },
  { id: 3, type: "Confidentiality", risk: "low", text: "Each party agrees to protect the other's confidential information using reasonable care for a period of three years following disclosure.", explain: "A mutual, time-limited confidentiality obligation.", why: "The obligation is mutual and the three-year term is standard.", action: "No action needed.", conf: 93, evidence: ["Mutual reasonable care standard"], questions: ["What constitutes confidential material?"], uncertainties: ["Jurisdiction trade secret laws"] },
  { id: 4, type: "Limitation of Liability", risk: "high", text: "In no event shall either party's liability be limited, and each party shall be fully liable for any and all direct, indirect, incidental, or consequential damages arising from this Agreement.", explain: "This clause may expose you to financial responsibility without a defined maximum.", why: "Most contracts cap liability at the contract value or a fixed amount. This one removes any cap entirely.", action: "Consider negotiating a reasonable liability cap.", conf: 91, evidence: ["In no event shall either party's liability be limited", "fully liable for any and all damages"], questions: ["Can we cap liability to fees paid in the past 12 months?", "Can consequential damages be excluded?"], uncertainties: ["Statutory gross negligence exemptions"] },
  { id: 5, type: "Termination for Convenience", risk: "medium", text: "Either party may terminate this Agreement for convenience upon fifteen (15) days written notice, without further obligation.", explain: "Either side can walk away with only two weeks' notice.", why: "A short notice window gives you little time to plan around losing the arrangement.", action: "Consider whether 15 days gives you enough time to transition if the other party exits.", conf: 84, evidence: ["Termination for convenience on 15 days notice"], questions: ["Is 30 to 60 days notice negotiable?"], uncertainties: ["Payment for work in progress upon notice"] },
  { id: 6, type: "Automatic Renewal", risk: "high", text: "This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least ninety (90) days prior to the end of the then-current term.", explain: "You could be locked into another full year if you miss a narrow cancellation window.", why: "A 90-day advance notice requirement is easy to miss and commits you well before the term actually ends.", action: "Set a calendar reminder well ahead of the 90-day cutoff, or negotiate a shorter notice window.", conf: 89, evidence: ["Successive one-year terms", "90 days prior notice required"], questions: ["Can we change this to explicit written renewal?"], uncertainties: ["Price escalation on renewal"] },
  { id: 7, type: "Indemnification", risk: "high", text: "Contractor shall indemnify, defend, and hold harmless Client from and against any and all claims, losses, damages, liabilities, and expenses, including reasonable attorneys' fees, arising out of or related to Contractor's performance under this Agreement.", explain: "You may be responsible for covering a wide range of losses or legal claims.", why: "The scope of 'any and all claims... related to performance' is very broad and not limited to the contractor's own negligence.", action: "Review the scope of indemnification before signing, and consider limiting it to claims caused by your own fault.", conf: 88, evidence: ["Hold harmless from any and all claims", "Attorneys' fees included"], questions: ["Can indemnification be limited to our sole negligence?"], uncertainties: ["Commercial insurance indemnity coverage"] },
  { id: 8, type: "Governing Law and Dispute Resolution", risk: "medium", text: "This Agreement shall be governed by the laws of the State of Delaware, and any disputes shall be resolved through binding arbitration in Wilmington, Delaware.", explain: "Disputes go to arbitration in a specific location rather than a local court.", why: "Binding arbitration in a distant venue can be costly to attend and waives your right to a jury trial.", action: "Consider whether the arbitration location is practical for you, or negotiate a more neutral venue.", conf: 82, evidence: ["Binding arbitration in Wilmington, Delaware"], questions: ["Can venue be shifted to our home jurisdiction?"], uncertainties: ["Arbitration administrative fees"] },
  { id: 9, type: "Non-Compete", risk: "medium", text: "During the term of this Agreement and for twelve (12) months thereafter, Contractor shall not provide similar services to any direct competitor of Client.", explain: "You're restricted from similar work for a year after this ends.", why: "A 12-month restriction can limit your future income if this client relationship ends.", action: "Confirm the scope of 'similar services' and 'direct competitor' are clearly and narrowly defined.", conf: 80, evidence: ["12 months post-termination restriction"], questions: ["Can non-compete be replaced by non-solicitation?"], uncertainties: ["Enforceability under regional employment laws"] },
  { id: 10, type: "Warranty Disclaimer", risk: "medium", text: "Except as expressly stated herein, the services are provided \"as is\" without warranties of any kind, whether express or implied, including merchantability or fitness for a particular purpose.", explain: "You have limited recourse if the service doesn't work as expected.", why: "Disclaiming implied warranties removes a common legal fallback if something goes wrong.", action: "Consider asking for a specific performance warranty for critical deliverables.", conf: 79, evidence: ["Services provided 'as is'", "Disclaims merchantability and fitness"], questions: ["Can we insert an express conformity warranty?"], uncertainties: ["Statutory consumer protection overrides"] },
  { id: 11, type: "Force Majeure", risk: "low", text: "Neither party shall be liable for delays caused by circumstances beyond its reasonable control, including natural disasters, war, or governmental action.", explain: "A standard clause excusing delays caused by events outside anyone's control.", why: "This is mutual and limited to genuinely uncontrollable events.", action: "No action needed.", conf: 94, evidence: ["Circumstances beyond reasonable control"], questions: ["Does it cover power or telecommunication outages?"], uncertainties: ["Pandemic or regulatory shutdown coverage"] },
  { id: 12, type: "Assignment", risk: "low", text: "Neither party may assign this Agreement without the prior written consent of the other party, except in connection with a merger or sale of substantially all assets.", explain: "Neither party can hand this contract off to someone else without agreement.", why: "This is mutual and includes a standard carve-out for mergers or acquisitions.", action: "No action needed.", conf: 92, evidence: ["Prior written consent required with merger carve-out"], questions: ["Are affiliate transfers permitted?"], uncertainties: ["Corporate restructuring implications"] }
];

const LANGS = ["English", "Tamil", "Hindi", "Malayalam", "Telugu"];

const TRANSLATIONS = {
  English: "This clause renews automatically unless you cancel at least 90 days before it ends.",
  Tamil: "இந்தப் பிரிவு தானாகவே புதுப்பிக்கப்படும், நீங்கள் அது முடிவதற்கு குறைந்தது 90 நாட்களுக்கு முன் ரத்து செய்யாவிட்டால்.",
  Hindi: "यह खंड अपने आप नवीनीकृत हो जाता है जब तक कि आप इसके समाप्त होने से कम से कम 90 दिन पहले रद्द न करें।",
  Malayalam: "ഇത് അവസാനിക്കുന്നതിന് കുറഞ്ഞത് 90 ദിവസം മുമ്പ് നിങ്ങൾ റദ്ദാക്കിയില്ലെങ്കിൽ, ഈ വ്യവസ്ഥ സ്വയമേവ പുതുക്കപ്പെടും.",
  Telugu: "మీరు దీని ముగింపుకు కనీసం 90 రోజుల ముందు రద్దు చేయకపోతే, ఈ నిబంధన స్వయంచాలకంగా పునరుద్ధరించబడుతుంది."
};

const CLIENT_TRANSLATIONS = {
  Tamil: {
    summary: "இந்த ஒப்பந்தத்தில் கையொப்பமிடுவதற்கு முன் கவனம் செலுத்த வேண்டிய சில முக்கிய பிரிவுகள் உள்ளன. வரம்பற்ற நிதிப் பொறுப்பு, தானாக புதுப்பித்தல் மற்றும் ஒருதலைப்பட்ச இழப்பீட்டு உத்தரவாதம் ஆகியவை மிக முக்கியமான கவலைகளாகும்.",
    review: "கையொப்பமிடுவதற்கு முன், பொறுப்பு உச்சவரம்பை நிர்ணயிக்கவும், புதுப்பித்தல் அறிவிப்பு காலத்தை 30 நாட்களாக மாற்றவும் பேச்சுவார்த்தை நடத்தவும்.",
    categories: {
      "Limitation of Liability": "பொறுப்பு வரம்பு",
      "Indemnification": "இழப்பீட்டு உத்தரவாதம்",
      "Termination for Convenience": "வசதிக்கான முடிவுறுத்தல்",
      "Termination": "முடிவுறுத்தல் / ரத்து செய்தல்",
      "Automatic Renewal": "தானாக புதுப்பித்தல்",
      "Confidentiality": "ரகசியத்தன்மை",
      "Payment Terms": "பணம் செலுத்தும் விதிமுறைகள்",
      "Governing Law and Dispute Resolution": "சட்ட வரம்பு மற்றும் தகராறு தீர்வு",
      "Non-Compete": "போட்டியிடாமை கட்டுப்பாடு",
      "Warranty Disclaimer": "உத்தரவாத மறுப்பு",
      "Force Majeure": "கட்டாய நிகழ்வு",
      "Assignment": "ஒப்பந்த உரிமைகள் மாற்றல்",
      "Definitions": "வரையறைகள்"
    },
    clauses: {
      1: { explain: "ஒப்பந்தத்தில் பிற இடங்களில் வரையறுக்கப்பட்ட சொற்களைக் குறிக்கும் நிலையான விதிமுறை.", why: "இந்தப் பிரிவால் எந்தவொரு புதிய கடமைகளும் உருவாக்கப்படவில்லை.", action: "எந்த நடவடிக்கையும் தேவையில்லை." },
      2: { explain: "விலைப்பட்டியல் தேதியிலிருந்து 30 நாட்களுக்குள் வாடிக்கையாளர் பணம் செலுத்த வேண்டும் என்ற நிலையான காலக்கெடு.", why: "காலக்கெடுவும் கட்டண முறையும் நியாயமானவை.", action: "எந்த நடவடிக்கையும் தேவையில்லை." },
      3: { explain: "இரு தரப்பினரும் ரகசிய தகவல்களை 3 ஆண்டுகளுக்கு நியாயமான கவனத்துடன் பாதுகாக்க ஒப்புக்கொள்கிறார்கள்.", why: "இந்த கடமை இரு தரப்பிற்கும் பொதுவானது மற்றும் 3 ஆண்டு காலம் சரியானது.", action: "எந்த நடவடிக்கையும் தேவையில்லை." },
      4: { explain: "வரையறுக்கப்பட்ட அதிகபட்ச வரம்பு இல்லாமல் வரம்பற்ற நிதிப் பொறுப்புக்கு உங்களை ஆளாக்கக்கூடும்.", why: "பெரும்பாலான ஒப்பந்தங்கள் பொறுப்பு வரம்பை நிர்ணயிக்கின்றன. ஆனால் இந்தப் பிரிவு உச்சவரம்பு எதையும் வைக்கவில்லை.", action: "நியாயமான பொறுப்பு உச்சவரம்பை (எ.கா. முந்தைய 12 மாத கட்டணம்) நிர்ணயிக்க பேச்சுவார்த்தை நடத்தவும்." },
      5: { explain: "இரு தரப்பிலும் வெறும் 15 நாட்கள் அறிவிப்புடன் எந்தவொரு கடமையும் இன்றி விலகிச் செல்ல முடியும்.", why: "குறுகிய 15 நாள் அறிவிப்பு காலம் ஒப்பந்தம் ரத்தானால் மாற்றீடு செய்ய போதுமான நேரத்தை அளிக்காது.", action: "15 நாட்கள் போதுமானதா என்பதை கவனியுங்கள், அல்லது 30 முதல் 60 நாட்களாக மாற்ற பேச்சுவார்த்தை நடத்தவும்." },
      6: { explain: "முடிவதற்கு 90 நாட்களுக்கு முன்னதாக அறிவிக்காவிட்டால் இந்த ஒப்பந்தம் தானாகவே மற்றொரு வருடத்திற்கு புதுப்பிக்கப்படும்.", why: "90 நாள் முன்னறிவிப்பு சாளரத்தை தவறவிட்டால் மற்றொரு முழு வருடத்திற்கு நீங்கள் பிணைக்கப்படுவீர்கள்.", action: "90 நாள் முடிவிற்கு முன்பே நினைவூட்டலை அமைக்கவும் அல்லது குறுகிய அறிவிப்பு காலத்தை கேட்கவும்." },
      7: { explain: "வாடிக்கையாளருக்கு ஏற்படும் பரந்த அளவிலான இழப்புகள் அல்லது சட்ட உரிமைகோரல்களை ஈடுசெய்வதற்கு நீங்கள் பொறுப்பாக நேரிடலாம்.", why: "ஒப்பந்ததாரரின் சொந்த தவறுக்கு மட்டுமே மட்டுப்படுத்தப்படாமல் மிக விரிவான இழப்பீட்டு பொறுப்பை சுமத்துகிறது.", action: "கையொப்பமிடுவதற்கு முன் இழப்பீட்டின் வரம்பை உங்கள் நேரடி தவறுக்கு மட்டுமே மட்டுப்படுத்துங்கள்." },
      8: { explain: "டெலாவேர் மாநில சட்டங்களின் கீழ் பிணைக்கப்பட்ட நடுவர் மன்றம் மூலம் மட்டுமே தகராறுகள் தீர்க்கப்படும்.", why: "தொலைதூர இடத்தில் நடுவர் மன்றத்திற்கு செல்வது அதிக செலவை ஏற்படுத்தும்.", action: "நடுவர் மன்ற இடம் உங்களுக்கு நடைமுறைக்கு உகந்ததா என்பதை கவனியுங்கள்." },
      9: { explain: "ஒப்பந்தம் முடிந்த பிறகும் 12 மாதங்களுக்கு நேரடி போட்டியாளர்களுக்கு சேவை வழங்க தடை விதிக்கப்பட்டுள்ளது.", why: "12 மாத கால தடை இந்த வாடிக்கையாளர் உறவு முடிந்த பிறகும் உங்கள் வருமானத்தை பாதிக்கலாம்.", action: "'நேரடி போட்டியாளர்' மற்றும் 'இதேபோன்ற சேவைகள்' சரியாக வரையறுக்கப்பட்டுள்ளதா என உறுதிப்படுத்தவும்." },
      10: { explain: "சேவைகள் எந்தவொரு வெளிப்படையான அல்லது மறைமுகமான உத்தரவாதமும் இன்றி 'உள்ளவாறே' வழங்கப்படுகின்றன.", why: "மறைமுக உத்தரவாதங்களை நீக்குவது குறைபாடுகள் ஏற்பட்டால் தீர்வை குறைக்கிறது.", action: "முக்கிய பணிகளுக்கு குறிப்பிட்ட தர உத்தரவாதத்தை கேட்கவும்." },
      11: { explain: "இயற்கை பேரிடர் போன்ற கட்டுப்பாடற்ற நிகழ்வுகளால் ஏற்படும் தாமதங்களுக்கு எந்தவொரு தரப்பும் பொறுப்பாகாது.", why: "இது நியாயமான இருதரப்பு நிலையான விதி.", action: "எந்த நடவடிக்கையும் தேவையில்லை." },
      12: { explain: "மற்ற தரப்பின் எழுத்துப்பூர்வ அனுமதியின்றி இந்த ஒப்பந்தத்தை மாற்றவோ உரிமை மாற்றவோ முடியாது.", why: "இது பரஸ்பர ஒப்புதல் தேவைப்படும் நிலையான விதிமுறை.", action: "எந்த நடவடிக்கையும் தேவையில்லை." }
    }
  },
  Hindi: {
    summary: "इस अनुबंध में कई ऐसे खंड हैं जिन पर हस्ताक्षर करने से पहले ध्यान देने की आवश्यकता है। सबसे महत्वपूर्ण चिंताओं में असीमित वित्तीय दायित्व, स्वचालित नवीनीकरण और एकतरफा क्षतिपूर्ति शामिल हैं।",
    review: "हस्ताक्षर करने से पहले दायित्व सीमा तय करने और नवीनीकरण नोटिस अवधि 30 दिन करने पर बातचीत करें।",
    categories: {
      "Limitation of Liability": "दायित्व की सीमा",
      "Indemnification": "क्षतिपूर्ति",
      "Termination for Convenience": "सुविधा अनुसार समाप्ति",
      "Termination": "समाप्ति / रद्दीकरण",
      "Automatic Renewal": "स्वचालित नवीनीकरण",
      "Confidentiality": "गोपनीयता",
      "Payment Terms": "भुगतान की शर्तें",
      "Governing Law and Dispute Resolution": "शासी कानून और विवाद समाधान",
      "Non-Compete": "गैर-प्रतिस्पर्धा प्रतिबंध",
      "Warranty Disclaimer": "वारंटी अस्वीकरण",
      "Force Majeure": "अनिवार्य घटना",
      "Assignment": "समनुदेशन",
      "Definitions": "परिभाषाएं"
    },
    clauses: {
      1: { explain: "मानक सामान्य खंड जो केवल अनुबंध में अन्यत्र परिभाषित शब्दों को संदर्भित करता है।", why: "इस खंड द्वारा कोई नया दायित्व या जोखिम उत्पन्न नहीं होता है।", action: "किसी कार्रवाई की आवश्यकता नहीं है।" },
      2: { explain: "चालान तिथि के 30 दिनों के भीतर भुगतान करने की मानक समय सीमा।", why: "समय सीमा और भुगतान का तरीका दोनों उचित और सामान्य हैं।", action: "किसी कार्रवाई की आवश्यकता नहीं है।" },
      3: { explain: "दोनों पक्ष तीन साल की अवधि के लिए उचित सावधानी से गोपनीय जानकारी की रक्षा करने के लिए सहमत हैं।", why: "यह दायित्व दोनों पक्षों के लिए पारस्परिक और उचित है।", action: "किसी कार्रवाई की आवश्यकता नहीं है।" },
      4: { explain: "यह खंड आपको बिना किसी निर्धारित अधिकतम सीमा के असीमित वित्तीय जिम्मेदारी में डाल सकता है।", why: "अधिकांश अनुबंध दायित्व को सीमित करते हैं। यह खंड किसी भी सीमा को पूरी तरह से हटा देता है।", action: "कुल दायित्व सीमा (उदा. पिछले 12 महीनों में भुगतान की गई फीस) तय करने के लिए बातचीत करें।" },
      5: { explain: "कोई भी पक्ष केवल 15 दिनों के लिखित नोटिस पर बिना किसी बाध्यता के अलग हो सकता है।", why: "कम समय का नोटिस अनुबंध समाप्त होने पर योजना बनाने का बहुत कम समय देता है।", action: "विचार करें कि क्या 15 दिन पर्याप्त हैं, या 30-60 दिनों की नोटिस अवधि मांगें।" },
      6: { explain: "यदि समाप्ति से 90 दिन पहले सूचना नहीं दी गई तो यह अनुबंध स्वतः एक वर्ष के लिए नवीनीकृत हो जाएगा।", why: "90-दिन की संकीर्ण समय सीमा चूक जाने पर आप एक और पूरे वर्ष के लिए बंध सकते हैं।", action: "कैलेंडर अनुस्मारक सेट करें या छोटी नोटिस अवधि के लिए बातचीत करें।" },
      7: { explain: "आप कानूनी दावों और हानियों की एक विस्तृत श्रृंखला को कवर करने के लिए जिम्मेदार हो सकते हैं।", why: "यह ठेकेदार की केवल अपनी गलती तक सीमित नहीं है, बल्कि बहुत व्यापक दायित्व डालता है।", action: "हस्ताक्षर करने से पहले क्षतिपूर्ति के दायरे की समीक्षा करें और इसे अपनी गलती तक सीमित करें।" },
      8: { explain: "विवादों को स्थानीय अदालत के बजाय डेलावेयर में बाध्यकारी मध्यस्थता द्वारा सुलझाया जाएगा।", why: "दूरस्थ स्थान पर मध्यस्थता में भाग लेना महंगा हो सकता है।", action: "विचार करें कि क्या मध्यस्थता का स्थान आपके लिए व्यावहारिक है।" },
      9: { explain: "अनुबंध समाप्त होने के बाद 12 महीने तक सीधे प्रतिस्पर्धियों को समान सेवाएं देने पर प्रतिबंध है।", why: "12 महीने का प्रतिबंध आपकी भविष्य की आय को सीमित कर सकता है।", action: "सुनिश्चित करें कि 'प्रतिस्पर्धी' और 'समान सेवाएं' स्पष्ट रूप से परिभाषित हैं।" },
      10: { explain: "सेवाएं बिना किसी व्यक्त या निहित वारंटी के 'जैसी हैं वैसी' प्रदान की जाती हैं।", why: "वारंटी अस्वीकार करने से समस्या होने पर कानूनी विकल्प सीमित हो जाते हैं।", action: "महत्वपूर्ण कार्यों के लिए विशिष्ट गुणवत्ता वारंटी मांगें।" },
      11: { explain: "प्राकृतिक आपदाओं जैसे अनियंत्रित कारणों से होने वाली देरी के लिए कोई दंड नहीं होगा।", why: "यह पारस्परिक और वास्तविक अप्रत्याशित घटनाओं तक सीमित है।", action: "किसी कार्रवाई की आवश्यकता नहीं है।" },
      12: { explain: "कोई भी पक्ष बिना पूर्व लिखित सहमति के इस अनुबंध को किसी अन्य को हस्तांतरित नहीं कर सकता।", why: "यह पारस्परिक है और विलय के लिए मानक छूट शामिल है।", action: "किसी कार्रवाई की आवश्यकता नहीं है।" }
    }
  },
  Malayalam: {
    summary: "ഒപ്പിടുന്നതിന് മുമ്പ് ശ്രദ്ധിക്കേണ്ട ചില പ്രധാന വ്യവസ്ഥകൾ ഈ കരാറിലുണ്ട്. പരിധിയില്ലാത്ത ബാധ്യതയും സ്വയമേവ പുതുക്കലും പ്രധാന ആശങ്കകളാണ്.",
    review: "ബാധ്യതാ പരിധി നിശ്ചയിക്കുന്നതിനും നോട്ടീസ് കാലാവധി 30 ദിവസമാക്കുന്നതിനും ചർച്ച ചെയ്യുക.",
    categories: {
      "Limitation of Liability": "ബാധ്യതാ പരിധി",
      "Indemnification": "നഷ്ടപരിഹാരം",
      "Termination for Convenience": "സൗകര്യപ്രദമായ റദ്ദാക്കൽ",
      "Termination": "റദ്ദാക്കൽ",
      "Automatic Renewal": "സ്വയമേവ പുതുക്കൽ",
      "Confidentiality": "രഹസ്യാത്മകത",
      "Payment Terms": "പേയ്മെന്റ് നിബന്ധനകൾ",
      "Governing Law and Dispute Resolution": "നിയമപരിധിയും തർക്ക പരിഹാരവും",
      "Non-Compete": "മത്സരവിലക്ക്",
      "Warranty Disclaimer": "വാറന്റി നിരാകരണം",
      "Force Majeure": "നിർബന്ധിത സാഹചര്യം",
      "Assignment": "കരാർ കൈമാറ്റം",
      "Definitions": "നിർവചനങ്ങൾ"
    },
    clauses: {
      1: { explain: "കരാറിലെ മറ്റ് ഭാഗങ്ങളിൽ നിർവചിച്ചിരിക്കുന്ന പദങ്ങളെ പരാമർശിക്കുന്ന സാധാരണ വ്യവസ്ഥ.", why: "ഈ വ്യവസ്ഥ പുതിയ ബാധ്യതകളോ അപകടസാധ്യതകളോ സൃഷ്ടിക്കുന്നില്ല.", action: "നടപടികൾ ഒന്നും ആവശ്യമില്ല." },
      2: { explain: "ഇൻവോയ്സ് തീയതി മുതൽ 30 ദിവസത്തിനകം ഉപഭോക്താവ് പണം നൽകണമെന്ന സാധാരണ സമയപരിധി.", why: "സമയപരിധിയും പേയ്‌മെന്റ് രീതിയും സാധാരണ വാണിജ്യ രീതിയാണ്.", action: "നടപടികൾ ഒന്നും ആവശ്യമില്ല." },
      3: { explain: "രഹസ്യ വിവരങ്ങൾ 3 വർഷത്തേക്ക് ന്യായമായ ശ്രദ്ധയോടെ സംരക്ഷിക്കാൻ ഇരു കക്ഷികളും സമ്മതിക്കുന്നു.", why: "ഈ ബാധ്യത ഇരു കക്ഷികൾക്കും ബാധകവും ന്യായവുമാണ്.", action: "നടപടികൾ ഒന്നും ആവശ്യമില്ല." },
      4: { explain: "സാമ്പത്തിക ബാധ്യതയ്ക്ക് പരമാവധി പരിധിയില്ലാതെ വലിയ നഷ്ടത്തിലേക്ക് നയിച്ചേക്കാം.", why: "ഈ വ്യവസ്ഥ ബാധ്യതാ പരിധി പൂർണ്ണമായും ഒഴിവാക്കുന്നു.", action: "ന്യായമായ ബാധ്യതാ പരിധി നിശ്ചയിക്കാൻ ചർച്ച ചെയ്യുക." },
      5: { explain: "15 ദിവസത്തെ രേഖാമൂലമുള്ള നോട്ടീസോടെ ഇരു കക്ഷികൾക്കും ബാധ്യതകളില്ലാതെ പിന്മാറാം.", why: "കുറഞ്ഞ നോട്ടീസ് കാലയളവ് കരാർ റദ്ദായാൽ പുതിയ ക്രമീകരണങ്ങൾ ചെയ്യാൻ കുറഞ്ഞ സമയം മാത്രമേ നൽകുന്നുള്ളൂ.", action: "നോട്ടീസ് കാലാവധി 30 മുതൽ 60 ദിവസമാക്കാൻ ചർച്ച ചെയ്യുക." },
      6: { explain: "90 ദിവസം മുമ്പ് അറിയിച്ചില്ലെങ്കിൽ കരാർ സ്വയമേവ ഒരു വർഷത്തേക്ക് കൂടി പുതുക്കപ്പെടും.", why: "നോട്ടീസ് കാലാവധി തെറ്റിയാൽ അടുത്ത ഒരു വർഷത്തേക്ക് കൂടി ബാധ്യസ്ഥനാകും.", action: "നോട്ടീസ് കാലാവധി കുറയ്ക്കാൻ ചർച്ച ചെയ്യുക." },
      7: { explain: "എല്ലാ നഷ്ടങ്ങൾക്കും നഷ്ടപരിഹാരം നൽകാനുള്ള വിപുലമായ ബാധ്യത.", why: "നിങ്ങൾ മാത്രം കുറ്റക്കാരനല്ലാത്തപ്പോഴും മറ്റേ കക്ഷിയുടെ നഷ്ടങ്ങൾ നൽകാൻ ബാധ്യസ്ഥനാക്കുന്നു.", action: "നഷ്ടപരിഹാര ബാധ്യത സ്വന്തം തെറ്റുകൾക്ക് മാത്രമായി ചുരുക്കുക." },
      8: { explain: "ഡെലവെയർ സംസ്ഥാന നിയമങ്ങൾക്ക് കീഴിൽ ആർബിട്രേഷൻ വഴി മാത്രമേ തർക്കങ്ങൾ പരിഹരിക്കൂ.", why: "വിദൂര സ്ഥലത്ത് ആർബിട്രേഷനിൽ പങ്കെടുക്കുന്നത് കൂടുതൽ ചിലവിലേക്ക് നയിക്കും.", action: "തർക്ക പരിഹാര വേദി നിങ്ങൾക്ക് അനുയോജ്യമാണോ എന്ന് പരിശോധിക്കുക." },
      9: { explain: "കരാർ അവസാനിച്ചതിന് ശേഷവും 12 മാസത്തേക്ക് സമാനമായ സേവനങ്ങൾ നൽകുന്നത് വിലക്കുന്നു.", why: "ഈ നിയന്ത്രണം ഭാവി വരുമാന സാധ്യതകളെ പ്രതികൂലമായി ബാധിച്ചേക്കാം.", action: "മത്സരവിലക്ക് നിർവചനം വ്യക്തമാക്കാനും കാലയളവ് കുറയ്ക്കാനും ആവശ്യപ്പെടുക." },
      10: { explain: "സേവനങ്ങൾ യാതൊരു ഉറപ്പുമില്ലാതെ 'ഉള്ളതുപോലെ' നൽകുന്നു.", why: "ഉത്തരവാദിത്ത നിരാകരണം സേവനങ്ങളിൽ പിഴവുകളുണ്ടായാൽ പരിഹാരം കുറയ്ക്കുന്നു.", action: "പ്രധാന ജോലികൾക്ക് ഗുണനിലവാര ഉറപ്പ് നൽകാൻ ആവശ്യപ്പെടുക." },
      11: { explain: "പ്രകൃതി ദുരന്തങ്ങൾ പോലുള്ള നിയന്ത്രണാതീതമായ കാരണങ്ങളാൽ ഉണ്ടാകുന്ന കാലതാമസങ്ങൾക്ക് ബാധ്യതയില്ല.", why: "ഇത് ഇരു കക്ഷികൾക്കും ബാധകമായ സാധാരണ വ്യവസ്ഥയാണ്.", action: "നടപടികൾ ഒന്നും ആവശ്യമില്ല." },
      12: { explain: "രേഖാമൂലമുള്ള അനുമതിയില്ലാതെ കരാർ കൈമാറ്റം ചെയ്യാനോ മാറ്റാനോ സാധ്യമല്ല.", why: "ഇത് സാധാരണ പരസ്പര വ്യവസ്ഥയാണ്.", action: "നടപടികൾ ഒന്നും ആവശ്യമില്ല." }
    }
  },
  Telugu: {
    summary: "సంతకం చేయడానికి ముందు గమనించవలసిన ముఖ్యమైన నిబంధనలు ఈ ఒప్పందంలో ఉన్నాయి. పరిమితి లేని బాధ్యత మరియు స్వయంచాలక పునరుద్ధరణ ముఖ్యమైన ఆందోళనలు.",
    review: "బాధ్యతా పరిమితిని నిర్ణయించడానికి మరియు నోటీసు వ్యవధిని 30 రోజులకు మార్చడానికి చర్చలు జరపండి.",
    categories: {
      "Limitation of Liability": "బాధ్యత పరిమితి",
      "Indemnification": "నష్టపరిహారం",
      "Termination for Convenience": "సౌలభ్యం మేరకు రద్దు",
      "Automatic Renewal": "స్వయంచాలక పునరుద్ధరణ",
      "Confidentiality": "రహస్యత",
      "Payment Terms": "చెల్లింపు నిబంధనలు",
      "Governing Law and Dispute Resolution": "వర్తించే చట్టం మరియు వివాద పరిష్కారం",
      "Non-Compete": "పోటీ నిషేధం",
      "Warranty Disclaimer": "వారంటీ నిరాకరణ",
      "Force Majeure": "అనివార్య సంఘటన",
      "Assignment": "ఒప్పంద బదిలీ",
      "Definitions": "నిర్వచనాలు"
    },
    clauses: {
      1: { explain: "ఒప్పందంలో ఇతర ప్రాంతాలలో నిర్వచించబడిన పదాలను సూచించే ప్రామాణిక నిబంధన.", why: "ఈ నిబంధన ద్వారా ఎటువంటి కొత్త బాధ్యతలు లేదా ప్రమాదాలు ఏర్పడవు.", action: "ఎటువంటి చర్య అవసరం లేదు." },
      2: { explain: "ఇన్వాయిస్ తేదీ నుండి 30 రోజుల్లోగా చెల్లింపు చేయవలసిన ప్రామాణిక నిబంధన.", why: "సమయ వ్యవధి మరియు చెల్లింపు విధానం సాధారణమైనవి.", action: "ఎటువంటి చర్య అవసరం లేదు." },
      3: { explain: "రహస్య సమాచారాన్ని 3 సంవత్సరాల పాటు రక్షించేందుకు ఇరు పక్షాలు అంగీకరిస్తాయి.", why: "ఈ బాధ్యత పరస్పరమైనది మరియు సమంజసమైనది.", action: "ఎటువంటి చర్య అవసరం లేదు." },
      4: { explain: "పరిమితి లేకుండా అపరిమిత ఆర్థిక బాధ్యతకు దారితీయవచ్చు. ఒప్పంద విలువ కంటే ఎక్కువ నష్టం రావచ్చు.", why: "ఈ నిబంధన ఎటువంటి గరిష్ట బాధ్యతా పరిమితిని లేకుండా చేస్తుంది.", action: "సహేతుకమైన బాధ్యతా పరిమితిని నిర్ణయించేందుకు చర్చలు జరపండి." },
      5: { explain: "15 రోజుల వ్రాతపూర్వక నోటీసుతో ఏ పక్షమైనా ఒప్పందాన్ని రద్దు చేసుకోవచ్చు.", why: "తక్కువ నోటీసు వ్యవధి మార్పులకు ప్రణాళిక వేసుకోవడానికి తక్కువ సమయాన్ని ఇస్తుంది.", action: "నోటీసు వ్యవధిని 30 నుండి 60 రోజులకు పెంచడానికి చర్చలు జరపండి." },
      6: { explain: "90 రోజుల ముందు నోటీసు ఇవ్వకపోతే ఈ ఒప్పందం స్వయంచాలకంగా ఒక సంవత్సరం పునరుద్ధరించబడుతుంది.", why: "సమయానికి నోటీసు ఇవ్వకపోతే మరొక సంవత్సరం పాటు కట్టుబడి ఉండాల్సి వస్తుంది.", action: "నోటీసు వ్యవధిని తగ్గించేందుకు చర్చలు జరపండి." },
      7: { explain: "క్లయింట్‌కు కలిగే అన్ని నష్టాలు మరియు న్యాయవాది రుసుములను భరించేందుకు బాధ్యత పడవచ్చు.", why: "మీరు మాత్రమే తప్పు చేయనప్పటికీ అన్ని నష్టాలను భరించాల్సి రావచ్చు.", action: "నష్టపరిహారాన్ని మీ స్వంత తప్పులకు మాత్రమే పరిమితం చేయండి." },
      8: { explain: "డెలావేర్ రాష్ట్ర చట్టాల ప్రకారం మధ్యవర్తిత్వం ద్వారా మాత్రమే వివాదాలు పరిష్కరించబడతాయి.", why: "సుదూర ప్రాంతంలో మధ్యవర్తిత్వం ఖర్చుతో కూడుకున్నది కావచ్చు.", action: "వివాద పరిష్కార వేదిక మీకు ఆచరణాత్మకమైనదో కాదో పరిశీలించండి." },
      9: { explain: "ఒప్పందం ముగిసిన తర్వాత కూడా 12 నెలల పాటు పోటీదారులకు సేవలు అందించడం నిషేధించబడింది.", why: "ఈ ఆంక్ష మీ భవిష్యత్ ఆదాయాన్ని పరిమితం చేయవచ్చు.", action: "పోటీ నిషేధ పరిధిని మీ వ్యక్తిగత క్లయింట్లకు మాత్రమే పరిమితం చేయండి." },
      10: { explain: "సేవలు ఎటువంటి హామీలు లేకుండా 'ఉన్నవి ఉన్నట్లుగా' అందించబడతాయి.", why: "హామీల నిరాకరణ సమస్యలు వచ్చినప్పుడు చట్టపరమైన అవకాశాలను తగ్గిస్తుంది.", action: "కీలకమైన పనులకు నాణ్యతా హామీని కోరండి." },
      11: { explain: "సహజ విపత్తుల వంటి నియంత్రణ లేని సంఘటనల వల్ల ఆలస్యానికి ఎటువంటి జరిమానా ఉండదు.", why: "ఇది పరస్పర ఆమోదయోగ్యమైన సాధారణ నిబంధన.", action: "ఎటువంటి చర్య అవసరం లేదు." },
      12: { explain: "ముందస్తు వ్రాతపూర్వక అనుమతి లేకుండా ఈ ఒప్పందాన్ని బదిలీ చేయడం సాధ్యం కాదు.", why: "ఇది ప్రామాణిక పరస్పర నిబంధన.", action: "ఎటువంటి చర్య అవసరం లేదు." }
    }
  }
};

const ORIGINAL_EN = "This Agreement shall automatically renew for successive one-year terms unless notice is given at least ninety (90) days prior to the end of the term.";

const SAMPLE_CONTRACTS = [
  { id: "demo-1", name: "Vendor_Services_Agreement.pdf", date: "2026-07-18", lang: "English", risk: "high", flagged: 3, status: "Complete", total_clauses: 12 },
  { id: "demo-2", name: "Regional_Lease_Chennai.pdf", date: "2026-07-14", lang: "Tamil", risk: "medium", flagged: 2, status: "Complete", total_clauses: 8 },
  { id: "demo-3", name: "Freelance_NDA.docx", date: "2026-07-10", lang: "English", risk: "low", flagged: 0, status: "Complete", total_clauses: 6 },
  { id: "demo-4", name: "Franchise_Agreement_Kochi.pdf", date: "2026-07-05", lang: "Malayalam", risk: "high", flagged: 4, status: "Complete", total_clauses: 14 },
  { id: "demo-5", name: "Employment_Offer_Hyderabad.pdf", date: "2026-06-29", lang: "Telugu", risk: "medium", flagged: 2, status: "Complete", total_clauses: 10 },
  { id: "demo-6", name: "Rental_Deposit_Terms.txt", date: "2026-06-21", lang: "Hindi", risk: "low", flagged: 1, status: "Complete", total_clauses: 7 }
];

const PROC_STEPS = [
  "Document uploaded & validated", "Language detected & verified", "Text extracted & normalized",
  "Translation completed (if required)", "Segmenting legal clauses", "Legal-BERT classification",
  "Evaluating contractual risks", "Generating SLM & LLM explanations"
];

const PROC_MESSAGES = [
  "Validating document format and security boundaries...",
  "Running language detection and script verification...",
  "Extracting text page-by-page and normalizing legal syntax...",
  "Executing multilingual translation for analysis...",
  "Identifying clause boundaries, numbering, and headings...",
  "Applying Legal-BERT representations and CUAD taxonomy...",
  "Assessing liability caps, indemnification, and risk exposure...",
  "Synthesizing plain-language summaries and detailed analysis...",
  "Compiling risk report and final structured assessment..."
];

const PIPELINE = [
  ["01", "Upload", "PDF, DOCX, or TXT documents"],
  ["02", "Detect language", "Any of 5 supported languages"],
  ["03", "Translate", "Preserves clause mapping into English"],
  ["04", "Normalize text", "Cleans artifacts without altering legal terms"],
  ["05", "Segment clauses", "Legal boundary & numbering detection"],
  ["06", "Legal-BERT Classify", "CUAD-aligned taxonomy representation"],
  ["07", "Risk Engine", "Independent exposure & mutuality scoring"],
  ["08", "Hybrid SLM-LLM", "Plain-English summaries & detailed counsel"]
];

function riskLabel(r) {
  const norm = (r || "low").toLowerCase();
  return norm === "high" ? "HIGH RISK" : norm === "medium" ? "MEDIUM RISK" : "LOW RISK";
}

function riskClass(r) {
  const norm = (r || "low").toLowerCase();
  return norm === "high" ? "high" : norm === "medium" ? "med" : "low";
}

const CSS = `
:root{
  --paper:#EDE7D9; --paper-panel:#E4DCC8; --paper-raised:#F6F1E5;
  --ink:#1F2340; --ink-soft:#565C7D; --ink-faint:#8A8FA8;
  --rule:#C7BCA0; --rule-strong:#B2A583;
  --risk-high:#A63A34; --risk-high-bg:#F3DEDB;
  --risk-med:#93641F; --risk-med-bg:#F1E2C4;
  --risk-low:#3E6B5C; --risk-low-bg:#DCE9E1;
  --accent:#6E2C3C; --accent-soft:#F0DCD9; --accent-dark:#4E1E2A;
  --font-display:'Fraunces', serif; --font-body:'IBM Plex Sans', sans-serif; --font-mono:'IBM Plex Mono', monospace;
}
.clausent-root{background:var(--paper);color:var(--ink);font-family:var(--font-body);line-height:1.55;-webkit-font-smoothing:antialiased;min-height:100vh;width:100%;display:flex;flex-direction:column;}
.clausent-root *{box-sizing:border-box;}
.clausent-root h1,.clausent-root h2,.clausent-root h3,.clausent-root h4{font-family:var(--font-display);font-weight:560;color:var(--ink);margin:0;}
.clausent-root p{margin:0;}
.clausent-root .mono{font-family:var(--font-mono);}
.clausent-root .eyebrow{font-family:var(--font-mono);font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:var(--accent);}
.clausent-root button{font-family:var(--font-body);cursor:pointer;}
.clausent-root select,.clausent-root input{font-family:var(--font-body);}
.topnav{position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:16px 44px;background:rgba(237,231,217,0.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule);gap:16px;width:100%;}
.logo{display:flex;align-items:center;gap:10px;cursor:pointer;}
.logo-mark{height:30px;width:auto;display:block;flex-shrink:0;image-rendering:-webkit-optimize-contrast;}
.logo-word{font-family:var(--font-display);font-weight:650;font-size:21px;letter-spacing:0.01em;}
.navlinks{display:flex;gap:4px;align-items:center;flex-wrap:wrap;}
.navlink{padding:8px 14px;border-radius:3px;border:none;background:none;font-size:14px;color:var(--ink-soft);font-weight:500;}
.navlink:hover{color:var(--ink);background:var(--paper-panel);}
.navlink.active{color:var(--accent);background:var(--accent-soft);}
.nav-actions{display:flex;align-items:center;gap:12px;}
.nav-cta{padding:9px 18px;border-radius:3px;border:1px solid var(--ink);background:var(--ink);color:var(--paper);font-size:14px;font-weight:500;}
.nav-cta:hover{background:var(--accent-dark);border-color:var(--accent-dark);}
.api-pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:11px;padding:4px 10px;border-radius:12px;border:1px solid var(--rule-strong);background:var(--paper-raised);color:var(--ink-soft);}
.api-dot{width:7px;height:7px;border-radius:50%;}
.api-dot.green{background:#2e7d32;}
.api-dot.amber{background:#d97706;}
.mode-toggle-btn{font-family:var(--font-mono);font-size:11px;padding:4px 9px;border-radius:3px;border:1px solid var(--rule-strong);background:var(--paper-raised);color:var(--ink);}
.mode-toggle-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);}
main{max-width:1600px;width:100%;margin:0 auto;padding:0 36px 80px;box-sizing:border-box;flex:1;}
section.block{padding:88px 0;border-bottom:1px solid var(--rule);}
section.block:last-child{border-bottom:none;}
.section-head{max-width:640px;margin-bottom:48px;}
.section-head h2{font-size:34px;line-height:1.15;margin-top:10px;}
.section-head p{color:var(--ink-soft);font-size:16px;margin-top:14px;}
.hero{padding:76px 0 60px;display:grid;grid-template-columns:1.05fr 1fr;gap:56px;align-items:center;border-bottom:1px solid var(--rule);}
.hero h1{font-size:52px;line-height:1.06;letter-spacing:-0.01em;}
.hero .eyebrow{margin-bottom:16px;display:block;}
.hero-desc{margin-top:22px;font-size:17px;color:var(--ink-soft);max-width:460px;}
.hero-cta-row{margin-top:34px;display:flex;gap:14px;flex-wrap:wrap;}
.btn-primary{padding:13px 24px;border-radius:3px;border:1px solid var(--accent);background:var(--accent);color:#fff;font-size:15px;font-weight:500;transition:background 0.15s;}
.btn-primary:hover{background:var(--accent-dark);border-color:var(--accent-dark);}
.btn-secondary{padding:13px 24px;border-radius:3px;border:1px solid var(--ink);background:transparent;color:var(--ink);font-size:15px;font-weight:500;}
.btn-secondary:hover{background:var(--paper-panel);}
.btn-ghost{padding:8px 14px;border-radius:3px;border:1px solid var(--rule-strong);background:var(--paper-raised);color:var(--ink);font-size:13px;font-weight:500;transition:all 0.15s;}
.btn-ghost:hover{border-color:var(--ink-soft);background:var(--paper-panel);}
.btn-ghost.on{background:var(--accent);color:#fff;border-color:var(--accent);}
.doc-card{background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:30px 32px;position:relative;overflow:hidden;box-shadow:0 18px 40px -28px rgba(31,35,64,0.35);}
.doc-card::before{content:"AGREEMENT — PREVIEW";position:absolute;top:14px;right:18px;font-family:var(--font-mono);font-size:10px;letter-spacing:0.08em;color:var(--ink-faint);}
.doc-line{font-family:var(--font-display);font-size:15.5px;line-height:1.7;color:var(--ink-soft);margin-bottom:12px;}
.doc-clause{position:relative;border-radius:2px;padding:1px 4px;margin:0 -4px;transition:background 0.5s, color 0.5s;}
.doc-clause.tagged-high{background:var(--risk-high-bg);color:var(--risk-high);}
.doc-clause.tagged-med{background:var(--risk-med-bg);color:var(--risk-med);}
.doc-clause.tagged-low{background:var(--risk-low-bg);color:var(--risk-low);}
.scanline{position:absolute;left:0;right:0;height:38px;background:linear-gradient(180deg, rgba(110,44,60,0) 0%, rgba(110,44,60,0.16) 50%, rgba(110,44,60,0) 100%);animation:sweep 3.6s ease-in-out infinite;pointer-events:none;}
@keyframes sweep{0%{top:0%;opacity:0;}8%{opacity:1;}92%{opacity:1;}100%{top:100%;opacity:0;}}
.float-card{position:absolute;bottom:-14px;right:-14px;width:240px;background:var(--paper);border:1px solid var(--rule-strong);border-radius:4px;padding:14px 16px;box-shadow:0 12px 28px -14px rgba(31,35,64,0.4);opacity:0;transform:translateY(10px);transition:all 0.5s;}
.float-card.show{opacity:1;transform:translateY(0);}
.float-card .tag{font-family:var(--font-mono);font-size:10.5px;letter-spacing:0.06em;font-weight:500;}
.float-card .tag.high{color:var(--risk-high);}
.float-card p.explain{font-size:12.5px;color:var(--ink-soft);margin-top:6px;line-height:1.45;}
.pipeline{display:flex;gap:0;overflow-x:auto;padding-bottom:8px;}
.pipe-step{flex:1;min-width:145px;padding:20px 18px 20px 0;position:relative;}
.pipe-step:not(:last-child)::after{content:"";position:absolute;top:22px;right:0;width:100%;height:1px;background:var(--rule-strong);}
.pipe-step:not(:last-child)::before{content:"→";position:absolute;top:12px;right:-4px;color:var(--rule-strong);font-size:14px;z-index:2;}
.pipe-num{font-family:var(--font-mono);font-size:12px;color:var(--accent);margin-bottom:10px;}
.pipe-title{font-size:15px;font-weight:600;color:var(--ink);}
.pipe-sub{font-size:12.5px;color:var(--ink-soft);margin-top:4px;}
.pipe-step.is-active .pipe-num{color:var(--risk-low);}
.lang-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:28px;}
.lang-chip{padding:8px 16px;border-radius:20px;border:1px solid var(--rule-strong);background:var(--paper-raised);font-size:13.5px;font-weight:500;color:var(--ink-soft);}
.lang-chip.active{background:var(--ink);color:var(--paper);border-color:var(--ink);}
.ml-demo{display:grid;grid-template-columns:1fr auto 1fr;gap:24px;align-items:center;}
.ml-panel{background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:22px 24px;min-height:120px;}
.ml-panel .cap{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;}
.ml-panel .txt{font-family:var(--font-display);font-size:16px;line-height:1.6;}
.ml-arrow{font-size:20px;color:var(--ink-faint);text-align:center;}
.ml-tag{display:inline-block;margin-top:14px;font-family:var(--font-mono);font-size:11px;padding:3px 8px;border-radius:2px;}
.clause-demo-wrap{display:grid;grid-template-columns:1.1fr 0.9fr;gap:32px;}
.mini-doc{background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:26px 28px;}
.mini-clause{font-family:var(--font-display);font-size:14.5px;line-height:1.75;padding:4px 8px;margin:0 -8px 6px;border-radius:2px;cursor:pointer;transition:filter 0.15s;}
.mini-clause:hover{filter:brightness(0.97);}
.mini-clause.high{background:var(--risk-high-bg);color:var(--risk-high);}
.mini-clause.med{background:var(--risk-med-bg);color:var(--risk-med);}
.mini-clause.low{background:var(--risk-low-bg);color:var(--risk-low);}
.mini-clause.selected{outline:1.5px solid currentColor;}
.explain-panel{background:var(--ink);color:var(--paper);border-radius:4px;padding:26px 26px;}
.explain-panel h4{color:var(--paper);font-size:19px;margin-bottom:4px;}
.explain-row{margin-top:16px;}
.explain-row .lbl{font-family:var(--font-mono);font-size:10.5px;letter-spacing:0.08em;text-transform:uppercase;color:#B8A8AE;margin-bottom:5px;}
.explain-row .val{font-size:14px;color:var(--paper);line-height:1.55;}
.explain-row .val.q{font-family:var(--font-display);font-style:italic;color:#D9CFC2;}
.conf-bar-track{background:rgba(255,255,255,0.12);height:5px;border-radius:3px;margin-top:6px;overflow:hidden;}
.conf-bar-fill{height:100%;background:#C7896D;}
.feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--rule);border:1px solid var(--rule);}
.feat-card{background:var(--paper-raised);padding:26px 24px;min-height:132px;}
.feat-card .fnum{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}
.feat-card h4{font-size:15.5px;margin-top:10px;}
.feat-card p{font-size:13px;color:var(--ink-soft);margin-top:8px;line-height:1.5;}
.footer-cta{text-align:center;padding:80px 0;}
.footer-cta h2{font-size:32px;max-width:560px;margin:0 auto;}
.site-footer{border-top:1px solid var(--rule);padding:26px 32px;display:flex;justify-content:space-between;font-size:12.5px;color:var(--ink-faint);flex-wrap:wrap;gap:12px;}
.analyze-wrap{max-width:720px;margin:50px auto;text-align:center;}
.dropzone{border:1.5px dashed var(--rule-strong);border-radius:6px;padding:50px 32px;background:var(--paper-raised);transition:border-color 0.15s,background 0.15s;margin-top:24px;cursor:pointer;}
.dropzone.drag{border-color:var(--accent);background:var(--accent-soft);}
.dz-title{font-size:16px;font-weight:500;margin-top:16px;}
.dz-sub{font-size:13px;color:var(--ink-soft);margin-top:6px;}
.dz-formats{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);margin-top:14px;}
.file-chosen{margin-top:20px;text-align:left;background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;}
.file-chosen .fname{font-weight:500;font-size:14.5px;}
.file-chosen .fmeta{font-family:var(--font-mono);font-size:11.5px;color:var(--ink-soft);margin-top:3px;}
.analyze-opts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:22px;text-align:left;}
.opt-field label{font-family:var(--font-mono);font-size:11px;letter-spacing:0.05em;text-transform:uppercase;color:var(--ink-soft);}
.opt-field select{width:100%;margin-top:6px;padding:10px 12px;border-radius:3px;border:1px solid var(--rule-strong);background:var(--paper-raised);font-size:14px;color:var(--ink);}
.secure-note{margin-top:20px;font-size:12.5px;color:var(--ink-faint);}
.analyze-btn-row{margin-top:24px;display:flex;justify-content:center;gap:12px;align-items:center;}
.error-banner{background:#F8D7DA;border:1px solid #F5C6CB;color:#721C24;border-radius:4px;padding:12px 18px;margin-top:20px;font-size:13.5px;text-align:left;}
.quick-samples{margin-top:32px;padding:18px 20px;background:var(--paper-panel);border-radius:4px;text-align:left;}
.quick-samples .qs-title{font-family:var(--font-mono);font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:10px;}
.quick-samples-btns{display:flex;gap:8px;flex-wrap:wrap;}
.processing-wrap{max-width:580px;margin:60px auto;}
.proc-doc{background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:22px 24px;position:relative;overflow:hidden;margin-bottom:8px;}
.proc-msg{text-align:center;font-family:var(--font-mono);font-size:13px;color:var(--ink-soft);height:20px;margin:18px 0 10px;}
.proc-bar{width:100%;height:6px;background:var(--rule);border-radius:3px;overflow:hidden;margin-bottom:20px;}
.proc-bar-fill{height:100%;background:var(--accent);transition:width 0.4s ease;}
.proc-steps{display:flex;flex-direction:column;gap:0;}
.proc-step{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--rule);font-size:14px;color:var(--ink-faint);}
.proc-step:last-child{border-bottom:none;}
.proc-step .mark{width:16px;height:16px;border-radius:50%;border:1.5px solid var(--rule-strong);flex-shrink:0;position:relative;}
.proc-step.done{color:var(--ink);}
.proc-step.done .mark{background:var(--risk-low);border-color:var(--risk-low);}
.proc-step.done .mark::after{content:"";position:absolute;left:4px;top:1px;width:4px;height:8px;border:solid #fff;border-width:0 1.5px 1.5px 0;transform:rotate(45deg);}
.proc-step.active{color:var(--ink);font-weight:500;}
.proc-step.active .mark{border-color:var(--accent);}
.proc-step.active .mark::after{content:"";position:absolute;inset:3px;border-radius:50%;background:var(--accent);animation:pulse 1s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:0.4;}50%{opacity:1;}}
.dash-top{display:flex;justify-content:space-between;align-items:flex-start;padding-top:40px;flex-wrap:wrap;gap:20px;}
.dash-id .dsub{font-size:13px;color:var(--ink-soft);margin-top:4px;}
.dash-id h2{font-size:26px;}
.score-card{display:flex;align-items:center;gap:18px;background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:16px 24px;}
.score-num{font-family:var(--font-mono);font-size:34px;font-weight:500;}
.score-num.high{color:var(--risk-high);}
.score-num.med{color:var(--risk-med);}
.score-num.low{color:var(--risk-low);}
.score-lbl{font-family:var(--font-mono);font-size:11px;letter-spacing:0.06em;color:var(--ink-soft);}
.stat-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);border:1px solid var(--rule);margin-top:28px;}
.stat-card{background:var(--paper-raised);padding:18px 20px;}
.stat-num{font-family:var(--font-mono);font-size:26px;font-weight:500;}
.stat-num.high{color:var(--risk-high);}
.stat-num.med{color:var(--risk-med);}
.stat-num.low{color:var(--risk-low);}
.stat-lbl{font-size:12px;color:var(--ink-soft);margin-top:4px;}
.dash-lang-bar{display:flex;align-items:center;justify-content:space-between;background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:6px;padding:16px 24px;margin-top:22px;flex-wrap:wrap;gap:16px;box-shadow:0 4px 12px -4px rgba(31,35,64,0.08);}
.dl-left{display:flex;align-items:center;gap:14px;}
.dl-icon{font-size:24px;line-height:1;}
.dl-text-title{font-family:var(--font-mono);font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:var(--accent);font-weight:600;}
.dl-text-sub{font-size:13.5px;color:var(--ink);font-weight:500;margin-top:2px;}
.dl-buttons{display:flex;gap:8px;flex-wrap:wrap;align-items:center;}
.dl-pill{font-family:var(--font-body);font-size:13px;font-weight:500;padding:8px 16px;border-radius:20px;border:1px solid var(--rule-strong);background:var(--paper);color:var(--ink);transition:all 0.15s;cursor:pointer;}
.dl-pill:hover{border-color:var(--ink);background:var(--paper-panel);}
.dl-pill.active{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;box-shadow:0 3px 8px rgba(110,44,60,0.3);}
.dl-spinner{font-family:var(--font-mono);font-size:11.5px;color:var(--accent);margin-left:6px;animation:pulse 1s infinite;}
.dash-actions-toolbar{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap;align-items:center;}
.btn-export-primary{padding:11px 22px;border-radius:4px;border:1px solid var(--accent);background:var(--accent);font-size:14px;font-weight:600;color:#fff;display:inline-flex;align-items:center;gap:8px;transition:all 0.15s;cursor:pointer;}
.btn-export-primary:hover{background:var(--accent-dark);border-color:var(--accent-dark);}
.btn-export{padding:10px 18px;border-radius:4px;border:1px solid var(--rule-strong);background:var(--paper-raised);font-size:13.5px;font-weight:500;color:var(--ink);display:inline-flex;align-items:center;gap:8px;transition:all 0.15s;cursor:pointer;}
.btn-export:hover{border-color:var(--ink);background:var(--paper-panel);}
.summary-box{margin-top:24px;background:var(--accent-soft);border-left:3px solid var(--accent);border-radius:0 4px 4px 0;padding:18px 22px;}
.summary-box p{font-size:14.5px;color:var(--accent-dark);line-height:1.6;}
.dash-body{display:grid;grid-template-columns:300px 1.2fr 1.3fr;gap:0;margin-top:28px;border:1px solid var(--rule);border-radius:4px;overflow:hidden;background:var(--paper-raised);}
.dash-col{border-right:1px solid var(--rule);}
.dash-col:last-child{border-right:none;}
.col-head{padding:16px 18px;border-bottom:1px solid var(--rule);background:var(--paper-panel);display:flex;justify-content:space-between;align-items:center;}
.col-head h4{font-size:13px;font-family:var(--font-mono);letter-spacing:0.04em;text-transform:uppercase;color:var(--ink-soft);margin:0;}
.filter-row{display:flex;gap:6px;padding:12px 18px;border-bottom:1px solid var(--rule);flex-wrap:wrap;}
.map-list{max-height:560px;overflow-y:auto;}
.map-item{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;border-bottom:1px solid var(--rule);cursor:pointer;font-size:13.5px;}
.map-item:hover{background:var(--paper-panel);}
.map-item.selected{background:var(--accent-soft);}
.map-item .mi-num{font-family:var(--font-mono);color:var(--ink-faint);margin-right:8px;}
.risk-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0;display:inline-block;}
.risk-dot.high{background:var(--risk-high);}
.risk-dot.med{background:var(--risk-med);}
.risk-dot.low{background:var(--risk-low);}
.viewer{max-height:560px;overflow-y:auto;padding:20px 22px;}
.v-clause{font-family:var(--font-display);font-size:14px;line-height:1.75;padding:6px 10px;margin:0 -8px 8px;border-radius:3px;cursor:pointer;transition:filter 0.15s;}
.v-clause.high{background:var(--risk-high-bg);color:var(--risk-high);}
.v-clause.med{background:var(--risk-med-bg);color:var(--risk-med);}
.v-clause.low{background:var(--risk-low-bg);color:var(--risk-low);}
.v-clause.selected{outline:2px solid currentColor;}
.v-clause.dim{opacity:0.25;}
.detail-pane{max-height:560px;overflow-y:auto;padding:20px 22px;}
.detail-empty{color:var(--ink-faint);font-size:13.5px;padding:20px 0;text-align:center;}
.detail-risk-badge{display:inline-block;font-family:var(--font-mono);font-size:11px;letter-spacing:0.05em;padding:4px 10px;border-radius:2px;margin-bottom:12px;}
.detail-risk-badge.high{background:var(--risk-high-bg);color:var(--risk-high);}
.detail-risk-badge.med{background:var(--risk-med-bg);color:var(--risk-med);}
.detail-risk-badge.low{background:var(--risk-low-bg);color:var(--risk-low);}
.detail-type{font-size:17px;margin-bottom:2px;font-family:var(--font-display);font-weight:560;}
.d-row{margin-top:14px;}
.d-row .lbl{font-family:var(--font-mono);font-size:10px;letter-spacing:0.07em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:4px;}
.d-row .val{font-size:13.5px;color:var(--ink);line-height:1.55;}
.d-row .val.orig{font-family:var(--font-display);font-style:italic;color:var(--ink-soft);}
.evidence-tag{display:inline-block;background:var(--paper-panel);border:1px solid var(--rule);padding:2px 8px;border-radius:2px;font-size:12px;margin:3px 3px 0 0;}
.conf-track{background:var(--rule);height:5px;border-radius:3px;margin-top:5px;overflow:hidden;}
.conf-fill{height:100%;background:var(--accent);}
.reason-toggle{margin-top:16px;font-size:12.5px;color:var(--accent);border:none;background:none;padding:0;font-weight:500;}
.reason-flow{margin-top:14px;background:var(--paper-panel);border-radius:4px;padding:14px 16px;}
.rf-step{font-size:12px;padding:6px 0;border-bottom:1px dashed var(--rule-strong);color:var(--ink-soft);}
.rf-step:last-child{border-bottom:none;}
.rf-step b{color:var(--ink);}
.llm-card{margin-top:16px;background:var(--ink);color:var(--paper);border-radius:4px;padding:16px 18px;}
.llm-card h5{font-family:var(--font-mono);font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:#C7896D;margin:0 0 8px;}
.llm-card p{font-size:13px;line-height:1.55;color:#E4DCC8;white-space:pre-wrap;}
.lang-switch-row{display:flex;gap:4px;margin-top:14px;flex-wrap:wrap;}
.lang-switch-row button{font-size:11px;padding:5px 9px;}
.report-doc{max-width:760px;margin:44px auto 80px;background:var(--paper-raised);border:1px solid var(--rule-strong);border-radius:4px;padding:48px 52px;}
.rmasthead{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid var(--ink);padding-bottom:20px;}
.rmasthead h2{font-size:24px;}
.rmasthead .stamp{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);text-align:right;}
.rsection{margin-top:30px;}
.rsection h3{font-size:15px;font-family:var(--font-mono);text-transform:uppercase;letter-spacing:0.05em;color:var(--accent);border-bottom:1px solid var(--rule);padding-bottom:8px;margin-bottom:14px;}
.rsection p{font-size:14px;line-height:1.7;color:var(--ink-soft);}
.rlist{display:flex;flex-direction:column;gap:8px;}
.rlist-item{display:flex;justify-content:space-between;font-size:13.5px;padding:8px 12px;border-radius:3px;background:var(--paper-panel);}
.rlist-item .rl-tag{font-family:var(--font-mono);font-size:11px;}
.rstat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.rstat-grid .rs{text-align:center;}
.rstat-grid .rsnum{font-family:var(--font-mono);font-size:22px;font-weight:500;}
.rstat-grid .rslbl{font-size:11.5px;color:var(--ink-soft);margin-top:2px;}
.report-actions{display:flex;gap:12px;justify-content:center;margin-top:36px;flex-wrap:wrap;}
.disclaimer{margin-top:34px;padding-top:18px;border-top:1px solid var(--rule);font-size:11.5px;color:var(--ink-faint);text-align:center;font-style:italic;}
.mc-toolbar{display:flex;gap:12px;padding:36px 0 20px;flex-wrap:wrap;align-items:center;}
.mc-toolbar input[type=text]{flex:1;min-width:200px;padding:10px 14px;border-radius:3px;border:1px solid var(--rule-strong);background:var(--paper-raised);font-size:14px;}
.mc-toolbar select{padding:10px 12px;border-radius:3px;border:1px solid var(--rule-strong);background:var(--paper-raised);font-size:13.5px;}
table.mc-table{width:100%;border-collapse:collapse;margin-bottom:60px;}
table.mc-table th{text-align:left;font-family:var(--font-mono);font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:var(--ink-soft);padding:10px 14px;border-bottom:1px solid var(--rule-strong);}
table.mc-table td{padding:14px 14px;border-bottom:1px solid var(--rule);font-size:13.5px;}
table.mc-table tr:hover td{background:var(--paper-raised);}
.mc-risk-pill{font-family:var(--font-mono);font-size:11px;padding:3px 9px;border-radius:10px;}
.mc-actions button{margin-right:6px;font-size:12px;padding:6px 10px;}
.modal-backdrop{position:fixed;inset:0;background:rgba(31,35,64,0.6);backdrop-filter:blur(4px);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px;}
.modal-box{background:var(--paper);border:1px solid var(--rule-strong);border-radius:6px;max-width:540px;width:100%;padding:32px;box-shadow:0 20px 50px -20px rgba(0,0,0,0.5);text-align:left;}
.modal-box h3{font-size:22px;margin-bottom:12px;}
.modal-box p{font-size:13.5px;color:var(--ink-soft);line-height:1.6;margin-bottom:16px;}
.modal-close-row{display:flex;justify-content:flex-end;margin-top:24px;}
@media (max-width:900px){
  .hero{grid-template-columns:1fr;} .feat-grid{grid-template-columns:repeat(2,1fr);}
  .dash-body{grid-template-columns:1fr;} .dash-col{border-right:none;border-bottom:1px solid var(--rule);}
  .clause-demo-wrap{grid-template-columns:1fr;} .ml-demo{grid-template-columns:1fr;}
  .rstat-grid{grid-template-columns:repeat(2,1fr);} .stat-row{grid-template-columns:repeat(2,1fr);}
  .analyze-opts{grid-template-columns:1fr;}
}
`;

function Logo({ onClick }) {
  return (
    <div className="logo" onClick={onClick}>
      <img src={LOGO_SRC} alt="Clausent logo" className="logo-mark" />
      <span className="logo-word">Clausent</span>
    </div>
  );
}

function ClauseDetail({ clause, _analysisId, dashLang, onSwitchLang, reasonOpen, setReasonOpen, onExplainRequested, isExplaining }) {
  if (!clause) return <div className="detail-empty">Select a clause to see its full risk analysis.</div>;

  const risk = clause.risk_level || clause.risk || "low";
  const category = clause.category_display || clause.category || clause.type || "General";
  const text = clause.original_text || clause.text || "";
  const explain = clause.slm_explanation || clause.explain || "";
  const why = clause.risk_rationale || clause.why || "";
  const action = clause.suggested_action || clause.action || "";
  const conf = Math.round(clause.confidence || clause.conf || 85);
  const evidence = clause.evidence || [];
  const questions = clause.suggested_questions || [];
  const modelName = clause.explanation_model || "SLM (Qwen2.5-3B)";
  const llmExplain = clause.llm_explanation;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexWrap: "wrap", gap: 6 }}>
        <span className={"detail-risk-badge " + riskClass(risk)}>{riskLabel(risk)}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {dashLang !== "English" && (
            <span className="mono" style={{ fontSize: 11, padding: "2px 8px", background: "var(--accent-soft)", borderRadius: 3, color: "var(--accent-dark)", fontWeight: 600 }}>
              🌐 {dashLang}
            </span>
          )}
          <span className="mono" style={{ fontSize: 11, color: "var(--ink-faint)" }}>{modelName}</span>
        </div>
      </div>

      <div className="detail-type">{category}</div>
      <div className="d-row">
        <div className="lbl">Original contract text</div>
        <div className="val orig">&quot;{text}&quot;</div>
      </div>

      {clause.english_text && clause.english_text !== text && (
        <div className="d-row">
          <div className="lbl">English Translation</div>
          <div className="val">&quot;{clause.english_text}&quot;</div>
        </div>
      )}

      {clause.translated_text && clause.translated_text !== text && dashLang !== "English" && (
        <div className="d-row">
          <div className="lbl">{dashLang} Translation</div>
          <div className="val" style={{ color: "var(--ink-rich)", fontStyle: "italic" }}>&quot;{clause.translated_text}&quot;</div>
        </div>
      )}

      <div className="d-row">
        <div className="lbl">
          {dashLang !== "English" ? `Simplified explanation (${dashLang})` : "Simplified explanation (SLM)"}
        </div>
        <div className="val" style={{ fontWeight: 500, color: "var(--ink)" }}>{explain}</div>
      </div>

      <div className="d-row">
        <div className="lbl">
          {dashLang !== "English" ? `Why it may be risky (${dashLang})` : "Why it may be risky"}
        </div>
        <div className="val">{why}</div>
      </div>

      {evidence.length > 0 && (
        <div className="d-row">
          <div className="lbl">Identified Evidence Spans</div>
          <div>
            {evidence.map((ev, i) => (
              <span key={i} className="evidence-tag">{ev}</span>
            ))}
          </div>
        </div>
      )}

      <div className="d-row">
        <div className="lbl">
          {dashLang !== "English" ? `Suggested action (${dashLang})` : "Suggested action"}
        </div>
        <div className="val">{action}</div>
      </div>

      {questions.length > 0 && (
        <div className="d-row">
          <div className="lbl">Points for Legal Review</div>
          <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: "13px", color: "var(--ink-soft)" }}>
            {questions.map((q, i) => (
              <li key={i} style={{ marginBottom: 4 }}>{q}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="d-row">
        <div className="lbl">Confidence score</div>
        <div className="conf-track"><div className="conf-fill" style={{ width: conf + "%" }} /></div>
        <div className="val mono" style={{ marginTop: 4, fontSize: 12 }}>{conf}%</div>
      </div>

      {/* On-demand LLM detailed counsel */}
      <div style={{ marginTop: 16 }}>
        <button
          className="btn-ghost"
          style={{ width: "100%", fontSize: 12, padding: "8px 12px" }}
          disabled={isExplaining}
          onClick={() => onExplainRequested(clause.id)}
        >
          {isExplaining ? "Invoking LLM for deep analysis..." : "Request In-Depth LLM Legal Analysis ⚡"}
        </button>
      </div>

      {llmExplain && (
        <div className="llm-card">
          <h5>
            {dashLang === "Hindi"
              ? "वृहद भाषा मॉडल (LLM) विस्तृत कानूनी परामर्श"
              : dashLang === "Malayalam"
              ? "ലാർജ് ലാംഗ്വേജ് മോഡൽ (LLM) വിശദമായ നിയമോപദേശം"
              : dashLang === "Telugu"
              ? "లార్జ్ లాంగ్వేజ్ మోడల్ (LLM) సమగ్ర చట్టపరమైన సలహా"
              : dashLang === "Tamil"
              ? "பெரிய மொழி மாதிரி (LLM) விரிவான சட்ட ஆலோசனை"
              : "Large Language Model (LLM) Detailed Counsel"}
          </h5>
          <p style={{ whiteSpace: "pre-line", lineHeight: 1.6, marginTop: 8 }}>{llmExplain}</p>
        </div>
      )}


      <button className="reason-toggle" onClick={() => setReasonOpen(!reasonOpen)}>
        {reasonOpen ? "Hide reasoning ↑" : "Show how this was decided →"}
      </button>

      {reasonOpen && (
        <div className="reason-flow">
          <div className="rf-step"><b>Original text</b> → clause extracted from document boundary</div>
          <div className="rf-step"><b>Clause identification</b> → Legal-BERT CUAD representation as {category}</div>
          <div className="rf-step"><b>Risk classification</b> → {riskLabel(risk)} ({conf}% confidence)</div>
          <div className="rf-step"><b>Why it was flagged</b> → {why}</div>
          <div className="rf-step"><b>Plain-language explanation</b> → {explain}</div>
          <div className="rf-step"><b>Suggested action</b> → {action}</div>
        </div>
      )}

      <div className="lang-switch-row" style={{ marginTop: 20 }}>
        <span style={{ fontSize: 11, color: "var(--ink-faint)", alignSelf: "center", marginRight: 4 }}>Language:</span>
        {LANGS.map((l) => (
          <button key={l} className={"btn-ghost" + (l === dashLang ? " on" : "")} onClick={() => onSwitchLang(l)}>
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ClausentApp() {
  const [view, setView] = useState("home");
  const go = (v) => { setView(v); window.scrollTo({ top: 0, behavior: "instant" }); };

  // Backend Health State
  const [backendStatus, setBackendStatus] = useState({ online: false, info: null });
  const [demoMode, setDemoMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    api.checkHealth().then((res) => {
      if (res && res.status === "online") {
        setBackendStatus({ online: true, info: res });
      } else {
        setBackendStatus({ online: false, info: null });
      }
    });
  }, []);

  // Hero animation
  const [heroTags, setHeroTags] = useState({ hc1: "", hc2: "", hc3: "", hc4: "" });
  const [showFloat, setShowFloat] = useState(false);
  useEffect(() => {
    const sequence = [
      ["hc1", "tagged-low"], ["hc2", "tagged-high"], ["hc3", "tagged-med"], ["hc4", "tagged-low"]
    ];
    let timeouts = [];
    function run() {
      setHeroTags({ hc1: "", hc2: "", hc3: "", hc4: "" });
      setShowFloat(false);
      sequence.forEach(([key, cls], i) => {
        timeouts.push(setTimeout(() => {
          setHeroTags((prev) => ({ ...prev, [key]: cls }));
          if (key === "hc2") setShowFloat(true);
        }, 600 + i * 750));
      });
    }
    run();
    const interval = setInterval(run, 7200);
    return () => { timeouts.forEach(clearTimeout); clearInterval(interval); };
  }, []);

  // Pipeline scroll highlight
  const pipeRefs = useRef([]);
  const [activePipe, setActivePipe] = useState({});
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const idx = Number(entry.target.dataset.idx);
          setActivePipe((prev) => ({ ...prev, [idx]: true }));
        }
      });
    }, { threshold: 0.6 });
    pipeRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, [view]);

  // Multilingual demo on home page
  const [currentLang, setCurrentLang] = useState("Tamil");

  // Clause demo teaser on home page
  const [selectedMini, setSelectedMini] = useState(4);
  const miniClause = CLAUSES.find((c) => c.id === selectedMini) || CLAUSES[0];

  // Upload & File State
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [docLang, setDocLang] = useState("Auto detect");
  const [explainLang, setExplainLang] = useState("English");
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);

  // Real Processing & Polling State
  const [processing, setProcessing] = useState(false);
  const [procStage, setProcStage] = useState("Document received");
  const [procPercent, setProcPercent] = useState(10);
  const [completedStages, setCompletedStages] = useState([]);
  const [_activeDocId, setActiveDocId] = useState(null);

  // Real Active Analysis Result
  const [analysisResult, setAnalysisResult] = useState({
    analysis_id: "demo-live",
    document_id: "demo-doc",
    filename: "Vendor_Services_Agreement.pdf",
    detected_language: "English",
    target_language: "English",
    overall_risk_score: 72,
    overall_risk_level: "high",
    high_risk_count: 3,
    medium_risk_count: 4,
    low_risk_count: 5,
    total_clauses: 12,
    executive_summary: "This contract contains several clauses that may require attention before signing. The most significant concerns involve unlimited liability, automatic renewal, and a broadly worded indemnification obligation.",
    suggested_review_areas: "Before signing, consider negotiating a liability cap, clarifying renewal notice window, and narrowing indemnification scope.",
    clauses: CLAUSES
  });

  // Dashboard state
  const [dashFilter, setDashFilter] = useState("all");
  const [selectedClauseId, setSelectedClauseId] = useState(null);
  const [dashLang, setDashLang] = useState("English");
  const [reasonOpen, setReasonOpen] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [showTranslatedText, setShowTranslatedText] = useState(true);

  async function handleSwitchLanguage(newLang) {
    setDashLang(newLang);
    if (backendStatus.online && analysisResult.analysis_id && !analysisResult.analysis_id.startsWith("demo-")) {
      try {
        setIsTranslating(true);
        const res = await api.translateAnalysis(analysisResult.analysis_id, newLang);
        if (res && res.clauses) {
          setAnalysisResult(res);
        }
      } catch (err) {
        console.warn("Backend translation fallback:", err);
        applyLocalTranslation(newLang);
      } finally {
        setIsTranslating(false);
      }
    } else {
      applyLocalTranslation(newLang);
    }
  }

  function applyLocalTranslation(newLang) {
    const dict = CLIENT_TRANSLATIONS[newLang];
    if (!dict) {
      if (newLang === "English") {
        setAnalysisResult((prev) => ({
          ...prev,
          target_language: "English",
          clauses: (prev.clauses || CLAUSES).map((c) => ({
            ...c,
            category_display: c.category || c.type,
            slm_explanation: c.english_text ? c.slm_explanation : c.slm_explanation,
          }))
        }));
      }
      return;
    }

    setAnalysisResult((prev) => ({
      ...prev,
      target_language: newLang,
      executive_summary: dict.summary || prev.executive_summary,
      suggested_review_areas: dict.review || prev.suggested_review_areas,
      clauses: (prev.clauses || CLAUSES).map((c) => {
        const cKey = c.clause_number || c.id;
        const ct = dict.clauses && (dict.clauses[cKey] || dict.clauses[c.id]);
        const catT = dict.categories && dict.categories[c.category || c.type];
        const categoryName = catT || c.category_display || c.category || c.type || "General";
        const snippet = (c.translated_text || c.original_text || c.text || "").slice(0, 180);

        let localizedCounsel = c.llm_explanation;
        if (c.llm_explanation) {
          if (newLang === "Hindi") {
            localizedCounsel = `${categoryName} के लिए विस्तृत कानूनी विश्लेषण (उच्च जोखिम):\n\n1. अनुबंध संबंधी दायित्व: यह खंड निर्दिष्ट करता है: "${snippet}..."\n\n2. जोखिम मूल्यांकन का आधार: ${(ct && ct.why) || c.risk_rationale || c.why || "व्यापक एकतरफा प्रावधान बिना किसी संतुलन के अनुबंधकर्ता पर भारी कानूनी बोझ डालते हैं।"}\n\n3. व्यावहारिक परिणाम: बिना संशोधन के इस प्रावधान पर हस्ताक्षर करने से आपके व्यवसाय को असीमित देनदारियों या विवाद की स्थिति में प्रक्रियात्मक नुकसान का सामना करना पड़ सकता है।\n\n4. कानूनी समीक्षा के लिए सुझाव: अपने कानूनी सलाहकार से परामर्श करें कि क्या इस खंड में उचित वित्तीय सीमा (Liability Cap) तय की जा सकती है और क्या दोनों पक्षों के बीच पारस्परिक सुरक्षा जोड़ी जा सकती है।`;
          } else if (newLang === "Malayalam") {
            localizedCounsel = `${categoryName} സംബന്ധിച്ച സമഗ്ര നിയമ വിശകലനം (ഉയർന്ന അപകടസാധ്യത):\n\n1. കരാർ ബാധ്യത: വ്യവസ്ഥ വ്യക്തമാക്കുന്നത്: "${snippet}..."\n\n2. അപകടസാധ്യതയുടെ കാരണം: ${(ct && ct.why) || c.risk_rationale || c.why || "ഏകപക്ഷീയമായ വ്യവസ്ഥകൾ കരാറുകാരന് വലിയ സാമ്പത്തിക നഷ്ടസാധ്യത ഉണ്ടാക്കുന്നു."}\n\n3. പ്രായോഗിക പ്രത്യാഘാതങ്ങൾ: നിലവിലെ രൂപത്തിൽ ഒപ്പുവെക്കുന്നത് നിങ്ങളുടെ സ്ഥാപനത്തിന് അപ്രതീക്ഷിത ബാധ്യതകളും തർക്കപരിഹാര വേളകളിൽ വലിയ നഷ്ടങ്ങളും വരുത്തിവച്ചേക്കാം.\n\n4. നിയമപരമായ അവലോകനത്തിനുള്ള നിർദ്ദേശങ്ങൾ: ബാധ്യതാ പരിധി നിശ്ചയിക്കാനും ഇരു കക്ഷികൾക്കും തുല്യ പരിരക്ഷ ഉറപ്പാക്കാനും കഴിയുമോ എന്ന് അഭിഭാഷകനോട് ചോദിക്കുക.`;
          } else if (newLang === "Telugu") {
            localizedCounsel = `${categoryName} కోసం సమగ్ర చట్టపరమైన విశ్లేషణ (అధిక ప్రమాదం):\n\n1. ఒప్పంద బాధ్యత: ఈ నిబంధన నిర్దేశిస్తుంది: "${snippet}..."\n\n2. ప్రమాద అంచనా హేతువు: ${(ct && ct.why) || c.risk_rationale || c.why || "ఏకపక్ష నిబంధనలు కాంట్రాక్టర్‌పై అసమాన చట్టపరమైన భారాన్ని మోపుతాయి."}\n\n3. ఆచరణాత్మక పరిణామాలు: సవరణలు లేకుండా సంతకం చేయడం వల్ల ఊహించని ఆర్థిక భారాలు లేదా వివాద పరిష్కార సమయంలో గణనీయమైన నష్టాలు ఎదురవుతాయి.\n\n4. చట్టపరమైన సమీక్ష కోసం సూచనలు: ఆర్థిక పరిమితిని (Liability Cap) చేర్చి ఇరు పక్షాలకు పరస్పర రక్షణ కల్పించేలా సవరించవచ్చో లేదో న్యాయ సలహాదారునితో చర్చించండి.`;
          } else if (newLang === "Tamil") {
            localizedCounsel = `${categoryName} குறித்த விரிவான சட்ட பகுப்பாய்வு (உயர் அபாயம்):\n\n1. ஒப்பந்தக் கடமை: இந்த விதிமுறை குறிப்பிடுவது: "${snippet}..."\n\n2. இடர் மதிப்பீட்டு அடிப்படை: ${(ct && ct.why) || c.risk_rationale || c.why || "ஒருதலைப்பட்சமான உத்தரவாதங்கள் ஒப்பந்ததாரருக்கு அதிக சட்டரீதியான சுமையை ஏற்படுத்துகின்றன."}\n\n3. நடைமுறை விளைவுகள்: தற்போதைய வடிவத்தில் கையொப்பமிடுவது உங்கள் நிறுவனத்திற்கு எதிர்பாராத நிதி இழப்புகள் அல்லது தகராறு தீர்வின் போது கடுமையான பாதிப்புகளை ஏற்படுத்தக்கூடும்.\n\n4. சட்ட மறுஆய்வுக்கான பரிந்துரைகள்: பொறுப்பு உச்சவரம்பு (Liability Cap) நிர்ணயித்து பரஸ்பர சமநிலையை ஏற்படுத்த முடியுமா என்று வழக்கறிஞரிடம் ஆலோசிக்கவும்.`;
          }
        }

        return {
          ...c,
          category_display: catT || c.category_display || c.category || c.type,
          slm_explanation: (ct && ct.explain) || c.slm_explanation || c.explain,
          explain: (ct && ct.explain) || c.explain,
          risk_rationale: (ct && ct.why) || c.risk_rationale || c.why,
          why: (ct && ct.why) || c.why,
          suggested_action: (ct && ct.action) || c.suggested_action || c.action,
          action: (ct && ct.action) || c.action,
          llm_explanation: localizedCounsel
        };
      })

    }));
  }

  const activeClauses = analysisResult.clauses || CLAUSES;
  const selectedClause = activeClauses.find((c) => c.id === selectedClauseId) || activeClauses[0] || null;

  function selectClause(id) {
    setSelectedClauseId(id);
    setReasonOpen(false);
    const el = document.getElementById("vclause-" + id);
    if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  const highCount = activeClauses.filter((c) => (c.risk_level || c.risk) === "high").length;
  const medCount = activeClauses.filter((c) => (c.risk_level || c.risk) === "medium").length;
  const lowCount = activeClauses.filter((c) => (c.risk_level || c.risk) === "low").length;

  // File selection handler with real validation
  function handleFiles(files) {
    if (!files || !files.length) return;
    const f = files[0];
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx", "txt"].includes(ext)) {
      setUploadError(`Unsupported format '.${ext}'. Please upload a PDF, DOCX, or TXT document.`);
      return;
    }
    if (f.size > 25 * 1024 * 1024) {
      setUploadError("File exceeds 25 MB limit. Please upload a smaller document.");
      return;
    }
    setUploadError(null);
    setSelectedFile(f);
  }

  // Real backend analysis pipeline triggering and status polling
  async function startAnalysisWorkflow() {
    if (!selectedFile) return;

    setProcessing(true);
    setProcStage("Uploading document...");
    setProcPercent(10);
    setCompletedStages([]);
    setUploadError(null);

    // If backend is offline or Demo Mode is toggled, run graceful local demonstration
    if (!backendStatus.online || demoMode) {
      runDemoSimulation();
      return;
    }

    try {
      // 1. Upload to backend
      const uploadResp = await api.uploadDocument(selectedFile);
      const docId = uploadResp.document_id;
      setActiveDocId(docId);

      // 2. Start analysis
      await api.startAnalysis(docId, explainLang, docLang);

      // 3. Poll real progress
      const pollInterval = setInterval(async () => {
        try {
          const statusResp = await api.getAnalysisStatus(docId);
          setProcStage(statusResp.current_stage || "Processing contract...");
          setProcPercent(statusResp.progress_percent || 40);
          setCompletedStages(statusResp.completed_stages || []);

          if (statusResp.status === "completed") {
            clearInterval(pollInterval);
            // Fetch complete results
            const results = await api.getAnalysisResults(docId);
            setAnalysisResult(results);
            setSelectedClauseId(results.clauses && results.clauses.length ? results.clauses[0].id : null);
            setProcessing(false);
            go("dashboard");
            loadMyContracts();
            if (explainLang && explainLang !== "English") {
              handleSwitchLanguage(explainLang);
            }
          } else if (statusResp.status === "failed") {
            clearInterval(pollInterval);
            setProcessing(false);
            setUploadError(statusResp.error_message || "Analysis failed. Please try a different document.");
          }
        } catch (pollErr) {
          console.warn("Polling status error:", pollErr);
        }
      }, 750);

    } catch (err) {
      setProcessing(false);
      setUploadError(err.message || "Failed to initiate analysis pipeline.");
    }
  }

  function runDemoSimulation() {
    let step = 0;
    const interval = setInterval(() => {
      if (step < PROC_STEPS.length) {
        setProcStage(PROC_MESSAGES[step]);
        setProcPercent(Math.round(((step + 1) / PROC_STEPS.length) * 100));
        setCompletedStages((prev) => [...prev, PROC_STEPS[step]]);
        step++;
      } else {
        clearInterval(interval);
        setTimeout(() => {
          setProcessing(false);
          setAnalysisResult({
            analysis_id: "demo-" + Date.now(),
            document_id: "demo-doc",
            filename: selectedFile ? selectedFile.name : "Vendor_Services_Agreement.pdf",
            detected_language: docLang === "Auto detect" ? "English" : docLang,
            target_language: explainLang,
            overall_risk_score: 72,
            overall_risk_level: "high",
            high_risk_count: 3,
            medium_risk_count: 4,
            low_risk_count: 5,
            total_clauses: 12,
            executive_summary: "Demonstration analysis completed. Several clauses require negotiation, specifically regarding unlimited financial liability, automatic renewal, and one-sided indemnification.",
            suggested_review_areas: "Negotiate liability caps and require 30-day non-renewal notice window.",
            clauses: CLAUSES
          });
          setSelectedClauseId(4);
          go("dashboard");
          if (explainLang && explainLang !== "English") {
            handleSwitchLanguage(explainLang);
          }
        }, 400);
      }
    }, 550);
  }

  // Request deep LLM analysis on-demand
  async function handleExplainRequested(clauseId) {
    if (!analysisResult.analysis_id || demoMode || !backendStatus.online) {
      const updatedClauses = activeClauses.map((c) => {
        if (c.id === clauseId) {
          const cat = c.category_display || c.category || c.type || "General";
          const snippet = (c.translated_text || c.original_text || c.text || "").slice(0, 180);
          let localizedCounsel = "";
          if (dashLang === "Hindi") {
            localizedCounsel = `${cat} के लिए विस्तृत कानूनी विश्लेषण (उच्च जोखिम):\n\n1. अनुबंध संबंधी दायित्व: यह खंड निर्दिष्ट करता है: "${snippet}..."\n\n2. जोखिम मूल्यांकन का आधार: ${c.risk_rationale || c.why || "व्यापक एकतरफा प्रावधान बिना किसी संतुलन के अनुबंधकर्ता पर भारी कानूनी बोझ डालते हैं।"}\n\n3. व्यावहारिक परिणाम: बिना संशोधन के इस प्रावधान पर हस्ताक्षर करने से आपके व्यवसाय को असीमित देनदारियों या विवाद की स्थिति में प्रक्रियात्मक नुकसान का सामना करना पड़ सकता है।\n\n4. कानूनी समीक्षा के लिए सुझाव: अपने कानूनी सलाहकार से परामर्श करें कि क्या इस खंड में उचित वित्तीय सीमा (Liability Cap) तय की जा सकती है और क्या दोनों पक्षों के बीच पारस्परिक सुरक्षा जोड़ी जा सकती है।`;
          } else if (dashLang === "Malayalam") {
            localizedCounsel = `${cat} സംബന്ധിച്ച സമഗ്ര നിയമ വിശകലനം (ഉയർന്ന അപകടസാധ്യത):\n\n1. കരാർ ബാധ്യത: വ്യവസ്ഥ വ്യക്തമാക്കുന്നത്: "${snippet}..."\n\n2. അപകടസാധ്യതയുടെ കാരണം: ${c.risk_rationale || c.why || "ഏകപക്ഷീയമായ വ്യവസ്ഥകൾ കരാറുകാരന് വലിയ സാമ്പത്തിക നഷ്ടസാധ്യത ഉണ്ടാക്കുന്നു."}\n\n3. പ്രായോഗിക പ്രത്യാഘാതങ്ങൾ: നിലവിലെ രൂപത്തിൽ ഒപ്പുവെക്കുന്നത് നിങ്ങളുടെ സ്ഥാപനത്തിന് അപ്രതീക്ഷിത ബാധ്യതകളും തർക്കപരിഹാര വേളകളിൽ വലിയ നഷ്ടങ്ങളും വരുത്തിവച്ചേക്കാം.\n\n4. നിയമപരമായ അവലോകനത്തിനുള്ള നിർദ്ദേശങ്ങൾ: ബാധ്യതാ പരിധി നിശ്ചയിക്കാനും ഇരു കക്ഷികൾക്കും തുല്യ പരിരക്ഷ ഉറപ്പാക്കാനും കഴിയുമോ എന്ന് അഭിഭാഷകനോട് ചോദിക്കുക.`;
          } else if (dashLang === "Telugu") {
            localizedCounsel = `${cat} కోసం సమగ్ర చట్టపరమైన విశ్లేషణ (అధిక ప్రమాదం):\n\n1. ఒప్పంద బాధ్యత: ఈ నిబంధన నిర్దేశిస్తుంది: "${snippet}..."\n\n2. ప్రమాద అంచనా హేతువు: ${c.risk_rationale || c.why || "ఏకపక్ష నిబంధనలు కాంట్రాక్టర్‌పై అసమాన చట్టపరమైన భారాన్ని మోపుతాయి."}\n\n3. ఆచరణాత్మక పరిణామాలు: సవరణలు లేకుండా సంతకం చేయడం వల్ల ఊహించని ఆర్థిక భారాలు లేదా వివాద పరిష్కార సమయంలో గణనీయమైన నష్టాలు ఎదురవుతాయి.\n\n4. చట్టపరమైన సమీక్ష కోసం సూచనలు: ఆర్థిక పరిమితిని (Liability Cap) చేర్చి ఇరు పక్షాలకు పరస్పర రక్షణ కల్పించేలా సవరించవచ్చో లేదో న్యాయ సలహాదారునితో చర్చించండి.`;
          } else if (dashLang === "Tamil") {
            localizedCounsel = `${cat} குறித்த விரிவான சட்ட பகுப்பாய்வு (உயர் அபாயம்):\n\n1. ஒப்பந்தக் கடமை: இந்த விதிமுறை குறிப்பிடுவது: "${snippet}..."\n\n2. இடர் மதிப்பீட்டு அடிப்படை: ${c.risk_rationale || c.why || "ஒருதலைப்பட்சமான உத்தரவாதங்கள் ஒப்பந்ததாரருக்கு அதிக சட்டரீதியான சுமையை ஏற்படுத்துகின்றன."}\n\n3. நடைமுறை விளைவுகள்: தற்போதைய வடிவத்தில் கையொப்பமிடுவது உங்கள் நிறுவனத்திற்கு எதிர்பாராத நிதி இழப்புகள் அல்லது தகராறு தீர்வின் போது கடுமையான பாதிப்புகளை ஏற்படுத்தக்கூடும்.\n\n4. சட்ட மறுஆய்வுக்கான பரிந்துரைகள்: பொறுப்பு உச்சவரம்பு (Liability Cap) நிர்ணயித்து பரஸ்பர சமநிலையை ஏற்படுத்த முடியுமா என்று வழக்கறிஞரிடம் ஆலோசிக்கவும்.`;
          } else {
            localizedCounsel = `Detailed Analysis for ${cat} (HIGH RISK):\n\n1. Contractual Obligation: The clause specifies: "${snippet}..."\n\n2. Risk Assessment Rationale: ${c.risk_rationale || c.why || "Provisions that fail to cap liability or restrict unilateral termination impose asymmetrical burdens."}\n\n3. Practical Consequences: Signing this provision in its current form may expose your organization to unforeseen liabilities or procedural disadvantages during dispute resolution.\n\n4. Suggested Points for Professional Review: Ask legal counsel to clarify whether this clause is standard in your commercial jurisdiction and whether reciprocal mutual protections can be inserted.`;
          }
          return {
            ...c,
            llm_explanation: localizedCounsel
          };
        }
        return c;
      });
      setAnalysisResult((prev) => ({ ...prev, clauses: updatedClauses }));
      return;
    }


    try {
      setIsExplaining(true);
      const res = await api.explainClause(analysisResult.analysis_id, clauseId, dashLang, true);
      const updatedClauses = activeClauses.map((c) => {
        if (c.id === clauseId) {
          return {
            ...c,
            slm_explanation: res.slm_explanation,
            llm_explanation: res.llm_explanation,
            explanation_model: res.model_used
          };
        }
        return c;
      });
      setAnalysisResult((prev) => ({ ...prev, clauses: updatedClauses }));
    } catch (err) {
      alert("Could not generate detailed explanation: " + err.message);
    } finally {
      setIsExplaining(false);
    }
  }

  // Load sample contract shortcut
  function loadSampleContract(lang = "English") {
    setSelectedFile({ name: `Sample_${lang}_Contract.pdf`, size: 245000 });
    setDocLang(lang);
    setExplainLang(lang);
    setUploadError(null);
  }

  // My Contracts History
  const [contractsList, setContractsList] = useState(SAMPLE_CONTRACTS);
  const [mcSearch, setMcSearch] = useState("");
  const [mcRiskFilter, setMcRiskFilter] = useState("all");
  const [mcLangFilter, setMcLangFilter] = useState("all");
  const [mcSort, setMcSort] = useState("date");

  const loadMyContracts = React.useCallback(async () => {
    if (backendStatus.online) {
      try {
        const liveDocs = await api.listDocuments();
        if (liveDocs && liveDocs.length) {
          setContractsList(liveDocs.map((d) => ({
            id: d.id,
            name: d.filename,
            date: d.upload_date,
            lang: d.language,
            risk: d.overall_risk,
            flagged: d.flagged_clauses,
            status: d.status,
            total_clauses: d.total_clauses
          })));
        } else {
          setContractsList(SAMPLE_CONTRACTS);
        }
      } catch {
        setContractsList(SAMPLE_CONTRACTS);
      }
    }
  }, [backendStatus.online]);

  useEffect(() => {
    loadMyContracts();
  }, [loadMyContracts, view]);


  async function handleDeleteContract(docId) {
    if (!window.confirm("Are you sure you want to delete this contract analysis?")) return;
    if (backendStatus.online && !docId.startsWith("demo-")) {
      try {
        await api.deleteDocument(docId);
        loadMyContracts();
      } catch (err) {
        alert("Failed to delete document: " + err.message);
      }
    } else {
      setContractsList((prev) => prev.filter((c) => c.id !== docId));
    }
  }

  async function handleOpenContract(docId) {
    if (backendStatus.online && !docId.startsWith("demo-")) {
      try {
        const res = await api.getAnalysisResults(docId);
        setAnalysisResult(res);
        setSelectedClauseId(res.clauses && res.clauses.length ? res.clauses[0].id : null);
        go("dashboard");
      } catch (err) {
        alert("Could not load analysis: " + err.message);
      }
    } else {
      go("dashboard");
    }
  }

  const contractRows = useMemo(() => {
    let rows = contractsList.filter((r) =>
      r.name.toLowerCase().includes(mcSearch.toLowerCase()) &&
      (mcRiskFilter === "all" || r.risk.toLowerCase() === mcRiskFilter.toLowerCase()) &&
      (mcLangFilter === "all" || r.lang.toLowerCase() === mcLangFilter.toLowerCase())
    );
    if (mcSort === "date") rows = [...rows].sort((a, b) => (b.date || "").localeCompare(a.date || ""));
    if (mcSort === "risk") {
      const order = { high: 0, medium: 1, low: 2, unprocessed: 3 };
      rows = [...rows].sort((a, b) => (order[a.risk.toLowerCase()] ?? 4) - (order[b.risk.toLowerCase()] ?? 4));
    }
    return rows;
  }, [contractsList, mcSearch, mcRiskFilter, mcLangFilter, mcSort]);

  const reportHigh = activeClauses.filter((c) => (c.risk_level || c.risk) === "high");
  const reportMed = activeClauses.filter((c) => (c.risk_level || c.risk) === "medium");

  return (
    <div className="clausent-root">
      <style>{"@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,450;9..144,560;9..144,650&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');" + CSS}</style>

      {/* Top Navigation */}
      <nav className="topnav">
        <Logo onClick={() => go("home")} />
        <div className="navlinks">
          {["home", "analyze", "dashboard", "report", "contracts"].map((v) => (
            <button key={v} className={"navlink" + (view === v ? " active" : "")} onClick={() => go(v)}>
              {v === "home" ? "Home" : v === "analyze" ? "Analyze" : v === "dashboard" ? "Dashboard" : v === "report" ? "Report" : "My contracts"}
            </button>
          ))}
        </div>

        <div className="nav-actions">
          {/* API Health indicator */}
          <div className="api-pill" title={backendStatus.online ? "Connected to FastAPI Backend API" : "Running offline / standalone demo mode"}>
            <span className={"api-dot " + (backendStatus.online ? "green" : "amber")} />
            <span>{backendStatus.online ? "AI Engine Active" : "Demo Mode"}</span>
          </div>

          <button className={"mode-toggle-btn" + (demoMode ? " active" : "")} onClick={() => setDemoMode(!demoMode)}>
            {demoMode ? "Demo Mode ON" : "Live API"}
          </button>

          <button className="btn-ghost" style={{ padding: "6px 10px" }} onClick={() => setSettingsOpen(true)} title="System Architecture & Settings">
            ⚙️ About
          </button>

          <button className="nav-cta" onClick={() => go("analyze")}>Analyze a contract</button>
        </div>
      </nav>

      {/* Main Content Areas */}
      <main>
        {/* 1. HOME / LANDING VIEW */}
        {view === "home" && (
          <section>
            <div className="hero">
              <div>
                <span className="eyebrow">AI-Powered Multilingual Contract Risk Analyzer</span>
                <h1>Understand the contract<br />before you sign it.</h1>
                <p className="hero-desc">
                  Clausent reads legal contracts clause by clause in English, Tamil, Hindi, Malayalam, and Telugu.
                  Powered by Legal-BERT, Small Language Models (SLM), and LLMs to identify hazardous terms, explain obligations plainly, and protect your interests.
                </p>
                <div className="hero-cta-row">
                  <button className="btn-primary" onClick={() => go("analyze")}>Analyze a contract</button>
                  <button className="btn-secondary" onClick={() => document.getElementById("how-it-works").scrollIntoView({ behavior: "smooth" })}>
                    See how it works
                  </button>
                </div>
              </div>

              <div className="doc-card">
                <div className="scanline" />
                <div className="doc-line">1. <span className={"doc-clause " + heroTags.hc1}>Payment shall be remitted within thirty days of invoice date.</span></div>
                <div className="doc-line">2. <span className={"doc-clause " + heroTags.hc2}>Either party shall be fully liable for any and all direct, indirect, or consequential damages arising from this Agreement, without limitation.</span></div>
                <div className="doc-line">3. <span className={"doc-clause " + heroTags.hc3}>This Agreement renews automatically for successive one year terms unless notice is given ninety days prior.</span></div>
                <div className="doc-line">4. <span className={"doc-clause " + heroTags.hc4}>Each party shall protect the other's confidential information using reasonable care.</span></div>
                <div className={"float-card" + (showFloat ? " show" : "")}>
                  <span className="tag high">UNLIMITED LIABILITY — HIGH RISK</span>
                  <p className="explain">This clause removes any cap on damages. A single dispute could expose you to costs far beyond the contract's total value.</p>
                </div>
              </div>
            </div>

            <section className="block" id="how-it-works">
              <div className="section-head">
                <span className="eyebrow">How it works</span>
                <h2>Eight stages, one clause at a time.</h2>
                <p>Clausent doesn't just summarize a document — it decomposes contracts into individual legal provisions, runs Legal-BERT representations, applies rigorous risk heuristics, and generates plain-language explanations.</p>
              </div>
              <div className="pipeline">
                {PIPELINE.map(([num, title, sub], i) => (
                  <div key={num} ref={(el) => (pipeRefs.current[i] = el)} data-idx={i} className={"pipe-step" + (activePipe[i] ? " is-active" : "")}>
                    <div className="pipe-num">{num}</div>
                    <div className="pipe-title">{title}</div>
                    <div className="pipe-sub">{sub}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="block">
              <div className="section-head">
                <span className="eyebrow">Multilingual analysis</span>
                <h2>Read in one language. Understood in yours.</h2>
                <p>Contracts written in regional Indic languages undergo identical risk assessment as English agreements — with explanations translated back into the language you speak.</p>
              </div>
              <div className="lang-row">
                {LANGS.map((l) => (
                  <button key={l} className={"lang-chip" + (l === currentLang ? " active" : "")} onClick={() => setCurrentLang(l)}>{l}</button>
                ))}
              </div>
              <div className="ml-demo">
                <div className="ml-panel"><div className="cap">Original clause (English / Normalized)</div><div className="txt">{ORIGINAL_EN}</div></div>
                <div className="ml-arrow">→</div>
                <div className="ml-panel">
                  <div className="cap">Explained in {currentLang}</div>
                  <div className="txt">{TRANSLATIONS[currentLang]}</div>
                  <span className="ml-tag detail-risk-badge high">HIGH RISK — preserved across languages</span>
                </div>
              </div>
            </section>

            <section className="block">
              <div className="section-head">
                <span className="eyebrow">Clause-level detail</span>
                <h2>Click any clause. See exactly why it's flagged.</h2>
                <p>Every clause gets an independent risk level, a plain explanation, and actionable questions for legal review.</p>
              </div>
              <div className="clause-demo-wrap">
                <div className="mini-doc">
                  {CLAUSES.slice(0, 7).map((c) => (
                    <div key={c.id} className={"mini-clause " + riskClass(c.risk) + (c.id === selectedMini ? " selected" : "")} onClick={() => setSelectedMini(c.id)}>
                      {c.type} — {c.text}
                    </div>
                  ))}
                </div>
                <div className="explain-panel">
                  <span className="risk-badge detail-risk-badge" style={{ background: "transparent", border: "1px solid currentColor", color: "#fff" }}>{riskLabel(miniClause.risk)}</span>
                  <h4>{miniClause.type}</h4>
                  <div className="explain-row"><div className="lbl">Original clause</div><div className="val q">&quot;{miniClause.text}&quot;</div></div>
                  <div className="explain-row"><div className="lbl">Plain-language explanation (SLM)</div><div className="val">{miniClause.explain}</div></div>
                  <div className="explain-row"><div className="lbl">Why it may be risky</div><div className="val">{miniClause.why}</div></div>
                  <div className="explain-row"><div className="lbl">Suggested action</div><div className="val">{miniClause.action}</div></div>
                  <div className="explain-row">
                    <div className="lbl">Confidence score</div>
                    <div className="conf-bar-track"><div className="conf-bar-fill" style={{ width: miniClause.conf + "%" }} /></div>
                  </div>
                </div>
              </div>
            </section>

            <section className="block">
              <div className="section-head">
                <span className="eyebrow">What Clausent does</span>
                <h2>Built for the moment before you sign.</h2>
              </div>
              <div className="feat-grid">
                {[
                  ["01", "Multilingual understanding", "Analyzes contracts in English, Tamil, Hindi, Malayalam, and Telugu."],
                  ["02", "Automatic language detection", "Identifies source language automatically using Unicode script and n-gram analysis."],
                  ["03", "Contract translation", "Translates regional contracts for analysis while preserving original clause IDs."],
                  ["04", "Clause segmentation", "Separates dense contracts into structured, numbered provisions."],
                  ["05", "Legal-BERT classification", "Maps clauses to CUAD-aligned legal taxonomies."],
                  ["06", "Independent risk scoring", "Evaluates exposure and mutuality rather than equating category with risk."],
                  ["07", "SLM plain explanations", "Small language model generates concise, routine explanations without legal jargon."],
                  ["08", "LLM deep legal counsel", "Large language model analyzes complex, high-risk clauses with actionable questions."],
                  ["09", "PDF, JSON & CSV reports", "Export professional assessment reports with a single click."]
                ].map(([num, title, desc]) => (
                  <div className="feat-card" key={num}><div className="fnum">{num}</div><h4>{title}</h4><p>{desc}</p></div>
                ))}
              </div>
            </section>

            <section className="footer-cta">
              <h2>Read it once. Understand every clause.</h2>
              <div className="hero-cta-row" style={{ justifyContent: "center", marginTop: 24 }}>
                <button className="btn-primary" onClick={() => go("analyze")}>Analyze a contract now</button>
              </div>
            </section>

            <footer className="site-footer">
              <span>CLAUSENT — AI-Powered Multilingual Contract Risk Analyzer</span>
              <span>Informational & Educational only. Does not replace professional legal advice.</span>
            </footer>
          </section>
        )}

        {/* 2. ANALYZE / UPLOAD VIEW */}
        {view === "analyze" && !processing && (
          <div className="analyze-wrap">
            <span className="eyebrow">Analyze a contract</span>
            <h2 style={{ fontSize: 28, marginTop: 10 }}>Upload your document</h2>

            {uploadError && (
              <div className="error-banner">
                <b>Error:</b> {uploadError}
              </div>
            )}

            <div
              className={"dropzone" + (dragOver ? " drag" : "")}
              onClick={() => fileInputRef.current.click()}
              onDragEnter={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" style={{ margin: "0 auto", display: "block" }}>
                <path d="M12 3v12m0-12l-4 4m4-4l4 4M5 17v2a2 2 0 002 2h10a2 2 0 002-2v-2" stroke="#1F2340" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="dz-title">Drag and drop your contract here</div>
              <div className="dz-sub">or click to browse your files</div>
              <div className="dz-formats">PDF · DOCX · TXT (Max 25 MB)</div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              style={{ display: "none" }}
              accept=".pdf,.docx,.txt"
              onChange={(e) => handleFiles(e.target.files)}
            />

            {selectedFile && (
              <div className="file-chosen">
                <div>
                  <div className="fname">{selectedFile.name}</div>
                  <div className="fmeta">
                    {selectedFile.size ? (selectedFile.size / (1024 * 1024)).toFixed(2) + " MB" : "Sample Contract"} · Ready for analysis
                  </div>
                </div>
                <button className="btn-ghost" onClick={() => setSelectedFile(null)}>Remove</button>
              </div>
            )}

            <div className="analyze-opts">
              <div className="opt-field">
                <label>Document language</label>
                <select value={docLang} onChange={(e) => setDocLang(e.target.value)}>
                  <option>Auto detect</option>
                  {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
              <div className="opt-field">
                <label>Explanation language</label>
                <select value={explainLang} onChange={(e) => setExplainLang(e.target.value)}>
                  {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>

            <p className="secure-note">
              Uploaded contracts are processed locally for analysis only and are never transmitted to unauthorized third parties.
            </p>

            <div className="analyze-btn-row">
              <button
                className="btn-primary"
                style={{ opacity: selectedFile ? 1 : 0.4, pointerEvents: selectedFile ? "auto" : "none" }}
                onClick={startAnalysisWorkflow}
              >
                Analyze contract
              </button>
            </div>

            {/* Quick-test sample contract options */}
            <div className="quick-samples">
              <div className="qs-title">Or test with a pre-configured sample contract:</div>
              <div className="quick-samples-btns">
                <button className="btn-ghost" onClick={() => loadSampleContract("English")}>
                  📄 Vendor Agreement (English)
                </button>
                <button className="btn-ghost" onClick={() => loadSampleContract("Tamil")}>
                  📄 Commercial Lease (Tamil)
                </button>
                <button className="btn-ghost" onClick={() => loadSampleContract("Hindi")}>
                  📄 Rental Terms (Hindi)
                </button>
                <button className="btn-ghost" onClick={() => loadSampleContract("Malayalam")}>
                  📄 Franchise Terms (Malayalam)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 3. PROCESSING IN PROGRESS VIEW */}
        {view === "analyze" && processing && (
          <div className="processing-wrap">
            <div className="proc-doc">
              <div className="scanline" />
              <div className="doc-line" style={{ fontSize: 14 }}>
                <b>Contract:</b> {selectedFile ? selectedFile.name : "Contract_Document.pdf"}
              </div>
              <div className="doc-line" style={{ fontSize: 13.5 }}>
                {procStage}
              </div>
            </div>

            <div className="proc-bar">
              <div className="proc-bar-fill" style={{ width: procPercent + "%" }} />
            </div>

            <div className="proc-msg">{procStage} ({procPercent}%)</div>

            <div className="proc-steps">
              {PROC_STEPS.map((s, i) => {
                const isDone = completedStages.includes(s) || (procPercent >= ((i + 1) / PROC_STEPS.length) * 100);
                const isActive = !isDone && (completedStages.length === i || procStage.toLowerCase().includes(s.slice(0, 8).toLowerCase()));
                return (
                  <div key={s} className={"proc-step" + (isDone ? " done" : isActive ? " active" : "")}>
                    <div className="mark" />
                    <span>{s}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. DASHBOARD VIEW */}
        {view === "dashboard" && (
          <section>
            <div className="dash-top">
              <div className="dash-id">
                <span className="eyebrow">Analysis Dashboard</span>
                <h2>{analysisResult.filename || "Contract"}</h2>
                <div className="dsub">
                  Detected language: <b>{analysisResult.detected_language}</b> · Target: <b>{analysisResult.target_language}</b> · {activeClauses.length} clauses analyzed
                </div>
              </div>

              <div className="score-card">
                <div>
                  <div className={"score-num " + riskClass(analysisResult.overall_risk_level)}>
                    {analysisResult.overall_risk_score}<span style={{ fontSize: 16 }}>/100</span>
                  </div>
                  <div className="score-lbl">{riskLabel(analysisResult.overall_risk_level)}</div>
                </div>
              </div>
            </div>

            <div className="stat-row">
              <div className="stat-card">
                <div className="stat-num high">{highCount}</div>
                <div className="stat-lbl">High-risk clauses</div>
              </div>
              <div className="stat-card">
                <div className="stat-num med">{medCount}</div>
                <div className="stat-lbl">Medium-risk clauses</div>
              </div>
              <div className="stat-card">
                <div className="stat-num low">{lowCount}</div>
                <div className="stat-lbl">Low-risk clauses</div>
              </div>
              <div className="stat-card">
                <div className="stat-num">{activeClauses.length}</div>
                <div className="stat-lbl">Total clauses analyzed</div>
              </div>
            </div>

            {/* Language Switcher Toolbar */}
            <div className="dash-lang-bar">
              <div className="dl-left">
                <span className="dl-icon">🌐</span>
                <div>
                  <div className="dl-text-title">Interactive Translation & Explanation Language</div>
                  <div className="dl-text-sub">
                    Translate the contract analysis, risk breakdowns, and recommendations instantly:
                  </div>
                </div>
              </div>
              <div className="dl-buttons">
                {LANGS.map((lang) => {
                  const isActive = (dashLang || "English").toLowerCase() === lang.toLowerCase();
                  const labels = {
                    English: "🇬🇧 English",
                    Tamil: "🇮🇳 தமிழ் (Tamil)",
                    Hindi: "🇮🇳 हिन्दी (Hindi)",
                    Malayalam: "🇮🇳 മലയാളം (Malayalam)",
                    Telugu: "🇮🇳 తెలుగు (Telugu)",
                  };
                  return (
                    <button
                      key={lang}
                      className={"dl-pill" + (isActive ? " active" : "")}
                      disabled={isTranslating}
                      onClick={() => handleSwitchLanguage(lang)}
                      title={`Translate analysis to ${lang}`}
                    >
                      {labels[lang] || lang}
                    </button>
                  );
                })}
                {isTranslating && (
                  <span className="dl-spinner">⏳ Translating...</span>
                )}
              </div>
            </div>

            {/* Quick Export & Actions Toolbar */}
            <div className="dash-actions-toolbar">
              <button
                className="btn-export-primary"
                onClick={() => {
                  const id = analysisResult.analysis_id || analysisResult.document_id;
                  window.open(api.getPdfReportUrl(id, dashLang), "_blank");
                }}
                title={`Download comprehensive legal risk PDF report in ${dashLang}`}
              >
                📥 Download PDF Report ({dashLang})
              </button>

              <button
                className="btn-export"
                onClick={() => {
                  const id = analysisResult.analysis_id || analysisResult.document_id;
                  window.open(api.getJsonReportUrl(id), "_blank");
                }}
                title="Export structured JSON data"
              >
                📄 Export JSON
              </button>

              <button
                className="btn-export"
                onClick={() => {
                  const id = analysisResult.analysis_id || analysisResult.document_id;
                  window.open(api.getCsvReportUrl(id), "_blank");
                }}
                title="Export clause breakdown spreadsheet"
              >
                📊 Export CSV
              </button>

              <button
                className="btn-export"
                onClick={() => go("report")}
                title="View formatted executive brief"
              >
                📜 View Formatted Brief →
              </button>
            </div>

            <div className="summary-box">
              <p>{analysisResult.executive_summary}</p>
            </div>

            <div className="dash-body">
              {/* Column 1: Risk Map */}
              <div className="dash-col">
                <div className="col-head"><h4>Risk map</h4></div>
                <div className="map-list">
                  {activeClauses.map((c) => (
                    <div
                      key={c.id}
                      className={"map-item" + (c.id === (selectedClause ? selectedClause.id : null) ? " selected" : "")}
                      onClick={() => selectClause(c.id)}
                    >
                      <span>
                        <span className="mi-num">{c.clause_number || c.id}.</span>
                        {c.category || c.type}
                      </span>
                      <span className={"risk-dot " + riskClass(c.risk_level || c.risk)} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Column 2: Contract Viewer */}
              <div className="dash-col">
                <div className="col-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <h4>Contract viewer</h4>
                  {dashLang !== "English" && (
                    <button
                      className="btn-ghost"
                      style={{ fontSize: "11px", padding: "2px 8px" }}
                      onClick={() => setShowTranslatedText(!showTranslatedText)}
                    >
                      {showTranslatedText ? "Show Original" : `Show ${dashLang}`}
                    </button>
                  )}
                </div>
                <div className="filter-row">
                  {[["all", "All"], ["high", "High risk"], ["medium", "Medium risk"], ["low", "Low risk"]].map(([val, label]) => (
                    <button
                      key={val}
                      className={"btn-ghost" + (dashFilter === val ? " on" : "")}
                      onClick={() => setDashFilter(val)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <div className="viewer">
                  {activeClauses.map((c) => {
                    const cRisk = (c.risk_level || c.risk || "low").toLowerCase();
                    const dimmed = dashFilter !== "all" && cRisk !== dashFilter;
                    const isSelected = selectedClause && selectedClause.id === c.id;
                    const clauseBody = (showTranslatedText && dashLang !== "English" && c.translated_text) ? c.translated_text : (c.original_text || c.text);
                    return (
                      <div
                        key={c.id}
                        id={"vclause-" + c.id}
                        className={"v-clause " + riskClass(cRisk) + (isSelected ? " selected" : "") + (dimmed ? " dim" : "")}
                        onClick={() => selectClause(c.id)}
                      >
                        <b>{c.clause_number || c.id}.</b> {clauseBody}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Column 3: Clause Analysis */}
              <div className="dash-col">
                <div className="col-head"><h4>Clause analysis</h4></div>
                <div className="detail-pane">
                  <ClauseDetail
                    clause={selectedClause}
                    analysisId={analysisResult.analysis_id}
                    dashLang={dashLang}
                    setDashLang={setDashLang}
                    onSwitchLang={handleSwitchLanguage}
                    reasonOpen={reasonOpen}
                    setReasonOpen={setReasonOpen}
                    onExplainRequested={handleExplainRequested}
                    isExplaining={isExplaining}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 24, gap: 12 }}>
              <button className="btn-secondary" onClick={() => go("report")}>View full report →</button>
            </div>
          </section>
        )}

        {/* 5. REPORT VIEW */}
        {view === "report" && (
          <section>
            <div className="report-doc">
              <div className="rmasthead">
                <div>
                  <h2>Contract Risk Assessment Report</h2>
                  <div className="dsub" style={{ marginTop: 6 }}>{analysisResult.filename || "Contract"}</div>
                </div>
                <div className="stamp">
                  Generated by Clausent AI<br />
                  Language: {analysisResult.detected_language} · {activeClauses.length} clauses
                </div>
              </div>

              <div className="rsection">
                <h3>Overall risk score</h3>
                <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
                  <span className={"score-num " + riskClass(analysisResult.overall_risk_level)} style={{ fontSize: 40 }}>
                    {analysisResult.overall_risk_score}<span style={{ fontSize: 18 }}>/100</span>
                  </span>
                  <span className={"detail-risk-badge " + riskClass(analysisResult.overall_risk_level)}>
                    {riskLabel(analysisResult.overall_risk_level)}
                  </span>
                </div>
              </div>

              <div className="rsection">
                <h3>Executive summary</h3>
                <p>{analysisResult.executive_summary}</p>
              </div>

              <div className="rsection">
                <h3>Clause statistics</h3>
                <div className="rstat-grid">
                  <div className="rs"><div className="rsnum high">{highCount}</div><div className="rslbl">High risk</div></div>
                  <div className="rs"><div className="rsnum med">{medCount}</div><div className="rslbl">Medium risk</div></div>
                  <div className="rs"><div className="rsnum low">{lowCount}</div><div className="rslbl">Low risk</div></div>
                  <div className="rs"><div className="rsnum">{activeClauses.length}</div><div className="rslbl">Total clauses</div></div>
                </div>
              </div>

              <div className="rsection">
                <h3>High-risk provisions ({reportHigh.length})</h3>
                <div className="rlist">
                  {reportHigh.map((c) => (
                    <div className="rlist-item" key={c.id}>
                      <span><b>{c.clause_number || c.id}.</b> {c.category || c.type}</span>
                      <span className="rl-tag" style={{ color: "var(--risk-high)", fontWeight: 600 }}>HIGH</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rsection">
                <h3>Medium-risk provisions ({reportMed.length})</h3>
                <div className="rlist">
                  {reportMed.map((c) => (
                    <div className="rlist-item" key={c.id}>
                      <span><b>{c.clause_number || c.id}.</b> {c.category || c.type}</span>
                      <span className="rl-tag" style={{ color: "var(--risk-med)", fontWeight: 600 }}>MEDIUM</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rsection">
                <h3>Suggested review & negotiation points</h3>
                <p>{analysisResult.suggested_review_areas || "Review high-risk clauses with qualified legal counsel."}</p>
              </div>

              {/* Report Language Selector Bar */}
              <div style={{ marginTop: 28, padding: "14px 18px", background: "var(--paper-panel)", borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>
                  🌐 Report Language: <b>{dashLang}</b>
                </span>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
                  {LANGS.map((lang) => (
                    <button
                      key={lang}
                      className={"btn-ghost" + (dashLang === lang ? " on" : "")}
                      style={{ fontSize: 12, padding: "5px 10px" }}
                      disabled={isTranslating}
                      onClick={() => handleSwitchLanguage(lang)}
                    >
                      {lang}
                    </button>
                  ))}
                  {isTranslating && (
                    <span style={{ fontSize: 12, color: "var(--accent)" }}>⏳</span>
                  )}
                </div>
              </div>

              {/* Real Export Actions */}
              <div className="report-actions">
                <button
                  className="btn-primary"
                  onClick={() => {
                    const id = analysisResult.analysis_id || analysisResult.document_id;
                    window.open(api.getPdfReportUrl(id, dashLang), "_blank");
                  }}
                  title={`Download official contract report in ${dashLang}`}
                >
                  Download PDF Report ({dashLang}) 📥
                </button>

                <button
                  className="btn-secondary"
                  onClick={() => {
                    const id = analysisResult.analysis_id || analysisResult.document_id;
                    window.open(api.getJsonReportUrl(id), "_blank");
                  }}
                >
                  Export JSON 📄
                </button>

                <button
                  className="btn-secondary"
                  onClick={() => {
                    const id = analysisResult.analysis_id || analysisResult.document_id;
                    window.open(api.getCsvReportUrl(id), "_blank");
                  }}
                >
                  Export CSV 📊
                </button>

                <button className="btn-ghost" onClick={() => window.print()}>
                  Print Report 🖨️
                </button>
              </div>

              <div className="disclaimer">
                Clausent provides AI-assisted contract analysis for informational and educational purposes only.
                It does not constitute formal legal advice and does not substitute for review by a qualified legal professional.
              </div>
            </div>
          </section>
        )}

        {/* 6. MY CONTRACTS VIEW */}
        {view === "contracts" && (
          <section>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 12 }}>
              <div>
                <span className="eyebrow" style={{ marginTop: 36, display: "block" }}>Contract Archive</span>
                <h2 style={{ fontSize: 28, marginTop: 10 }}>Previously Analyzed Contracts</h2>
              </div>
              <button className="btn-primary" onClick={() => go("analyze")}>+ Upload new contract</button>
            </div>

            <div className="mc-toolbar">
              <input
                type="text"
                placeholder="Search contracts by name..."
                value={mcSearch}
                onChange={(e) => setMcSearch(e.target.value)}
              />
              <select value={mcRiskFilter} onChange={(e) => setMcRiskFilter(e.target.value)}>
                <option value="all">All risk levels</option>
                <option value="high">High risk</option>
                <option value="medium">Medium risk</option>
                <option value="low">Low risk</option>
              </select>
              <select value={mcLangFilter} onChange={(e) => setMcLangFilter(e.target.value)}>
                <option value="all">All languages</option>
                {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
              <select value={mcSort} onChange={(e) => setMcSort(e.target.value)}>
                <option value="date">Sort by date</option>
                <option value="risk">Sort by risk</option>
              </select>
            </div>

            <table className="mc-table">
              <thead>
                <tr>
                  <th>Contract Name</th>
                  <th>Date Analyzed</th>
                  <th>Language</th>
                  <th>Risk Level</th>
                  <th>Flagged Clauses</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {contractRows.map((r) => (
                  <tr key={r.id || r.name}>
                    <td><b>{r.name}</b></td>
                    <td className="mono">{r.date || "2026-07-18"}</td>
                    <td>{r.lang}</td>
                    <td>
                      <span className="mc-risk-pill" style={{
                        background: `var(--risk-${r.risk.toLowerCase() === "medium" ? "med" : r.risk.toLowerCase()}-bg)`,
                        color: `var(--risk-${r.risk.toLowerCase() === "medium" ? "med" : r.risk.toLowerCase()})`
                      }}>
                        {r.risk.toUpperCase()}
                      </span>
                    </td>
                    <td className="mono">{r.flagged}</td>
                    <td>{r.status}</td>
                    <td className="mc-actions" style={{ textAlign: "right" }}>
                      <button className="btn-ghost" onClick={() => handleOpenContract(r.id)}>Open</button>
                      <button className="btn-ghost" onClick={() => handleDeleteContract(r.id)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </main>

      {/* Settings & System Architecture Modal */}
      {settingsOpen && (
        <div className="modal-backdrop" onClick={() => setSettingsOpen(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3>About CLAUSENT</h3>
            <p>
              <b>CLAUSENT</b> is an AI-powered multilingual contract risk analyzer developed for educational and small-business legal empowerment.
            </p>

            <div style={{ fontSize: 13, marginBottom: 16 }}>
              <div style={{ marginBottom: 6 }}><b>Backend Status:</b> {backendStatus.online ? "🟢 Connected (Live Backend)" : "🟡 Offline (Standalone Demo)"}</div>
              <div style={{ marginBottom: 6 }}><b>Encoder:</b> Legal-BERT (nlpaueb/legal-bert-base-uncased)</div>
              <div style={{ marginBottom: 6 }}><b>Classification:</b> CUAD-aligned 13-category legal taxonomy</div>
              <div style={{ marginBottom: 6 }}><b>SLM Service:</b> Qwen2.5-3B-Instruct / Local Plain-Language Engine</div>
              <div style={{ marginBottom: 6 }}><b>LLM Service:</b> Gemini-2.5-Flash / OpenAI / Heuristic Legal Counsel</div>
              <div style={{ marginBottom: 6 }}><b>Languages Supported:</b> English, Tamil, Hindi, Malayalam, Telugu</div>
            </div>

            <p style={{ fontSize: 12, color: "var(--ink-faint)" }}>
              <b>Legal Notice:</b> CLAUSENT provides preliminary educational risk assessment only and does not constitute formal legal counsel. Always consult a qualified attorney for binding contractual negotiations.
            </p>

            <div className="modal-close-row">
              <button className="btn-primary" onClick={() => setSettingsOpen(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
