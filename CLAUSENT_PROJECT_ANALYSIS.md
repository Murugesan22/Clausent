# CLAUSENT — Implementation-Verified Project Analysis

> **Scope and evidence.** This report is based on the repository code and configuration available in this project. Where README/`tech.md` claims differ from executable code, the implementation takes precedence. Model availability, actual deployments, remote API credentials, and test execution in another environment cannot be verified just from source. No Git commit, push, or GitHub changes were made.

## 1. Executive summary

**One line:** CLAUSENT is a React/FastAPI application that stores uploaded contracts, extracts text, detects language, splits it into approximate clauses, applies regex-based category and risk rules, and displays/export findings.

In plain language: a user uploads a PDF, DOCX, or TXT. The backend saves it, extracts readable text, identifies a likely language, normalizes the text, optionally attempts translation, then searches clause text for legal phrases. Separate hard-coded rules assign risk labels/scores and canned explanations/actions. Results are stored in SQLAlchemy tables and can be viewed by the frontend and exported as PDF, JSON, or CSV. It is a preliminary screening/demo tool, not a legal expert and not a demonstrated learned contract classifier.

**30-second explanation:** “CLAUSENT helps a user screen a contract for provisions worth reviewing. It accepts PDF, Word, and text documents, extracts text, detects English or selected Indian languages, segments the text heuristically, and matches clauses against a legal keyword taxonomy. A separate rule engine assigns risk levels and suggested review questions. The results are stored and presented in a React dashboard with PDF/JSON/CSV export. Legal-BERT embeddings and external LLM calls are optional paths, but the default setup does not use a trained clause classifier, a loaded SLM, or a remote LLM. The output is educational triage, not legal advice.”

**Slide problem statement:** Small businesses and individuals may lack affordable time for first-pass contract review; dense legal wording and language barriers make important terms hard to spot. CLAUSENT aims to surface possible review areas quickly, with a clear warning that a qualified lawyer must make legal judgments.

**Detailed problem statement:** Contract documents can be lengthy, use specialized language, and contain obligations whose commercial impact is difficult for non-lawyers to assess. Manual review requires time and legal expertise; it can be inaccessible to smaller organizations and speakers reading in a second language. This project implements a document-processing interface that attempts to surface selected clause categories and rule-triggered risk indicators, while preserving excerpts and suggesting questions for professional review. It does not establish legal enforceability or replace counsel.

### Problem, audience, motivation and objectives

- **Who may benefit:** freelancers, small businesses, startups, and other people doing an initial review. This is the intended audience documented in `README.md`, not a validated user study.
- **Why it matters:** missing renewal deadlines, uncapped liability, broad indemnities, or termination asymmetry can have material financial or operational consequences. The rules flag examples of these patterns; they cannot establish legal harm on their own.
- **Motivation/objectives:** streamline text ingestion and first-pass review; display clause-oriented findings; provide some English/Indic-language support; retain prior uploads; generate portable reports.
- **Scope actually present:** PDF/DOCX/TXT ingestion, text extraction, script/language detection, normalization, heuristic segmentation, pattern classification, rule-based severity, stored analysis, an interactive frontend, and exports.
- **Important limits:** no OCR; no CUAD dataset or training pipeline found; no evidence of model evaluation against a labeled test set; heuristic boundaries and rules can miss or misread clauses; legal/jurisdictional context is not modeled; translation is best-effort and can silently fall back to original text; no authentication or tenant isolation was found.
- **Difference from summarizer/chatbot:** the product has an upload-to-report workflow and a deterministic category/risk rules layer. That is structurally different from a generic conversation. However, its default explanation engine is also mostly templates/rules, not evidence of an autonomous legal reasoning model.
- **SDGs:** SDG 16 (Peace, Justice and Strong Institutions) is a reasonable *intended alignment* through accessibility of preliminary legal information. SDG 10 (Reduced Inequalities) may be a secondary aspiration through language support. These impacts are not measured, so claim alignment rather than proven contribution.

## 2. Proposed solution

The intended solution is a browser-based contract review flow: upload → text extraction → language-aware processing → clause findings → risk dashboard/report. This lowers the effort of finding selected terms and provides questions/actions to take to counsel.

**Implemented versus design intent:**

| Capability | Implementation status and evidence |
|---|---|
| Contract upload and validation | Implemented: `backend/app/api/routes/documents.py`, `DocumentService.save_upload`, `backend/app/utils/file_validation.py`; extension check and streaming 25 MB limit. No actual MIME/content signature verification despite README language. |
| Text extraction | Implemented for PDF via PyMuPDF with pypdf fallback, DOCX via python-docx, TXT via encoding attempts: `extraction_service.py`. |
| OCR | Not implemented; image-only PDFs fail with an OCR-required message. |
| Language handling | Implemented: Indic Unicode script counts, then optional `langdetect`; source language can also be user-selected. |
| Translation | Best-effort translation attempts via `deep-translator` GoogleTranslator, small hard-coded translations/dictionaries, and fallback to original text. Not IndicTrans2/NLLB in the checked code. |
| Clause identification | Regex/paragraph heuristics in `segmentation_service.py`; not a trained boundary model. |
| Category/risk | Regex taxonomy plus deterministic rules in `classification_service.py` and `risk_assessment_service.py`. |
| Explanation | Default SLM path returns canned domain text. Default LLM path returns deterministic templates; external Gemini/OpenAI is possible when configured with a key. |
| Final report | Implemented PDF/JSON/CSV routes and report service. |

Multilingual design supports English, Tamil, Hindi, Malayalam, Telugu in settings and translation maps. Actual behavior is uneven: English is the analysis baseline, some detection is script-based, translation calls are remote Google Translate through `deep-translator`, and simple/local fallback strings are used on errors. Classification has several Indic keyword patterns but risk logic is predominantly English phrase matching. Hindi/Tamil, etc. are not validated on a multilingual benchmark.

Safeguards needed include a prominent non-legal-advice warning, uncertainty and source-span display, human review, validated translation quality, jurisdiction/context capture, calibrated confidence, privacy/deletion controls, and avoiding “safe” conclusions from low risk. The report PDF contains a disclaimer; result scores remain heuristic and should not be treated as legal outcomes.

## 3. Complete pipeline and flowchart

```text
Browser (React)
  │ multipart upload: PDF/DOCX/TXT
  ▼
FastAPI POST /api/documents/upload ── validate extension + stream size limit
  │ save UUID filename under backend data/uploads + Document DB row
  ▼
POST /api/analysis/{document_id}/start ── schedule FastAPI BackgroundTasks
  ▼
Extract text (PyMuPDF/pypdf, python-docx, or Python text IO)
  ├─ no PDF text → mark failed (“OCR required”; no OCR stage)
  ▼
Language: user preference or Indic Unicode script counts / langdetect
  ▼
Normalize legal text
  ▼
Attempt non-English → English translation (deep-translator; dictionary/fallback)
  ▼
Regex + paragraph segmentation (original-language segmentation attempted too)
  ▼
For each English clause:
  ├─ Legal-BERT encoder attempted (cached local weights only; fallback metadata)
  ├─ category from regex keyword taxonomy (NOT from embedding classifier)
  ├─ severity/score/action from deterministic risk rules
  ├─ canned SLM explanation; LLM path for high risk/specified category
  │    └─ API only if provider is Gemini/OpenAI AND API key exists; otherwise templates
  └─ optional translation/display fields
  ▼
Persist clause/job data in SQLAlchemy DB; aggregate contract score
  ▼
Frontend polls status → results dashboard; PDF/JSON/CSV report endpoints
```

### Stages, data and failure behavior

1. **Upload/validation:** `POST /api/documents/upload` accepts multipart `file`. Extension allowlist defaults to pdf/docx/txt; configured maximum defaults to 25 MB. Filename sanitized and internally UUID-named. Extension is not equivalent to content validation. Errors return HTTP 400/500. Stored under `backend/data/uploads` by default, plus database metadata.
2. **Extraction:** `ExtractionService.extract_from_file(path, type)` returns full text, page text mapping/count. PDF uses PyMuPDF, falling back to pypdf only if PyMuPDF import fails. DOCX extracts paragraphs and table cells; TXT tries UTF-8 variants, UTF-16, cp1252, Latin-1. Unsupported/empty/bad files raise an extraction error. Scanned PDF is explicitly failed; no OCR.
3. **Language detection:** chosen source-language preference bypasses detection; otherwise `LanguageDetectionService.detect_language` samples up to 2,500 characters. At least 15 Indic-script chars trigger script selection; otherwise `langdetect` is attempted. A fallback may label unknown text English. Language confidence is heuristic/probabilistic and can be misleading.
4. **Normalization:** `NormalizationService` validates content and calls `normalize_legal_text`; outputs normalized text and metadata. It raises an extraction-stage error on invalid content. See `backend/app/utils/text_processing.py`.
5. **Translation to English:** `TranslationService.translate_to_english(text, detected_lang)` skips English; otherwise splits on blank lines and calls `_neural_translate`. The call uses GoogleTranslator with source `auto`, truncates each call to 500 characters, and has a 1.2-second timeout. Failing translation returns the paragraph unchanged. Thus the claim “all non-English text converted to English” is not guaranteed.
6. **Segmentation:** `SegmentationService.segment_text(english_text, page_texts)` splits paragraphs and recognizes numbered/section labels. Long blocks split by rough sentence/character heuristic. If no clauses, pipeline fails. Original-language text is segmented separately for non-English then paired by index, which can misalign when segmentation differs. Page matching uses substring matching.
7. **Tokens/representation:** `LegalBertService.encode_clause` tries cached `nlpaueb/legal-bert-base-uncased` with Transformers/PyTorch, local files only, truncating to 512 tokens and computing CLS embedding under no-grad. It returns metadata, not the vector to classification/risk. If unavailable/disabled, it returns deterministic fallback metadata (no semantic vector calculation). The encoding does not affect category decisions.
8. **Classification:** `ClassificationService.classify_clause` calls encoder for metadata, then applies regex taxonomy patterns. Pattern count produces a pseudo-confidence score (70% + 8 points per match, capped 96); no match defaults to “General Provisions” at 65%. This is a rule score, not model probability. If multiple categories match, highest heuristic match score wins.
9. **Risk:** `RiskAssessmentService.assess_risk(text, category)` applies substring/regex-like rules and category-specific mappings. Returns low/medium/high and fixed numeric values plus rationale, evidence, action, questions, and uncertainty. No learned risk model or calibrated confidence.
10. **Explanations:** `ExplanationOrchestrator` always invokes `SLMService`, which in the default `mock_local` mode returns category/risk templates. High-risk and selected categories then invoke `LLMService`; absent enabled API credentials the service generates deterministic multilingual templates. An API error falls back to the templates. A target-language translation attempt may follow.
11. **Persist and aggregate:** `DocumentService.execute_pipeline` persists clauses, counts risk levels, computes overall score from average clause score plus high/medium counts, assigns overall tier using thresholds, and stores summary/review text in analysis tables. Any thrown exception marks job and document failed; it also propagates to task logger.
12. **Return/report:** frontend polls `/status` every 750ms and fetches `/results`; outputs are Pydantic response structures. `GET /api/reports/{id}/pdf|json|csv` generates downloadable outputs. PDF generation errors produce HTTP 500. No generated report record is evident in the report route despite a Report table in models.

## 4. Technology stack and justification

Versions below are declared minimums/ranges, not proof of the installed runtime version. Frontend locked versions are in `package-lock.json`.

| Layer/technology | Evidence and actual role | Essential / replaceable; alternatives |
|---|---|---|
| React 19.2.7, JavaScript/JSX | `package.json`, `src/Clausent_front.jsx`, `src/main.jsx`; UI, state and dashboard. | Essential to current frontend, replaceable with Vue/Svelte/etc. |
| Vite 8.1.1; React plugin 6.x | `package.json`, `vite.config.js`; dev server/build. | Build tooling, replaceable by another bundler. |
| Custom CSS; Lucide React 1.25.0 | `src/index.css`, inline component styles; design and icons. No component framework found. | Replaceable. |
| Native browser `fetch` | `src/services/api.js`; REST calls. | Replaceable by Axios/client generation. |
| Python + FastAPI >=0.115.0, Uvicorn >=0.30 | `backend/requirements.txt`, `backend/app/main.py`; REST APIs and ASGI serving. | Core backend choices, replaceable by Flask/Django/Starlette. |
| Pydantic >=2.8; python-multipart >=0.0.9 | schemas and multipart upload. | Used for request/response validation and upload handling. |
| SQLAlchemy >=2.0, psycopg2-binary >=2.9.9 | `backend/app/database`; ORM. SQLite is default from config, PostgreSQL via `DATABASE_URL`. | Database abstraction useful; SQLite/PostgreSQL replaceable. No evidence live PostgreSQL exists. |
| PyMuPDF >=1.24, pypdf >=4 | PDF extraction implementation. PyMuPDF preferred, pypdf fallback on ImportError. | Replaceable; OCR would be an additional tool, not present. |
| python-docx >=1.1 | DOCX paragraphs and table extraction. | Replaceable. |
| ReportLab >=4.2 | PDF generation (`report_service.py`). | Replaceable by another PDF renderer. Font handling assumes Windows font paths for some Indic glyph support. |
| langdetect >=1.0.9 | fallback language detection. Script range counter is project code, not a model package. | Replaceable/additional detector useful for short/mixed text. |
| PyTorch >=2.0, Transformers >=4.40 | Optional cached Legal-BERT encoder implementation. | Only essential if actual encoder is enabled and cached; not needed by regex taxonomy/risk rules. |
| deep-translator >=1.11 | GoogleTranslator call in translation service. This is external network translation, not local NLLB/IndicTrans2. | Replaceable with vetted translation API/model; privacy, latency, and quality tradeoffs. |
| httpx >=0.27 | External Gemini/OpenAI API requests. | Used only in configured LLM path. |
| pandas >=2.2 | Listed dependency; no demonstrated use in report generation (CSV uses Python `csv`). | Not currently essential based on inspected code. |
| Hosting/config | `Dockerfile`, `render.yaml`, `render-build.sh` indicate Docker/Render deployment configuration. Actual deployment not verified. `backend/app/config.py` supports `.env`, SQLite default and env model/provider names. | Render, Docker, env configuration replaceable. No GitHub integration is part of runtime analysis; do not infer deployment from config alone. |

No dataset files, CUAD corpus, or model checkpoint artifacts were located in the project file listing. The app creates a model-cache directory, but no checked-in weights were found. Avoid sending real confidential contracts to external translation/LLM providers without user consent and an appropriate privacy review.

## 5. SLM, LLM and model analysis

### Beginner definitions

- **LLM:** a large generative language model that predicts/generates text from prompts; often accessed via a provider API.
- **SLM:** a smaller generative language model intended to be cheaper/faster or run on less hardware. “Small” describes scale, not guaranteed quality or local execution.
- **Traditional NLP classifier:** a model or rules system that maps text to labels. It need not generate prose. This repository’s actual clause labeler is keyword/regex rules, not a trained classifier.
- **Machine-translation model/service:** converts text between languages. Google Translate call is a translation service; it is not the project’s clause classifier or LLM explanation model.
- A transformer encoder (BERT/Legal-BERT) converts text into representations and generally does not generate conversational answers. An application can combine several model types, but AI branding alone does not mean an LLM is invoked.

### Inventory

| Model | Model type | Task | Input | Output | Local/API | Evidence |
|---|---|---|---|---|---|---|
| `nlpaueb/legal-bert-base-uncased` | BERT-family legal-domain encoder (not LLM/SLM) | Optional clause embedding/metadata only | English clause, max 512 tokenizer tokens | CLS embedding computed, but only metadata is returned to classifier; embedding does not determine label | Local cached weights only (`local_files_only=True`); otherwise deterministic metadata fallback | `backend/app/services/legal_bert_service.py`; called by `classification_service.py` |
| Regex CUAD-aligned taxonomy | Rule-based classifier, not a model | Clause category | Clause string | Category, matched keyword evidence, heuristic confidence | Local | `backend/app/services/classification_service.py` |
| RiskAssessmentService | Rule-based scoring engine | Severity, score, rationale and action | Clause text + category | Fixed score/tier and templated text | Local | `backend/app/services/risk_assessment_service.py` |
| `Qwen/Qwen2.5-3B-Instruct` (default config name) | Intended SLM family identifier | Intended plain-language summary | Would be clause/category/risk prompt | Actual service returns canned category templates; model not loaded/invoked | Not actually local/API in checked service | `config.py`, `slm_service.py`; no Transformers/model loading or API call there |
| Gemini model name default `gemini-2.5-flash`; optional OpenAI model via config | LLM provider options | Detailed explanation when configured | Clause/category/risk/rationale/evidence/target language | Provider-generated text if API key and provider configured; otherwise deterministic templates | External API only on configured Gemini/OpenAI path; default `mock_local` means no external request | `llm_service.py`; default config in `config.py` |
| Google Translate via `deep-translator` | External machine translation service | Text translation | Up to 500 chars per call, source auto + target language | Translated text or original/fallback | External network call | `translation_service.py`; dependency in requirements |
| `langdetect` | Statistical language-detection library | Language guess | Up to 2,500 characters | language code/probability mapped to supported names | Local library | `language_detection_service.py` |

**Is an SLM actually used?** No model inference is evidenced for Qwen. The service contains a prompt string but the default branch returns static templates; its non-default branch also returns a template and does not load a model. **Is an LLM actually used?** Only if deployment config sets a Gemini/OpenAI provider and API key. Default config is `mock_local`, so standard default use is deterministic templates, not an LLM. The on-demand endpoint calls the same orchestrator and does not guarantee remote inference.

**Model selection rationale vs evidence:** Legal-BERT is plausibly selected for legal-domain representation, but currently its vector is not consumed by classifier/risk logic. Qwen/Gemini names are configuration/design intentions, not proof of active inference. A single large model for everything could simplify orchestration but increase latency/cost, require privacy review, and make outputs less deterministic; however, this project has not experimentally compared approaches. An actual SLM could produce more contextual explanations at local compute cost, while an LLM could improve nuanced prose but may hallucinate and send sensitive text externally. Replacement must preserve interfaces and be validated on labeled contracts, multilingual translations, latency/cost, and privacy. The current AI contribution is chiefly NLP-oriented document processing and a rules-based legal-pattern prototype with an optional Legal-BERT encoder/API integration point—not a demonstrated trained AI classifier.

## 6. Background working: illustrative execution trace

Suppose a user uploads a contract containing: (a) automatic renewal for another year unless 90-days’ notice is given; (b) one party may terminate immediately; (c) liability is unlimited.

1. React checks extension and 25 MB size, then sends `FormData` to `/api/documents/upload`. Backend saves a UUID file and DB row.
2. User starts analysis. The route adds `run_pipeline_task` to FastAPI `BackgroundTasks`; UI polls status.
3. Extraction reads embedded PDF text (or DOCX/TXT). A scanned-only PDF stops here because OCR is absent.
4. Language is user-selected or estimated from script/langdetect. For English, translation is skipped. For other languages, translator attempts GoogleTranslator; errors can leave source-language text in the English pipeline.
5. Normalization cleans text; segmentation groups paragraphs/numbered headings. It may group several clauses or split incorrectly. No robust semantic chunker is implemented.
6. For each segment, Legal-BERT may create a 768-d CLS vector if local weights already exist. The vector is not used downstream. Clause labels come from regular expressions: renewal phrases can match “Automatic Renewal”; termination terms can match “Termination”; liability terms can match “Limitation of Liability”.
7. Risk rules inspect text/category. The explicit unlimited liability phrase can trigger a global high rule with score 94. Automatic renewal can become medium/high depending on parsed notice length (>=60 days high). Immediate/without-cause termination can be high. These are fixed heuristics, not model probabilities. “One-sided” is only partially handled, especially outside specific categories.
8. Category confidence is a match-count-derived number and must not be described as calibrated probability. Risk score and classification confidence are separate fields.
9. Default explanation is canned. High-risk clause may also invoke the “LLM” service; with default mock settings this yields deterministic generated template text. With configured external provider/key, the clause may be sent to Gemini/OpenAI. API failures fall back.
10. Clauses, risk and explanations are persisted; overall score is aggregated from arithmetic rules. Dashboard fetches response JSON and shows summary/cards.
11. User downloads PDF/JSON/CSV via report routes. PDF includes disclaimer; exports do not constitute legal advice.

This trace explains code paths, not a verified result for any particular file or model output.

## 7. Dataset and training methodology

- **CUAD:** Contract Understanding Atticus Dataset is referenced in comments/docs as a taxonomy inspiration. CUAD is a labeled contract-understanding dataset with clause/question categories and span annotations; it is not loaded by this code.
- **Repository evidence:** no CUAD data files or training scripts were found; no train/validation/test split or fine-tuning routine was found. `ClassificationService.TAXONOMY_PATTERNS` is hand-written regex. “CUAD-aligned” means labels/patterns are named around contract categories, not that this app was trained on CUAD.
- **Model status:** Legal-BERT pretrained encoder is optionally loaded for representations only. No fine-tuned checkpoint or training workflow is included. Default service may use offline metadata fallback.
- **Evaluation:** pytest files test code behavior/rules, not predictive generalization on a held-out labeled dataset. No multilingual test corpus or benchmark results are evidenced.
- **Hindi/Tamil/etc.:** implemented support includes Unicode script detection, some Indic keyword regexes, dictionaries, and translation attempts. No evidence of evaluation against human translations or annotated Indic contracts.
- **Translation risk:** a mistranslated negation, party, duration, exception, or amount can change legal meaning. Truncation/fallback may omit content. Preserve original text and require human/legal validation; do not infer that a translation-backed label is reliable without metrics.

## 8. Risk detection and scoring

Risk is computed by hand-authored conditions in `RiskAssessmentService`, not directly produced by a model. It checks global hazards such as uncapped liability, penalty/forfeiture, unilateral modification, and broad IP forfeiture; then applies category-specific logic for liability, indemnification, auto-renewal, termination, non-compete, IP, dispute resolution, and warranty. Unhandled categories fall to a low baseline score of 20, which may create false reassurance.

Examples:

- **Category:** “Automatic Renewal” answers what the clause concerns.
- **Risk:** fixed rule maps a long cancellation window (>=60 days) to high and score 88, or shorter/no parsed period to medium score 50.
- **Explanation:** template/API prose explains a rule result. It does not establish enforceability or prove the provision is harmful in context.

The classifier’s confidence score is not calibrated; risk score is also not a learned probability. Contract-level calculation uses average clause score plus counts (high ×20, medium ×8, weighted) then tier thresholds. This aggregation can depend strongly on segmentation: splitting one clause may alter counts and score. There is no proven calibration, error bar, or false-negative control. Clause presence is not proof of unfairness; mutuality, scope, jurisdiction, parties, price, and surrounding clauses matter. Some advice strings make broad legal/commercial assumptions and require professional review.

## 9. Frontend/backend architecture and data flow

```text
React UI: src/Clausent_front.jsx
   │ fetch + FormData (src/services/api.js)
   ▼
FastAPI app (backend/app/main.py; routers under /api)
   ├─ documents.py → DocumentService → file validation/extraction
   ├─ analysis.py → BackgroundTasks → DocumentService pipeline
   │     ├─ detection / normalization / translation / segmentation
   │     ├─ classification / risk / explanation services
   │     └─ SQLAlchemy repositories and models
   ├─ reports.py → ReportService → PDF (ReportLab), JSON, CSV
   └─ health.py
        │
        ├─ Local upload/report folders
        └─ SQLite default; DATABASE_URL can select PostgreSQL
```

**Routes:** `POST /api/documents/upload`; `GET /api/documents`; `GET/DELETE /api/documents/{id}`; `POST /api/analysis/{id}/start`; `GET /status`, `/results`, `/clauses`, `/clauses/{clause_id}`; `POST /clauses/{clause_id}/explain`; `POST /translate`; report PDF/JSON/CSV endpoints; health endpoint. Upload request is multipart; analysis starts with query parameters `target_language` and `source_language`; responses use Pydantic schemas in `backend/app/schemas`.

**Storage:** document records, analysis jobs, and clauses are SQLAlchemy models. SQLite default is `backend/clausent.db` (config path); PostgreSQL can be selected. Uploaded files and generated PDF outputs are local directories. No external object storage, user account/authentication, or retention cleanup scheduler was identified. A Report model exists, but report routes appear to generate files without persisting Report rows.

**Failure/security/performance observations:** unsupported extensions and size over limit are rejected; corrupted extraction and empty text fail; scanned PDF fails without OCR; translation failure may pass untranslated input; Legal-BERT failure silently degrades to metadata; external LLM failure falls back to heuristic; long input is not globally bounded beyond upload size, translation call truncates to 500 characters, and Legal-BERT truncates each clause to 512 tokens. A FastAPI in-process background task is not a durable queue. There is no authentication/authorization, so deployment exposure of document endpoints is a privacy concern. CORS can be permissive depending on config. Extension validation does not inspect actual file content. Uploaded contracts contain sensitive data; external translation/API calls require explicit consent and safeguards. PDF report embeds user text into ReportLab Paragraph markup; escaping should be reviewed to avoid malformed markup/injection in generated documents.

## 10. Final output and user experience

| Output feature | Status |
|---|---|
| Original/extracted clause text | Implemented in API response and dashboard. |
| Clause categories | Implemented, but regex taxonomy can misclassify. |
| Low/medium/high risk labels and numeric scores | Implemented as rules/fixed mappings. |
| Confidence | Implemented as regex match heuristic, not calibrated probability. |
| Plain-language explanations | Partially implemented: default static templates; optional API-generated detailed text. |
| Suggested actions/questions/uncertainties | Implemented as rules/templates; legal validity unverified. |
| Translated findings | Partially implemented with remote translation attempt and dictionaries/fallback. Not guaranteed full, exact translation. |
| Overall summary/risk | Implemented by formula and canned summary. |
| PDF report | Implemented via ReportLab; Indic font rendering depends on machine fonts. |
| JSON and CSV | Implemented. |
| Hard-coded demonstration results | Implemented frontend demo mode, distinct from backend analysis; `CLAUSES` and sample outputs are constants in `src/Clausent_front.jsx`. |

**Illustrative only — not a model result:**

```text
Overall: HIGH (illustrative score 72/100)
Clause: Automatic Renewal
Finding: Automatically renews for successive one-year terms unless notice is given 90 days before expiry.
Rule-based severity: HIGH (because the configured rule treats >=60 days as high)
Suggested review: Ask counsel whether the notice window can be shortened and whether renewal can be opt-in.
Disclaimer: Preliminary automated screening; verify the original clause and consult qualified counsel.
```

## 11. Evaluation against project rubrics

No official grading rubric was supplied. This is an evidence-based qualitative review, not a course mark.

| Criterion | Evidence-based assessment |
|---|---|
| Problem relevance | Strong and understandable use case; real need, but impact/user research not shown. |
| Technical depth | Good modular full-stack structure and end-to-end workflow; ML depth is overstated by docs relative to current code. |
| Dataset relevance/quality | CUAD-inspired category naming only; no data artifact, annotation processing, or data provenance found. Major gap. |
| NLP/ML implementation | Real extraction, script detection, normalization, segmentation, optional encoder. Actual category/risk are rules; no trained classifier. |
| Multilingual functionality | Languages appear in configuration/maps/patterns; external translation and static fallback; translation quality and balanced language risk rules not evaluated. Partial. |
| Model choice | Legal-BERT encoder integration is plausible but disconnected from decisions; named Qwen is not invoked; LLM is conditional API path. Needs precise truthful presentation. |
| Experimental evaluation | Unit/integration tests exist, but no labeled test set, metrics, baselines, ablation, calibration, latency/cost measurements, or human review study found. |
| Frontend/backend integration | Solid API route separation, status polling, dashboard, and exports. In-process background tasks can be fragile for production. |
| Reproducibility | Dependency manifests, config, Docker/Render files and tests aid setup. Exact dependency pins, model artifacts/data and external service reproducibility are limited. |
| Practical usefulness | Helpful first-pass navigation if clearly labeled; false confidence and legal overclaim are risks. |
| Innovation/research | Product integration and bilingual/Indic accessibility concept; research contribution requires dataset/measurement and working model inference evidence. |
| SDGs | Plausible SDG 16/10 intent; no measurable outcomes established. |

## 12. Limitations and realistic improvements

1. **Make claims match behavior:** label the current category/risk engine as rule-based; remove/qualify active SLM/Legal-BERT claims unless real inference is enabled and verified.
2. **Build an evaluation set:** annotate representative clauses (with permissions), establish splits, report macro-F1/precision/recall per category, risk confusion matrix, calibration, and multilingual results. Compare regex baseline against a fine-tuned Legal-BERT classifier.
3. **Connect or remove the encoder:** either use embeddings in a tested classifier, or avoid expensive unused model loading and describe as optional metadata only.
4. **Translation validation:** replace ad hoc truncation/fallback with a documented provider/model strategy; preserve source spans, detect failed translation, flag low confidence, test negation/numbers/party names with bilingual reviewers.
5. **Segmentation and scoring:** test nested numbering and tables; retain offsets/page positions; avoid index-only pairing of independent language segmentations; aggregate by clause identity instead of raw count.
6. **Safety:** show evidence excerpts and “possible issue” language, calibrate outputs, avoid low-risk/legal-safe implication, and require lawyer review for decisions.
7. **Privacy/security:** authentication, authorization, encrypted storage/transit, retention/deletion policy, content type validation, request limits, API key handling, audit log, and explicit consent before remote translation/LLM use.
8. **Reliability:** durable job queue, timeout/retry policy, non-blocking translation, standardized stage-specific errors, cleanup of abandoned uploads/reports.
9. **PDF hardening:** escape content, test non-Windows deployment and Indic shaping/fonts.
10. **Project reporting:** document actual provider/model settings, versions, and benchmark conditions; distinguish demo data from production output.

## 13. Viva questions and answers

1. **Problem statement?** Contracts are lengthy and hard for non-lawyers to screen; the app attempts to surface selected categories and possible risks for review, not provide legal advice.
2. **Proposed solution?** Upload a document, extract and segment its text, apply category/risk rules, show findings, and export a report.
3. **Pipeline?** Upload → extraction → language detection → normalization → optional translation → heuristic segmentation → regex categorization → rule-based risk → template/optional API explanation → database → dashboard/report.
4. **Why this stack?** React/Vite gives a responsive browser UI; FastAPI provides a compact Python API; SQLAlchemy supports SQLite/PostgreSQL; Python packages cover document extraction and optional NLP inference.
5. **Which SLM/LLM?** Qwen2.5-3B is only a configured name; it is not loaded. Gemini/OpenAI can be called if provider and key are configured; default is mock/deterministic, so do not claim always-on LLM use.
6. **Why a traditional classifier?** A category classifier answers what the provision concerns; a separate risk engine can assess wording. In this implementation, categorization is regex rules rather than a trained classifier.
7. **What is CUAD?** A public contract-understanding dataset with annotated legal clause/question categories. This repo references its taxonomy concept but does not load/train on CUAD.
8. **How does multilingual translation work?** Script-based detection plus langdetect; translation attempts use deep-translator/GoogleTranslator and static legal dictionaries/fallback. It is not an integrated local IndicTrans2 model.
9. **How detect high risk?** Hand-coded phrase/threshold rules—e.g., explicit unlimited liability triggers high. This is a heuristic alert, not proof of legal harm.
10. **How evaluate performance?** Current tests check expected code behavior. Proper predictive evaluation still needs labeled held-out data, precision/recall/F1, risk confusion matrix, translation review, and human assessment.
11. **Translation errors?** Current code may return the original text; that can silently contaminate English analysis. Production should detect and surface translation failure and require source-language review.
12. **Incorrect prediction?** User must verify original contract and consult counsel. Current implementation has no learned confidence calibration or human correction feedback loop.
13. **Classification vs risk scoring?** Category says “what kind of clause”; risk score estimates potential concern under explicit rules. They are separate fields and one does not imply the other.
14. **Main technical contribution?** Full-stack document workflow integrating extraction, heuristic multilingual processing, contract taxonomy/risk rules, persistence, dashboard, and exports—not novel model training.
15. **Limitations?** No OCR, no CUAD training, rule brittleness, weakly verified translations, no benchmark, jurisdiction missing, no authentication, and optional models are inactive by default.
16. **Next version?** Add annotated evaluation data, train/evaluate a clause classifier, validate translation, improve segmentation, secure storage, and calibrate risk explanations.
17. **SDG 16?** It aims to improve access to understandable preliminary legal information; actual social impact has not been measured.
18. **Different from generic chatbot?** It has file ingestion, clause segmentation, deterministic rule scoring, persistent findings, and report export. Its default explanations are templates; it is not a general conversational legal authority.

## 14. Two-minute presentation script

“CLAUSENT is a web application for preliminary contract screening. The problem we address is that contracts are long, use legal language, and can be difficult for small businesses, freelancers, or individuals to review quickly, especially when language is a barrier.

The user uploads a PDF, DOCX, or TXT file. The backend validates the extension and size, stores the file and metadata, extracts text, detects a likely language, normalizes it, and attempts to translate non-English text into English. It then uses paragraph and numbering heuristics to form clause segments. Category identification is currently based on regular-expression patterns aligned conceptually with common contract topics. A separate rule engine assigns risk tiers and scores based on phrases and conditions such as uncapped liability, renewal notice periods, or termination wording.

Results are stored using SQLAlchemy and shown in a React dashboard. The application can generate PDF, JSON, and CSV reports. The system also has multilingual labels and translation attempts for English, Tamil, Hindi, Malayalam, and Telugu.

An important implementation detail is that the current default is not a trained AI classifier or an active Qwen model. Legal-BERT is an optional local encoder whose vector is not used to make the category decision. The default explanation services use templates; external Gemini or OpenAI generation is possible only when configured with credentials. The project includes no CUAD training pipeline or OCR. Therefore, we present CLAUSENT as a first-pass educational screening tool, not legal advice. Future work is to evaluate against labeled contract data, validate multilingual translation, improve segmentation, and add security and human-review safeguards.”

## 15. What Our Project Actually Does

CLAUSENT is a React 19/Vite frontend with a Python FastAPI backend. It accepts PDF, DOCX, and TXT uploads; checks file extension and a 25 MB streaming limit; stores uploaded files locally and metadata/results in SQLAlchemy-backed SQLite by default (PostgreSQL is configurable). PyMuPDF/pypdf, python-docx, and Python text IO extract text. Image-only PDFs are rejected because OCR is not implemented. Language handling uses custom Indic Unicode-script counts and optional `langdetect`; normalization is project code. Non-English-to-English and result translation attempts use `deep-translator`’s GoogleTranslator plus dictionaries/templates/fallbacks—not an included IndicTrans2/NLLB model.

Clause segmentation uses regular expressions and paragraph/length heuristics. Clause categories come from hard-coded keyword regexes inspired by a CUAD-aligned taxonomy; risk levels, numeric scores, rationales, actions, and overall score come from hand-coded rules. Confidence is a match-count heuristic, not a calibrated probability. `nlpaueb/legal-bert-base-uncased` can be loaded from a local Transformers/PyTorch cache to produce a CLS embedding, but that representation does not drive classification or risk; absent cached weights, the service returns fallback metadata. The configured Qwen2.5-3B name is not actually loaded or called: default SLM output is canned templates. Gemini/OpenAI can generate detailed explanations only if explicitly configured with a matching provider and API key; default LLM behavior is deterministic templates.

The working features are document upload, text extraction for supported text-based files, approximate language detection, heuristic segmentation/category/risk analysis, database-backed analysis status/results, React dashboard and demo mode, and PDF/JSON/CSV exports. Still missing or unverified are OCR, CUAD data/training/fine-tuning, a trained clause classifier, active SLM inference, default external LLM inference, validated Indic translation quality, benchmark metrics, production deployment status, and legal reliability. Treat all risk outputs as preliminary flags for qualified human/legal review.
