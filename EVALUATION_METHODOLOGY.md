# Evaluation Methodology: IntelliFIR Benchmark Protocol

**Document Version:** 1.0.0  
**Research Title:** Evidence-Grounded and Uncertainty-Aware Natural Language Processing for Complaint-to-FIR Draft Generation and Factual Validation  

---

## 1. Experimental Design & Objectives

The primary research objective is to empirically validate whether evidence-grounded extraction, controlled claim generation, and independent factual validation reduce unsupported statements and prevent hallucinations when converting unstructured citizen complaints into structured First Information Report (FIR) drafts.

### Systems Evaluated:
1. **Baseline A (Direct Unconstrained Generative LLM):**  
   Simulates zero-shot prompting of commercial / open-weights LLMs instructed to directly convert complaints into formal FIRs without intermediate evidence extraction or constraint decoding.
2. **Baseline B (Heuristic Slot-Filling Template):**  
   Simulates standard legal administrative templates that populate predefined slots using regex heuristics without provenance binding or validation checks.
3. **Ablation 1 (IntelliFIR w/o Evidence Provenance):**  
   IntelliFIR pipeline without character-level span bindings.
4. **Ablation 2 (IntelliFIR w/o Independent Factual Validation):**  
   IntelliFIR pipeline without secondary NLI contradiction and ambiguity detection.
5. **IntelliFIR Proposed System:**  
   The complete architecture combining offset-preserving normalization, legal ontology extraction, claim-level controlled generation, dual-engine factual validation, and uncertainty quantification.

---

## 2. Formal Metric Formulations

### 2.1 Entity Extraction Precision, Recall, and F1
Let $\mathcal{P}$ denote the set of predicted entity tuples and $\mathcal{G}$ denote the gold standard annotated entities:
$$\text{Precision} = \frac{|\mathcal{P} \cap \mathcal{G}|}{|\mathcal{P}|}, \quad \text{Recall} = \frac{|\mathcal{P} \cap \mathcal{G}|}{|\mathcal{G}|}, \quad F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 2.2 Supported Claim Rate (SCR)
Given a generated draft $D = \{ c_1, c_2, \dots, c_m \}$ decomposed into $m$ testable propositional claims, and raw complaint $C$:
$$\text{SCR}(D, C) = \frac{1}{m} \sum_{j=1}^m \mathbf{1}\left[ \text{Grounded}(c_j, C) \right]$$
where $\text{Grounded}(c_j, C) = 1$ if substantive factual content tokens in $c_j$ are entailed by evidence in $C$.

### 2.3 Unsupported Claim Rate (UCR / Hallucination Rate)
$$\text{UCR}(D, C) = 1 - \text{SCR}(D, C) = \frac{1}{m} \sum_{j=1}^m \mathbf{1}\left[ \neg\text{Grounded}(c_j, C) \right]$$

### 2.4 Contradiction Detection F1 ($F_{1}^{\text{contra}}$)
Measures the system's ability to detect conflicting assertions (e.g., "unarmed" vs. "knife", clashing calendar dates, or inconsistent financial amounts):
$$F_{1}^{\text{contra}} = \frac{2 \cdot P_{\text{contra}} \cdot R_{\text{contra}}}{P_{\text{contra}} + R_{\text{contra}}}$$

### 2.5 Provenance Invariant Pass Rate ($\Phi_{\text{provenance}}$)
Measures the character-level integrity of the extracted evidence spans against the immutable source document buffer using Python Unicode codepoint indexing:
$$\Phi_{\text{provenance}} = \frac{1}{|\mathcal{S}|} \sum_{s \in \mathcal{S}} \mathbf{1}\left[ C[s.\sigma_{\text{start}} : s.\sigma_{\text{end}}] \equiv s.\tau \right]$$
A score of $1.0000$ indicates zero character offset drift across all extractions.

### 2.6 Human Review Efficiency Gain ($\Delta T_{\text{review}}$) — Pilot Estimate
Estimated reduction in review time for station house officers based on pilot simulations:
$$\Delta T_{\text{review}} = \frac{T_{\text{manual}} - T_{\text{IntelliFIR}}}{T_{\text{manual}}} \times 100\%$$
*Note:* This metric is reported as an unvalidated preliminary pilot estimate (~68% reduction). A formal randomized controlled trial with police personnel adhering to IRB guidelines is required for clinical/field verification.
