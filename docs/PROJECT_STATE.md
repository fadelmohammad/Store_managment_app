# PROJECT STATE

## System Overview
Desktop Store Management / POS system built with:
- **Python**
- **customtkinter** (GUI)
- **SQLite** (persistence)
- **matplotlib** (charts in reports/dashboard)

Target architecture (stated intent):
**UI → Services → Repositories → Database**

That layering largely exists now, but the UI layer still behaves like a *composition + orchestration shell* (expected for Tk), and a few “composition” responsibilities have been centralized into new UI helpers (`services/ui/ui_service.py`, `services/ui/frame_router.py`).

---

## What a senior engineer would say about the architecture right now
The project is **mid-migration from “god-object UI with embedded routing” to a layered system**. The biggest improvement is that:
- most frames are already service-backed (no raw SQL in UI),
- the **navigation boilerplate** is reduced by a shared `UIService`,
- and **frame routing/state** is no longer purely in `main.py`.

However, there are still **two architectural boundary risks**:

1) **“Routing is UI logic, but it still instantiates UI frames”**
   - `services/ui/frame_router.py` improves separation by taking routing/state out of `main.py`,
   - but it still effectively acts as a *UI composition factory* (instantiates frames directly and depends on `main`-wired dependencies).
   - This is acceptable for a Tk app, but it means the router is still tightly coupled to `StoreApp` construction lifecycle.

2) **Data-shape inconsistency (dict vs tuple) leaks into UI**
   - Several UI/report flows still contain defensive checks for `dict-like` vs tuple row shapes.
   - This is a classic symptom that repositories/services are not fully standardized on one row type (e.g., `sqlite3.Row` → dict conversion).
   - Until normalized, every new UI feature risks repeating this branching.

---

## Architecture Progress (Reality-based)
| Layer | Senior read |
|---|---|
| Repository pattern | **Partially complete**. Core repos exist and implement most queries/writes. Row shaping is inconsistent (some repos return dicts, others return sqlite rows/tuples). |
| Service layer | **Partially complete but improving**. Many services delegate fully to repos. Ledger/journaling flows are more “service-first” than before. |
| UI layer | **Partially clean**. Frames generally avoid raw SQL and call services. Remaining UI complexity is mostly presentation logic + row shape handling. |

---

## Modules (Senior review by area)

### Users (COMPLETED)
- `user_repo.py` → strong CRUD/permission/log/password operations.
- `user_service.py` → correct “delegate only” posture (good separation).
- UI (`user_profile.py`, `user_management_module.py`, `login_module.py`) → uses services; no raw SQL.

**Opinion:** Auth and permission are the best-behaved part of the system. Continue keeping UI dumb and service-driven here.

---

### Inventory (COMPLETE)
- `inventory_service.py` → business logic sits in services.
- `inventory_module.py` → decoupled UI.

**Opinion:** Inventory migration is a model for other modules: UI searches/inputs, services execute, repos query.

---

### Categories (COMPLETE)
- `category_repo.py`, `category_service.py`, `category_module.py` are aligned with the architecture intent.

**Opinion:** Category is stable and provides hierarchical querying patterns you can reuse for other “graph-like” domains.

---

### Accounts (MOSTLY COMPLETE)
- `account_repo.py` → CRUD exists.
- `accounts_service.py` → validation and business rules exist.
- `accounts_module.py` → now uses `account_service` (good direction), but row-shape conventions between repos/services can still be a source of fragility.

**Opinion:** Accounts UI is mostly fine now; the remaining risk is consistency: returning dicts vs sqlite rows should be standardized.

---

### Ledger / Cashbox (MOSTLY COMPLETE)
- `ledger_repo.py` + `ledger_service.py` are the correct structure for journalized accounting.
- `cashbox_module.py` uses `ledger_service` rather than DB directly.

**Opinion:** Ledger/Cashbox is one of the more “correctly layered” subsystems now.

---

### Sales / POS (MOSTLY COMPLETE)
- `sales_service.py` → repo-backed logic; ledger entries via `ledger_service`.
- `pos_module.py` → uses services; no direct SQL.

**Opinion:** POS is operationally correct, but it’s still a heavy UI frame (large but acceptable). Keep extracting “UI-only helpers” if it grows.

---

### Purchases (MOSTLY COMPLETE)
- `purchase_service.py` uses repo ops and ledger integration exists via `ledger_service`.
- `purchase_module.py` is UI-driven, using services for stock updates and journal entries.

**Opinion:** Purchases are close to the intended architecture. The open risk is “hidden legacy paths” (any remaining direct DB writes inside purchase code paths would be a regression).

---

### Reports / Dashboard (MOSTLY COMPLETE)
- `report_repo.py` implements reporting queries.
- `report_service.py` delegates to repo and formats results.
- `reports_module.py` and `dashboard.py` should depend only on services.

**Opinion:** Reports are mostly service-driven, but the **row-shape inconsistency** problem is more visible here because charts/tables are sensitive to data shape.

---

## Key structural changes you should notice in this revision

### 1) Shared UI actions: `services/ui/ui_service.py`
- Centralizes repeated UI actions (currently: Back/Home nav bar + message helpers).
- Reduces duplication across “left modules”.

**Senior take:** This is the right first step for Tk apps—shared widget/layout patterns belong in a UI helper, not scattered across frames.

---

### 2) Frame routing/state: `services/ui/frame_router.py`
- Routing/state moved out of `main.py` and into a router module.
- `main.py` now delegates `init_frames/show_frame/go_back/go_home` to `FrameRouter`.

**Senior take:** This reduces `main.py` complexity and isolates routing logic.
**But** the router still instantiates frames directly and depends on `StoreApp` wiring—so it’s not a fully independent “UI routing layer”; it’s a *composition-router*.

If the project grows, the next step would be:
- a frame registry/factory that accepts already-constructed dependencies,
- or a declarative route config that reduces direct frame instantiation inside the router.

---

## Known Issues / Risks (not “to-dos”, but what still hurts design)

### Security
- `safe_eval.py` is still expression-evaluation with hard limits. This is safer than `eval`, but still a surface area.
- `session.json` persistence is plaintext and non-integrity-protected.
- No brute-force / lockout strategy is present for failed logins in `login_service`.
- Password hashing migrated from **unsalted SHA-256** to **salted PBKDF2** (with legacy-hash verification + auto-upgrade on successful login), which materially improves password security posture. Remaining hardening should focus on session integrity and login throttling.

### UI / Data consistency
- **dict vs tuple** inconsistency persists. This increases UI complexity and makes regressions likely when new queries are added.

### Code Quality
- `main.py` is still a composition root (expected), but it’s less risky now since routing/state is externalized.
- UI constants (colors/fonts/sizes) are still scattered as literal hex strings.

---

## Data Flow (What’s actually true now)
| Module | Flow |
|---|---|
| Inventory | UI → `InventoryService` → Repos → DB ✅ |
| Categories | UI → `CategoryService` → Repo → DB ✅ |
| Users/Auth | UI → services → repos → DB ✅ |
| Accounts | UI → `AccountService` → repo → DB ✅ (UI no direct DB) |
| Reports/Dashboard | UI → `ReportingService` → report repos → DB ✅ |
| Purchases | UI → purchase service → stock ops + ledger journal entries ✅/⚠️ |
| Cashbox | UI → ledger service → ledger repo → DB ✅ |
| Sales/POS | UI → sales service → ledger service → journal → DB ✅ |

---

## Next Improvements (prioritized by senior impact)
1. **Standardize repository row output**
   - Make repo/service return a single row shape (prefer dict).
   - Remove UI branching on `hasattr(x,'keys')`.

2. **Reduce coupling in routing/frames**
   - Keep `FrameRouter`, but move toward a *frame registry/factory* pattern where dependencies are injected rather than recreated/assumed.

3. **Harden security**
   - Add session expiry + integrity (HMAC or encrypted token).
   - Add login throttling/lockout.

4. **Clean UI consistency**
   - Create UI constants module for colors/fonts/sizes.
   - Replace hard-coded repeated styles gradually.

---

## Completed Milestones (kept for historical context)
### Milestone 1 — Category Module (2024-04-29)
- CategoryRepository, CategoryService, CategoryManagementWindow
- Hierarchical category paths, product counts, safe delete

### Milestone 2 — Inventory UI Migration (2024-04-30)
- inventory_module fully decoupled from DB

### Milestone 3 — Repository Standardization (2024-04-30)
- standardized reads/writes patterns across repos

### Milestone 4 — Users & Auth (current)
- user repo/service/profile/login migration
- login service handles auth + permissions + last_login + logs
- forgot password dialog uses `user_service.reset_password()`

### Milestone 5 — Sales/POS, Ledger, Reports UI integration (current)
- POS uses services (`inventory_service`, `account_service`, `sales_service`)
- Sales uses repo-based DB ops + ledger_service journal entries
- Cashbox uses ledger_service only
- Dashboard & Reports use report_service only
