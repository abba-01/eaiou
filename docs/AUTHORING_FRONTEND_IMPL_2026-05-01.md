# eaiou Authoring Frontend Implementation Guide

**Date:** 2026-05-01
**Author:** Eric D. Martin
**Companion to:** `AUTHORING_WORKFLOW_IMPL_2026-05-01.md` (backend), `IID_PROVIDER_MODULE_PATTERN.md`, `TOS_COMPLIANCE_DOCTRINE.md`, `UXPILOT_AUTHORING_SCRIPT.md` (UX spec)
**Visual baseline:** Metronic v9.4.10 `layout-1` (HTML/Tailwind variant) + ReadEase color tokens
**Working preview:** `/tmp/eaiou-shell.html` (standalone responsive shell demonstrating the three-zone surface)

This guide translates the UX spec and backend architecture into concrete Jinja2 + Tailwind + minimal-JS implementation steps. The engineer reading this should be able to ship Phase A (shell stub) in 1–2 days and Phase B (wired to backend) in a follow-on week.

---

## 1. Why Metronic + ReadEase color tokens

eaiou runs FastAPI + Jinja2 + Tailwind 3 on the server side, with a thin client-side JS layer (no React/Vue/etc). Metronic v9.4.10's `tailwind-html-starter-kit` is the right baseline because:

- Pure HTML + Tailwind utility classes — drops into Jinja2 templates with no transpile step
- 17 layout shells; `layout-1` (left fixed sidebar + fixed top header) matches eaiou's three-zone need with one mirror addition (right sidebar)
- 122 pre-built component pages in `tailwind-html-demos/dist/html/demo1/` — the demo equivalent of layout-1 — give us account/api-keys, integrations, settings, store-client, user-table, network/get-started, public-profile, dashboards, authentication flows, and plugin pages all pre-styled
- Metronic's `kt-*` class system is utility-driven, no runtime dependency
- Apexcharts + Keenicons already wired

ReadEase brings the **color tokens** (proven on the responsive shell preview) and the **PWA scaffolding** Metronic does not ship.

---

## 2. Repository layout decisions

### 2.1 Asset placement

```
/scratch/repos/eaiou/
├── app/
│   ├── templates/
│   │   ├── layout/
│   │   │   ├── base.html                  # Three-zone shell (extends nothing; root template)
│   │   │   ├── _sidebar_left.html         # Section nav + manuscript meta
│   │   │   ├── _sidebar_right.html        # IID provider modules + activity
│   │   │   ├── _header.html               # Manuscript title + sidebar toggles + IID chip + user menu
│   │   │   └── _footer.html               # Eaiou + checksubmit footer
│   │   ├── author/
│   │   │   ├── manuscript_edit.html       # Editor surface (Phase A focus)
│   │   │   ├── manuscript_list.html       # Author dashboard
│   │   │   ├── _editor_body.html          # Center editor (markdown-backed)
│   │   │   ├── _iid_output_card.html      # Per-output card (with mandatory disclosure)
│   │   │   └── _selection_action_bar.html # Floating action bar partial
│   │   ├── account/
│   │   │   ├── api_keys.html              # IID provider API keys (from demo1/account/api-keys.html)
│   │   │   ├── integrations.html          # IID provider list (from demo1/account/integrations.html)
│   │   │   └── activity.html              # IID activity roster (from demo1/account/activity.html)
│   │   ├── auth/
│   │   │   ├── sign_in.html
│   │   │   ├── sign_up.html
│   │   │   └── verify_otp.html
│   │   └── store/                         # checksubmit storefront (Phase 0 of MVP)
│   │       ├── home.html
│   │       ├── product_detail.html
│   │       ├── shopping_cart.html
│   │       └── order_receipt.html
│   └── static/
│       ├── metronic/                      # Bundled Metronic assets (CSS + JS + media)
│       │   ├── css/styles.css
│       │   ├── vendors/                   # apexcharts, keenicons
│       │   └── media/
│       └── eaiou/
│           ├── css/eaiou.css              # eaiou-specific styles + ReadEase color overrides
│           ├── js/sidebar.js              # ajax-removable sidebar toggle persistence
│           ├── js/selection_actions.js    # Selection-to-IID floating bar wiring
│           └── js/iid_dispatch.js         # Calls /api/iid/invoke from the action buttons
├── ui-projects/
│   ├── metronic/metronic-v9.4.10/        # Source kit (kept; not deployed to production)
│   ├── readease-tailwind-pwa/            # Color-token + PWA reference
│   └── UXPILOT_AUTHORING_SCRIPT.md       # UX spec
└── docs/
    ├── AUTHORING_WORKFLOW_IMPL_2026-05-01.md  # Backend
    ├── AUTHORING_FRONTEND_IMPL_2026-05-01.md  # This file
    ├── IID_PROVIDER_MODULE_PATTERN.md
    └── TOS_COMPLIANCE_DOCTRINE.md
```

### 2.2 Asset deployment to droplet

```bash
# from eaiou repo root
rsync -av --delete \
  app/static/metronic/ app/static/eaiou/ \
  mae@edm.aybllc.org:/home/mae/eaiou/app/static/

# nginx already serves /static via the eaiou systemd service; nothing else to wire
sudo systemctl restart eaiou
```

---

## 3. Bringing Metronic assets into the eaiou static tree

### 3.1 What to copy

From `ui-projects/metronic/metronic-v9.4.10/metronic-tailwind-html-starter-kit/dist/`:

```bash
EAIOU=/scratch/repos/eaiou
METRONIC=$EAIOU/ui-projects/metronic/metronic-v9.4.10/metronic-tailwind-html-starter-kit/dist
mkdir -p $EAIOU/app/static/metronic/{css,vendors,media}

cp -r $METRONIC/assets/css/* $EAIOU/app/static/metronic/css/
cp -r $METRONIC/assets/vendors/keenicons $EAIOU/app/static/metronic/vendors/
cp -r $METRONIC/assets/vendors/apexcharts $EAIOU/app/static/metronic/vendors/
cp -r $METRONIC/assets/media/* $EAIOU/app/static/metronic/media/
```

### 3.2 What to drop

- React/Next/Vite variants in `metronic-tailwind-react-*`, `metronic-tailwind-nextjs-*` — eaiou is HTML+Jinja2
- The Figma source files
- Demos 2–10 — visual variants of the same layout-1 shell. We cherry-pick component snippets from `demo1` only
- `vendors/leaflet`, `vendors/fullcalendar` etc. — load only the vendors actually used by eaiou pages, not the full set

### 3.3 ReadEase color-token override

Create `app/static/eaiou/css/eaiou.css` to layer ReadEase tokens onto Metronic's CSS-variable theme:

```css
/* eaiou.css — color overlay on top of Metronic's styles.css */
:root {
  /* ReadEase amber/cream palette → Metronic semantic tokens */
  --color-background: #FAF3EA;          /* y50 — body background */
  --color-foreground: #090909;          /* n900 — primary text */
  --color-muted: #F5EAD8;
  --color-muted-foreground: #898989;    /* n90 */
  --color-accent: #ECCFA9;              /* y75 — sidebar active item bg */
  --color-accent-foreground: #5A3301;   /* b300 */
  --color-primary: #D0892D;             /* y300 — primary brand */
  --color-primary-foreground: #FAF3EA;
  --color-border: #DFDFDF;              /* n40 */
  --color-input: #DFDFDF;
  --color-secondary: #ECCFA9;
  --color-secondary-foreground: #5A3301;

  /* eaiou academic accents — used for state, not surface */
  --color-acad-red: #C0392B;
  --color-acad-yellow: #F1C40F;
  --color-acad-green: #27AE60;
  --color-acad-blue: #2E86C1;

  /* IID provider chip colors */
  --color-iid-mae: #D0892D;
  --color-iid-openai: #27AE60;
  --color-iid-gemini: #2E86C1;
  --color-iid-llama: #8E44AD;
  --color-iid-custom: #7F8C8D;
}

.dark {
  --color-background: #090909;
  --color-foreground: #FAF3EA;
  --color-muted: #242424;
  --color-muted-foreground: #B3B3B3;
  --color-accent: #353535;
  --color-accent-foreground: #ECCFA9;
  --color-primary: #D0892D;
  --color-primary-foreground: #090909;
  --color-border: #353535;
}

/* eaiou-specific additions */
.pin-stripe {
  background-image:
    linear-gradient(to right, rgba(208, 137, 45, 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(208, 137, 45, 0.02) 1px, transparent 1px);
  background-size: 4px 4px, 4px 4px;
}

.iid-chip-mae    { background: rgba(208, 137, 45, 0.18); color: #5A3301; border: 1px solid rgba(208, 137, 45, 0.4); }
.iid-chip-openai { background: rgba(39, 174, 96, 0.14);  color: #1B6B3D; border: 1px solid rgba(39, 174, 96, 0.4); }
.iid-chip-gemini { background: rgba(46, 134, 193, 0.14); color: #1B5A82; border: 1px solid rgba(46, 134, 193, 0.4); }
.iid-chip-llama  { background: rgba(142, 68, 173, 0.14); color: #5E2D74; border: 1px solid rgba(142, 68, 173, 0.4); }

.iid-disclosure {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 10.5px;
  color: var(--color-muted-foreground);
  background: var(--color-background);
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px dashed var(--color-border);
}

/* Right sidebar mirror — Metronic's kt-sidebar-fixed only handles the left.
   We add a parallel rule for the right side using the same drawer machinery. */
@media (min-width: 1024px) {
  body.kt-sidebar-right-fixed .kt-sidebar-right {
    position: fixed;
    top: 0; bottom: 0; right: 0;
    width: var(--sidebar-right-width, 260px);
    border-left: 1px solid var(--color-border);
    background: var(--color-background);
    z-index: 20;
  }
  body.kt-sidebar-right-fixed.kt-sidebar-right-collapse .kt-sidebar-right { width: 64px; }
  body.kt-sidebar-right-fixed.kt-sidebar-right-hidden .kt-sidebar-right { transform: translateX(100%); }
}
```

---

## 4. The base layout template

`app/templates/layout/base.html` is the root for every authenticated page. The structure mirrors Metronic `layout-1` with the right-sidebar mirror added.

```html
<!DOCTYPE html>
<html class="h-full" data-kt-theme="true" data-kt-theme-mode="light" dir="ltr" lang="en">
<head>
  <title>{% block title %}eaiou{% endblock %}</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"/>
  <link rel="icon" href="{{ url_for('static', path='metronic/media/app/favicon.ico') }}"/>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap"/>
  <link rel="stylesheet" href="{{ url_for('static', path='metronic/vendors/keenicons/styles.bundle.css') }}"/>
  <link rel="stylesheet" href="{{ url_for('static', path='metronic/vendors/apexcharts/apexcharts.css') }}"/>
  <link rel="stylesheet" href="{{ url_for('static', path='metronic/css/styles.css') }}"/>
  <link rel="stylesheet" href="{{ url_for('static', path='eaiou/css/eaiou.css') }}"/>
  {% block head_extra %}{% endblock %}
</head>
<body class="antialiased flex h-full text-base text-foreground bg-background pin-stripe demo1
             kt-sidebar-fixed kt-sidebar-right-fixed kt-header-fixed">
  <script>
    // Theme-mode bootstrap (Metronic's pattern, retained as-is)
    const defaultThemeMode = 'light';
    let themeMode = localStorage.getItem('kt-theme') || defaultThemeMode;
    if (themeMode === 'system') {
      themeMode = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.classList.add(themeMode);

    // Restore eaiou per-user sidebar state from localStorage
    {% if current_user and manuscript %}
    const sidebarKey = 'eaiou-sidebar-{{ current_user.id }}-{{ manuscript.id }}';
    const sidebarState = JSON.parse(localStorage.getItem(sidebarKey) || '{}');
    if (sidebarState.leftCollapsed)  document.body.classList.add('kt-sidebar-collapse');
    if (sidebarState.leftHidden)     document.body.classList.add('kt-sidebar-hidden');
    if (sidebarState.rightCollapsed) document.body.classList.add('kt-sidebar-right-collapse');
    if (sidebarState.rightHidden)    document.body.classList.add('kt-sidebar-right-hidden');
    {% endif %}
  </script>

  <div class="flex grow">
    {% include 'layout/_sidebar_left.html' %}
    <div class="kt-wrapper flex grow flex-col">
      {% include 'layout/_header.html' %}
      <main class="grow pt-[60px]" id="content" role="content">
        {% block main %}{% endblock %}
      </main>
      {% include 'layout/_footer.html' %}
    </div>
    {% include 'layout/_sidebar_right.html' %}
  </div>

  <script src="{{ url_for('static', path='metronic/vendors/apexcharts/apexcharts.min.js') }}" defer></script>
  <script src="{{ url_for('static', path='metronic/css/scripts.js') }}" defer></script>
  <script src="{{ url_for('static', path='eaiou/js/sidebar.js') }}" defer></script>
  <script src="{{ url_for('static', path='eaiou/js/selection_actions.js') }}" defer></script>
  <script src="{{ url_for('static', path='eaiou/js/iid_dispatch.js') }}" defer></script>
  {% block body_extra %}{% endblock %}
</body>
</html>
```

---

## 5. Sidebar templates

### 5.1 Left sidebar — `app/templates/layout/_sidebar_left.html`

Adapted from Metronic's `layout-1/index.html` left sidebar, with Metronic's `kt-menu` accordion replaced by manuscript-section navigation. Backend supplies `manuscript`, `sections`, `tags`, `versions` context.

```html
<aside class="kt-sidebar bg-background border-e border-e-border fixed top-0 bottom-0 z-20 hidden lg:flex flex-col items-stretch shrink-0 [--kt-drawer-enable:true] lg:[--kt-drawer-enable:false]"
       data-kt-drawer="true"
       data-kt-drawer-class="kt-drawer kt-drawer-start top-0 bottom-0"
       id="sidebar">
  <div class="kt-sidebar-header hidden lg:flex items-center justify-between px-3 lg:px-6 shrink-0 h-[60px]">
    <a href="/" class="flex items-center gap-2">
      <div class="w-7 h-7 rounded bg-primary text-primary-foreground grid place-items-center font-bold text-sm">e</div>
      <span class="kt-sidebar-not-collapsed:inline hidden font-semibold text-foreground">eaiou</span>
    </a>
    <button class="kt-btn kt-btn-outline kt-btn-icon size-[30px]" data-kt-toggle="body" data-kt-toggle-class="kt-sidebar-collapse">
      <i class="ki-filled ki-black-left-line kt-toggle-active:rotate-180 transition-all duration-300"></i>
    </button>
  </div>

  <div class="kt-sidebar-content flex grow shrink-0 py-3 px-3 overflow-y-auto kt-scrollable-y-hover">
    {% if manuscript %}
    <!-- Manuscript meta -->
    <div class="kt-module mb-3 w-full">
      <div class="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 kt-sidebar-not-collapsed:block hidden">Manuscript</div>
      <div class="font-semibold text-foreground leading-snug kt-sidebar-not-collapsed:block hidden">{{ manuscript.title }}</div>
      <div class="flex flex-wrap gap-1 mt-2 kt-sidebar-not-collapsed:flex hidden">
        <span class="kt-chip">{{ manuscript.status }}</span>
        {% if manuscript.target_venue %}
          <span class="kt-chip iid-chip-gemini">{{ manuscript.target_venue }}</span>
        {% endif %}
      </div>
    </div>

    <!-- Section navigator -->
    <div class="text-[10px] uppercase tracking-wider text-muted-foreground px-2 mb-1 kt-sidebar-not-collapsed:block hidden">Sections</div>
    <nav class="flex flex-col gap-0.5 w-full">
      {% for section in sections %}
      <a class="px-2 py-1.5 rounded hover:bg-accent flex items-center justify-between text-sm
                {% if section.id == active_section_id %}bg-accent text-accent-foreground font-medium{% endif %}"
         href="#section-{{ section.anchor }}">
        <span>{{ section.title }}</span>
        {% if section.iid_output_count %}
          <span class="section-badge">{{ section.iid_output_count }}</span>
        {% endif %}
      </a>
      {% endfor %}
    </nav>

    <!-- Version timeline -->
    <div class="text-[10px] uppercase tracking-wider text-muted-foreground px-2 mt-4 mb-1 kt-sidebar-not-collapsed:block hidden">Versions</div>
    <ul class="text-xs text-muted-foreground px-2 space-y-1 kt-sidebar-not-collapsed:block hidden">
      {% for v in versions[:5] %}
        <li>{{ v.label }} — {{ v.created_at | naturaltime }}{% if v.is_current %} <span class="text-acad-green">●</span>{% endif %}</li>
      {% endfor %}
    </ul>
    {% else %}
    <div class="text-sm text-muted-foreground px-2">No manuscript loaded</div>
    {% endif %}
  </div>
</aside>
```

### 5.2 Right sidebar — `app/templates/layout/_sidebar_right.html`

The IID provider modules. Each entry is rendered server-side from `current_user.iid_providers` + per-provider catalog of `actions`. ToS Compliance Doctrine §1 Rule 4: every output card MUST emit the disclosure block — that is enforced in `_iid_output_card.html`, not here.

```html
<aside class="kt-sidebar kt-sidebar-right bg-background border-s border-s-border fixed top-0 bottom-0 z-20 hidden lg:flex flex-col items-stretch shrink-0 [--kt-drawer-enable:true] lg:[--kt-drawer-enable:false]"
       data-kt-drawer="true"
       data-kt-drawer-class="kt-drawer kt-drawer-end top-0 bottom-0"
       id="sidebar_right">
  <div class="hidden lg:flex items-center justify-between px-4 h-[60px] shrink-0 border-b border-border">
    <span class="kt-sidebar-not-collapsed:inline hidden font-semibold text-foreground text-sm">IID Providers</span>
    <button class="kt-btn kt-btn-outline kt-btn-icon size-[30px]" data-kt-toggle="body" data-kt-toggle-class="kt-sidebar-right-collapse">
      <i class="ki-filled ki-black-right-line kt-toggle-active:rotate-180 transition-all duration-300"></i>
    </button>
  </div>

  <div class="flex grow shrink-0 py-3 px-3 flex-col gap-3 overflow-y-auto kt-scrollable-y-hover">
    {% for provider in current_user.iid_providers %}
    <div class="kt-module" data-provider-id="{{ provider.id }}">
      <div class="flex items-center justify-between mb-2">
        <span class="kt-chip iid-chip-{{ provider.name }}">{{ provider.display_name }}</span>
        <span class="text-acad-green text-[10px]">●  ready</span>
      </div>
      <div class="text-xs text-muted-foreground mb-3 font-mono">{{ provider.default_model }}</div>
      <div class="grid grid-cols-2 gap-1.5">
        {% for action in provider.enabled_actions %}
        <button class="kt-btn kt-btn-outline kt-btn-sm"
                data-iid-action
                data-provider-id="{{ provider.id }}"
                data-action-name="{{ action.name }}">
          {{ action.label }} {{ action.cost_display }}
        </button>
        {% endfor %}
      </div>
    </div>
    {% endfor %}

    <!-- Add-IID -->
    <button class="kt-btn kt-btn-ghost w-full justify-center text-muted-foreground border border-dashed border-border"
            data-kt-modal-open="#add_iid_modal">
      + Add IID Module
    </button>

    <!-- Activity summary -->
    <div class="kt-module">
      <div class="text-[10px] uppercase tracking-wider text-muted-foreground mb-2">Session Activity</div>
      <div class="flex items-center justify-between text-xs">
        <span>Outputs</span><span class="font-semibold">{{ session_iid_count }}</span>
      </div>
      <div class="flex items-center justify-between text-xs mt-1">
        <span>Cost</span><span class="font-semibold">${{ '%.2f'|format(session_iid_cost) }}</span>
      </div>
      <a href="/account/activity" class="kt-btn kt-btn-ghost kt-btn-sm w-full mt-2 text-acad-blue justify-center">View roster →</a>
    </div>
  </div>
</aside>
```

---

## 6. Header — `app/templates/layout/_header.html`

```html
<header class="kt-header fixed top-0 z-10 flex items-stretch shrink-0 bg-background border-b border-border h-[60px]"
        data-kt-sticky="true" id="header">
  <div class="flex items-center justify-between gap-4 px-5 grow">
    <button class="kt-btn kt-btn-ghost kt-btn-icon hidden lg:inline-flex"
            onclick="document.body.classList.toggle('kt-sidebar-hidden')"
            title="Hide / show left sidebar">
      <i class="ki-filled ki-side-panel-left"></i>
    </button>

    {% if manuscript %}
      <input type="text"
             value="{{ manuscript.title }}"
             class="font-serif text-[15px] font-medium text-foreground bg-transparent border-0 outline-none flex-grow min-w-0 truncate"
             data-manuscript-title-input
             data-manuscript-id="{{ manuscript.id }}" />
      <span class="text-xs text-acad-green flex items-center gap-1 shrink-0" data-save-state>
        <i class="ki-filled ki-shield-tick"></i> saved
      </span>
      <span class="text-xs text-muted-foreground shrink-0">{{ manuscript.word_count }} words</span>
      {% if manuscript.target_venue %}
        <span class="kt-chip iid-chip-gemini shrink-0">→ {{ manuscript.target_venue }}</span>
      {% endif %}
      <button class="kt-btn kt-btn-outline kt-btn-sm shrink-0" data-kt-modal-open="#iid_activity_modal">
        <i class="ki-filled ki-time"></i>
        {{ session_iid_count }} outputs · ${{ '%.2f'|format(session_iid_cost) }}
      </button>
    {% else %}
      <span class="font-semibold text-foreground">eaiou</span>
    {% endif %}

    <button class="kt-btn kt-btn-ghost kt-btn-icon shrink-0" title="Account">
      <div class="w-7 h-7 rounded-full bg-y100 grid place-items-center text-xs font-semibold text-b300">
        {{ current_user.initials }}
      </div>
    </button>

    <button class="kt-btn kt-btn-ghost kt-btn-icon hidden lg:inline-flex"
            onclick="document.body.classList.toggle('kt-sidebar-right-hidden')"
            title="Hide / show right sidebar">
      <i class="ki-filled ki-side-panel-right"></i>
    </button>
  </div>
</header>
```

---

## 7. The editor surface — `app/templates/author/manuscript_edit.html`

```html
{% extends 'layout/base.html' %}
{% block title %}{{ manuscript.title }} — eaiou{% endblock %}

{% block main %}
<div class="max-w-3xl mx-auto px-6 py-8">
  <div class="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
    <span>Sections</span><span>›</span>
    <span class="text-primary font-medium">{{ active_section.title }}</span>
  </div>

  <article class="font-serif text-[15.5px] leading-[1.7] text-foreground space-y-4"
           data-manuscript-editor
           data-manuscript-id="{{ manuscript.id }}"
           contenteditable="true">
    {% for block in manuscript.blocks %}
      {% if block.type == 'heading_2' %}
        <h2 class="text-2xl font-semibold tracking-tight" id="section-{{ block.anchor }}">{{ block.text }}</h2>
      {% elif block.type == 'heading_3' %}
        <h3 class="text-lg font-semibold mt-6">{{ block.text }}</h3>
      {% elif block.type == 'paragraph' %}
        <p>{{ block.html | safe }}</p>
      {% endif %}
    {% endfor %}
  </article>

  {% include 'author/_selection_action_bar.html' %}

  <section class="mt-10">
    <h3 class="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wider">IID Outputs</h3>
    <div class="space-y-3" data-iid-output-stream>
      {% for output in recent_iid_outputs %}
        {% include 'author/_iid_output_card.html' %}
      {% endfor %}
    </div>
  </section>
</div>
{% endblock %}
```

---

## 8. The IID output card — `app/templates/author/_iid_output_card.html`

```html
<article class="kt-module" data-iid-output-id="{{ output.id }}" data-provider="{{ output.provider.name }}">
  <header class="flex items-center justify-between mb-2">
    <div class="flex items-center gap-2">
      <span class="kt-chip iid-chip-{{ output.provider.name }}">{{ output.provider.display_name }} · {{ output.action.name }}</span>
      <span class="text-xs text-muted-foreground">{{ output.created_at | naturaltime }} · ${{ '%.2f'|format(output.cost) }}</span>
    </div>
    <div class="flex gap-1.5">
      <button class="kt-btn kt-btn-ghost kt-btn-sm" data-iid-insert-comment>Insert as comment</button>
      <button class="kt-btn kt-btn-ghost kt-btn-sm" data-iid-dismiss>Dismiss</button>
    </div>
  </header>

  <div class="font-serif text-[14px] leading-[1.6] text-foreground space-y-2">
    {{ output.body_html | safe }}
  </div>

  <!-- MANDATORY DISCLOSURE BLOCK — Rule 4 of the ToS Compliance Doctrine -->
  <!-- Never collapsible, never hidden, never optional. Stripped only on author-explicit redaction. -->
  <footer class="iid-disclosure mt-3">
    provider={{ output.provider.legal_name }} ·
    model_family={{ output.model_family }} ·
    instance_hash={{ output.instance_hash }}<br>
    action={{ output.action.name }} ·
    timestamp={{ output.created_at.isoformat() }}Z ·
    input_tokens={{ output.input_tokens }} ·
    output_tokens={{ output.output_tokens }}
  </footer>
</article>
```

---

## 9. The selection-action floating bar

`app/templates/author/_selection_action_bar.html`:

```html
<div class="kt-module fixed z-30 hidden flex-wrap gap-1.5 max-w-md shadow-md"
     id="selection_action_bar"
     data-iid-selection-bar>
  {% for provider in current_user.iid_providers %}
    {% for action in provider.enabled_actions %}
      <button class="kt-btn kt-btn-outline kt-btn-sm"
              data-iid-action
              data-provider-id="{{ provider.id }}"
              data-action-name="{{ action.name }}">
        <span class="kt-chip iid-chip-{{ provider.name }}" style="padding:0 4px; font-size:10px;">
          {{ provider.short_letter }}
        </span>
        {{ action.short_label }}
      </button>
    {% endfor %}
  {% endfor %}
</div>
```

JS wiring in `app/static/eaiou/js/selection_actions.js`:

```javascript
(function() {
  const bar = document.getElementById('selection_action_bar');
  if (!bar) return;

  document.addEventListener('selectionchange', () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) {
      bar.classList.add('hidden');
      return;
    }
    const editor = sel.anchorNode?.closest?.('[data-manuscript-editor]');
    if (!editor) {
      bar.classList.add('hidden');
      return;
    }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    bar.classList.remove('hidden');
    bar.classList.add('flex');
    bar.style.top = `${window.scrollY + rect.top - bar.offsetHeight - 8}px`;
    bar.style.left = `${window.scrollX + rect.left}px`;
    bar.dataset.selectedText = sel.toString();
  });

  bar.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-iid-action]');
    if (!btn) return;
    window.eaiou.iidDispatch({
      providerId: btn.dataset.providerId,
      actionName: btn.dataset.actionName,
      inputs: { selected_text: bar.dataset.selectedText },
      manuscriptId: document.querySelector('[data-manuscript-editor]').dataset.manuscriptId,
    });
  });
})();
```

---

## 10. IID dispatch from the client

`app/static/eaiou/js/iid_dispatch.js`:

```javascript
(function() {
  window.eaiou = window.eaiou || {};
  window.eaiou.iidDispatch = async function({ providerId, actionName, inputs, manuscriptId }) {
    const idemKey = crypto.randomUUID();
    const stream = document.querySelector('[data-iid-output-stream]');
    const placeholder = renderPlaceholderCard({ providerId, actionName });
    stream.prepend(placeholder);

    try {
      const res = await fetch('/api/iid/invoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idemKey,
        },
        body: JSON.stringify({
          provider_id: providerId,
          action_name: actionName,
          manuscript_id: manuscriptId,
          inputs,
        }),
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const output = await res.json();
      placeholder.replaceWith(renderOutputCard(output));
    } catch (err) {
      placeholder.querySelector('[data-iid-status]').textContent = 'failed';
      console.error('IID dispatch failed', err);
    }
  };

  function renderPlaceholderCard({ providerId, actionName }) {
    const el = document.createElement('article');
    el.className = 'kt-module animate-pulse';
    el.innerHTML = `
      <div class="text-xs text-muted-foreground" data-iid-status>running ${actionName}...</div>
    `;
    return el;
  }

  function renderOutputCard(output) {
    // Server returns a pre-rendered HTML fragment via /api/iid/invoke?as_html=1.
    // For pure-JSON callers, build the card client-side with the same disclosure layout.
    const el = document.createElement('article');
    el.className = 'kt-module';
    el.dataset.iidOutputId = output.id;
    el.dataset.provider = output.provider.name;
    el.innerHTML = output.html_fragment; // server emits the full card incl. mandatory disclosure
    return el;
  }
})();
```

The server endpoint is `app/api_iid.py::POST /api/iid/invoke` and is documented in `AUTHORING_WORKFLOW_IMPL_2026-05-01.md` §5.

---

## 11. Sidebar persistence — `app/static/eaiou/js/sidebar.js`

```javascript
(function() {
  const userId = document.body.dataset.userId;
  const manuscriptId = document.body.dataset.manuscriptId;
  if (!userId || !manuscriptId) return;
  const key = `eaiou-sidebar-${userId}-${manuscriptId}`;

  function persist() {
    localStorage.setItem(key, JSON.stringify({
      leftCollapsed:  document.body.classList.contains('kt-sidebar-collapse'),
      leftHidden:     document.body.classList.contains('kt-sidebar-hidden'),
      rightCollapsed: document.body.classList.contains('kt-sidebar-right-collapse'),
      rightHidden:    document.body.classList.contains('kt-sidebar-right-hidden'),
    }));
  }
  // Watch class changes
  new MutationObserver(persist).observe(document.body, { attributes: true, attributeFilter: ['class'] });
})();
```

---

## 12. FastAPI route mapping

| Route | Template | Purpose |
|---|---|---|
| `GET /` | `pages/landing.html` | Public landing |
| `GET /sign-in` | `auth/sign_in.html` | Sign-in (Metronic auth pattern) |
| `GET /sign-up` | `auth/sign_up.html` | Sign-up + IID-disclosure agreement |
| `GET /dashboard` | `author/dashboard.html` | Manuscript list + recent activity |
| `GET /manuscripts/{id}/edit` | `author/manuscript_edit.html` | The authoring surface (this guide's focus) |
| `POST /api/iid/invoke` | (JSON) | Dispatch IID action; returns rendered output card |
| `GET /account/api-keys` | `account/api_keys.html` | IID provider API keys (Metronic demo1 page) |
| `GET /account/integrations` | `account/integrations.html` | IID provider list + enable/disable |
| `GET /account/activity` | `account/activity.html` | IID activity roster |
| `GET /store` | `store/home.html` | checksubmit storefront (Phase 0) |

---

## 13. Phased build sequence

Each phase is shippable on its own.

### Phase A — Shell stub (1–2 days)

- [ ] Copy Metronic assets into `app/static/metronic/`
- [ ] Create `app/static/eaiou/css/eaiou.css` with the color-token overrides
- [ ] Create `app/templates/layout/{base,_sidebar_left,_sidebar_right,_header,_footer}.html`
- [ ] Create `app/templates/author/manuscript_edit.html` extending `layout/base.html` with stub editor
- [ ] Create `app/static/eaiou/js/sidebar.js` for persistence
- [ ] Wire FastAPI route `GET /manuscripts/{id}/edit` to render `manuscript_edit.html` with stub manuscript context
- [ ] Verify in browser at `localhost:63xxx/manuscripts/1/edit` — both sidebars visible at ≥1024px, drawer behavior on narrow viewports, toggles persist

### Phase B — Real manuscript backend wiring (2–3 days)

- [ ] Replace stub manuscript context with DB-backed `tbleaiou_manuscripts` join + `tbleaiou_manuscript_blocks` for the editor body
- [ ] Wire title-input save to `PUT /api/manuscripts/{id}` (debounced)
- [ ] Wire editor body autosave to `PUT /api/manuscripts/{id}/blocks`
- [ ] Section-jump anchors generated from `tbleaiou_manuscript_blocks.anchor`
- [ ] Version timeline from `tbleaiou_manuscript_snapshots`

### Phase C — IID dispatcher + output cards (2 days)

- [ ] Implement `app/services/iid_dispatcher.py` per `AUTHORING_WORKFLOW_IMPL_2026-05-01.md` §4
- [ ] Implement `app/api_iid.py::POST /api/iid/invoke` that returns both JSON and rendered HTML fragment of the output card
- [ ] Implement `_iid_output_card.html` partial that emits the mandatory disclosure block
- [ ] Implement `_selection_action_bar.html` partial + `selection_actions.js` wiring
- [ ] Implement `iid_dispatch.js` client
- [ ] Verify a real Mae call flow: select text → click Mae · scope_check → output card renders with disclosure

### Phase D — Provider configuration UI (1 day)

- [ ] Adapt `account/api-keys.html` from Metronic demo1
- [ ] Adapt `account/integrations.html` for IID provider list
- [ ] Adapt `account/activity.html` for IID activity roster
- [ ] Wire `app/api_iid_providers.py` for CRUD on `tbleaiou_iid_providers`

### Phase E — checksubmit storefront sidebar (per `manusights_competitor_mvp_plan.md`, parallel-safe)

- [ ] Add Quick Reviews sidebar partial to manuscript_edit.html (§7 of MVP plan)
- [ ] Wire `app/routers/marketplace.py` per the MVP plan

---

## 14. Things explicitly excluded from this guide

- **Image / file uploads** — covered separately when the manuscript-editor block model needs media support
- **LaTeX / MathJax rendering** — defer to Phase F; will use KaTeX as the lightweight option
- **Real-time multi-author editing** — out of scope for Phase A–E; the manuscript model assumes single-author edits with snapshots
- **Mobile UX details** — Metronic's drawer system handles narrow viewports adequately for now; mobile-first polish is Phase G
- **Print / PDF export** — handled by an existing eaiou pipeline, no frontend changes required

---

## 15. Verification checklist

Before declaring Phase A complete:

- [ ] In Chrome at width ≥1280px: left sidebar + center editor + right sidebar all visible, no horizontal scroll
- [ ] Click left toggle: left sidebar hides via translate, editor expands to fill, header offset adjusts
- [ ] Click right toggle: same on the right
- [ ] Click left collapse button: left sidebar shrinks to 64px icon rail, all `label-full` elements hidden
- [ ] Click right collapse button: same on the right
- [ ] Reload page: sidebar states restored from localStorage
- [ ] At width <1024px: both sidebars hidden by default; drawer toggles slide them in from edges
- [ ] Light/dark theme toggle: all sidebars + editor switch palette correctly
- [ ] No console errors

Before declaring Phase C complete:

- [ ] Click any IID action button → placeholder card appears in output stream
- [ ] Server returns rendered fragment → placeholder replaced with full card
- [ ] Disclosure block visible on every output
- [ ] Network panel: only one IID call per click; no chaining; no background calls
- [ ] Audit log row exists in `tbleaiou_iid_actions` for every output card
