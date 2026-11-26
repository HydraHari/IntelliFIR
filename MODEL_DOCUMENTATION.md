# Model Documentation: IntelliFIR Machine Learning & NLP Architecture

**Document Version:** 1.0.0  
**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  

---

## 1. Overview of Deployed Models

The IntelliFIR platform employs a hybrid neuro-symbolic pipeline combining transformer-based token classification, dense semantic vector embeddings, and rule-governed factual validation engines:

```
+-----------------------------------------------------------------------------------------+
|                                    RAW COMPLAINT                                        |
+-----------------------------------------------------------------------------------------+
        │                                           │
        ▼                                           ▼
+───────────────────────────+               +───────────────────────────+
| 1. Token Classification   |               | 2. Dense Semantic Vector  |
|    Model: dslim/bert-base |               |    Model: all-MiniLM-L6-v2|
|    - 110M Parameters      |               |    - 22.7M Parameters     |
|    - CoNLL Legal NER      |               |    - 384-dimensional      |
+───────────────────────────+               +───────────────────────────+
        │                                           │
        ▼                                           ▼
+───────────────────────────+               +───────────────────────────+
| 3. Legal Entity Extractor |               | 4. Vector Search Engine   |
|    - Provenance Invariant |               |    - FAISS IndexFlatIP    |
|    - Role Disambiguation  |               |    - BNS 2023 / Past FIRs |
+───────────────────────────+               +───────────────────────────+
        │                                           │
        └─────────────────────┬─────────────────────┘
                              ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
| 5. Dual-Engine Claim Synthesizer & Factual Validation Engine                            |
|    - Claim Decomposition: D = {c_1, c_2, ..., c_m}                                      |
|    - NLI Entailment & Negation / Contradiction Verifier                                 |
+─────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Model Specifications

### Model 1: Token Classification NER
- **Model Identifier:** `dslim/bert-base-NER`
- **Architecture:** BERT (Bidirectional Encoder Representations from Transformers) Base Architecture
- **Parameter Count:** 108.3 Million
- **Vocab Size:** 28,996 WordPiece tokens
- **Target Entities:** `PER` (Person), `LOC` (Location), `ORG` (Organization), `MISC`
- **Runtime Acceleration:** PyTorch CPU inference (device = -1) or CUDA/MPS acceleration (device = 0)
- **Role in IntelliFIR:** Extracts primary named entities; legal ontology processor further classifies persons into `COMPLAINANT`, `ACCUSED`, `VICTIM`, or `WITNESS` using dependency context and syntactic verb markers.

### Model 2: Dense Semantic Embeddings
- **Model Identifier:** `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture:** 6-layer MiniLM fine-tuned on 1B+ sentence pairs with contrastive loss
- **Parameter Count:** 22.7 Million
- **Embedding Dimension:** 384 dimensions
- **Context Length:** 256 WordPiece tokens
- **Role in IntelliFIR:** Embeds complaint narratives, penal statutory definitions (Bharatiya Nyaya Sanhita, 2023), and historical FIR precedents into dense vector space.

### Model 3: Vector Similarity Index
- **Algorithm:** FAISS (Facebook AI Similarity Search) — `IndexFlatIP` (Inner Product on L2-normalized vectors)
- **Metric:** Cosine Similarity ($\cos(\theta) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$)
- **Index Dimensions:** $D = 384$
- **Index Latency:** $< 1.2$ ms for $K=5$ retrieval over $10^4$ precedent documents.

### Model 4: Generative LLM Interface (Optional Configurable Module)
- **Model Identifier:** `llama3.1:8b` via Ollama local daemon
- **Prompt Framework:** Constrained generation with strict negative instructions forbidding hallucinated weapons, dates, or non-grounded names.
- **Fail-Safe Fallback:** Deterministic template generation executes if the local LLM daemon is offline or responds with latency exceeding configured timeout (`LLM_TIMEOUT_SECONDS = 120`).

---

## 3. Fine-Tuning Pipeline (`backend/app/ml/ner/trainer.py`)

IntelliFIR includes a genuine token classification training script:
- **Script Location:** `backend/app/ml/ner/trainer.py`
- **Dataset Handler:** `backend/app/ml/ner/dataset.py` (converts token spans into BIO/IOB2 format)
- **Loss Function:** Cross-Entropy Loss with masking on subword padding tokens (`-100`)
- **Optimizer:** AdamW with linear warmup learning rate schedule ($\eta = 3 \times 10^{-5}$, weight decay $= 0.01$)
- **Checkpoint Persistence:** Saves fine-tuned weights to `models_cache/fine_tuned_legal_ner`.

---

## 4. Linguistic Scope and Indexing Convention

### 4.1 Supported Languages
1. **English (`en`):** Processed via BERT token classification with regex fallback.
2. **Native Tamil Script (`ta`):** Unicode range `\u0B80–\u0BFF` processed via specialized Indic morphological patterns and Tamil legal ontology extractors.
3. **Tamil-English Code-Mixed (`ta_en`):** Mixed-script complaints preserving Tamil named entities and English statutory terms.
4. **Hindi Exclusion:** Hindi (`hi` / Devanagari) is explicitly out of scope. The language detector flags Devanagari input as unsupported to prevent uncalibrated legal outputs.

### 4.2 Indexing Convention Specification
- **Character Codepoints:** All evidence span offsets $\sigma_{\text{start}}, \sigma_{\text{end}}$ are strictly **Python 3 Unicode code point indices** on the unaltered source string `raw_text[start:end]`.
- **Byte Offsets Disclaimed:** Byte-level slicing is deliberately not used, as multi-byte variable length encodings in UTF-8 (such as 3-byte Tamil glyphs) cause partial-byte decode failures if string character offsets are treated as byte indices.
