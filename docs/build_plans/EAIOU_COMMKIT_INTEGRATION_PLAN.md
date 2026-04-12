# EAIOU — CommKit Integration Plan (Claude Code Lockfile)

**Version:** 1.0.0 — 2026-04-12
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742
**Purpose:** This document specifies how to integrate scientific communication guidance into eaiou's authorship workflow. The MIT CommKit (Broad Institute) provides 31 structured guides covering every aspect of scientific writing and presentation. We synthesize this content into contextual **drawers** (slide-out panels) and **modals** (overlay dialogs) that appear at the exact moment an author needs them — during submission, writing, revision, and presentation preparation.
**Companions:** All four build plans (Frontend, Backend, API, MCP)
**Status:** CANONICAL
**Source material:** MIT Broad Institute CommKit (mitcommlab.mit.edu/broad/commkit/) — adapted, restructured, and contextualized for eaiou's observer-preserving publishing workflow.

---

## 0. RULES FOR CLAUDE CODE

1. **CommKit content is guidance, not enforcement.** Drawers and modals are OPTIONAL help — authors can dismiss them. They never block submission.
2. **Content is adapted, not copied verbatim.** Restructure for eaiou's context. Use eaiou terminology. Respect eaiou's design system (Spectral + JetBrains Mono, eaiou colors).
3. **Drawers slide in from the right** (320px wide) over the sidebar. They don't replace the sidebar — they overlay it.
4. **Modals are centered overlays** (max-width 640px) with a dark backdrop. Used for longer walkthroughs with multiple steps.
5. **Every drawer/modal has a close button** (× in top-right) and can be dismissed with Escape.
6. **Trigger points are inline help icons** (ⓘ) next to field labels in the submission wizard, or "Writing Guide" buttons in the authorship workspace.
7. **Content is organized by the CommKit's own structure:** Criteria for Success → Document Map → Purpose → Audience → Skills. This is the pedagogical flow — don't rearrange it.
8. **Use the eaiou design system.** Drawers use `module-panel` styling. Typography follows the spec. No external CSS.

---

## 1. THE 31 COMMKIT GUIDES (SOURCE INVENTORY)

Each guide has a consistent internal structure that maps cleanly to drawer/modal content:

| # | Guide Title | Category | eaiou Context |
|---|------------|----------|---------------|
| 1 | Slideshow | Visual | Presentation prep (future feature) |
| 2 | Poster | Visual | Conference poster prep (future) |
| 3 | Figure Design | Visual | Figures in manuscripts |
| 4 | General Tips | Journal Article | All writing stages |
| 5 | Journal Article: Abstract | Journal Article | Submit Step 1 (Abstract field) |
| 6 | Journal Article: Introduction | Journal Article | Author workspace — writing |
| 7 | Journal Article: Methods | Journal Article | Author workspace — methods |
| 8 | Journal Article: Discussion | Journal Article | Author workspace — discussion |
| 9 | Journal Article: Results | Journal Article | Author workspace — results |
| 10 | Elevator Pitch | Professional | Author profile / collaboration |
| 11 | CV/Resume | Professional | Author profile (future) |
| 12 | Cover Letter: General | Professional | Future: job board integration |
| 13 | Cover Letter: Faculty | Professional | Future: job board integration |
| 14 | NSF GRFP Research Proposal | Applications | Grant writing guide |
| 15 | NSF GRFP Personal Statement | Applications | Grant writing guide |
| 16 | Graduate School Personal Statement | Applications | Onboarding content |
| 17 | Fellowship Application | Applications | Grant writing guide |
| 18 | NIHGRI UM1 Application | Applications | Specialized guide |
| 19 | Postdoc Fellowships Index | Applications | Resource directory |
| 20 | Public Policy Communication: Intro | Science Policy | Cross-domain writing |
| 21 | Policy Elevator Pitch | Science Policy | Cross-domain writing |
| 22 | Policy Memo | Science Policy | Cross-domain writing |
| 23 | Policy Presentation | Science Policy | Cross-domain writing |
| 24 | Congressional Hill Meeting | Science Policy | Specialized guide |
| 25 | Letter of Support | Science Policy | Specialized guide |
| 26 | Op-Ed | Science Policy | Public communication |
| 27 | Public Comment on Regulation | Science Policy | Specialized guide |
| 28 | Coding Mindset | Coding | Code submissions |
| 29 | Coding and Comment Style | Coding | Code submissions |
| 30 | File Structure | Coding | Bundle organization |

---

## 2. WHERE DRAWERS AND MODALS APPEAR

### 2.1 Submission Wizard (6 steps — highest priority)

| Wizard Step | Drawer/Modal Triggers | CommKit Guides Used |
|-------------|----------------------|---------------------|
| **Step 1: Metadata** | ⓘ next to "Abstract" field → Abstract Drawer | #5 Abstract |
| | ⓘ next to "Title" field → Title Tips Drawer | #4 General Tips (title section) |
| | ⓘ next to "Keywords" field → Keywords Drawer | #4 General Tips (keywords) |
| **Step 2: Bundle** | ⓘ next to "Manuscript upload" → Structure Guide Modal | #4 General Tips, #6 Intro, #7 Methods, #8 Discussion, #9 Results |
| | ⓘ next to "Figures" → Figure Design Drawer | #3 Figure Design |
| | ⓘ next to "Code" → Code Style Drawer | #28 Coding Mindset, #29 Coding Style, #30 File Structure |
| **Step 3: AI Usage** | "How to disclose AI usage" → AI Disclosure Drawer | eaiou-native content (from AI Disclosure Policy) |
| **Step 4: Triage** | ⓘ next to "Citation" → Literature Review Drawer | #4 General Tips (lit review section) |
| | "Why Remsearch?" → Remsearch Explainer Modal | eaiou-native content |
| **Step 5: Declarations** | ⓘ next to "Authorship" → CRediT Roles Drawer | eaiou-native + CommKit #4 |
| **Step 6: Confirm** | "Writing Checklist" button → Pre-Submit Checklist Modal | #4 General Tips (checklist) |

### 2.2 Author Workspace (manuscript editing)

| Context | Trigger | CommKit Guides Used |
|---------|---------|---------------------|
| Writing abstract | ⓘ icon or "Guide" button | #5 Abstract (full guide as modal) |
| Writing introduction | ⓘ or "Guide" | #6 Introduction (full guide as modal) |
| Writing methods | ⓘ or "Guide" | #7 Methods (full guide as modal) |
| Writing discussion | ⓘ or "Guide" | #8 Discussion (full guide as modal) |
| Writing results | ⓘ or "Guide" | #9 Results (full guide as modal) |
| Any writing context | "General Tips" in toolbar | #4 General Tips (full guide as modal) |
| Figure creation/upload | "Figure Guide" button | #3 Figure Design (drawer) |
| Slide preparation | "Presentation Guide" | #1 Slideshow (modal) |
| Poster preparation | "Poster Guide" | #2 Poster (modal) |

### 2.3 Author Dashboard / Profile

| Context | Trigger | CommKit Guides Used |
|---------|---------|---------------------|
| Elevator pitch field | ⓘ icon | #10 Elevator Pitch (drawer) |
| CV/bio section | ⓘ icon | #11 CV/Resume (drawer) |

### 2.4 Discovery / Collaboration

| Context | Trigger | CommKit Guides Used |
|---------|---------|---------------------|
| Open Collab board — "Describe your need" | ⓘ icon | #10 Elevator Pitch (adapted for research needs) |
| Gap Map — "Write against this gap" | "Writing Guide" button | #4 General Tips + #6 Introduction (adapted for gap-filling papers) |

### 2.5 Reviewer Console

| Context | Trigger | CommKit Guides Used |
|---------|---------|---------------------|
| Writing review notes | "Review Writing Tips" | #4 General Tips (adapted: concise, constructive, specific) |

---

## 3. DRAWER SPECIFICATIONS

### 3.1 Drawer Component (shared)

```
Class: .commkit-drawer
Width: 320px
Position: fixed right, top to bottom
z-index: 900 (above sidebar, below modals)
Background: var(--paper)
Border-left: 2px solid var(--river)
Animation: slide in from right (200ms ease)
Close: × button (top-right) + Escape key
Scrollable: yes (scroll-area class)
```

**Internal structure:**
```html
<div class="commkit-drawer">
  <div class="commkit-drawer-header">
    <span class="commkit-drawer-title">{Guide Title}</span>
    <span class="commkit-drawer-source">Adapted from MIT CommKit</span>
    <button class="commkit-drawer-close">×</button>
  </div>
  <div class="commkit-drawer-body scroll-area">
    <!-- Sections from the guide -->
    <div class="commkit-section">
      <div class="commkit-section-label">{Section Name}</div>
      <div class="commkit-section-content">{Content}</div>
    </div>
  </div>
</div>
```

**Styling:**
- `.commkit-drawer-header`: padding 14px, border-bottom 0.5px solid var(--paper3), display flex, justify-content space-between
- `.commkit-drawer-title`: font-family var(--mono), font-size 11px, uppercase, letter-spacing 0.08em, color var(--river)
- `.commkit-drawer-source`: font-family var(--mono), font-size 9px, color var(--ink3)
- `.commkit-section-label`: same as `section-label` from design system
- `.commkit-section-content`: font-family var(--serif), font-size 13px, line-height 1.7, color var(--ink2)

### 3.2 Individual Drawer Content

Each drawer below lists its sections in order. Claude Code: implement these as the drawer body content.

---

#### DRAWER: Abstract Guide
**Trigger:** ⓘ next to Abstract field in Submit Step 1
**Source:** CommKit #5 — Journal Article: Abstract

**Sections:**
1. **When to Write** — Write the abstract LAST, after the paper is complete. It's a summary, not a starting point.
2. **Purpose** — The abstract is a self-contained summary that allows readers to decide whether to read the full paper. It must stand alone.
3. **Formula** — Four-part structure:
   - **Background/Motivation** (1–2 sentences): Why does this research matter?
   - **Methods** (1–2 sentences): What did you do?
   - **Results** (2–3 sentences): What did you find?
   - **Implications** (1–2 sentences): Why do the results matter?
4. **eaiou Note** — Your abstract becomes the `introtext` of the php article. It's what appears in paper cards on the discovery surface. Make it count — it's the first thing readers see, sorted by q_signal, not time.

---

#### DRAWER: Title Tips
**Trigger:** ⓘ next to Title field in Submit Step 1
**Source:** CommKit #4 — General Tips

**Sections:**
1. **Strong Titles Tell a Message** — A strong title is a full sentence that conveys the main finding or claim. Weak titles are nouns ("Analysis of X"). Strong titles are claims ("X causes Y under Z conditions").
2. **Test Your Title** — If someone reads only your title and your abstract, do they get the point? If not, revise.
3. **eaiou Note** — Your title is the `paper-card-title` in the discovery feed. With Temporal Blindness, your title has to do ALL the work of attracting readers — there's no "newest first" to help you.

---

#### DRAWER: Figure Design
**Trigger:** ⓘ next to Figures upload in Submit Step 2
**Source:** CommKit #3 — Figure Design

**Sections:**
1. **Criteria for Success** — Each figure makes exactly one point. The point is obvious within 5 seconds. Labels are readable. Colors are accessible.
2. **Signal-to-Noise** — Remove everything that doesn't support the point. Simplify labels. Add emphasis with color/arrows. Publication figures ≠ presentation figures.
3. **Platform Awareness** — Figures in eaiou will appear in both the article reader (max-width ~640px) and potentially in discovery cards. Design for both scales.
4. **Accessibility** — Use colorblind-safe palettes. Add text labels, don't rely on color alone.

---

#### DRAWER: Code Style
**Trigger:** ⓘ next to Code upload in Submit Step 2
**Source:** CommKit #28 Coding Mindset + #29 Coding Style + #30 File Structure

**Sections:**
1. **Coding Mindset** — Code is communication. Write code for humans first, machines second. Your future self (and reviewers) need to understand it.
2. **Comment Style** — Comment the WHY, not the WHAT. The code says what it does; comments explain why.
3. **File Structure** — Organize code like a paper: clear hierarchy, README at the top, logical naming, no orphan files.
4. **eaiou Note** — Code uploaded to your submission bundle goes into `. It's part of the full-context archive and is searchable. Clean code is discoverable code.

---

#### DRAWER: Elevator Pitch
**Trigger:** ⓘ next to collaboration description in Discover Open
**Source:** CommKit #10 — Elevator Pitch

**Sections:**
1. **Criteria for Success** — In 30 seconds, the listener understands what you do, why it matters, and what you need.
2. **Structure** — Hook (why should they care?) → What you do → Why it matters → The ask (what you need)
3. **Audience** — Tailor to who's reading. On the collaboration board, your audience is potential collaborators from OTHER domains.
4. **eaiou Note** — Your `collab_seek` field is your elevator pitch for collaboration. rs:LookCollab tags make it discoverable. Be specific about what you need.

---

#### DRAWER: Literature Review / Citation
**Trigger:** ⓘ next to citation fields in Submit Step 4 (Triage)
**Source:** CommKit #4 — General Tips (literature review section)

**Sections:**
1. **Why Cite** — Citations establish your work's position in the field. They're not decoration — they're the intellectual lineage.
2. **What to Include** — Cite foundational work, recent advances, and directly relevant methods. Include work you disagree with.
3. **What Remsearch Adds** — eaiou's Remsearch (literature triage) goes further: you also log what you DIDN'T use and WHY. This is the "un-space made searchable" — your excluded sources might be someone else's breakthrough.
4. **eaiou Note** — Every source you add to Remsearch — used or unused — becomes part of the searchable archive. Cross-domain serendipity is real.

---

### 3.3 Additional Drawers (lower priority — build after core)

| Drawer | Trigger | Source |
|--------|---------|--------|
| Keywords Guide | ⓘ next to Keywords | General Tips (adapted) |
| CRediT Roles | ⓘ next to Authorship in Step 5 | eaiou-native + CRediT taxonomy |
| AI Disclosure | ⓘ next to AI fields in Step 3 | AI Disclosure Policy (eaiou-native) |
| Review Writing Tips | ⓘ in Reviewer Console | General Tips (adapted for reviews) |
| CV/Resume Guide | ⓘ in Author Profile | CommKit #11 |
| Poster Guide | ⓘ in future poster feature | CommKit #2 |

---

## 4. MODAL SPECIFICATIONS

### 4.1 Modal Component (shared)

```
Class: .commkit-modal
Max-width: 640px
Position: fixed center
z-index: 1000
Background: #fff
Border-radius: 4px
Box-shadow: 0 16px 64px rgba(0,0,0,0.2)
Backdrop: rgba(14,13,11,0.5)
Animation: fade in (200ms)
Close: × button + Escape + backdrop click
Scrollable: yes (max-height 80vh, scroll-area inside)
```

**Internal structure:**
```html
<div class="commkit-modal-backdrop">
  <div class="commkit-modal">
    <div class="commkit-modal-header">
      <span class="commkit-modal-title">{Guide Title}</span>
      <span class="commkit-modal-source">Adapted from MIT CommKit</span>
      <button class="commkit-modal-close">×</button>
    </div>
    <div class="commkit-modal-nav">
      <!-- Step tabs for multi-section walkthrough -->
      <span class="commkit-modal-tab active">Criteria</span>
      <span class="commkit-modal-tab">Structure</span>
      <span class="commkit-modal-tab">Purpose</span>
      <span class="commkit-modal-tab">Audience</span>
      <span class="commkit-modal-tab">Skills</span>
    </div>
    <div class="commkit-modal-body scroll-area">
      <!-- Active section content -->
    </div>
    <div class="commkit-modal-footer">
      <button class="btn btn-secondary">← Previous</button>
      <span class="commkit-modal-progress">2 / 5</span>
      <button class="btn btn-primary">Next →</button>
    </div>
  </div>
</div>
```

### 4.2 Modal Walkthroughs (5 core article guides)

Each modal is a multi-step walkthrough. The author navigates with Previous/Next buttons or clicks tabs directly. Each step maps to one section of the CommKit guide.

---

#### MODAL: Introduction Walkthrough
**Source:** CommKit #6 — Journal Article: Introduction

**Steps:**
1. **When to Write** — Write the introduction AFTER the results and discussion. You need to know what you found before you can motivate it.
2. **Purpose** — The introduction moves from broad context to your specific question. It funnels the reader from "why does this field matter" to "here's what we did."
3. **Formula** — Three-part structure:
   - **Context** (1–2 paragraphs): What is the broad field? Why does it matter?
   - **Gap** (1 paragraph): What's missing? What don't we know?
   - **Your Contribution** (1 paragraph): What did you do to fill the gap?
4. **Audience** — Write for the broadest reasonable audience. Your introduction should be understandable by someone in a neighboring field.
5. **Skills** — Start broad, end narrow. Each paragraph should narrow the focus. The last sentence of the introduction states your contribution or hypothesis.

---

#### MODAL: Methods Walkthrough
**Source:** CommKit #7 — Journal Article: Methods

**Steps:**
1. **Criteria for Success** — A reader should be able to reproduce your experiment from the methods section alone. Every material, every condition, every analysis step.
2. **Structure** — Organize by experiment, not by chronology. Group related procedures. Use subheadings.
3. **Purpose** — Methods establish reproducibility and credibility. They're not filler — they're the foundation of trust.
4. **Audience** — Your audience is a competent researcher in your field who wants to replicate or build on your work.
5. **Skills** — Use past tense. Be precise about quantities, conditions, and controls. Reference established protocols rather than re-describing them. State statistical methods.
6. **eaiou Note** — eaiou's Transparency Block (plg_content_transparency) pulls directly from your methods disclosure. `transp_methods` and `transp_limitations` are required fields. Complete methods = complete transparency.

---

#### MODAL: Results Walkthrough
**Source:** CommKit #9 — Journal Article: Results

**Steps:**
1. **Criteria for Success** — Each result is stated clearly. Figures support the claims. The text guides the reader through the figures, not the other way around.
2. **Structure** — Present results in logical order (not chronological). Each paragraph: state the finding → point to the evidence → interpret briefly.
3. **Purpose** — Results present what you found. Save interpretation for the discussion.
4. **Audience** — Experts will scrutinize your data. Make it easy for them by being clear about what each figure shows.
5. **Skills** — Strong results sentences state the finding, not the method: "Gene X was upregulated 100-fold" NOT "RT-qPCR was performed." Reference figures inline. Use consistent formatting for statistics.

---

#### MODAL: Discussion Walkthrough
**Source:** CommKit #8 — Journal Article: Discussion

**Steps:**
1. **Criteria for Success** — The discussion connects your results back to the broader context. It acknowledges limitations. It suggests future work.
2. **Structure** — Inverted funnel: start narrow (your results), end broad (implications for the field).
   - **Summary** (1 paragraph): Restate the main finding.
   - **Interpretation** (2–3 paragraphs): What do the results mean?
   - **Limitations** (1 paragraph): What could have gone wrong? What don't your results prove?
   - **Future Work** (1 paragraph): What's next?
3. **Purpose** — The discussion is where you make your case. Results are facts; discussion is argument.
4. **Audience** — Both experts (who want to see rigor) and non-experts (who want to see significance).
5. **Skills** — Don't overclaim. Use hedging language appropriately. Acknowledge alternative explanations. Cite related work that supports or contradicts your findings.
6. **eaiou Note** — Your limitations paragraph feeds directly into `transp_limitations` in the Transparency Block. Future work can be tagged with `rs:ForLater` or `rs:OpenQuestion` to feed the discovery surface.

---

#### MODAL: Full Manuscript Structure
**Trigger:** "Structure Guide" button in Submit Step 2 (Bundle upload)
**Source:** All five article guides combined

**Steps:**
1. **Overview** — A journal article follows a predictable structure: Abstract → Introduction → Methods → Results → Discussion. Each section has a distinct purpose and audience expectation.
2. **Abstract** — Summary of the guide from CommKit #5
3. **Introduction** — Summary from CommKit #6
4. **Methods** — Summary from CommKit #7
5. **Results** — Summary from CommKit #9
6. **Discussion** — Summary from CommKit #8
7. **eaiou Checklist** — Before submitting, verify:
   - [ ] Title states a claim, not a topic
   - [ ] Abstract follows the 4-part formula
   - [ ] Introduction funnels from broad to specific
   - [ ] Methods are reproducible
   - [ ] Results are clearly stated with figure references
   - [ ] Discussion connects results to broader context
   - [ ] Limitations are acknowledged
   - [ ] All figures are accessible and labeled
   - [ ] Transparency fields are complete
   - [ ] AI usage is disclosed if applicable

---

#### MODAL: Pre-Submit Checklist
**Trigger:** "Writing Checklist" button in Submit Step 6 (Confirm)
**Source:** Synthesized from all CommKit guides + eaiou requirements

**Steps (single scrollable view, not tabbed):**

**Writing Quality**
- [ ] Title is a complete sentence stating the main finding
- [ ] Abstract follows Background → Methods → Results → Implications
- [ ] Introduction funnels from broad context to specific question
- [ ] Methods are reproducible (materials, conditions, analysis)
- [ ] Results state findings, not methods
- [ ] Discussion connects results to broader context
- [ ] Limitations are explicitly stated
- [ ] Jargon is minimized or defined

**Figures**
- [ ] Each figure makes one point
- [ ] Labels are readable at article width (~640px)
- [ ] Colors are colorblind-safe
- [ ] Figures are referenced in text

**eaiou Requirements**
- [ ] ORCID linked and verified
- [ ] Transparency Block complete (sources, datasets, methods, limitations)
- [ ] AI Usage disclosed if ai_used=Yes
- [ ] Remsearch entries complete (used + unused with reasons)
- [ ] Authorship declarations made
- [ ] Research State Tags applied if relevant
- [ ] Submission date will be sealed (Temporal Blindness acknowledged)

---

### 4.3 Additional Modals (build as needed)

| Modal | Trigger | Source |
|-------|---------|--------|
| Slideshow Guide | "Presentation Guide" in workspace | CommKit #1 |
| Poster Guide | "Poster Guide" in workspace | CommKit #2 |
| General Writing Tips | "General Tips" in toolbar | CommKit #4 |
| Grant Writing Guide | Future: grant prep feature | CommKit #14, #15, #17 |
| Policy Writing Guide | Future: policy section | CommKit #20–27 |
| Coding Guide | "Code Guide" in bundle step | CommKit #28–30 |

---

## 5. MCP TOOL INTEGRATION

Two new MCP tools support the CommKit system:

### `commkit.get_guide`
| Field | Value |
|-------|-------|
| Input | `{guide_id: int, section?: string}` |
| ACL | AUTH |
| Output | Guide content structured as sections array |
| Notes | Returns adapted CommKit content for the requested guide. Section filter returns a single section. |

### `commkit.get_checklist`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int, context: "pre_submit"|"writing"|"figures"}` |
| ACL | AUTHOR |
| Output | Checklist items with completion status derived from paper's current state (transparency fields filled? AI disclosed? etc.) |
| Composite | Reads `transparency.get_completeness`, `ai.get_disclosure`, `paper.get` |

---

## 6. IMPLEMENTATION ORDER

| Phase | Task | Dependencies |
|-------|------|-------------|
| 1 | Drawer component (CSS + JS) | Frontend design system |
| 2 | Modal component (CSS + JS) | Frontend design system |
| 3 | Abstract Drawer | Submit Step 1 view |
| 4 | Title Tips Drawer | Submit Step 1 view |
| 5 | Figure Design Drawer | Submit Step 2 view |
| 6 | Code Style Drawer | Submit Step 2 view |
| 7 | Literature/Citation Drawer | Submit Step 4 view |
| 8 | Pre-Submit Checklist Modal | Submit Step 6 view |
| 9 | Full Manuscript Structure Modal | Submit Step 2 view |
| 10 | Introduction Modal | Author workspace |
| 11 | Methods Modal | Author workspace |
| 12 | Results Modal | Author workspace |
| 13 | Discussion Modal | Author workspace |
| 14 | Elevator Pitch Drawer | Discover Open view |
| 15 | All remaining drawers/modals | As features are built |

---

## 7. ATTRIBUTION

All CommKit content is adapted from the MIT Communication Lab at the Broad Institute of MIT and Harvard. Original contributors are credited per guide. eaiou's adaptation restructures this content for the observer-preserving publishing context and adds eaiou-specific notes connecting each guide to the platform's Transparency Block, Temporal Blindness, Remsearch, and AI disclosure features.

The CommKit adaptation follows eaiou's own principle: **Treat Things That Can Talk Like Humanity.** The CommKit's pedagogical knowledge is a participant in the authorship process — surfaced, structured, and credited. Not hidden.

---

*End of EAIOU CommKit Integration Plan v1.0.0*
*31 guides → drawers + modals across the authorship workflow*
*ORCID: 0009-0006-5944-1742 — Eric D. Martin*
*The river teaches you how to write before you wade in.*
