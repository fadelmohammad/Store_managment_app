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


## Architecture Progress

| Layer | Status |
|---|---|
| Repository pattern | Partially complete — Users, Accounts, Products, Categories, Stock, Ledger, Reports, Purchases done. `invoice_repo.py` is empty. |
| Service layer | Partially complete — Users, Accounts, Inventory, Categories, Reports, Purchases fully repo-based. Sales and Ledger still use raw `self.db` access. |
| UI layer | Partially clean — Inventory, Categories, User Profile, User Management fully decoupled. Login, POS, Accounts, Cashbox, Reports, Dashboard still use direct DB or raw cursors. |


## Modules

### Users (COMPLETED)
- `user_repo.py` → full CRUD, permissions, logs, password ops
- `user_service.py` → fully delegates to repo, no raw SQL
- `user_profile.py` → fully decoupled, uses `user_service` only
- `user_management_module.py` → uses `user_service`
- `login_module.py` → **partially migrated**: `reset_password` uses `user_service`, but `login()` still runs raw SQL directly (auth query, permissions fetch, last_login update, log insert)

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
- `accounts_module.py` → status unknown, needs verification

### Ledger / Cashbox (PARTIAL)
- `ledger_repo.py` → read operations only (cash balance, recent transactions)
- `ledger_service.py` → `get_cash_balance` and `get_recent_cash_transactions` use repo correctly. `create_entry()` still uses `self.db.cursor.execute()` directly — **not repo-based**
- `cashbox_module.py` → uses `ledger_service`, status of direct DB calls unknown

### Sales / POS (NOT MIGRATED)
- `sales_service.py` → uses `self.db.cursor.execute()` and `self.db.conn` throughout. Calls `self.db.update_stock_with_log()` (legacy DB class method). No repository usage.
- `pos_module.py` → uses `sales_service` but service itself is not clean

### Purchases (MOSTLY COMPLETE)
- `purchase_repo.py` → implemented
- `purchase_service.py` → uses repos for invoice and stock ops. Still calls `self.ledger.create_entry()` which internally uses raw DB access.

### Reports (MOSTLY COMPLETE)
- `report_repo.py` → implemented
- `report_service.py` → fully delegates to `report_repo`
- `reports_module.py` → passes `self.conn` directly — needs verification

### Dashboard
- `dashboard.py` → status unknown, likely still uses direct DB calls


## Known Issues

### Critical
- `login_module.py` — `login()` bypasses `user_service` entirely: runs raw SQL for auth, permissions, last_login update, and log insert
- `sales_service.py` — uses `self.db.cursor`, `self.db.conn`, and `self.db.update_stock_with_log()` (legacy). No repo layer.
- `ledger_service.py` — `create_entry()` uses `self.db.cursor.execute()` directly
- `invoice_repo.py` — empty file, invoices have no repository

### Security
- `login_module.py` — `hash_password()` duplicated from `user_service`. Login should delegate to the service.
- `session.json` — stores username in plaintext with no expiry or integrity check
- No brute-force / lockout protection on failed logins
- `safe_eval.py` — eval-based logic is a security risk regardless of guards

### Code Quality
- `main.py` — god object: wires all services, repos, frames, handles login/logout, session, sidebar, and routing
- `main.py` — `logout()` and `on_close()` write raw SQL directly instead of using `user_service.log_user_action()`
- `main.py` — `print()` statements left in production code (should be `logging`)
- `user_service.py` — `get_user_profile()` and `get_user_by_id()` are near-duplicates querying the same table
- Magic color strings (`#1f538d`, `#2ecc71`, etc.) scattered across 8+ files with no constants file
- `import json / import os` inside functions in `login_module.py` instead of top-level


## Data Flow (Current)

| Module | Flow |
|---|---|
| Inventory | UI → InventoryService → Repos → DB ✅ |
| Categories | UI → CategoryService → Repo → DB ✅ |
| Users | UI → UserService → UserRepo → DB ✅ |
| Accounts | UI → AccountService → AccountRepo → DB ✅ |
| Reports | UI → ReportingService → ReportRepo → DB ✅ |
| Purchases | UI → PurchaseService → Repos → DB ✅ (ledger step is dirty) |
| Cashbox | UI → LedgerService → LedgerRepo → DB ✅ (read only; write is dirty) |
| Login | UI → raw SQL ❌ |
| Sales/POS | UI → SalesService → raw DB ❌ |
| Dashboard | UI → unknown ❓ |


## Next Tasks (Priority Order)

**1. Migrate `login_module.py` to use `user_service`**
- Move auth query, permissions fetch, last_login update, and login log into `user_service.login()`
- Remove `hash_password()` from `LoginFrame`

**2. Fix `ledger_service.create_entry()`**
- Move journal insert logic into `ledger_repo`
- `LedgerService.create_entry()` should call `self.ledger_repo.create_entry()`

**3. Create `InvoiceRepository`**
- `invoice_repo.py` is empty
- Move invoice SQL from `sales_service` and `purchase_service` into it

**4. Migrate `sales_service.py`**
- Replace `self.db.cursor`, `self.db.conn`, `self.db.update_stock_with_log()` with repo calls
- Depends on InvoiceRepository and clean LedgerService

**5. Clean up `main.py`**
- Replace raw SQL in `logout()` and `on_close()` with `user_service.log_user_action()`
- Replace `print()` with `logging`

**6. Verify and clean `dashboard.py`, `cashbox_module.py`, `reports_module.py`**
- Confirm whether they use direct DB or go through services


## Completed Milestones

### Milestone 1 — Categories Module (2024-04-29)
- CategoryRepository, CategoryService, standalone CategoryManagementWindow
- Hierarchical category paths, product counts, safe delete
- Reference implementation for target architecture

### Milestone 2 — Inventory UI Migration (2024-04-30)
- inventory_module.py fully decoupled from DB
- All product/stock operations through InventoryService

### Milestone 3 — Repository Standardization (2024-04-30)
- Removed `_execute()` wrapper from all repos
- Standardized: reads use `.execute().fetchone/all()`, writes use `with self.conn:`
- Applied to: category_repo, account_repo, purchase_repo, report_repo, stock_movement_repo

### Milestone 4 — Users Module (current session)
- Created `user_repo.py` with full CRUD, permissions, logs
- Migrated `user_service.py` to fully delegate to `user_repo` — no raw SQL
- Migrated `user_profile.py` to use `user_service` — no direct DB access
- Added `reset_password()` to `user_service` and `login_module` (Forgot Password dialog)
- Added auto-dismiss welcome toast on login (replaces blocking messagebox)


## Architecture Rules

- Repository layer: SQL only, no business logic
- Service layer: business logic only, no SQL, no `conn` access
- UI layer: no DB access, no SQL, calls services only
- Write operations: `with self.conn:` context manager (auto-commit + rollback)
- Read operations: `.execute(query).fetchone/all()` — no commit needed
