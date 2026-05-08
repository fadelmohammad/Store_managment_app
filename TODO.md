# TODO

## Completed This Session
- [x] Login flow uses `LoginService` (no raw SQL in `login_module.py`)
- [x] `login_module.py` uses `login_service.login()` and supports “Remember me”
- [x] Forgot Password flow uses `user_service.reset_password()`
- [x] Sales/POS uses `SalesService.process_sale()` (repo-backed sale logic)
- [x] `LedgerService` delegates to `LedgerRepository` (no `self.db` usage in service)
- [x] `ledger_repo.create_entry()` performs writes via repository DB access (`with self.conn:`)
- [x] `reports_module.py` uses `report_service` for report data (UI builds from service results)
- [x] `dashboard.py` uses `report_service` for dashboard metrics/charts
- [x] `cashbox_module.py` uses `ledger_service` only (reads + writes go through `LedgerService`)

---

## Up Next (Priority Order)

- [x] Verify `accounts_module.py`
  - UI uses `account_service` only (no direct DB calls)

- [x] Verify `purchase_service.py` ledger integration
  - Journal writes go through `PurchaseService` → `LedgerService` → `LedgerRepository` ✅
  - No legacy raw DB journal writes found in the purchase path

- [x] Verify `report_repo.py` query coverage + output shape consistency
  - `report_repo.py` implements all methods used by `report_service.py` ✅
  - Note: UI still has dict-vs-tuple branching; next item handles normalization

- [x] Harden `safe_eval.py` (small hardening only)
  - Add limits:
    - maximum expression length
    - maximum exponent magnitude / result bounds for `**`
  - Keep AST-only evaluation (no `eval`/`exec`)

- [x] Reduce dict-vs-tuple branching in UI
  - Invoice UI now receives normalized dict-like rows from `InvoiceService` (so the UI can rely on `keys()` without tuple fallbacks).

- [ ] Split `main.py` god object (refactor)
  - Separate: wiring/container setup, routing/frame management, and sidebar logic

---

## Backlog

- [ ] Consolidate UI constants (colors/fonts/sizes)
  - Reduce repeated hex color strings across UI modules

- [ ] Session hardening
  - Add expiry + integrity (at minimum), or switch to token-based storage

- [ ] Brute-force / lockout protection on failed logins
  - Add rate limiting / lockout in `login_service` and/or `user_repo`

- [ ] Remove/clean unused/empty legacy files
  - e.g. check `invoice_repo.py` (empty) and legacy DB artifacts

- [ ] PEP8 / cleanup sweep
  - Fix remaining minor style issues that surfaced during migrations
