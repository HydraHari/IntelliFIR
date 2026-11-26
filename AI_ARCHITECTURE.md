# AI Architecture Specification: Evidence-Grounded and Uncertainty-Aware FIR Generation and Validation

**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  
**Target Category:** AI/NLP Applied Research (IEEE AI / NLP Track)  
**Document Version:** 1.0.0  

---

## 1. Research Question and Mathematical Formalization

### 1.1 Core Problem Statement
Given an unstructured citizen complaint $C = \langle t_1, t_2, \dots, t_N \rangle$ of characters $t_i$, the objective is to generate a structured First Information Report (FIR) draft $D$ consisting of $m$ discrete factual claims $D = \{ c_1, c_2, \dots, c_m \}$, such that:
1. **Evidence Grounding:** Every claim $c_j \in D$ is supported by an identifiable evidence span $E(c_j) \subset C$.
2. **Hallucination Minimization:** The unsupported claim rate $\mathcal{R}_{\text{unsupported}}(D, C) \to 0$.
3. **Contradiction Elimination:** No claim $c_j \in D$ contradicts any proposition in $C$.
4. **Information Completeness:** All legally essential elements $\mathcal{K}_{\text{statutory}}$ present in $C$ are retained in $D$.
5. **Human Review Transparency:** All uncertainties, ambiguous statements, and missing statutory elements are presented as structured investigative clarification prompts.

### 1.2 Mathematical Formulation of Evidence Provenance
Let $C$ denote the raw, immutable complaint text of length $|C|$.
An extracted evidence span $s$ is defined as a 4-tuple:
$$s = (k, \tau, \sigma_{\text{start}}, \sigma_{\text{end}})$$
where:
- $k \in \{\text{COMPLAINANT}, \text{ACCUSED}, \text{VICTIM}, \text{WITNESS}, \text{LOCATION}, \text{DATE\_TIME}, \text{STOLEN\_PROPERTY}, \text{OFFENCE\_ACT}, \text{EVIDENCE\_ITEM}\}$ represents the legal entity/relation category.
- $\sigma_{\text{start}}, \sigma_{\text{end}} \in \mathbb{N}$ are exact 0-indexed character offsets satisfying $0 \le \sigma_{\text{start}} < \sigma_{\text{end}} \le |C|$.
- $\tau = C[\sigma_{\text{start}} : \sigma_{\text{end}}]$ satisfies strict Python Unicode character (codepoint) alignment. (Byte-level slicing is avoided to ensure multi-byte character integrity).

Let $\mathcal{F} = \{ s_1, s_2, \dots, s_K \}$ denote the set of extracted factual spans from $C$.

### 1.3 Claim Decomposition and Factual Validation Engine
The draft $D$ is partitioned into atomic claims:
$$D \equiv \bigcup_{j=1}^m c_j$$
where each claim $c_j$ represents an atomic, non-decomposable propositional statement (e.g., *"The accused struck the complainant with an iron rod"*).

For each claim $c_j$, an alignment function $\alpha(c_j, \mathcal{F})$ identifies candidate evidence spans:
$$\mathcal{S}_j = \{ s \in \mathcal{F} \mid \text{Sim}(c_j, s) \ge \theta_{\text{align}} \}$$

The verification operator $\mathcal{V}(c_j, C)$ evaluates the claim under Natural Language Inference (NLI) principles:
$$\mathcal{V}(c_j, C) = \begin{cases} 
\text{SUPPORTED} & \text{if } P(\text{Entailment} \mid c_j, \mathcal{S}_j) \ge \tau_{\text{entail}} \\
\text{CONTRADICTED} & \text{if } P(\text{Contradiction} \mid c_j, C) \ge \tau_{\text{contra}} \\
\text{AMBIGUOUS} & \text{if } \mathcal{H}(c_j) \ge \tau_{\text{entropy}} \lor \text{VaguePredicate}(c_j) \\
\text{UNSUPPORTED} & \text{otherwise}
\end{cases}$$

---

## 2. Pipeline Modules Architecture

```
                          ┌────────────────────────┐
                          │   Citizen Complaint    │
                          │ (PDF, DOCX, TXT, OCR)  │
                          └───────────┬────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module A: Normalization   │
                        │ & Invariant Offset Map    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module B: Legal NER &     │
                        │ Relation Extraction       │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module C: Evidence Span   │
                        │ Provenance Graph          │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module D: Claim-Level     │
                        │ Controlled FIR Generator  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module E: Factual NLI &   │
                        │ Contradiction Validator   │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module F: Uncertainty &   │
                        │ Clarification Engine      │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Module G: Statutory BNS / │
                        │ Case Retrieval (FAISS)    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Human Review & PDF Export │
                        │ (Station House Officer)   │
                        └───────────────────────────┘
```

### Module A — Complaint Ingestion & Preprocessing
- Maintains two representations: `raw_text` (strictly immutable) and tokenized sentence spans $S_k = [start, end]$.
- Language detection identifies English, Native Tamil script, and Tamil-English code-mixed complaints. (Hindi / Devanagari is explicitly excluded from scope).
- Sentence boundary detection maps character spans directly to `raw_text` Unicode codepoint offsets.

### Module B & C — Legal Entity Extraction & Evidence Provenance
- Extended entity taxonomy:
  - `COMPLAINANT`: Person reporting the offence.
  - `ACCUSED`: Named suspect or known accused.
  - `UNKNOWN_ACCUSED`: Explicit references to unidentified perpetrators.
  - `VICTIM`: Person who suffered harm/loss.
  - `WITNESS`: Eyewitnesses or persons present.
  - `LOCATION`: Place of occurrence.
  - `DATE_TIME`: Temporal anchor of occurrence.
  - `STOLEN_PROPERTY`: Objects, cash, or vehicles misappropriated.
  - `OFFENCE_ACT`: Verbs/predicates denoting criminal action (assault, theft, trespass, fraud).
  - `WEAPON_USED`: Instruments of crime.
  - `INJURY_DAMAGE`: Physical hurt or financial loss described.
- **Span Verification Invariant**:
  $$\forall s \in \mathcal{F}, \quad \text{raw\_text}[s.\sigma_{\text{start}} : s.\sigma_{\text{end}}] \equiv s.\tau$$

### Module D — Claim-Level Controlled Draft Synthesizer
- Constrained generation generates an FIR partitioned into legal sections:
  1. *Complainant Particulars*
  2. *Details of Known / Suspected / Unknown Accused*
  3. *Date, Time, and Place of Occurrence*
  4. *Factual Narrative of Offence (Statement of Facts)*
  5. *Particulars of Property Involved*
  6. *Applicable Penal Sections (BNS 2023 / IPC 1860)*
- Each sentence within the factual narrative is emitted with explicit references to the evidence span IDs that ground it.

### Module E — Independent Factual Validation Engine
- Performs rigorous claim verification:
  - Proposition extraction splits each draft sentence into atomic assertions.
  - Alignment matches each assertion with its linked evidence span and surrounding context window.
  - Lexical, semantic, and polarity verification checks whether the claim asserts facts not present in the evidence.
  - Contradiction detector identifies numeric discrepancies (e.g. ₹5,000 claimed vs ₹50,000 in complaint), negation mismatch ("unarmed" vs "armed with knife"), and temporal discrepancies.

### Module F — Uncertainty & Clarification Engine
- Analyzes missing legal requisites:
  - Missing precise time of occurrence.
  - Missing specific location/jurisdiction anchor.
  - Unidentified suspect descriptions (physical features, vehicle numbers, direction of escape).
  - Ambiguous statements (e.g., "many people attacked me", "lost valuable items").
- Outputs structured question prompts for the investigating officer during complainant examination.

### Module G — Legal & Similar-Case Retrieval
- Statutory mapping:
  - Dual coverage of **Bharatiya Nyaya Sanhita, 2023 (BNS)** and **Indian Penal Code, 1860 (IPC)**.
  - Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) procedure references (e.g., Sec 173 BNSS for FIR registration).
  - Bharatiya Sakshya Adhiniyam, 2023 (BSA) for electronic and documentary evidence rules.
- FAISS cosine similarity retrieval over penal code descriptions and past FIR precedent dockets.

---

## 3. Autonomous AI Investigation Agent Architecture

### 3.1 Overview and Purpose
The IntelliFIR AI Investigation Agent upgrades the legacy single-turn RAG assistant into an autonomous, tool-using multi-step agent. Designed specifically for law enforcement investigators, the agent dynamically decomposes natural-language investigation directives, selects targeted tools, executes sequential workflows, checks data provenance, identifies contradictions, grounds statutory findings, and produces structured investigation reports.

### 3.2 Agent Core Architecture

```
                  ┌───────────────────────────────────────────────┐
                  │      Investigator Natural Language Query      │
                  │   ("Analyse CMP-001, find contradictions...")  │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                  ┌───────────────────────────────────────────────┐
                  │     Investigation Agent Orchestrator          │
                  │  - Intent Recognition & Goal Planning         │
                  │  - Consequential Action Safety Guardrail       │
                  │  - Dynamic Tool Selector                      │
                  │  - Execution State & Telemetry Log            │
                  └───────┬───────────────┬───────────────┬───────┘
                          │               │               │
     ┌────────────────────┴───┐   ┌───────┴────────┐   ┌──┴─────────────────────┐
     ▼                        ▼   ▼                ▼   ▼                        ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    TOOL A    │ │    TOOL B    │ │    TOOL C    │ │    TOOL D    │ │    TOOL E    │ │    TOOL F    │
│  Complaint   │ │   Evidence   │ │   Factual    │ │    Legal     │ │ Similar Case │ │Investigation │
│   Analysis   │ │  Provenance  │ │  Validation  │ │   Research   │ │  Retrieval   │ │    Report    │
│  (Entities & │ │ (Offset In-  │ │(Contradiction│ │  (BNS/BNSS/  │ │ (FAISS Vector│ │  (Structured │
│ Allegations) │ │   variants)  │ │   & Gaps)    │ │  BSA Corpus) │ │  Precedents) │ │   Synthesis) │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │                │                │
       └────────────────┴────────────────┼────────────────┴────────────────┴────────────────┘
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │     Evidence-Grounded Response Synthesis      │
                  │  - Strict Provenance Invariant Check          │
                  │  - Applicable BNS 2023 Provisions             │
                  │  - Precedent Case Modus Operandi              │
                  │  - Contextual Investigator Inquiries          │
                  │  - Mandatory Human-in-the-Loop Review Notice  │
                  └───────────────────────────────────────────────┘
```

### 3.3 The 6 Agent Tools
1. **TOOL A – Complaint Analysis (`analyze_complaint`):** Retrieves complaint by UUID or human-readable reference (e.g. `CMP-001`). Extracts complainant, accused parties, victims, witnesses, incident date/time, location, property, and weapons. Distinguishes established facts from unverified allegations.
2. **TOOL B – Evidence Provenance (`verify_evidence_provenance`):** Audits character offsets $[ \sigma_{\text{start}}, \sigma_{\text{end}} ]$ against the raw text. Enforces the strict invariant:
   $$\text{raw\_text}[\sigma_{\text{start}} : \sigma_{\text{end}}] \equiv \text{span\_text}$$
   Flags unsupported facts and offset drifts.
3. **TOOL C – Factual Validation (`validate_complaint_facts`):** Decoupled validation engine checking for missing statutory elements (date, time, jurisdiction), timeline inconsistencies, numeric contradictions, and unsupported claims. Emits severity-tiered findings (`high`, `medium`, `low`) with actionable police recommendations.
4. **TOOL D – Legal Research (`research_legal_provisions`):** Grounded search over the Bharatiya Nyaya Sanhita (BNS 2023), BNSS 2023, and BSA 2023 statutory corpus with historical IPC correspondences. Never invents non-existent sections.
5. **TOOL E – Similar Case Retrieval (`retrieve_similar_cases`):** Semantic vector search across previous case records using `all-MiniLM-L6-v2` embeddings and FAISS. Returns cosine similarity scores and attaches mandatory statutory disclaimers noting that similarity does not establish guilt.
6. **TOOL F – Investigation Report Generator (`generate_investigation_report`):** Aggregates findings from Tools A–E into a structured markdown Investigation Support Report with human review controls.

### 3.4 Consequential Action Guardrail and Safety Governance
To prevent unlawful autonomous law enforcement actions:
- **Statutory Guardrail:** Substantive criminal justice actions (FIR registration, arrest warrants, case dismissal, guilt/innocence declarations) are blocked by automated regex and policy checks.
- **Human-in-the-Loop:** The agent operates exclusively in a decision-support advisory capacity. Formal registration requires explicit manual confirmation by the Investigating Officer under Section 173 BNSS.

