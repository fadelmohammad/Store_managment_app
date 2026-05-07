# TODO

## Completed This Session
- [x] Created `user_repo.py` — full CRUD, permissions, logs, password ops
- [x] Migrated `user_service.py` to use `user_repo` — no raw SQL
- [x] Migrated `user_profile.py` to use `user_service` — no direct DB access
- [x] Created `login_service.py` — auth, permissions fetch, last_login, login log
- [x] Migrated `login_module.py` to use `login_service` — no raw SQL
- [x] Added `reset_password()` to `user_service` + Forgot Password dialog in login UI
- [x] Added auto-dismiss welcome toast on login
- [x] Created `sales_repo.py` — all sales DB ops extracted from service
- [x] Migrated `sales_service.py` to use `sales_repo` — no raw SQL
- [x] Fixed `ledger_repo.py` — added `create_entry()` write method
- [x] Fixed `ledger_service.py` — removed `self.db`, delegates to repo fully
- [x] Fixed `purchase_repo.py` — removed `begin/commit/rollback_transaction` methods
- [x] Fixed `purchase_service.py` — owns transaction via `conn` directly
- [x] Fixed `main.py` — `logout()` and `on_close()` use `user_service.log_user_action()`
- [x] Fixed `main.py` — `print()` replaced with `logging`, `import os` moved to top
- [x] Fixed `report_service.py` — period input validated against allowlist (XSS fix)
- [x] Fixed `database/connection.py` — connection closed on constructor exception (resource leak fix)

---

## Up Next (Priority Order)

- [ ] **Verify `accounts_module.py`** — confirm it uses `account_service` only, no direct DB calls
- [ ] **Verify `cashbox_module.py`** — confirm it uses `ledger_service` only, no direct DB calls
- [ ] **Verify `dashboard.py`** — likely still uses direct DB calls, migrate to `report_service`
- [ ] **Verify `reports_module.py`** — passes `self.conn` directly, migrate to `report_service`
- [ ] **Delete dead files** — `invoice_repo.py` (empty), `POS.db` (legacy), check `invoices_service.py` and `init_db.py`
- [ ] **Fix `login_module.py` line 217** — bare `except Exception: pass` in `load_saved_user`, replace with specific exception + logging
- [ ] **Fix `database/init_db.py`** — resource leak, wrap `conn_check` and `cursor` in `with` block

---

## Backlog

- [ ] Merge `get_user_profile()` and `get_user_by_id()` in `user_service` — near-duplicate methods
- [ ] Add brute-force / lockout protection on failed logins in `login_service`
- [ ] Replace `session.json` plaintext storage with a token + expiry
- [ ] Create a UI constants file — consolidate magic color hex strings scattered across modules
- [ ] Split `main.py` god object — separate wiring, routing, and sidebar into smaller classes
- [ ] Fix `inventory_service.py` — `not x is None` → `x is not None` (PEP8)
- [ ] Fix `category_repo.py` — replace simple for loop with list comprehension (PEP8)
