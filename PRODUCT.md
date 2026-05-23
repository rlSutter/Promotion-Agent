# Product

## Register

product

## Users

Solo Substack writers — single operator, never teams. They arrive at the dashboard after publishing a piece, ready for a focused ~15-minute post-publish ritual: reviewing AI-generated promotional drafts, editing as needed, and dispatching to LinkedIn, Facebook, Bluesky, X, and Substack Notes. They care deeply about their writing and are suspicious of anything that feels like a content-mill tool.

## Product Purpose

An autonomous promotional assistant for Substack writers. It monitors the writer's RSS feed, generates platform-specific promotional copy using Claude AI, and surfaces those drafts for review and one-click dispatch. The measure of success is a writer who finishes their review session without thinking about the interface at all — only about whether the copy is right.

## Brand Personality

Efficient, invisible, enabling. The interface does not have opinions about itself. It holds the writer's work at the center and steps back. No flourishes, no personality performance, no proof that it is well-designed. It simply works.

## Anti-references

- Social media management tools (Buffer, Hootsuite): scheduled post calendars, multi-account sprawl, the sense that posting is a production operation requiring dashboards and pipelines.

## Design Principles

1. **Content before chrome.** The promotional copy under review is the product. The interface is the container. Every pixel that draws attention to itself is a failure.
2. **Invisibility as excellence.** The best design interaction is the one the writer does not notice. Affordances should be obvious without announcing themselves.
3. **One signal per decision.** Each color maps to exactly one action category. Each UI element has one job. Ambiguity in the interface creates ambiguity in the workflow.
4. **Earned weight.** Visual emphasis — shadow, color, size — is earned by structural importance, not sprinkled for decoration. A shadow means elevation. A serif means content under review.
5. **Calm over clever.** When there's a choice between a surprising solution and a settled one, choose settled. The tool is used in a state of mild post-publish relief. It should meet that mood.

## Accessibility & Inclusion

WCAG AA. Keyboard navigable throughout (arrow keys, Enter, Space, Escape, action shortcuts c/e/p/s). `prefers-reduced-motion` respected — animations suppressed when system preference is set. Screen-reader support via `aria-live`, `aria-expanded`, `aria-controls`, and `.sr-only` labels.
