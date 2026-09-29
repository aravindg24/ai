# GenAI Cost Model

**Rates Verified On:** 16 September 2026  
**Last Reviewed:** 28 September 2026  
**Model Currency Check:** 28 September 2026 (Live Audit)  
**Status:** Active  

---

## 1. Executive Summary

This document establishes the cost and capacity model for the Saayam Generative AI microservices in response to leadership direction:
> *"We should be using the latest and the greatest LLM model services at the cheapest price. Please keep this as our goal... Please come up with our cost model — how much we are spending now, how much we may have to pay based on some approximate number of end users. We need to monitor this expense regularly."*

### Key Figures at a Glance: Floor vs. Ceiling Range

Following the token baseline audit (`docs/metrics/TOKEN_BASELINE.md`, PR #189) and the correction of LangChain reasoning token double counting (commit `28688c2`), our costs are stated as an empirical range. The **Floor** reflects clean measured prompts, measured classification completion, measured Groq-only organization search completion, and conservative completion estimates for subject and answer. The **Ceiling** reflects the empirical mean across all runs in `token_baseline.json` (which includes pre-fix reasoning overcounts on LangChain calls until re-measurement).

| Metric | Initial Estimate (16 Sep) | Floor (Clean Baseline) | Measured Mean (Ceiling) | Impact / Implication |
| :--- | :---: | :---: | :---: | :--- |
| **Tokens per Help Request** | 3,434 | **~4,990** | **8,116** | Initial estimate undercounted prompt sizes and reasoning tokens. |
| **Cost per Help Request (Groq)** | $0.000433 | **~$0.00072** | **~$0.00163** | Extremely affordable (<$0.002 per request on primary). |
| **Cost per 1,000 Help Requests** | $0.43 | **~$0.72** | **~$1.63** | Predictable, low-cost scaling. |
| **Free-Tier Daily Capacity** | 58 / day | **~40 / day** | **~24 / day** | **The capacity cliff arrives sooner than estimated.** |
| **Failover Multiplier (Gemini)** | 6.34× | **At least 6.8×** | **Up to 15×+** | Empty-result & thinking tokens inflate Gemini completion. |
| **Self-Hosting Breakeven** | ~875,000 / mo | **~524,000 / mo** | **~233,000 / mo** | Fixed EC2 GPU instance remains unviable vs serverless API. |

---

## 2. Token Baseline per Help Request

Tokens are measured against live model calls in `docs/metrics/token_baseline.json` and prompt builders using `tiktoken` (`o200k_base`). A standard help request workflow invokes model-backed microservices across up to six distinct calls.

### Measured Service Breakdown

| Service | Calls / Req | Prompt Tokens (Measured) | Completion Tokens (Measured / Est) | Total Tokens | Measurement & Operational Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `predict_category` | 2.25 *(2–3)* | 1,172 | 258 *(mean)* | 1,430 | Hierarchical taxonomy descent. Measured via raw Groq SDK (unaffected by LangChain double counting). |
| `search_orgs` | 1.12 *(1–2)* | 1,188–1,292 *(1,363 mean)* | 888–1,014 *(970 mean Groq)* | ~2,210–3,710 | Structured extraction of 6 organizations × 13 fields. Prompt is ~1,240 tokens (not 500 as early estimates assumed). |
| `generate_subject` | 1.00 | 523 | 20 *(clean est)* to 1,515 *(mean)* | 543–2,038 | Summarizes description into a 70-char title. 2 of 8 baseline runs hit a 4,094 ceiling due to high reasoning effort and LangChain double counting. |
| `generate_answer` | 1.00 | 528 | 300 *(clean est)* to 410 *(measured)* | 828–938 | Initial conversational advice turn based on category, location, and description. |
| `emergency_contacts`| 0.00 | 0 | 0 | 0 | Deterministic lookup against verified country dataset (zero LLM calls). |
| **Total (Floor: Clean Baseline)** | **~5.4** | **3,442** | **1,548** | **~4,990** | Baseline with reasoning double-counting removed and conservative subject/answer completions. |
| **Total (Ceiling: Measured Mean)**| **~5.4** | **3,586** | **4,530** | **8,116** | Empirical mean from `token_baseline.json` across all benchmark runs. |

### Accuracy & Measurement Notes
1. **Classification Descent Depth:** Of the 717 entries in the taxonomy, only **49 are actionable help categories**; the remaining 668 are form fields and questionnaires. Traversal stops once a leaf category is selected (e.g., `1 -> 1.1` terminates in 2 calls; `3 -> 3.3 -> 3.3.1` terminates in 3 calls). Deterministic pre-routing (`is_elderly_context`) cuts this to a single call (527 tokens).
2. **LangChain Reasoning Token Accounting (Commit `28688c2`):** In `langchain-groq`, `output_tokens` already includes reasoning tokens (`output_token_details.reasoning`). Prior to commit `28688c2`, `utils/token_usage.py` added reasoning tokens on top of `output_tokens`, inflating completion counts for LangChain services (`generate_subject`, `generate_answer`, and `search_orgs`).
3. **Reasoning Effort Control:** Models like `openai/gpt-oss-20b` default to high reasoning effort. Pinning `reasoning_effort="low"` in `utils/client.py` prevents runaway completion tokens while preserving response quality.

---

## 3. Provider Rates & Fallback Architecture

*Rates verified on 16 September 2026 and confirmed live on 28 September 2026.*

### Rate Table

| Provider | Model | Tier / Role | Input / 1M Tokens | Output / 1M Tokens | Rate Limits & Quotas |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Groq** | `openai/gpt-oss-20b` | Primary (All Services) | **$0.075** | **$0.30** | 30 req/min, 1,000 req/day, 8,000 tok/min, 200,000 tok/day |
| **Groq** | `openai/gpt-oss-120b` | Tier 2 (Classification) | **$0.150** | **$0.60** | 30 req/min, 1,000 req/day, 8,000 tok/min, 200,000 tok/day |
| **Groq** | `openai/gpt-oss-safeguard-20b`| Tier 3 (Classification, **Preview**) | **$0.075** | **$0.30** | Evaluation preview; subject to withdrawal at short notice. |
| **Google Gemini** | `gemini-2.5-flash` | Fallback Tier | **$0.300** | **$2.50** | 15 req/min, 1,500 req/day, 1,000,000 tok/min *(to confirm in AI Studio)* |

### Service Fallback Path Matrix
The repository currently maintains two distinct fallback routing architectures:
* **Hierarchical Classification (`predict_category`):** Uses the 4-tier chain introduced in PR #199 (`config/model_routing.json`):
  $$\text{Groq 20b} \longrightarrow \text{Groq 120b} \longrightarrow \text{Groq Safeguard 20b} \longrightarrow \text{Gemini 2.5 Flash}$$
* **Subject, Answer, and Org Search:** Currently use the 2-tier fallback pair:
  $$\text{Groq 20b} \longrightarrow \text{Gemini 2.5 Flash}$$
  *(Consolidating these services into the unified multi-tier router is tracked as remaining work under Issue #193).*

### Cost Calculation per Help Request (Reproducible Arithmetic)

**Floor Calculation (3,442 Prompt / 1,548 Completion):**
$$\text{Prompt Cost} = 3,442 \times \frac{\$0.075}{1,000,000} = \$0.00025815$$
$$\text{Completion Cost} = 1,548 \times \frac{\$0.30}{1,000,000} = \$0.00046440$$
$$\mathbf{\text{Total Floor Cost (Groq Primary)}} = \$0.00025815 + \$0.00046440 = \mathbf{\$0.00072255 \approx \$0.00072}$$

**Ceiling Calculation (3,586 Prompt / 4,530 Completion):**
$$\text{Prompt Cost} = 3,586 \times \frac{\$0.075}{1,000,000} = \$0.00026895$$
$$\text{Completion Cost} = 4,530 \times \frac{\$0.30}{1,000,000} = \$0.00135900$$
$$\mathbf{\text{Total Ceiling Cost (Groq Primary)}} = \$0.00026895 + \$0.00135900 = \mathbf{\$0.00162795 \approx \$0.00163}$$

**Gemini Sustained Fallback Cost (Floor Token Basis):**
$$\text{Prompt Cost} = 3,442 \times \frac{\$0.30}{1,000,000} = \$0.00103260$$
$$\text{Completion Cost} = 1,548 \times \frac{\$2.50}{1,000,000} = \$0.00387000$$
$$\mathbf{\text{Total Gemini Fallback Cost (Floor)}} = \$0.00103260 + \$0.00387000 = \mathbf{\$0.00490260 \approx \$0.00490}$$
$$\text{Nominal Rate Multiplier} = \frac{\$0.0049026}{\$0.00072255} \approx \mathbf{6.78\times}$$

> [!WARNING]
> **Operational Failover Multiplier:** The nominal multiplier of ~6.8× applies Gemini rates to Groq token baselines. In production, Gemini 2.5 Flash bills thinking tokens as output at $2.50/M. In `token_baseline.json`, a single fallback run on `search_orgs` produced **12,004 completion tokens** (costing ~$0.030 for one call alone). Furthermore, fallback in `search_orgs` fires on **empty results** (`len(results) == 0`) as well as outages. The true operational failover multiplier is **at least 6× and up to 15×+**.

---

## 4. Volume Projections

Monthly model expenditure projected across representative user volumes:

| Monthly Help Requests | Spend on Groq (Floor: $0.00072) | Spend on Groq (Ceiling: $0.00163) | Spend on Sustained Gemini Fallback | Implied Active Users (at 1 req/user/mo)* |
| ---: | ---: | ---: | ---: | ---: |
| **1,000** | $0.72 | $1.63 | $4.90 – $16.30 | 1,000 |
| **10,000** | $7.23 | $16.28 | $49.03 – $162.80 | 10,000 |
| **50,000** | $36.13 | $81.40 | $245.13 – $814.00 | 50,000 |
| **100,000** | $72.26 | $162.80 | $490.26 – $1,628.00 | 100,000 |
| **500,000** | $361.28 | $813.98 | $2,451.30 – $8,139.75 | 500,000 |
| **1,000,000** | $722.55 | $1,627.95 | $4,902.60 – $16,279.50 | 1,000,000 |

*\*Note: 1.0 request per active user per month is a documented placeholder pending empirical user analytics from the Product and Request teams.*

---

## 5. Capacity Constraints & Operational Risks

### 5.1 The Free-Tier Cliff
* **Daily Token Limit:** Groq's free tier permits 200,000 tokens/day organization-wide.
* **Effective Daily Platform Capacity:**
  $$\text{Daily Capacity (Floor)} = \frac{200,000 \text{ tokens/day}}{4,990 \text{ tokens/req}} \approx \mathbf{40 \text{ help requests/day}}$$
  $$\text{Daily Capacity (Ceiling)} = \frac{200,000 \text{ tokens/day}}{8,116 \text{ tokens/req}} \approx \mathbf{24 \text{ help requests/day}}$$
* **Request Quota:** 1,000 requests/day ÷ ~5.4 calls/request ≈ 185 requests/day.
* **Finding:** The platform is **strictly token-bound, not request-bound**. It will trigger `HTTP 429` rate limit rejections after only **24 to 40 completed help requests per day**.
* **Mitigation:** Upgrade to Groq's Pay-As-You-Go tier prior to public launch. At near-term volumes (e.g., 5,000–10,000 requests/month), total spend is **<$10.00/month**, completely eliminating the cliff.

### 5.2 Caller-Controlled Follow-up Transcripts
* `generate_answer` supports multi-turn follow-ups. The backend boundary is `MAX_HISTORY_MESSAGES = 20` and `MAX_MESSAGE_CHARS = 4000` (`utils/__init__.py`).
* **Typical turn:** 5 short messages ≈ 666 prompt tokens ($0.000050 Groq / $0.000200 Gemini).
* **Worst-case turn:** 20 × 4,000 characters ≈ **16,781 prompt tokens**.
* **Consequence:** Just 12 worst-case turns consume the entire daily free-tier quota. Furthermore, 16,781 tokens in a single request instantly exceeds Groq's 8,000 tokens/minute rate limit, failing immediately with a `429`.

### 5.3 Silent Failover & Empty-Result Triggering
* When Groq fails, the system automatically falls back to Gemini 2.5 Flash via `utils/model_fallback.py`.
* In `utils/search_orgs.py`, failover triggers not only on API outages, but also whenever a primary call returns zero organizations. Discarding Groq output and querying Gemini doubles the token cost for that turn and risks large completion token bills.

---

## 6. Self-Hosting Feasibility (Resolution of Issue #23)

Issue #23 proposed moving to self-hosted open models (e.g., on AWS EC2) to reduce costs. The economics dictate otherwise:

* **EC2 GPU Instance (`g4dn.xlarge` - 1x NVIDIA T4, 16GB VRAM):** On-demand price is ~$0.526/hour in `us-east-1`, totaling **~$378.72/month**.
* **Fixed Cost Nature:** The instance incurs this fee 24/7/365 regardless of request volume.
* **Breakeven Calculation:**
  $$\text{Breakeven (Floor: \$0.000723)} = \frac{\$378.72}{\$0.00072255} \approx \mathbf{524,143 \text{ requests/month}}$$
  $$\text{Breakeven (Ceiling: \$0.001628)} = \frac{\$378.72}{\$0.00162795} \approx \mathbf{232,636 \text{ requests/month}}$$
  *(Note on historical arithmetic: The original issue calculation of 854,500 requests used an older $370/mo estimate. At the exact $378.72 price and original $0.000433 rate, the quotient was 874,541).*
* **Conclusion:** Self-hosting remains substantially more expensive than serverless API calls until platform traffic surpasses **~233,000 to ~524,000 help requests per month**. Furthermore, self-hosting introduces infrastructure management, patching, GPU cold starts, auto-scaling complexities, and high availability engineering that a non-profit volunteer engineering team should avoid.

---

## 7. Model Strategy: Tiering vs. Single Frontier Model

Leadership requested: *"We should be using the latest and the greatest LLM model services at the cheapest price."*

Frontier models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) cost 10× to 50× more than open-weight lightweight tiers. A single frontier model across all microservices is financially inefficient because the services perform fundamentally distinct tasks:

| Service | Real Task | Frontier Required? | Recommended Tier |
| :--- | :--- | :---: | :--- |
| `predict_category` | Choose from 7–13 options; JSON output | **No** | Small, fast open-weights (`gpt-oss-20b`) or classical ML classifier. |
| `generate_subject` | 1-line summary under 70 chars | **No** | Small, fast open-weights (`gpt-oss-20b`). |
| `emergency_contacts`| Country directory lookup | **No LLM** | Deterministic static dataset (zero hallucination risk). |
| `search_orgs` | Structured organization extraction | **No** | Small open-weights with retrieval grounding. |
| `generate_answer` | Empathetic, nuanced beneficiary guidance | **Yes (conditional)** | Frontier or mid-tier model with reasoning capabilities. |

**Standing Policy:**
> Route each microservice to the lowest-cost model that satisfies its deterministic quality bar. Reserve frontier models strictly for services where reasoning and empathy directly touch the beneficiary (`generate_answer`).

---

## 8. Open Access Gaps

Three operational inputs require information from outside this repository. Inquiries were submitted on **28 September 2026**:

| Gap | Responsible Team / Leads | Current Status / Tracking |
| :--- | :--- | :--- |
| **Requests per User per Month** | Product & Request Teams (@srush-shah, @shivam131284, @MustakimFS) | Inquired on 28 Sep 2026. Documented with a placeholder of **1.0 request/user/month** pending user analytics. |
| **AWS Lambda Configurations** | DevOps / AWS Cloud Administrator | Inquired on 28 Sep 2026. Deployed workflow (`deploy_aws_lambda.yml`) specifies timeout for only 1 function (`Generate Answer` at 120s) and memory for **none**. Actual memory/timeout allocations reside exclusively in the AWS Console. Issue #153 recorded that console configurations differed from documentation across all 5 functions. |
| **Provider Account Billing Tiers** | DevOps / Account Administrator | Inquired on 28 Sep 2026. Verifying whether Groq and Gemini accounts are currently on Free or Pay-As-You-Go tiers, and whether nonprofit educational grant discounts (investigated Nov 2025) were secured. |

---

## 9. Model Currency & Deprecation Audit

*Audit Date: 28 September 2026 (Live Provider Verification)*

| Provider | Model Name | Code Location | Status as of 28 Sept 2026 | Deprecation / Sunset Schedule |
| :--- | :--- | :--- | :---: | :--- |
| **Google** | `gemini-2.0-flash` | Formerly `classification_service.py` | **RETIRED** | Decommissioned by Google on **1 June 2026**. Eradicated from codebase in PR #199 (`git grep "gemini-2.0"` returns 0). |
| **Google** | `gemini-2.5-flash` | `config/model_routing.json`, `client.py` | **ACTIVE / GA** | GA, no announced sunset date. Verified on Google API deprecations log. |
| **Groq** | `openai/gpt-oss-20b` | `config/model_routing.json`, `client.py` | **ACTIVE / PRODUCTION** | Primary production model. Verified on Groq supported models log. |
| **Groq** | `openai/gpt-oss-120b` | `config/model_routing.json` | **ACTIVE / PRODUCTION** | Secondary fallback tier. Verified on Groq supported models log. |
| **Groq** | `openai/gpt-oss-safeguard-20b`| `config/model_routing.json` | **ACTIVE / PREVIEW** | Tertiary safeguard tier. **Note:** Listed as Preview on Groq docs; preview models can be withdrawn on short notice. Flagged for review on Issue #193. |

### Deprecation Tracking References
Every model named in code must be checked quarterly against its provider's deprecation log:
* **Google Gemini API Deprecations:** [https://ai.google.dev/gemini-api/docs/deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
* **Groq Supported Models:** [https://console.groq.com/docs/models](https://console.groq.com/docs/models)
* **Groq Deprecations List:** [https://console.groq.com/docs/deprecations](https://console.groq.com/docs/deprecations)
* **OpenAI API Deprecations:** [https://platform.openai.com/docs/deprecations](https://platform.openai.com/docs/deprecations)

---

## 10. Governance & Review Rhythm

1. **Monthly Review Agenda:** A recurring agenda item during the final weekly AI meeting of each calendar month (within 30 days):
   * Total token usage by service and by provider (extracted from CloudWatch `TOKEN_USAGE` logs).
   * Actual monthly spend versus volume projections.
   * Primary vs. fallback invocation split (detecting silent Groq degradation to Gemini).
   * Free-tier / rate-limit headroom.
2. **Quarterly Model Currency Review:** Review all model identifiers against provider deprecation schedules. Any model scheduled for retirement within 60 days must have a migration PR opened immediately.
3. **Audit Freshness:** This documentation must display a **Last Reviewed** date. If the date is older than 30 days, the monthly review has lapsed.

---

## 11. Cost-Reduction Shortlist

The following optimization candidates are tracked. None are implemented by this issue:

| Optimization Candidate | Expected Impact | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Pin `reasoning_effort="low"` on Groq** | Eliminates reasoning runaway on LangChain models | **Proposed, PR pending** | Implemented in commit `28688c2`. Token savings to be re-measured after double-counting fix merges. |
| **Enforce `MAX_MESSAGE_CHARS` server-side** | Prevents 25× caller-controlled prompt ballooning | **Risk measured, change unmeasured** | Worst-case prompt turn measured at 16,781 tokens. Code change in `utils/__init__.py` pending. |
| **Trim Organization Description Fields** | Reduces 20–40% of `search_orgs` completion tokens | **Unmeasured** | Estimated in `TOKEN_BASELINE.md` §3.3. Requires cross-team agreement on `ORGANIZATION_FIELDS` contract (#170). |
| **Deterministic Pre-Routing Expansion** | Cuts 2–3 model calls down to 1 call | **Unmeasured** | Measured on `elderly-medium` (1 call, 527 tokens). Can expand to other unambiguous domain terms. |
| **Groq Prompt Caching on Classification** | 50% discount on cached input ($0.075 → $0.0375/M) | **Unmeasured** | Automatic on `gpt-oss-20b`. Level-1 prompt (~330 tokens) requires verifying minimum cacheable length (128–1,024 tokens). |
| **Trained Local Classifier (XGBoost/LightGBM)** | Eliminates 2–3 model calls per request entirely | **Unmeasured** | Proposed in April 2026 weekly minutes; replaces LLM classification with classical ML. |

---

## 12. Telemetry Query (CloudWatch Logs Insights)

Token metrics are written to CloudWatch Logs under the `TOKEN_USAGE` prefix by `utils/token_usage.py` (Issue #159). To inspect usage across services in CloudWatch Logs Insights:

```sql
fields @timestamp, @message
| filter @message like /TOKEN_USAGE/
| parse @message "TOKEN_USAGE *" as body
| stats 
    count(*) as total_requests,
    avg(total_tokens) as avg_tokens,
    max(total_tokens) as max_tokens,
    sum(total_tokens) as sum_tokens
  by service, provider
```

---

## 13. Scope Boundaries & Out of Scope

The boundaries of this issue and document are strictly defined:

* **Token Instrumentation (Issue #159):** Instrumenting the codebase to count tokens is owned by Issue #159 (`utils/token_usage.py`). This document consumes that telemetry.
* **Model Fallback Implementation (Issue #193):** Merging model fallback chains and eliminating deprecated constants (`gemini-2.0-flash`) is owned by Issue #193 / PR #199 (`utils/model_fallback.py`, `config/model_routing.json`).
* **Implementation of Reduction Shortlist:** Optimizations in §11 are documented candidates for future review. None are implemented by this issue; each surviving candidate requires independent measurement and its own PR.
* **Alerting Infrastructure:** Creating CloudWatch alarms or notification subscriptions is managed as operational infrastructure.
* **Commercial & Account Operations:** Negotiating nonprofit pricing with Groq or Google, purchasing credits, or switching vendors.
* **Non-AI Services:** Applies exclusively to the `ai` repository Lambda functions.

---

## 14. Recommendations & Future Scope

The following items are recommended for future implementation following the adoption of this cost model:

1. **Fallback Traffic Alerting:** Configure a CloudWatch metric alarm alerting when Gemini fallback traffic exceeds **>5% of total requests** in any 1-hour window (detecting silent Groq outages or empty-result fallback cascades).
2. **Automated CloudWatch Custom Metrics via EMF:** Upgrading `TOKEN_USAGE` log emission to native CloudWatch Custom Metrics using `aws-lambda-powertools` Metrics utility, enabling out-of-the-box alerting without running CloudWatch Logs Insights parse queries.
3. **Dynamic Quality-Gated Model Routing:** Once this model has completed two consecutive monthly reviews, feed it into the tiering policy outlined in §7. This requires curating an evaluation "golden set" per service to define the minimum acceptable quality bar ("passes").
4. **Empirical User Activity Forecasting:** Replacing the 1.0 request/active user/month placeholder with empirical analytics from the Request microservice to forecast platform costs against active user projections.
5. **Speech-to-Text Multimodal Integration (#22):** Evaluating natively multimodal models for voice input/output to consolidate audio transcription directly into the GenAI pipeline.
