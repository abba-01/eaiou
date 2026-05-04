# eaiou ToS Compliance Doctrine — IID Provider Isolation

**Date:** 2026-05-01
**Author:** Eric D. Martin
**Purpose:** Document the structural and procedural rules eaiou follows to remain compliant with each IID provider's Terms of Service while supporting multi-IID authoring assistance on a single user surface.

This doctrine is doctrine, not preference. Code review enforces it. Architecture enforces it. Audit logs make violations forensically discoverable.

---

## 1. The five non-negotiable rules

1. **No IID chaining.** A given IID's output is NEVER passed as input to another IID. If the author wants comparison, both IIDs receive identical source text in parallel; if the author wants synthesis, the author writes it themselves.
2. **No background IID invocation.** Every IID call is initiated by an authenticated, authenticated-and-current user request. No daemons, no schedulers, no agent loops invoke IIDs.
3. **Per-provider isolation of credentials.** Each provider's API key is stored separately, encrypted at rest, never logged, never shared across providers.
4. **Mandatory disclosure.** Every IID call produces a disclosure block (provider, model_family, instance_hash) attached to its output. The disclosure is never optional, never collapsible, never stripped from exports.
5. **Author-owned manuscript text.** IID outputs are advisory only. Manuscript text changes only via explicit author action. No silent edits; no auto-applied suggestions.

---

## 2. Why each rule exists

### Rule 1: No IID chaining

**Risk if violated:** Many providers' Terms of Service prohibit using their output to train or improve competing models, and some prohibit feeding outputs into other AI systems. Chaining IID outputs as inputs to other IIDs creates ambiguity about whether such derivative use is occurring. Even where ToS technically permits it, the practice undermines IID-attribution integrity: an output produced by Provider B that incorporated Provider A's reasoning is no longer cleanly attributable to either.

**Structural enforcement:** the dispatcher's `invoke_action()` takes exactly one `provider_id` per call. The `invoke_parallel()` function takes one set of `inputs` and dispatches to multiple providers — never sequencing one's output into another's input. Any code path that attempts chaining is rejected at code review.

**Audit-trail enforcement:** the `tbleaiou_iid_actions` table records the inputs of every action. Cross-references between actions (`superseded_by` is the only allowed link, indicating a re-run) make any chaining attempt forensically discoverable.

### Rule 2: No background IID invocation

**Risk if violated:** Many providers charge per-call and most have rate limits per API key. Background invocations can rapidly consume quota, expose the platform to runaway costs, and violate "user-initiated" assumptions in some ToS.

More structurally: background IID invocation breaks user agency. Authors must always know an IID is being invoked on their content. Invocation must be a deliberate act.

**Structural enforcement:** the FastAPI router endpoints all require `Depends(get_current_user)` or a partner-key with explicit user-acting authorization. There are no celery/cron jobs that call IIDs. There are no agent loops in eaiou's codebase.

**The one exception is not an exception:** stub-mode handlers (Phase 0 build) make HTTP calls to the IID provider that produce a placeholder response. The user still initiated those calls; the stub is just a "real handler not yet shipped" status, not a background invocation.

### Rule 3: Per-provider isolation of credentials

**Risk if violated:** Provider A's API key being accessible to a request invoking Provider B can leak credentials, allow cross-provider impersonation, or create audit ambiguity. Providers' ToS almost universally prohibit sharing or transferring API keys.

**Structural enforcement:**

- Each provider has its own row in `tbleaiou_iid_providers` with its own `api_key_encrypted`
- The dispatcher decrypts only the relevant provider's key just before passing to that provider's adapter
- Adapter modules receive the API key via function argument; the key is never global state
- Provider modules are forbidden from accessing other providers' rows in the database

**Operational enforcement:**

- API keys are encrypted at rest using AES-GCM with a key from eaiou's secret store (NOT in the database)
- Logs explicitly redact API keys; the `instance_hash` may be logged but the raw key never
- Access to the secret store is restricted to the eaiou service account on the droplet

### Rule 4: Mandatory disclosure

**Risk if violated:** Removing or hiding IID attribution undermines the SAID framework, violates academic-integrity expectations for manuscripts, and may run afoul of provider ToS that require disclosure of AI use.

**Structural enforcement:**

- Every output card in the UI shows a disclosure block (per `UXPILOT_AUTHORING_07_disclosure.md`)
- The disclosure block is rendered server-side in the same JSON payload as the result, not as a separate optional field
- The auto-generated AI-use-disclosure paragraph for journal submissions includes every IID's full attribution
- The audit-log export includes the full disclosure record per output
- The `tbleaiou_iid_actions` table makes the disclosure permanent (immutable)

### Rule 5: Author-owned manuscript text

**Risk if violated:** Auto-applied IID suggestions undermine author ownership of the manuscript and create ambiguity about authorship for journal submissions. Many publishers' policies (Elsevier, Springer, Nature, etc.) require disclosure if AI was used to generate substantial text; auto-applied suggestions blur the line.

**Structural enforcement:**

- The manuscript editor (per `UXPILOT_AUTHORING_01_writing_surface.md`) explicitly does NOT support AI-tab-completion-style features
- IID outputs land in the side panel, never in the editor body
- Suggested rewordings are proposed as track-changes-style suggestions requiring explicit Accept/Decline
- Inserted comments from IIDs are clearly attributed to the IID, with full disclosure visible

---

## 3. Specific provider ToS notes (as of 2026-05-01; verify on each onboarding)

### Anthropic (Mae)

- Standard Terms of Service prohibit using outputs to train competing models
- Prohibit chaining outputs into other AI systems where the chain is used to circumvent Anthropic's pricing
- Allow publishing AI-generated content with attribution
- Acceptable Use Policy prohibits use to generate content violating intellectual property, privacy, etc.
- eaiou compliance: respected by Rule 1 (no chaining) + Rule 4 (disclosure)

### OpenAI

- ToS as of 2026 prohibit using outputs to train models that compete with OpenAI's services
- Allow publishing AI-generated content
- Require disclosure of AI use in some contexts (academic publishing varies)
- eaiou compliance: respected by Rule 1 (no chaining) + Rule 4 (disclosure)

### Gemini (Google)

- Generative AI Terms of Service prohibit certain harmful generation
- Allow commercial use of outputs subject to ToS
- Disclosure expectations similar to OpenAI
- eaiou compliance: respected by all five rules

### Llama (Meta) / self-hosted

- Open-weights license (Llama Community License) permits commercial use up to a scale threshold
- Self-hosted instances don't have per-call ToS, but the license still applies to outputs
- eaiou compliance: same five rules; the `custom` adapter handles self-hosted endpoints

### Custom IIDs

- Whatever ToS the provider sets; eaiou has no opinion beyond requiring the SAID-framework disclosure block in responses
- The custom-adapter validates disclosure presence; missing disclosure rejects the response

---

## 4. ToS-compliance audit procedures

### Daily

- `instance_hash` log review: any unexpected pattern (e.g., one author firing 1000+ scope_checks in an hour) flagged for review
- Cost-cap monitoring: any provider's monthly spend approaching cap triggers an admin alert
- Failed-action review: any provider's error rate >5% triggers an admin alert

### Weekly

- Provider-key rotation check: every API key should have been used recently; stale keys flagged
- Audit-log export sanity check: random sample of 10 actions verified to have complete disclosure blocks
- Cross-action chain detection: any pair of (action_A, action_B) where action_A's output text appears in action_B's input text is flagged for review

### On every code change

- Code review must verify: any new IID-related code does not create a chaining path
- Code review must verify: any new IID-related code does not bypass the disclosure block
- Tests must pass: `tests/test_iid_dispatcher.py::test_no_chaining_path` and `tests/test_iid_dispatcher.py::test_disclosure_always_present`

### On provider onboarding

- Read the provider's current ToS in full
- Document any new compliance considerations in this file as `## Specific provider ToS notes`
- Verify the adapter respects all five rules
- Document the wholesale rate, latency expectations, and rate limits

### On academic-integrity inquiry

- The `[Export audit log]` button on the output panel produces a complete record of IID interactions
- This export is sufficient evidence for any reviewer/editor inquiry about AI use in the manuscript
- The auto-generated AI-use-disclosure paragraph is the standard suggested submission text

---

## 5. Author-side responsibilities

eaiou enforces the structural rules but the author also has responsibilities the platform cannot fully enforce:

- The author should read each IID output critically and not trust IID claims uncritically
- The author should disclose IID use in cover letters and supplementary material per the venue's policy
- The author should not paste IID outputs verbatim into manuscript text without attribution
- The author retains responsibility for the manuscript's correctness, novelty, and integrity

These author-side responsibilities are reinforced in:

- The onboarding flow when the author first configures an IID provider
- The auto-generated AI-use-disclosure paragraph (which the author must review and edit before journal submission)
- Help docs accessible from the IID sidebar's [Help] button

---

## 6. eaiou's standing claim to providers

eaiou represents itself to providers as:

- A first-party multi-tenant platform with per-author API key configuration (each author's API calls bill the author's own provider account, not eaiou's bulk account)
- An author-driven invocation surface (no background calls)
- A provider-isolation surface (per-provider keys, per-provider quotas, no cross-pollination)
- A full-disclosure platform (every output retains attribution)
- A non-aggregating platform (no model-output corpus is built from provider responses)

This claim is supported by the architecture and the audit log. Any provider audit can be answered with: "Here's the audit log; here's the codebase; here are the five rules; here is the test suite verifying enforcement."

---

## 7. Known edge cases and how they're handled

### "What if an author copy-pastes Mae's output into the editor and then asks OpenAI to review the manuscript?"

This is allowed and not a chaining violation per eaiou's rules: the author has incorporated the text into their manuscript (taking ownership), and OpenAI is reviewing the author's manuscript text. The author has full disclosure responsibility under SAID and journal policy; the platform enforces what it can (the IID-output card disclosure), but cannot prevent author-incorporated text.

This is honest: the platform cannot police every paste-and-review flow. What it can do — and does — is preserve the audit trail so any inquiry can reconstruct what happened.

### "What if a partner-key holder calls eaiou's API to invoke Mae?"

The partner-key model is documented separately in `manusights_competitor_mvp_plan.md` §0.2. Partner keys must:

- Be issued explicitly by Eric/admin
- Be scoped to specific authors/users (the partner platform routes its end-users through the key)
- Bill at wholesale rates
- Carry the partner platform's name in the disclosure block (e.g., "Mae, via [partner platform], on behalf of [end user]")

This adds attribution depth without violating provider isolation: the IID call is still going from eaiou to the IID provider with eaiou's audit machinery in the middle.

### "What if a provider deprecates a model mid-session?"

The provider returns an error; the action row records `status='error'` with the error message; the UI shows the error state. The author can choose a different model or wait for the provider to update. eaiou doesn't auto-fall-back to a different model — that would violate the disclosure rule (the author asked for model X, the disclosure must reflect X).

### "What if the author's API key is revoked?"

The provider returns an auth error; the dispatcher catches it; the provider's row is marked with a soft-flag `disabled_at = NOW()`; the UI shows a "Re-add API key" prompt. Existing action records remain intact (they were valid at production time; current key state doesn't retroactively invalidate them).

### "What if the SAID framework's instance_hash collides for two different sessions?"

The hash is 16 hex chars (64 bits of entropy). Collision probability is negligible for any reasonable population. If it does happen: the IntelliId records would still be distinct (each has its own UUID) but their `instance_hash` field would match. This is a cosmetic event, not a data-integrity issue. The audit trail still uses `intellid_id` (UUID) as the primary key, not `instance_hash`.

---

## 8. Future provisions

When future providers are onboarded, this document gets updated to include their specific ToS notes. The five non-negotiable rules do not change.

If a provider's ToS introduces a new requirement (e.g., mandatory watermarking of AI-generated output), the requirement is implemented in:

- The provider's adapter module (handles the technical requirement)
- This doctrine document (records the requirement)
- The disclosure block (surfaces the requirement to the user)
- The auto-generated AI-use-disclosure paragraph (carries the requirement into manuscript submissions)

If a provider's ToS becomes incompatible with the five rules, eaiou will not onboard or will offboard that provider. The five rules are load-bearing.
