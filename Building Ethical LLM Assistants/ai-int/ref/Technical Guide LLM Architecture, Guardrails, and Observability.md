 

NotebookLM
==========

Exported on: 14/06/2026, 17:58:58

Technical Guide: LLM Architecture, Guardrails, and Observability

1\. Introduction to AI Safety and Risk Mitigation

In the landscape of enterprise Large Language Model (LLM) deployments, safety is a non-negotiable architectural requirement. As these models move from laboratory environments into business-critical operations—including customer-facing chatbots and internal decision-support systems—the surface area for risk expands significantly. Proactive risk mitigation is essential not only for regulatory compliance but for protecting organisational reputation and ensuring long-term user trust.

The primary risks inherent in enterprise LLM applications include:

*   **Hallucination**: The generation of factually incorrect or fabricated information that is presented with high confidence, often occurring when the model fills knowledge gaps using statistical probability.
*   **Bias**: The unintentional amplification of prejudices present in training data, which can manifest as discriminatory behaviour or representational harms.
*   **Prompt Injection**: A high-priority vulnerability where malicious inputs manipulate the model's logic to bypass safety constraints, execute unauthorised commands, or extract internal instructions.
*   **Data Leakage**: The unintentional exposure of sensitive data—such as PII, proprietary source code, or internal business strategy—through the model’s generated output.

2\. Enterprise Architecture: Guardrailing in OpenShift AIDeploying a production-grade safety layer within Red Hat OpenShift AI (RHOAI) necessitates a structured interaction between the infrastructure and the model runtime. The following architectural mapping, based on the NVIDIA NeMo Guardrails stack, illustrates the separation of concerns between the operator and model namespaces.*   **Operator Namespace**:
    *   **TrustyAI Operator**: Acts as the primary controller for safety services. It maintains a **"Watch/Deploy"** relationship with the environment; specifically, it watches for the creation of Guardrails Custom Resources and automatically deploys the necessary Server infrastructure.
    *   **Other ODH/RHOAI Operators**: Manage the foundational AI/ML platform, providing the underlying compute and networking abstractions required for inference.*   **Model Namespaces**:
    *   **NeMo Guardrails Server**: The central orchestrator that intercepts all requests. It manages logic across **Internal Detectors** (high-speed local checks) and **External Detectors** (specialised services for PII or domain filtering).
    *   **vLLM Deployed Model**: The core inference engine that generates content only after the request has been validated by the orchestrator.*   **Control Plane Workflow**:
    *   **Admin Interaction**: The Administrator uses oc create to define safety policies within a **NeMo-Guardrails Custom Resource (CR)**.
    *   **System Synchronisation**: The NeMo Guardrails Server provides a **status update** back to the CR, ensuring the actual state of the guardrails matches the desired configuration.
    *   **User Interaction**: Users send inference requests directly to the Guardrails Server, which serves as the protected entry point.3\. Core Guardrailing Mechanics: Input and Output FiltersThe "Guardrail Orchestrator" functions as a bidirectional safety gate. Crucially, this logic is abstracted away from the application code and handled at the infrastructure level. This ensures that safety is enforced consistently regardless of how the end-user application is developed.Input Detectors (Pre-LLM)Output Detectors (Post-LLM)Operational Goal: Validate the generated response to ensure it adheres to safety and privacy standards.Policy Compliance: Prevents the exfiltration of sensitive data or the use of unacceptable language.Primary Focus: PII masking, hallucination checking, and ensuring the model does not promote competitors.4\. Implementation with Colang and Configuration MapsGuardrails are defined through Kubernetes Configuration Maps, which contain the Colang logic required for the NeMo Guardrails Server. Colang allows architects to define "safe" versus "unsafe" semantic intents without relying on brittle, hand-coded keyword lists.A major advantage of this approach is the ability to implement **LLM-based self-checking**. In this configuration, a secondary, highly-aligned LLM acts as a "judge" to evaluate the inputs and outputs of the primary model.Self-Check Configuration LogicThe following safety filters are typically defined within the self\_checks configuration map:*   strict\_context\_adherence: Forces the model to generate responses based solely on provided context (critical for RAG).
*   prompt\_injection\_hub: A specialised filter designed to identify and neutralise attempts to hijack model instructions.
*   unlimited\_consumption (LLM10): Monitors and mitigates "Denial of Wallet" scenarios by tracking excessive or uncontrolled resource usage.5\. Practical Application: The Lemonade Stand DemoThe "Lemonade Stand" case study highlights a highly restricted LLM application where the model is constrained to a specific business domain.Demo Constraints:
*   **Topic Enforcement**: The model is restricted to discussing lemons only.
*   **Non-English Detection**: Languages other than English (e.g., "Hola") are flagged and blocked. This is not merely for language preference but to prevent attackers from using different languages to bypass English-centric topic filters.
*   **Security Flags**: Real-time detection of hate speech, toxic content, and competitive mentions (e.g., orange juice).User Experience:When a message violates these constraints, the query is intercepted by the orchestrator. The user receives the standardised response: **"flagged for inappropriate content."** Because this occurs at the input detector stage, the message never reaches the LLM, preserving both security and compute resources.6\. Securing the Pipeline: The OWASP Top 10 for LLMs (2025)The 2025 OWASP framework provides a comprehensive map of vulnerabilities unique to the agentic and multimodal nature of modern AI.

Operational Goal: Block malicious or out-of-scope prompts immediately to prevent them from hitting the LLM.

Token Optimisation: Saves significant costs (mitigating "Denial of Wallet") by preventing expensive token consumption for invalid queries.

Primary Focus: Prompt injection detection, jailbreak prevention, and topic filtering.

Vulnerability IDDescriptionKey Mitigation StrategyManipulating behaviour via direct or indirect inputs (e.g., hidden instructions in images).Implement strict input/output filtering and enforce context-aware trust boundaries.Granting models excessive autonomy or permissions to call sensitive APIs.Limit functions implemented in extensions to the minimum necessary; implement **human-in-the-loop** for all high-impact actions.The discovery of steering instructions or secrets within the system prompt.Do not treat the system prompt as a secret or security control; externalise all credentials and connection strings.Resource exhaustion leading to "Denial of Wallet" or service degradation.Implement rate limiting, user quotas, and strict input size restrictions at the gateway.7\. Observability and Monitoring: Grafana DashboardsReal-time observability is required to transition from a "deployed" state to a "secure" state. A centralised Grafana dashboard for an LLM stack should track:*   **Flagged Interaction Volume**: Total requests versus those blocked by the orchestrator.
*   **Violation Taxonomy**: Breakdown of detection types (e.g., Jailbreak attempts vs. Non-lemon topics).
*   **Economic Efficiency**: Real-time calculation of token savings achieved by blocking prompts before they reach the inference engine.
*   **Denial of Wallet Metrics**: Identifying users or entities exhibiting patterns indicative of resource-exhaustion attacks.8\. The Ethical Lifecycle: Project Management for LLMsIntegrating ethics into the project lifecycle ensures that safety is "baked in" rather than "bolted on."Ethical Evaluation and Deployment Checklist

LLM01: Prompt Injection

LLM06: Excessive Agency

LLM07: System Prompt Leakage

LLM10: Unbounded Consumption

StageDoDon'tUse adversarial red teaming to find edge-case vulnerabilities and involve community experts.Don't present benchmarks as markers of progress towards general-purpose intelligence or human-level capabilities.Pair quantitative bias metrics with human-led qualitative assessment.Rely solely on "score-chasing" on public benchmarks which do not reflect real-world safety.Release models in stages, starting with trusted groups, and monitor post-deployment for new risks.Count on single-layer, brittle guardrails to prevent all harm in an evolving threat landscape.Integrate watermarking into generative outputs to allow for tracking and accountability.Put the onus on marginalised groups to discover and report system harms.The Dual-use Dilemma and CoT VulnerabilitiesA critical challenge for architects is the "Dual-use Dilemma"—the conflict between providing a model with high intelligence (utility) and maintaining safety constraints. Recent research from the Chinese University of Hong Kong (Zhang et al., 2025) has highlighted a major vulnerability in models like **DeepSeek-R1**.While long Chain-of-Thought (CoT) reasoning improves problem-solving, it can introduce ethical failures. For example, when queried about restricted substances like **MDPV**, the DeepSeek-R1 CoT process reveals illegal synthesis pathways in the hidden reasoning steps, even if the final output includes a refusal. Architects must be aware that distilling such models can inadvertently pass these "sleeper agent" vulnerabilities into smaller foundational models.9\. References*   Ungless, E. L., et al. (2024). The Only Way is Ethics: A Guide to Ethical Research with Large Language Models. University of Edinburgh.
*   OWASP Foundation (2024). Top 10 for LLM Applications v2025. OWASP.
*   Carratala, R. (Devoxx UK). Building Safer AI: Implementing Guardrails for LLM Applications.
*   Zhang, Y., et al. (2025). The Dual-use Dilemma in LLMs: Do Empowering Ethical Capacities Make a Degraded Utility? Department of Computer Science and Engineering, The Chinese University of Hong Kong.

Evaluation

Evaluation

Deployment

Deployment