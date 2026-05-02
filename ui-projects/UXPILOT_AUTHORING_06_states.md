# UXPilot Prompt — eaiou IID Lifecycle States

**Title:** eaiou IID Module + Output Lifecycle States

---

## Frame

Every IID interaction passes through a finite state machine. The UI must show every state with a distinct visual, never silently transition. Authors should always know what's running, what's done, what failed, and why.

---

## IID module card states

| State | Trigger | Visual | Author actions |
|---|---|---|---|
| `unconfigured` | No API key entered | Card shown grayed, "Configure to enable" CTA | [Configure] button |
| `idle` | API key valid, quota available | Card normal, action buttons clickable | Click any action |
| `running` | Action invoked, awaiting response | Action button replaced by spinner; card shows "Running scope_check… 5s" with elapsed counter | [Cancel] |
| `complete` | Most recent action returned successfully | Card shows "Last: scope_check 14s ago ✓"; action buttons re-enabled | New action |
| `quota_exhausted` | Daily/monthly cap hit | Action buttons grayed; banner: "Quota reached. Resets at [time]. [Raise cap]" | Wait or upgrade |
| `provider_down` | Health check fails | Action buttons grayed; banner: "Mae unreachable. [Retry] [Switch to OpenAI]" | Retry or switch IID |
| `error` | Last call returned error | Action buttons re-enabled but banner shows "Last call failed: [reason]" | Retry or report |
| `disabled` | Author manually disabled this provider | Card folded to title only with [Re-enable] button | Re-enable |
| `stub` | Phase 0 build mode | Banner: "Mae is in stub mode — outputs are placeholders" with action buttons enabled but cost shown as $0 | Run anyway |

---

## Output card states

| State | Trigger | Visual |
|---|---|---|
| `arriving` | First 2 seconds after output lands | Card slides in from right, briefly highlighted in IID's accent color |
| `displayed` | After arrival animation | Normal output card, all zones visible |
| `expanded` | Author clicked source-text or full disclosure | Card expanded inline showing full source + full disclosure record |
| `collapsed` | Author clicked Hide | Card folded to single-line summary; "Show" link to restore |
| `comparing` | Part of a multi-IID parallel run | Card has a comparison-banner above; sibling cards shown side-by-side |
| `superseded` | Author re-ran the same action | Card shows "Re-run produced newer output [link]"; original preserved but flagged |
| `withdrawn` | Compliance redaction (admin action) | Card shows "Source redacted; result preserved per audit"; result still visible but source is "[REDACTED]" |
| `inserted` | Author clicked "Insert as comment" | Card shows "Inserted as comment on §X" badge; clicking jumps to manuscript comment |

---

## Action confirmation modal states

| State | Visual |
|---|---|
| `composing` | Modal open, source-text preview visible, action params editable |
| `pre-flight check` | Tiny spinner: "Checking provider availability…" before button enables |
| `confirmed` | Button clicked, modal closes, transitions to `running` on the IID card |
| `cancelled` | Modal closed without running; no API call fired |
| `idempotency replay` | Detected duplicate Idempotency-Key; modal shows "This action is already in flight" with link to the in-flight output |

---

## Sidebar collapse states

| State | Visual |
|---|---|
| `expanded` | Default; full IID cards visible at 25% viewport |
| `icon rail` | Author collapsed sidebar; only provider chips + status dots visible (60px wide rail) |
| `hidden` | Author dismissed sidebar entirely; restore button in top bar |

---

## Output panel states

| State | Visual |
|---|---|
| `closed` | Default before any output; small "Outputs" pill at right edge |
| `auto-opened` | First output of session lands; panel slides in to 30% width |
| `pinned-open` | Author clicked pin; panel stays open across sessions |
| `filtered` | Author applied filter; banner shows active filters with [Clear] button |
| `empty after filter` | Filter excludes all outputs; "No outputs match filter" placeholder |
| `loading-history` | Pagination loading older outputs from server; spinner at bottom |

---

## Manuscript-editor IID-aware states

| State | Visual |
|---|---|
| `clean` | No selection, no IID activity in current section |
| `selection-active` | Text selected; floating IID-action bar visible above selection |
| `section-with-iid-output` | Section navigator shows pill: "Methods: 2 IID notes" |
| `iid-comment-attached` | Inline margin comment attributed to an IID; expandable |
| `iid-suggesting-edit` | If an IID returned a suggested rewording, the rewording shows as a track-changes-style suggestion that requires explicit author Accept/Decline |

---

## Visual-design rules across all states

1. **Color is never the sole indicator.** Every state has a text label or icon in addition to color.
2. **Spinners always include elapsed time.** "Running… 7s" — not just a generic spinner.
3. **Errors always include a reason.** Never "Something went wrong"; always "Provider returned 429: rate limit; retry at [time]."
4. **State transitions are announced** to screen readers via ARIA live regions.
5. **Cancellable operations always show a [Cancel] button** during running state.

---

## Output requested from UXPilot

1. State-machine diagram showing all module-card transitions
2. State-machine diagram showing all output-card transitions
3. Visual mockup grid: every IID-card state side by side
4. Visual mockup grid: every output-card state side by side
5. Visual mockup of error variants (rate limit, provider down, stub mode)
6. Mobile / narrow-viewport: states accommodate vertical-stacked layout
