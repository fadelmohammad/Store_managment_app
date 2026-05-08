# PROJECT STATE

## System Overview

Desktop Store Management / POS system built with:
- Python
- customtkinter (UI)
- SQLite (database)
- matplotlib (reports)

Target architecture:

UI → Services → Repositories → Database

Primary goals:
- Enforce separation of concerns
- Improve maintainability
- Ensure data integrity
- Enable scalability

---

## Architecture Progress

| Layer | Status |
|---|---|
| Repository pattern | Partially complete — Users, Accounts, Products, Categories, Stock, Ledger, Reports, Purchases, Sales repo operations done. `invoice_repo.py` is empty (invoices are handled via other repo(s) currently). |
| Service layer | Partially complete — Most services delegate to repositories. Ledger/Cashbox, Login, Sales/POS, Purchases, Reports are now repo-backed. |
| UI layer | Partially clean — UI frames avoid raw SQL and call services. Some UI logic still formats/branches on returned row shapes (dict vs tuple). |

---

## Modules

### Users (COMPLETED)
- `user_repo.py` → full CRUD, permissions, logs, password ops
- `user_service.py` → fully delegates to repo, no raw SQL
- `user_profile.py` → fully decoupled, uses `user_service` only
- `user_management_module.py` → uses `user_service`
- `login_service.py` → auth + permissions + last_login + login log (repo-based)
- `login_module.py` → uses `login_service` (no raw SQL); supports Remember Me + Forgot Password dialog

### Inventory (COMPLETE)
- `inventory_service.py` → business logic, delegates to repos
- `product_repo.py` → stable
- `stock_movement_repo.py` → implemented
- `inventory_module.py` → fully decoupled, no direct DB calls

### Categories (COMPLETE)
- `category_repo.py` → full CRUD + hierarchical queries
- `category_service.py` → business logic layer
- `category_module.py` → standalone UI, fully decoupled

### Accounts (MOSTLY COMPLETE)
- `account_repo.py` → full CRUD
- `accounts_service.py` → fully repo-based with validation
- `accounts_module.py` → needs verification (ensure no direct DB calls)

### Ledger / Cashbox (MOSTLY COMPLETE)
- `ledger_repo.py` → supports:
  - `get_cash_balance()`
  - `get_recent_cash_transactions()`
  - `create_entry()` (writes journal entries + lines via repo, using `with self.conn:`)
- `ledger_service.py` → delegates to `ledger_repo` fully (no `self.db` usage)
- `cashbox_module.py` → uses `ledger_service` only for reads/writes

### Sales / POS (MOSTLY COMPLETE)
- `sales_service.py` → uses `sales_repo` for all DB ops + uses `ledger_service.create_entry()` for journal writes
- `pos_module.py` → uses:
  - `inventory_service.search_products()` for product listing
  - `account_service.get_by_role()` for customer listing
  - `sales_service.process_sale()` for checkout
  - no direct DB calls in the UI

### Purchases (MOSTLY COMPLETE)
- `purchase_repo.py` → implemented
- `purchase_service.py` → uses repos for invoice and stock ops
- Ledger integration: validate that purchase journal writes go through `ledger_service` (current docs previously flagged it; confirm if purchase uses the clean path)

### Reports (MOSTLY COMPLETE)
- `report_repo.py` → implemented (verify all needed query methods exist)
- `report_service.py` → delegates to `report_repo` and formats results
- `reports_module.py` → uses `report_service` (no direct DB calls); builds UI tables from returned dict/tuple shapes

### Dashboard (MOSTLY COMPLETE)
- `dashboard.py` → uses `report_service` for:
  - today metrics
  - best selling products
  - top stock items
  - best selling hours
- No direct SQL expected in the UI

---

## Known Issues (Updated)

### Security
- `safe_eval.py` — eval-based logic is a security risk regardless of guards.
- `session.json` — stores username in plaintext with no expiry or integrity check.
- No brute-force / lockout protection on failed logins in `login_service`.
- `safe_eval.py` remains a priority hardening target.

### Code Quality
- `main.py` — god object: wires services/repos/frames, handles login/logout, session, sidebar, and routing.
- Magic color strings scattered across multiple UI modules; no shared UI constants file.
- `reports_module.py` — defensive branching on return types (dict vs tuple) suggests inconsistent row shaping between repos/services; ideally normalize to dicts.

---

## Data Flow (Current)

| Module | Flow |
|---|---|
| Inventory | UI → InventoryService → Repos → DB ✅ |
| Categories | UI → CategoryService → Repo → DB ✅ |
| Users | UI → UserService → UserRepo → DB ✅ |
| Accounts | UI → AccountService → AccountRepo → DB ✅ (verify UI module) |
| Reports | UI → ReportingService → ReportRepo → DB ✅ |
| Purchases | UI → PurchaseService → PurchaseRepo/StockRepo → DB ✅/⚠️ (validate ledger path) |
| Cashbox | UI → LedgerService → LedgerRepo → DB ✅ |
| Login | UI → LoginService → UserRepo → DB ✅ |
| Sales/POS | UI → SalesService (+ repos) → LedgerService → DB ✅ |
| Dashboard | UI → ReportService → ReportRepo → DB ✅ |

---

## Next Tasks (Priority Order)

1. **Verify `accounts_module.py`**
   - Confirm it uses `account_service` only (no direct DB calls).

2. **Verify `purchase_service.py` ledger integration**
   - Ensure it uses `ledger_service` / `ledger_repo` write path, not legacy raw DB writes.

3. **Verify `report_repo.py` query coverage**
   - Ensure all methods used by `report_service` exist and return consistent shapes (prefer dict-like rows).

4. **Harden `safe_eval.py`**
   - Replace with a safe expression parser/evaluator approach.

5. **Reduce “dict vs tuple” branching**
   - Normalize repository outputs to dicts (sqlite3.Row / dict conversion in repo/service).

6. **Split `main.py` god object**
   - Extract wiring/routing/sidebar responsibilities into smaller components.

---

## Completed Milestones

### Milestone 1 — Category Module (2024-04-29)
- CategoryRepository, CategoryService, CategoryManagementWindow
- Hierarchical category paths, product counts, safe delete

### Milestone 2 — Inventory UI Migration (2024-04-30)
- `inventory_module.py` fully decoupled from DB

### Milestone 3 — Repository Standardization (2024-04-30)
- Standardized reads/writes patterns across repos

### Milestone 4 — Users & Auth (current)
- user repo/service/profile/login migration
- login service handles auth + permissions + last_login + logs
- forgot password dialog uses `user_service.reset_password()`

### Milestone 5 — Sales/POS, Ledger, Reports UI integration (current)
- POS uses services (`inventory_service`, `account_service`, `sales_service`)
- Sales uses repo-based DB ops + ledger_service journal entries
- Cashbox uses ledger_service only
- Dashboard & Reports use report_service only
