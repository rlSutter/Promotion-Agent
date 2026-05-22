# Changelog

All notable changes to this project are documented here.

---

## [Unreleased] — May 2026

### Multi-platform promotions

Previously the agent generated one promotional post per article, routed to a single suggested platform. It now generates five separate drafts — one per platform — on every article processed.

**Platforms:** LinkedIn, Facebook, Bluesky, X, Substack Notes

**Agent (`agent.py`):**
- Added `ALL_PLATFORMS` constant listing all five platform identifiers.
- `_process_new_post_impl()` now loops over `ALL_PLATFORMS` and calls `generate_promotional_post()` once per platform, rather than generating a single post for the keyword-matched platform. The keyword-matched platform is still computed but used only for commenting-task context.
- `generate_promotional_post()` gains `voice_description` parameter (see AI Voice section below) and new platform entries in `platform_guidelines` and `platform_len` dicts for Facebook and X, with character-count enforcement guidance for X.
- `generate_review_dashboard()` now groups pending promotions by `post_id` into a `platforms` dict rather than a flat list, so the frontend can render a tabbed card per article.

**Server (`server.py`):**
- `_regenerate_dashboard_json()` updated to match the new grouped-by-post structure (must stay in sync with `generate_review_dashboard()`).

**Dashboard (`dashboard.html`):**
- `renderPromotions()` fully rewritten to accept the grouped structure. Each article appears as one card with a platform tab strip. The active platform panel shows the draft, edit controls, and action buttons.
- New functions: `switchPlatformTab()`, `getActivePanel()`, `getActivePromoId()`, `copyCurrentPlatform()`, `editCurrentPlatform()`, `markCurrentPlatformPublished()`, `skipAllPlatforms()`.
- Keyboard shortcuts (`c`, `e`, `p`, `s`) updated to operate on the active platform within the focused card.
- Escape key handler checks whether the settings panel (see below) is open before handling card confirmations.
- New CSS: `.platform-tab`, `.platform-tab.active`, per-platform active-state colors, `.platform-panel`. New design tokens: `--facebook` and `--x-brand`.

---

### Manual Promote button (Article Inventory)

Articles already in the inventory had no way to trigger promotion after the fact. A **Promote** button now appears on every inventory row, running the full promotion pipeline (five platforms + commenting tasks) for any historical article on demand.

**Agent (`agent.py`):**
- New method `promote_inventory_article(article_id)`: checks for existing pending promos and returns `"already_pending"` if found; otherwise looks up the article from `article_inventory` (falling back to `posts`), ensures a `posts` row exists for the FK, extracts the outward sentence, generates all five platform drafts with voice, saves to `promotions`, and calls `generate_commenting_tasks()` and `generate_review_dashboard()`. Returns `"generated"` on success.

**Server (`server.py`):**
- New thread-safe background job: `_run_promote_article_thread()` with shared state dict `_promote_article_state` and lock.
- New endpoints:
  - `POST /api/promote-article` — accepts `{ article_id }`, starts the background thread, returns `{ status: "started" }` (or `"already_running"` if busy).
  - `GET /api/promote-article/status` — returns current job state (`running`, `result`, `error`, `last_run`).

**Dashboard (`dashboard.html`):**
- Inventory table gains a fifth column. Each row has a **Promote** button (`data-article-id` attribute).
- New functions: `promoteArticle()`, `startPromoteArticlePolling()`, `pollPromoteArticleStatus()` — polls `/api/promote-article/status` every two seconds until the job completes, then refreshes the promotions section.
- New CSS: `.promote-article-btn`.

---

### Settings panel with AI Voice

A ⚙ gear button in the dashboard header opens a slide-in settings panel. The first configurable option is **AI Voice**: a free-text description of the writer's style that is passed to the AI on every promotional post generation.

**Database:**
- New `settings` table (key/value with `updated_at`) added to `init_database()` in both `agent.py` and lazily in `server.py` endpoints.

**Agent (`agent.py`):**
- New method `get_setting(key, default)`: reads a value from the `settings` table.
- `promote_inventory_article()` and `_process_new_post_impl()` both fetch `ai_voice` via `get_setting()` and pass it as `voice_description` to `generate_promotional_post()`.

**Server (`server.py`):**
- New endpoints:
  - `GET /api/settings` — returns all settings as a JSON object.
  - `POST /api/settings` — accepts a JSON object of key/value pairs and upserts them.

**Dashboard (`dashboard.html`):**
- Gear button (`⚙`) added to dashboard header.
- Slide-in settings panel: full-page overlay + right-side drawer with header, scrollable body, and sticky save footer. AI Voice textarea with label and helper text.
- New functions: `openSettings()`, `closeSettings()`, `loadSettings()`, `saveSettings()`.
- `loadSettings()` called at startup.
- Reduced-motion media query extended to cover settings overlay and panel transitions.

---

### AI Voice prompt architecture fix

When a voice description was set, the generated promos still exhibited the exact patterns the voice prohibited (em-dashes, "X is not Y. It is Z." constructions, tricolon cadence). The root cause: the voice description was placed as a soft suggestion between platform guidelines and the article content, but a rigid numbered structural scaffold that followed it dominated the model's output.

**Fix (`agent.py` — `generate_promotional_post()`):**
- Split into two prompt paths based on whether `voice_description` is set.
- **Voice path:** voice is placed first under an explicit "primary constraint — overrides all other style suggestions" heading. The numbered structural scaffold is removed entirely. Platform guidelines are demoted to secondary. A self-check instruction is added at the end: the model must re-read the voice rules and rewrite the draft if any rule is violated before returning.
- **No-voice path:** original scaffold prompt preserved unchanged.

---

### Article inventory sort

Inventory rows are now explicitly sorted by `published_date` descending on the client side, so the most recent articles always appear at the top regardless of server response order.

---

## Previous releases

See git log for changes prior to May 2026.
