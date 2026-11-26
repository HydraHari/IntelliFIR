# Dataset Documentation: IntelliFIR Benchmark Corpora

**Document Version:** 2.0.0 (Corrected & Scoped)  
**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  
**Target Venue:** IEEE AI / NLP Research Track  
**Language Scope:** English (`en`), Native Tamil Script (`ta`), and Tamil-English Code-Mixed (`ta_en`). *(Hindi / Devanagari is explicitly excluded from current scope).*  
**Primary Dataset Paths:**  
- `backend/evaluation/benchmark_dataset.json` (Original 25-case baseline)
- `backend/evaluation/benchmark_dataset_multilingual.json` (Augmented 30-case multilingual benchmark)

---

## 1. Corpus Overview

The IntelliFIR Benchmark Corpora were constructed to empirically assess the transformation of unstructured citizen complaints into structured First Information Report (FIR) drafts under Indian criminal jurisprudence (Bharatiya Nyaya Sanhita, 2023).

### Corpus Variants:
1. **Standard Baseline Corpus (`benchmark_dataset.json`):**  
   - 25 cases covering diverse cognizable offences (burglary, robbery, snatching, assault, cyber fraud, extortion, criminal intimidation).
   - Serves as the standardized regression benchmark for pipeline components.
2. **Multilingual Scoped Corpus (`benchmark_dataset_multilingual.json`):**  
   - 30 cases: the 25 standard cases plus 5 native Tamil script and Tamil-English code-mixed complaints from Chennai, Madurai, and Coimbatore jurisdictions.
   - Evaluates cross-lingual transfer, script preservation, and Unicode codepoint indexing invariance.

---

## 2. Linguistic Scope and Indexing Invariants

### 2.1 Language Policy
- **Included Languages:**
  - **English (`en`):** Formal and colloquial police complaint narratives.
  - **Native Tamil Script (`ta`):** Complaints authored in Unicode block `U+0B80–U+0BFF`.
  - **Tamil-English Code-Mixed (`ta_en`):** Mixed-script statements commonly filed in urban Tamil Nadu police stations.
- **Excluded Languages:**
  - **Hindi (`hi` / Devanagari):** Explicitly excluded from the current experimental pipeline. The language detector flags Devanagari input as unsupported.

### 2.2 Indexing Convention Invariant
All character spans $\sigma_{\text{start}}, \sigma_{\text{end}}$ represent **Python 3 Unicode code point indices** in the immutable complaint string buffer:
$$\forall s \in \mathcal{F}, \quad 0 \le s.\sigma_{\text{start}} < s.\sigma_{\text{end}} \le \text{len}(C) \quad \land \quad C[s.\sigma_{\text{start}} : s.\sigma_{\text{end}}] \equiv s.\tau$$
*Note:* Byte-level offsets are explicitly avoided because UTF-8 variable-length encodings (e.g. 3 bytes per Tamil grapheme) lead to slice decode corruption if treated as string offsets.

---

## 3. Anomaly & Factual Consistency Annotations

Each complaint in the benchmark includes explicit gold annotations for:
1. `gold_entities`: Named entities with exact text and semantic legal type.
2. `gold_facts`: Canonical legal fact attributes (Complainant, Accused, Date, Time, Location, Offence Act, Weapon, Loss, Property, Injury, Evidence).
3. `gold_missing_facts`: Mandatory statutory elements omitted in the complaint (e.g., date, time, crime scene jurisdiction).
4. `gold_contradictions`: Conflicting assertions within the narrative (e.g., clashing calendar dates, unarmed statement accompanied by weapon allegation, contradictory financial loss figures).
5. `gold_ambiguities`: Vague temporal references ("sometime back", "சில நாட்களுக்கு முன்") or subjective speculation without evidence ("suspect that", "சந்தேகம் உள்ளது").
6. `gold_bns_sections`: Statutory penal sections under Bharatiya Nyaya Sanhita, 2023.

---

## 4. Known Dataset Limitations

1. **Synthetic Generation:** Benchmark instances were synthetically authored rather than extracted directly from live police station dockets to protect citizen privacy and avoid ongoing trial sub judice concerns.
2. **Positive Anomaly Sparsity:** In the 25-case baseline, contradictions occur in 2 cases (8%) and ambiguities in 4 cases (16%). Dataset-level Micro metrics must be reported alongside sample-level metrics to prevent class-imbalance distortion.
