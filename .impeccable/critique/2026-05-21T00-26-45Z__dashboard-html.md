---
target: dashboard.html
total_score: 23
p0_count: 0
p1_count: 3
timestamp: 2026-05-21T00-26-45Z
slug: dashboard-html
---
## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Sync/build feedback is good; per-card updating state has no spinner |
| 2 | Match System / Real World | 3 | "Outward sentence" is natural for this user; "Mark Published" slightly implies publishing happens here |
| 3 | User Control and Freedom | 2 | confirm() dialogs for Skip/Publish; Edit has no Cancel; recovery requires scrolling to Archive |
| 4 | Consistency and Standards | 3 | Mostly coherent; inline style="margin-top:15px" on archive cards breaks the system |
| 5 | Error Prevention | 2 | Native confirm() dialogs get click-through blindness; textarea edits silently don't persist to DB |
| 6 | Recognition Rather Than Recall | 3 | All actions are labeled; "Outward sentence" has no tooltip for new users |
| 7 | Flexibility and Efficiency | 1 | No keyboard shortcuts for any primary action; no batch operations |
| 8 | Aesthetic and Minimalist Design | 3 | Visually clean; Analytics above Pending Promotions is wrong priority |
| 9 | Error Recovery | 2 | Raw alert() for server errors; "Check console" is developer-facing copy |
| 10 | Help and Documentation | 1 | No contextual help anywhere; empty states are the only guidance |
| **Total** | | **23/40** | **Acceptable** |

## Anti-Patterns Verdict

LLM: Does not read as AI-generated. Two-register typography and OKLCH plum-tinted palette are coherent editorial system. Structural tell: six sections with identical visual weight.

Deterministic scan: CLI detector unavailable (bundled detector not found). Manual source inspection clean: no border-left accents, no gradient text, no hex literals. Two alert() + three confirm() calls found in JS (interaction violations, not CSS-detectable).

## Overall Impression

Visual system is genuinely good. Primary problem is structural: Analytics first when Pending Promotions is the primary task. Second problem: native JS dialogs (confirm/alert) break the calm editorial tone the CSS establishes.

## What's Working

1. Two-register typography (Georgia for content, system-ui for chrome)
2. Skip button hierarchy (ghost + margin-left: auto)
3. Collapsible sections with localStorage persistence

## Priority Issues

**[P1] Analytics is in the wrong place**
Analytics section renders first, before Pending Promotions. Writer's first question is "what do I need to review?" not "how did I perform?" Fix: move Analytics to bottom or make it collapsed-by-default.

**[P1] alert() and confirm() break the design contract**
Three confirm() calls, two alert() calls. Native browser dialogs ignore the design system; click-through blindness on daily repetitive tasks defeats the safety mechanism. Fix: inline confirmation states on cards, inline error messages.

**[P1] No keyboard efficiency for a daily ritual**
Zero keyboard shortcuts. Entire review flow requires mouse. Fix: C to copy, S to skip, P to mark published on focused card; arrow keys between cards.

**[P2] Edit state is ambiguous**
No Save button, no persistence to DB, no indication edits are session-local. Fix: either add /api/update-promotion endpoint, or explicit "scratch pad" label.

**[P2] Last-synced timestamp is ephemeral**
Sync status message disappears on page reload. No persistent indication of when Substack was last polled. Fix: store last_run in localStorage, render in header status line.

## Persona Red Flags

**Alex (Daily Power User):** No keyboard shortcuts; confirm() trains away within a week; no batch skip/publish.

**Sam (Accessibility):** Focus management not handled after DOM mutations; card state changes not announced via ARIA live regions.

**The Morning Writer (project-specific):** Scrolls past Analytics to find pending items; confirm() interrupts rhythm; edits lost on tab close; no persistent last-synced indicator.

## Minor Observations

- style="margin-top:15px" on archive card actions bypasses design token system
- "Commenting Tasks (10 min/day)" parenthetical awkward in uppercase eyebrow
- .toUpperCase() in JS + CSS text-transform: uppercase on .task-type is redundant
- "View post" uses Unicode arrow (U+2197) in HTML template
