# checksubmit — Build Plan (Commerce-First)

**Date:** 2026-05-01 (rev 3)
**Author:** Eric D. Martin
**Build inversion:** system first, review logic last. Storefront before inventory.
**Brand locked 2026-05-01 19:39 PDT:** `checksubmit.com` and `checksubmit.org` both registered to TM2YL LLC. Standalone customer-facing brand for the Manusights-competitor MVP. eaiou.org remains the broader platform; checksubmit is the productized review-as-a-service tier riding on top.

**DNS strategy locked 2026-05-01 19:50 PDT:**
- **`checksubmit.org`** — canonical surface. All UI, API, marketing, auth, Stripe customer-domain.
- **`checksubmit.com`** — accepted; 301-redirects to `https://checksubmit.org` (preserves URI path + query). Includes `www.` variants for both.
- nginx vhost block:
```nginx
server {
    listen 443 ssl;
    server_name checksubmit.com www.checksubmit.com www.checksubmit.org;
    return 301 https://checksubmit.org$request_uri;
}
server {
    listen 443 ssl;
    server_name checksubmit.org;
    location / { proxy_pass http://127.0.0.1:8000; }
}
```
- All four hostnames issued via `certbot --nginx -d checksubmit.org -d www.checksubmit.org -d checksubmit.com -d www.checksubmit.com` — single SAN cert, free.

## Strategic position

Manusights gates B2B integration on "wait for user volume." The gate is upside down — demand is queueing at the writing surface and being routed away by the absence of an API surface. Build native, route author-side micro-purchases inline as they write.

Build inversion principle: **the commerce infrastructure is reusable for any review service. Build the storefront infrastructure first, plug in inventory progressively.**

What this means in practice:
- Phase 0 = full API surface + auth + Stripe + subscription tiers + product catalog
- Phase 1+ = the actual review logic (scope-check, journal-fit, etc.) plugged into the storefront
- Phase 2+ = corpus indexing (Crossref) used by some — not all — products
- Eric can start invoicing as soon as Phase 0 is live, with review logic as simple as "forward to my Claude Code instance, return text" until Phase 1+ ships

## Phase 0 — API + commerce + auth (3–5 days)

This is the system. Everything else plugs into this.

### 0.1 Product catalog (broken-down objects)

Each product is a discrete, billable unit with a SKU, price, description, and a handler function. The catalog is data-driven — adding a new product is a database row + a handler module, not a code refactor.

**Initial catalog:**

| SKU | Product | Retail | Wholesale (B2B) | Latency target | Description |
|---|---|---|---|---|---|
| `scope_check` | "Is this in scope for venue X?" | $10 | $7 | < 30s | Single-question scope review with reasoning |
| `journal_select` | "Given abstract, what 3 venues fit?" | $10 | $7 | < 30s | Top-3 venue recommendation with reasoning |
| `outline_check` | "Is this outline coherent?" | $10 | $7 | < 30s | Outline structure review |
| `reference_audit` | "Are these references appropriate?" | $15 | $10 | < 60s | Reference relevance + recency review |
| `clarity_check` | "Is this section clear to a non-expert?" | $10 | $7 | < 30s | Section-level clarity review |
| `methods_check` | "Are these methods sufficient for the claim?" | $20 | $14 | < 60s | Methods-section review |
| `full_review` | Comprehensive scope + clarity + methods | $100 | $70 | < 5min | Bundled comprehensive review |
| `premium_review` | Premium depth comprehensive | $1500 | $1050 | < 24hr | Premium depth (may include human-in-loop later) |

**Subscription tiers** (orthogonal to per-call):

| Tier | Monthly | Includes |
|---|---|---|
| `free` | $0 | 1 free `scope_check` per month |
| `starter` | $19 | 5 `scope_check` + 5 `journal_select` per month |
| `pro` | $49 | 20 of any micro-product per month + 10% off à la carte |
| `studio` | $199 | Unlimited micro-products + 1 `full_review` + 20% off à la carte |
| `enterprise` | custom | B2B partner key + custom volume rate |

Hybrid: subscription provides included usage, à la carte covers overage (Stripe metered billing handles this natively).

### 0.2 API surface (the contract)

**Auth:** Two paths.
1. **User auth** — JWT bearer tokens (already in eaiou). Used by eaiou's own UI.
2. **Partner auth** — per-platform API keys (`Authorization: Bearer eaiou_pk_xxx`). Used by external integrations (e.g., a future Manusights-replacement partner ironically reversing the integration relationship; or any platform we license to).

**Endpoints (REST):**

```
POST   /api/v1/products                       → list available products + prices
GET    /api/v1/products/{sku}                 → product details
POST   /api/v1/orders                         → create order; pay or use subscription credit
GET    /api/v1/orders/{order_id}              → order status + result
POST   /api/v1/orders/{order_id}/cancel       → cancel pending order
GET    /api/v1/subscriptions                  → current subscription
POST   /api/v1/subscriptions                  → create or change subscription
DELETE /api/v1/subscriptions                  → cancel subscription
GET    /api/v1/usage                          → current period usage + balance
POST   /api/v1/webhook/stripe                 → Stripe webhook (billing events)
```

**Order request shape (POST /api/v1/orders):**

```json
{
  "sku": "scope_check",
  "manuscript_id": "uuid-or-null",
  "inputs": {
    "abstract": "...",
    "claimed_venue": "Journal of X"
  },
  "metadata": {
    "source": "eaiou.editor.scope-button",
    "session_id": "..."
  }
}
```

**Order response (success):**

```json
{
  "order_id": "ord_xxx",
  "status": "completed",
  "sku": "scope_check",
  "result": {
    "in_scope": true,
    "confidence": 0.84,
    "reasoning": "...",
    "similar_papers": ["10.xxx/yyy", "..."]
  },
  "iid": {
    "model_family": "claude-sonnet-4-6",
    "instance_hash": "..."
  },
  "billed": {
    "amount_cents": 1000,
    "via": "subscription_credit | stripe_meter",
    "stripe_meter_event_id": null
  },
  "created_at": "2026-05-01T19:32:00Z",
  "completed_at": "2026-05-01T19:32:14Z"
}
```

**Order response (async pending):**

```json
{
  "order_id": "ord_xxx",
  "status": "processing",
  "estimated_completion": "2026-05-01T19:33:00Z"
}
```

**Idempotency:** all order POSTs accept `Idempotency-Key` header per Stripe convention. Re-submitting same key returns the original order, not a new charge.

### 0.3 Stripe integration

- **Stripe Customer** per eaiou user (created on first paid order or subscription)
- **Stripe Subscription** per active eaiou subscription (one-to-one map to subscription tier)
- **Stripe Meters** per metered product (one meter per SKU; charges on overage past subscription credit)
- **Stripe Webhooks**: `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`, `meter.usage.updated`
- **Tax**: Stripe Tax handles VAT/sales-tax automatically
- **Refunds**: order-level refund flow with audit trail in eaiou DB

### 0.4 Database schema

```sql
-- migration_007_marketplace_core.sql

CREATE TABLE eaiou_products (
  sku VARCHAR(64) PRIMARY KEY,
  display_name VARCHAR(255) NOT NULL,
  description TEXT,
  retail_price_cents INT NOT NULL,
  wholesale_price_cents INT NOT NULL,
  latency_target_seconds INT NOT NULL,
  handler_module VARCHAR(255) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE eaiou_subscriptions (
  subscription_id CHAR(36) PRIMARY KEY,
  user_id CHAR(36) NOT NULL,
  tier VARCHAR(32) NOT NULL,
  stripe_subscription_id VARCHAR(128),
  status VARCHAR(32) NOT NULL,
  current_period_start TIMESTAMP NOT NULL,
  current_period_end TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user (user_id),
  INDEX idx_status (status)
);

CREATE TABLE eaiou_orders (
  order_id CHAR(36) PRIMARY KEY,
  user_id CHAR(36),
  partner_key_id CHAR(36),
  sku VARCHAR(64) NOT NULL,
  manuscript_id CHAR(36),
  inputs_json LONGTEXT NOT NULL,
  result_json LONGTEXT,
  status VARCHAR(32) NOT NULL,
  iid_id CHAR(36),
  amount_cents INT NOT NULL,
  via VARCHAR(32) NOT NULL,
  stripe_meter_event_id VARCHAR(128),
  idempotency_key VARCHAR(128),
  source VARCHAR(64),
  session_id VARCHAR(128),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  refunded_at TIMESTAMP,
  INDEX idx_user (user_id),
  INDEX idx_partner (partner_key_id),
  INDEX idx_status (status),
  INDEX idx_sku (sku),
  INDEX idx_idempotency (idempotency_key),
  FOREIGN KEY (sku) REFERENCES eaiou_products(sku)
);

CREATE TABLE eaiou_partner_keys (
  partner_key_id CHAR(36) PRIMARY KEY,
  display_name VARCHAR(128) NOT NULL,
  key_hash CHAR(64) NOT NULL UNIQUE,
  prefix VARCHAR(16) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  rate_limit_per_minute INT,
  wholesale_pricing BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP NULL
);

CREATE TABLE eaiou_subscription_credits (
  credit_id CHAR(36) PRIMARY KEY,
  subscription_id CHAR(36) NOT NULL,
  sku VARCHAR(64) NOT NULL,
  remaining_count INT NOT NULL,
  period_start TIMESTAMP NOT NULL,
  period_end TIMESTAMP NOT NULL,
  FOREIGN KEY (subscription_id) REFERENCES eaiou_subscriptions(subscription_id)
);
```

### 0.5 Workflow integration (eaiou author UI)

**The buy-while-you-write surface:**

- On the manuscript editor page (`/author/manuscript/{id}/edit`), add a "Quick Reviews" sidebar.
- Sidebar shows the catalog of micro-products with prices.
- Each product has a "Run for $X" button (or "Run with credit" if subscription credit available).
- Clicking the button:
  1. Confirms the action in a modal showing exact charge / credit usage
  2. Fires `POST /api/v1/orders` with the manuscript context auto-filled
  3. Shows progress indicator
  4. Renders result inline when complete (typically < 30s for micro-products)
  5. Persists result attached to manuscript for later review
- For subscription users: visible balance ("3 of 5 scope_checks used this month")
- For free-tier users: clear upsell to starter when balance hits zero

This is the "harness them while they write" surface Eric proposed in the email to Erik. Built natively, no vendor required.

## Phase 1 — Plug in review logic (2–3 days, parallel-safe)

The handlers are the inventory plugged into the storefront. Each handler is a module with a single function:

```python
# app/services/review_handlers/scope_check.py

def handle(inputs: dict, manuscript_context: dict | None) -> dict:
    """
    Returns: {in_scope: bool, confidence: float, reasoning: str, similar_papers: list[DOI]}
    """
    ...
```

Initial implementation strategy: each handler is a **thin LLM call** with a structured prompt. The corpus search (Phase 2+) is OPTIONAL — handlers can ship with LLM-only logic and incrementally add corpus retrieval as Phase 2+ lands.

Order of handler implementation (each ~half day):
- [ ] `scope_check` — LLM-only first, corpus-enhanced later
- [ ] `journal_select` — LLM-only first, corpus-enhanced later
- [ ] `outline_check` — LLM-only
- [ ] `clarity_check` — LLM-only
- [ ] `reference_audit` — needs corpus (DOI lookups), so postpone until Phase 2 lands or use Crossref REST API (free, rate-limited)
- [ ] `methods_check` — LLM-only initially
- [ ] `full_review` — composition of the above
- [ ] `premium_review` — placeholder, ships later with possible human-in-loop disclosure

## Phase 2 — Corpus indexing (3–7 days, compute-bound, optional)

The Crossref data on droplet becomes a corpus search backend that enhances `scope_check`, `journal_select`, `reference_audit`. NOT required for Phase 0–1 to ship.

- [ ] Decompress `/mnt/volume_nyc3_1777600565990/datasets-peerreview.7z` to a directory
- [ ] Schema scan + filter strategy (last 5 years for aggressive path, all for thorough)
- [ ] Stand up Qdrant via Docker on droplet
- [ ] `scripts/ingest_crossref.py` — parallel ingest into Qdrant with sentence-transformers embeddings
- [ ] `app/services/corpus_search.py` — Qdrant client wrapper used by handlers
- [ ] Upgrade `scope_check` and `journal_select` handlers to use corpus context

## Phase 3 — IID disclosure + audit (1 day)

Already mostly free given existing `app/services/intellid.py`:
- [ ] Every order writes its `iid_id` (linked to `tblintellids` already in DB)
- [ ] Order response includes IID disclosure block
- [ ] User-facing UI shows IID disclosure on result render
- [ ] Audit log via existing `tblapi_log`

## Phase 4 — Operations (1 day)

- [ ] Deploy via existing systemd service
- [ ] Smoke test: subscribe + run each product type + check Stripe records
- [ ] Monitoring: API latency, Stripe sync health, handler error rate
- [ ] Document the partner-API contract for external onboarding

## Files to create

```
/scratch/repos/eaiou/
├── manusights_competitor_mvp_plan.md           (this file)
├── app/services/
│   ├── marketplace.py                          (Phase 0 — order lifecycle, billing)
│   ├── stripe_client.py                        (Phase 0 — Stripe SDK wrapper)
│   ├── partner_keys.py                         (Phase 0 — partner-key auth)
│   ├── corpus_search.py                        (Phase 2)
│   └── review_handlers/
│       ├── __init__.py                         (Phase 1 — handler registry)
│       ├── scope_check.py                      (Phase 1)
│       ├── journal_select.py                   (Phase 1)
│       ├── outline_check.py                    (Phase 1)
│       ├── clarity_check.py                    (Phase 1)
│       ├── reference_audit.py                  (Phase 1/2)
│       ├── methods_check.py                    (Phase 1)
│       ├── full_review.py                      (Phase 1)
│       └── premium_review.py                   (Phase 1 — placeholder)
├── app/routers/
│   ├── marketplace.py                          (Phase 0 — public API endpoints)
│   ├── billing_webhook.py                      (Phase 0 — Stripe webhook)
│   └── partner.py                              (Phase 0 — partner key admin)
├── app/models/
│   ├── product.py                              (Phase 0)
│   ├── order.py                                (Phase 0)
│   ├── subscription.py                         (Phase 0)
│   └── partner_key.py                          (Phase 0)
├── app/templates/author/
│   └── _quick_reviews_sidebar.html             (Phase 0 — UI partial)
├── scripts/
│   ├── decompress_crossref.sh                  (Phase 2)
│   ├── ingest_crossref.py                      (Phase 2)
│   └── seed_products.py                        (Phase 0 — seed catalog)
├── schema/
│   └── migration_007_marketplace_core.sql      (Phase 0)
└── tests/
    ├── test_marketplace_orders.py              (Phase 0)
    ├── test_stripe_webhooks.py                 (Phase 0)
    ├── test_partner_keys.py                    (Phase 0)
    ├── test_subscription_credits.py            (Phase 0)
    └── test_handlers/                          (Phase 1)
        ├── test_scope_check.py
        └── ... etc
```

## Aggressive 5-day path (Phase 0 only, with stub handlers)

For a "show this works end-to-end" demo, ship Phase 0 with stub handlers that just return canned responses:

- Day 1: schema + Stripe customer/subscription/meter setup + product catalog seed
- Day 2: orders endpoint + idempotency + subscription credit consumption logic
- Day 3: partner key auth + webhook handler
- Day 4: Quick Reviews sidebar UI + end-to-end happy-path test
- Day 5: smoke test + deploy + screenshot

Stub handlers return `{"reasoning": "stub", "confidence": 0.5}` for now. Phase 1 swaps stubs for real handlers without touching the storefront.

## Decision gates

Before Phase 0:
1. Confirm Stripe account is in good standing for metered billing + Tax (yes per memory; eaiou stack already has Stripe scaffolded for individual review purchases)
2. Confirm pricing strategy with Eric (above is starting point; numbers easy to revise pre-launch)

Before Phase 2 (corpus):
3. Confirm Crossref license fit for embedding-based corpus search (likely yes; Crossref metadata is CC0, but document the position)

## Strategic outcome

Phase 0 alone is a complete, bookable system. Eric can sell scope-checks at $10 each as soon as Phase 0 is deployed, with stub handlers returning honest "this is a stub, will be a real review on [date]" responses. That's better than waiting for the full system because:
- It validates the commerce flow before any review-logic risk
- It lets eaiou onboard subscribers immediately
- It gives Erik Jia at Manusights something to actually look at — a working B2B surface he could integrate with TODAY by switching the partner-key direction

If Erik reverses position post-Phase 0, the API contract Eric promised to draft becomes "here's the contract; here's the deployment; you're a downstream handler now, not the gate." That's the strategic win.
