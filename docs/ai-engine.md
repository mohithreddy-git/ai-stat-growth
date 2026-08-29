# AI engine and assessment studio

## Provider boundary

`backend/app/ai/providers.py` defines `LLMProvider` with `generate_text()` and `generate_structured()`. Implementations are:

- `MockProvider`: deterministic, zero-cost fallback.
- `OllamaProvider`: optional local model through Ollama.
- `OpenAICompatibleProvider`: optional compatible endpoint using environment configuration.

External providers are never mandatory. Structured output is passed through Pydantic validation; malformed output raises a provider error and the feature can continue through deterministic fallback.

## Source-grounded pipeline

```text
Upload
 → extension/MIME/size validation
 → local storage
 → text extraction
 → page/slide metadata
 → normalized chunks
 → local lexical retrieval boundary
 → structured question candidate
 → Pydantic validation
 → source support and duplicate checks
 → PENDING_REVIEW
 → trainer/admin approval
 → publish
```

PDF extraction uses `pypdf` when available and a lightweight local fallback for simple text PDFs. DOCX and PPTX are extracted with the standard library ZIP/XML modules. The prototype keeps chunk text and document/chunk/page/slide provenance in the database.

## Question quality

`QuestionQualityValidator` checks:

- exactly four options;
- unique, non-empty options;
- correct index in `0..3`;
- allowed difficulty;
- non-empty source and explanation;
- competency existence at persistence time;
- source-text support;
- duplicate question detection;
- answer-leakage heuristic.

Every generated item starts as `PENDING_REVIEW`. Only `APPROVED` items can be placed in `PublishedQuiz`. Review actions create both `AssessmentItemReview` and `AuditLog` records.

## RAG boundary

The current retrieval implementation is local and deterministic. It is intentionally replaceable with FAISS, a vector database, or an embedding service. `retrieve_chunks()` is the seam for that replacement. StatBot document mode cites the selected chunk IDs and never presents a general answer as document-grounded evidence.

## Limitations

This is not a government-certified AI service. No official FRAC catalogue or live iGOT/NSSTA endpoint is connected. Production should add malware scanning, object storage, OCR, stronger semantic/source verification, model observability, content governance, multilingual evaluation, and a reviewed vector store.
