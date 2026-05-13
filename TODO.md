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
- [x] Verified `accounts_module.py` uses `account_service` only (no direct DB calls)
- [x] Verified `purchase_service.py` ledger integration path
- [x] Report repo query coverage + output shape consistency checks
- [x] Harden `safe_eval.py` (already hardened with AST + limits)
- [x] Reduce dict-vs-tuple branching (UI invoice flow normalization already handled)
- [x] Added global `UIService` (`services/ui/ui_service.py`)
- [x] Wired `UIService` into `main.StoreApp` (`self.ui_service = UIService(self)`)
- [x] Refactored nav bars to use `UIService`
  - [x] Accounts (`ui/accounts_module.py`)
  - [x] POS (`ui/pos_module.py`)
  - [x] Purchase (`ui/purchase_module.py`)
  - [x] Cashbox (`ui/cashbox_module.py`)
  - [x] Reports (`ui/reports_module.py`)
- [x] Split `main.py` god object: moved routing/frame management to `services/ui/frame_router.py`
- [x] Fixed `FrameRouter.init_frames()` to correctly construct frames (mirrors old `main.init_frames()`)
- [x] Compilation sanity checks (`py_compile`) for modified files
- [x] Manual runtime smoke verification (dashboard/accounts/pos/purchase/cashbox/reports) → Back/Home works, no “Frame not found” errors

---

## Backlog

- [ ] Consolidate UI constants (colors/fonts/sizes)
- [ ] Session hardening
- [ ] Brute-force / lockout protection on failed logins
- [ ] Remove/clean unused/empty legacy files
- [ ] PEP8 / cleanup sweep
