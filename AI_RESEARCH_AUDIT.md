# AI Research Audit — IntelliFIR Platform

**Document Version:** 1.0.0  
**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  
**Target Venue:** IEEE International Conference on Natural Language Processing / Applied Artificial Intelligence  
**Audit Date:** November 2026  

---

## 1. Executive Summary

IntelliFIR is designed as an evidence-grounded, human-in-the-loop legal assistive system that transforms unstructured citizen complaints into structured First Information Report (FIR) drafts while enforcing strict factual grounding. 

This audit evaluates the pre-transformation codebase across backend architectures, machine learning models, factual validation mechanisms, and evaluation pipelines to establish the empirical baseline and outline the required enhancements for publication-grade research rigor.

---

## 2. Existing AI Architecture

Prior to this transformation, the system comprised:
1. **Document Ingestion**:
   - `file_extractor.py`: Multi-format text ingestion (PDF via `pdfplumber`/`pypdf`, DOCX via `python-docx`, TXT, image via Tesseract OCR).
   - `preprocessing.py`: Rule-based text cleaning and simple whitespace normalization.
2. **Entity & Fact Extraction**:
   - `ner_service.py`: Wraps `dslim/bert-base-NER` via HuggingFace `pipeline("ner")` to detect standard CoNLL categories (`PER`, `LOC`, `ORG`, `MISC`). Rule-based heuristics map `PER` entities to complainant or accused based on simple keyword proximity.
   - `extraction_service.py`: Heuristic regex patterns for extracting incident dates, times, sections, stolen properties, and monetary amounts.
3. **Draft Generation**:
   - `draft_service.py`: Template-driven concatenation combining extracted metadata and unstructured narratives into statutory FIR sections.
4. **Validation Service**:
   - `validation_service.py`: Regex checks for ambiguous phrases (e.g., "sometime back", "around that time"), missing incident times, and basic token overlap.
5. **Retrieval**:
   - `similar_case_service.py` & `legal_service.py`: FAISS vector retrieval using `all-MiniLM-L6-v2` dense embeddings, indexing case summaries and statutory penal codes.

---

## 3. Existing Models and Actual Operational Status

| Component | Configured Artifact / Model | Actual Runtime Implementation | Research Status & Limitation |
|---|---|---|---|
| **Named Entity Recognition** | `dslim/bert-base-NER` | Hugging Face pipeline loaded on CPU/GPU fallback | Generic 4-class CoNLL model. Fails to distinguish legal roles (`COMPLAINANT`, `ACCUSED`, `VICTIM`, `WITNESS`) natively; lacks Indian/Indic name and legal term coverage. |
| **Embeddings & Search** | `sentence-transformers/all-MiniLM-L6-v2` | SentenceTransformer embedding into FAISS IndexFlatIP | Functional for general sentence semantic retrieval; needs evaluation against legal statutory taxonomy (BNS 2023 / IPC 1860). |
| **Factual Validation** | Substring / Regex Checkers | Python string operations and heuristic regex | **Incomplete research mechanism**: Lacks true atomic claim decomposition, Natural Language Inference (NLI) premise-hypothesis entailment verification, and explicit contradiction scoring. |
| **LLM Generation** | Ollama (`llama3.1:8b`) / Fallback template | Conditional HTTP client to local Ollama daemon; falls back to static template | Unguided LLM generation risks hallucination without constrained decoding or claim-level provenance linking. |
| **Evaluation Suite** | `evaluation/run_evaluation.py` | 3 synthetic examples in `sample_dataset.json` with token overlap `>= 0.6` | **Toy evaluation**: Uncalibrated sample size, lack of annotated gold claims, no baseline comparisons, and absence of formal statistical metrics (Precision, Recall, F1, Hallucination Rate, Provenance Alignment). |

---

## 4. Research Limitations Identified

1. **Character Offset Fragility**:
   - Text cleaning in earlier versions mutated whitespace and newlines, causing extracted span character indices `[start, end]` to drift relative to the original complaint document.
2. **Absence of Atomic Claim Decomposition**:
   - The draft was evaluated as a single monolithic block rather than being decomposed into discrete, testable factual propositions ($c_1, c_2, \dots, c_m$).
3. **Absence of Calibrated Entailment & Contradiction Verification**:
   - Factual consistency cannot be established by word overlap alone; a draft stating "The accused was armed with a firearm" when the complaint states "The accused had no weapons" has high lexical overlap but is a critical factual contradiction.
4. **Language Scope**:
   - Focuses on legal English, Native Tamil script, and Tamil-English code-mixed complaints. (Hindi is explicitly excluded from the project scope).
5. **Lack of Rigorous Baseline Benchmarking**:
   - No comparison against zero-shot LLM prompts, standard heuristic templates, or ablation without evidence grounding.

---

## 5. Recommended Architecture for IEEE Publication

```
+-----------------------------------------------------------------------------------------+
|                                    RAW COMPLAINT                                        |
|                     (PDF / DOCX / Scanned Image / Multi-lingual Text)                    |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Offset-Preserving Normalization]
+-----------------------------------------------------------------------------------------+
| Module A: Raw Text Immutability & Document Span Index                                  |
|   - Immutable character buffer C                                                        |
|   - Sentence segmentation with mapped interval coordinates S_k = [s_start, s_end]       |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Hybrid Neural-Symbolic Extraction]
+-----------------------------------------------------------------------------------------+
| Module B & C: Legal Entity Extraction & Evidence Provenance Graph                       |
|   - Legal-domain NER + Rule-based legal ontology parsing                                |
|   - Extracted fact tuple: F_i = (Type, Value, Span, Confidence, ContextWindow)          |
|   - Provenance mapping: C[F_i.start : F_i.end] == F_i.exact_text                        |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Evidence-Constrained Generation]
+-----------------------------------------------------------------------------------------+
| Module D: Claim-Level Controlled FIR Synthesizer                                        |
|   - Structured Statutory Sections (Complainant, Accused, Offence Narrative, Acts)      |
|   - Explicit claim decomposition: Draft D = {c_1, c_2, ..., c_m}                        |
|   - Every claim c_j binds explicitly to evidence span references E(c_j) subset of {F_i}  |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Dual-Engine Fact Verification]
+-----------------------------------------------------------------------------------------+
| Module E: Independent Factual Validation & Entailment Engine                            |
|   - Proposition Extraction & Semantic Alignment                                         |
|   - NLI Entailment & Negation / Contradiction Detection                                |
|   - Claim Status Classification: SUPPORTED | UNSUPPORTED | CONTRADICTED | AMBIGUOUS   |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Uncertainty & Decision Support]
+-----------------------------------------------------------------------------------------+
| Module F: Uncertainty Quantification & Investigative Clarification Engine               |
|   - Missing Essential Elements (Jurisdiction, Offence Elements, Modus Operandi)         |
|   - Officer Clarification Questionnaire Generator                                       |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼ [Statutory Grounding]
+-----------------------------------------------------------------------------------------+
| Module G: Bharatiya Nyaya Sanhita (BNS 2023) / BNSS / BSA Retrieval Engine              |
|   - Statutory Code Linking with Penal Sanctions & Cognizability Flags                   |
+-----------------------------------------------------------------------------------------+
```

---

## 6. Prioritized Implementation Plan

1. **Phase 1 — Audit & Architectural Formalization**: Establish mathematical model and empirical objectives.
2. **Phase 2 — Immutable Offset Normalization & Domain Extraction**: Guarantee `raw_text[start:end] == span_text` invariant; extend entity taxonomy to legal roles.
3. **Phase 3 — Claim-Level Controlled Draft Generation**: Generate drafts with atomic claims tagged with explicit evidence span IDs; add PDF/DOCX generation.
4. **Phase 4 — Factual Entailment & Contradiction Engine**: Implement formal claim verification classifying claims into `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, and `AMBIGUOUS`.
5. **Phase 5 — Uncertainty Quantification & Clarification Engine**: Generate diagnostic questions for investigative gaps.
6. **Phase 6 — Legal Statutory Retrieval**: Upgrade legal retrieval to BNS 2023, BNSS 2023, and BSA 2023 alongside IPC 1860 historical mappings.
7. **Phase 7 & 8 — Annotated Benchmark Dataset & Reproducible Evaluation**: Build 25+ diverse, multi-crime scenario gold benchmark; evaluate Baseline A (Zero-shot LLM), Baseline B (Standard Template), and IntelliFIR (Evidence-Grounded Pipeline); calculate PRF, Unsupported Claim Rate (UCR), Contradiction Rate (CR), and Human Review Latency reduction.
8. **Phase 9 — Test Suite**: Comprehensive pytest coverage across all modules.
