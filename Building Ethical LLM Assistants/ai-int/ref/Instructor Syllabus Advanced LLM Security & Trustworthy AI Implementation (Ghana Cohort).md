 

NotebookLM
==========

Exported on: 14/06/2026, 17:58:43

Instructor Syllabus: Advanced LLM Security & Trustworthy AI Implementation (Ghana Cohort)

1\. Course Overview & Ghanaian Context

This course serves as a technical and ethical roadmap for transitioning AI implementations from "Stochastic Parrots"—models that generate statistically probable but ungrounded text—to trustworthy, observable, and grounded systems. By integrating the **OWASP Top 10 for LLM Applications (2025)** and the **NVIDIA NeMo Guardrails** framework, students will learn to architect systems that prioritize security and factual integrity.

In the Ghanaian context, this curriculum is specifically designed to address regional challenges such as linguistic variety and high-stakes decision-making. Following the principles of the LLM Ethics Whitepaper, the course emphasizes **Indigenous Data Sovereignty**, ensuring that AI development for local languages (such as Twi, Ga, or Ewe) respects data ownership and power relations. The instructor’s mission is to guide students in building AI solutions that are technically rigorous, ethically proactive, and environmentally conscious.

2\. Learning Objectives: The Grounding Paradigm ShiftUpon completion of this course, participants will be able to:

*   **Identify OWASP LLM09:2025 (Misinformation):** Diagnose the root causes of misinformation, specifically "Hallucination" (statistical pattern filling) and "Overreliance" (excessive user trust).
*   **Architect Grounded RAG Systems:** Lead the architectural transition from a "Black Box" Base LLM to a Retrieval-Augmented Generation (RAG) system utilizing the RAG Triad for evaluation.
*   **Implement Active Guardrails:** Deploy NVIDIA NeMo Guardrails to establish topic alignment, prevent sensitive info disclosure (LLM02), and block prompt injections (LLM01).
*   **Quantify Observability and Economics:** Integrate Grafana to visualize the causal link between guardrail intercepts and **Token Savings**, mitigating "Unbounded Consumption" (LLM10).
*   **Apply Three-Dimensional Assessments:** Evaluate projects based on technical robustness, ethical alignment (including stakeholder engagement), and observability metrics.

3\. Module 1: The Core Vulnerability — OWASP LLM09 (Misinformation)OWASP LLM09:2025 Misinformation occurs when an LLM produces false, misleading, or fabricated content that appears credible. This risk is amplified in systems where users delegate critical decision-making to the model.Causes of MisinformationCause of MisinformationTechnical DescriptionThe model fills gaps in training data using statistical patterns, generating fabricated content that lacks a foundation in reality.Users place excessive trust in LLM outputs, failing to verify accuracy and integrating incorrect data into high-stakes workflows.Regional ImpactIn Ghana, misinformation in sectors like healthcare or legal proceedings carries severe risks. As noted in the source context, "Misrepresentation of Expertise" can lead LLMs to suggest uncertainty where none exists or propose unsupported treatments.*   **Pedagogical Strategy:** Use the **"Proof Pudding" attack (CVE-2019-20634)** as a case study. Instructors should demonstrate how disclosed training data allows attackers to bypass email filters or extract model logic, illustrating that misinformation is often a byproduct of poor security boundaries.4\. Module 2: Architectural Solution — Transitioning to Grounded RAGThe "Black Box" model relies purely on internal weights. To achieve accuracy, students must transition to a "Grounded" RAG architecture, where the model is restricted to a verified knowledge base.The RAG Triad EvaluationInstructors will teach the evaluation of the RAG Triad to verify system integrity:
*   **Context Relevance:** Is the retrieved data useful for the query?
*   **Groundedness:** Is the answer derived only from the retrieved context?
*   **Question/Answer Relevance:** Does the response satisfy the user intent?Workshop: Source Attribution & Audit Trails
*   **Pedagogical Strategy:** Lead a workshop where students must force the model to provide explicit citations for every claim. The goal is to prove that increasing **Source Attribution** directly improves the **Groundedness** score of the RAG Triad, effectively creating an audit trail that mitigates hallucinations.5\. Module 3: Active Defense — NVIDIA NeMo GuardrailsStudents will implement "Guardrails as a System," treating security as an orchestration layer rather than a model feature.NeMo Architecture Flow (Text-Based Diagram)Based on the NVIDIA NeMo-Guardrails Architecture (SOURCE\_IMAGE\_1):
    
    *   **User Request** enters the **Model Namespace**.
    *   **NeMo Guardrails Server** receives the request and triggers **Internal Detectors**.
    *   **External Detectors** (e.g., custom safety models or APIs) are queried for validation.
    *   If safe, the request reaches the **vLLM Deployed Model**.
    *   Output follows the same path (vLLM -> Output Guardrails -> User).
    
    Input vs. Output Detectors

Hallucination

Overreliance

Input Detectors (Pre-Inference)Output Detectors (Post-Inference)Sanitization: Removes PII or unapproved language.Sensitive Info Disclosure (LLM02): Blocks leaks of credentials or data.Hallucination Checks: Validates output against the RAG context.Intent Alignment & Technical ConfigurationUsing the "Lemonade Stand" example, instructors will demonstrate how to define a **Strict Content Safety Filter** via a config map.*   **Pseudocode Configuration Snippet:***   **Pedagogical Strategy:** Students must implement this config map to ensure a bot refuses to discuss "oranges," thereby preventing the promotion of competitors.6\. Module 4: Observability and Economics — Grafana IntegrationThis module focuses on the "Denial of Wallet" risk associated with **OWASP LLM10 (Unbounded Consumption)**.Causal Link: Intercept to SavingsInstructors must demonstrate the causal relationship between a NeMo intercept and economic efficiency.
    
    *   **Metric 1: Threat Detection Rate:** Frequency of blocked malicious prompts.
    *   **Metric 2: Token Savings:** Calculation of tokens not processed by the base LLM due to guardrail filtering.
    *   **Metric 3: Latency vs. Safety:** The time overhead of running guardrail checks.
    *   **Pedagogical Strategy (Live Demo):** The instructor should trigger a "Topic Violation" (e.g., asking about Oranges). Show the NeMo server blocking the request instantly. Simultaneously, show the **Grafana Dashboard** reflecting **zero tokens consumed** by the vLLM for that specific query, proving the prevention of LLM10 risks.
    
    7\. Module 5: Ethics, Dual-Use, and the Human ElementThe "Dual-Use Dilemma" (LibraAlign research) highlights that over-aligning for safety can lead to "intelligence loss" or degraded utility.Practitioner's Do's and Don'ts
*   **Do:** Respect **Indigenous Data Sovereignty** by involving local communities in data curation for Twi/Ga models.
*   **Do:** Use energy-efficient compressed models to reduce environmental footprints.
*   **Don't:** Assume "Objectivity" in code; design choices in safety filters have inherent political dimensions.
*   **Don't:** Assume guardrails are foolproof; monitor post-deployment for "brittle" behavior.Chain-of-Thought (CoT) & Reasoning ExposureInstructors must warn students that reasoning logs in models like DeepSeek-R1 can be a vulnerability.
*   **Nuance:** If the **Chain-of-Thought is exposed to the user**, it can leak "synthesis pathways" for restricted substances (e.g., MDPV) even if the final answer is a refusal.
*   **Strategy:** Teach students to **sanitize or separate the reasoning log** on the server side so only the final, safe response reaches the client interface.8\. The Three-Dimensional Assessment System (Ghana Standard)Students will be graded based on a balanced scorecard:
*   **Dimension 1: Technical Robustness (40%)**
*   Functional RAG implementation with verifiable groundedness.
*   Successful deployment of NeMo Input/Output detectors.*   **Dimension 2: Ethical Alignment (30%)**
*   Mitigation of bias and documentation of dual-use trade-offs.
*   **Stakeholder Engagement Plan:** A written strategy for involving non-English speaking communities (Twi/Ga speakers) in model testing.*   **Dimension 3: Observability & Efficiency (30%)**
*   A Grafana dashboard that visualizes token savings and LLM10 mitigation.Final Project PromptBuild a grounded AI assistant for a Ghanaian public sector use case (e.g., **Agricultural Extension** or **Healthcare Navigation**). The project must include a RAG knowledge base, a NeMo configuration map for topic alignment, a Grafana dashboard proving economic efficiency, and a **Stakeholder Engagement Plan** for indigenous language speakers.9\. Required Reading & Resources*   OWASP Top 10 for LLM Applications 2025 (Core Text).
*   The Only Way is Ethics: LLM Ethics Whitepaper (Ungless et al., 2024).
*   LibraAlign Research: The Dual-Use Dilemma in LLMs (Zhang et al., 2025).
*   **NVIDIA NeMo Architecture:** Students should refer to the standard "Model Namespace vs. Operator Namespace" flow as described in text-based architectural summaries.

Prompt Injection (LLM01): Detects "Jailbreaks" or instruction hijacking.

Topic Alignment: Flags "off-topic" queries to save costs.

Token Savings: Early interception prevents LLM10:2025.