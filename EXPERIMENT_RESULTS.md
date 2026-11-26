# Experiment Results: Comparative Evaluation of IntelliFIR Pipeline

**Document Version:** 2.0.0 (Corrected & Independently Audited)  
**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  
**Evaluation Dates:** Initial Audit: November 2026 | Corrected Re-evaluation: November 2026  
**Language Scope:** English, Native Tamil script (`\u0B80-\u0BFF`), and Tamil-English code-mixed text. *(Hindi is explicitly excluded from scope).*  
**Indexing Convention:** Python 3 Unicode code point indices (`str[start:end]`). *(Byte-level UTF-8 indexing is not used).*  

---

## 1. Comparative Evaluation: Original vs. Corrected Benchmark

The table below contrasts the previously reported (unverified/flawed) metrics against the independently audited, reproducible results produced by [`backend/evaluation/run_evaluation.py`](file:///Users/personal/PROJECTS/Intelli_Fir/backend/evaluation/run_evaluation.py) saved in `backend/evaluation_results_corrected.json`.

| System / Configuration | Supported Claim Rate (Facts) ↑ | Unsupported Claim Rate (Facts) ↓ | Hallucination Rate ↓ | Contradiction Micro $F_1$ ↑ | Ambiguity Micro $F_1$ ↑ | Missing Info Micro $F_1$ ↑ | Provenance Pass Rate ↑ |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline A (Direct LLM - Original Flawed)** | 0.2027 | 0.7973 | 0.7984* | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **Baseline A (Direct LLM - Corrected Unhobbled)** | **0.2080** | **0.7920** | **0.7920** | **0.0000** | **0.0000** | **0.0000** | **0.0000** |
| **Baseline B (Template)** | 0.3600 | 0.6400 | 0.0500 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **Ablation 1: w/o Provenance (Original Flawed)** | 0.7137* | 0.2863* | 0.1200* | 1.0000* | 1.0000* | 0.6733 | 0.0000 |
| **Ablation 1: w/o Provenance (Real Code Ablation)** | **0.8542** | **0.1458** | N/A | 0.6667 | 0.9333 | 0.7273 | **0.0000** |
| **Ablation 2: w/o Validation (Original Flawed)** | 0.8337* | 0.1783* | 0.0800* | 0.0000 | 0.0000 | 0.6733 | 1.0000 |
| **Ablation 2: w/o Validation (Real Code Ablation)** | **0.8542** | **0.1458** | N/A | **0.0000** | **0.0000** | 0.0000 | **1.0000** |
| **IntelliFIR Proposed (Original Flawed)** | 0.8337 | 0.1663 | 0.0000* | 1.0000* | 1.0000* | 0.6733* | 1.0000 |
| **IntelliFIR Proposed (Corrected Audit)** | **0.8542** | **0.1458** | **0.0000** | **0.6667** | **0.9333** | **0.7273** | **1.0000** |

*\*Note on Flawed Baselines & Metrics:*  
- *Baseline A original had an artificial knife claim manually injected via code.*
- *Original Ablations 1 & 2 were hardcoded arithmetic (`-0.12`, `+0.15`).*
- *Original Contradiction and Ambiguity $F_1 = 1.0$ were artifacts of awarding $1.0$ to true negative instances ($0/0$).*

---

## 2. Multilingual Benchmark Performance (English + Native Tamil)

Evaluated on the expanded 30-case benchmark ([`backend/evaluation/benchmark_dataset_multilingual.json`](file:///Users/personal/PROJECTS/Intelli_Fir/backend/evaluation/benchmark_dataset_multilingual.json)), containing 25 English cases, 4 Native Tamil script cases (`\u0B80-\u0BFF`), and 1 Tamil-English code-mixed case:

| Metric | Corrected Measured Score | 95% Bootstrap CI | Notes |
|---|:---:|:---:|---|
| **Entity Extraction Precision** | **0.7240** | [0.635, 0.805] | Improved with location indicator disambiguation. |
| **Entity Extraction Recall** | **0.9433** | [0.890, 0.985] | High coverage across English and Tamil named entities. |
| **Entity Extraction Macro $F_1$** | **0.8031** | [0.730, 0.865] | Macro average across Person, Location, Date, Time. |
| **Supported Claim Rate (Fact Tuples)** | **0.8128** | [0.775, 0.850] | Measured on extracted structured legal propositions. |
| **Supported Claim Rate (Full Draft Prose)** | **0.1093** | [0.085, 0.135] | Reflects raw sentence overlap; template administrative prose is ungrounded by design. |
| **Contradiction Detection Micro $F_1$** | **0.6667** | [0.400, 0.900] | Correctly flags conflicting dates, weapon denials, and financial revisions. |
| **Ambiguity Detection Micro $F_1$** | **0.9000** | [0.750, 1.000] | Flags vague timelines and subjective suspicions in English and Tamil. |
| **Missing Information Micro $F_1$** | **0.7333** | [0.580, 0.860] | Accurately identifies missing date, time, and locus of offence. |
| **Provenance Invariant Pass Rate** | **1.0000 (100.0%)** | [1.000, 1.000] | $\text{raw}[s:e] == \text{span}$ across all English and native Tamil text. |

---

## 3. Human Review Efficiency Evaluation

- **Reported Pilot Estimate:** **~68% reduction** in draft preparation time.
- **Scientific Audit Status:** **UNVALIDATED PILOT ESTIMATE.**
- **Peer-Review Transparency Statement:**  
  No formal randomized human-subject trial with police officers or Station House Officers has been completed to date. The figure represents a preliminary pilot projection based on a 4-subject internal simulation comparing manual entry against interactive validation assistance. A formal field trial adhering to IRB / ethics standards is planned as pre-deployment validation.
