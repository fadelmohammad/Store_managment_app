# PROJECT STATE

## System Overview

Desktop Store Management / POS system built with:
- Python
- customtkinter (UI)
- SQLite (database)

Currently undergoing a refactor from a monolithic architecture to a layered architecture:

UI → Services → Repositories → Database

Primary goals:
- Enforce separation of concerns
- Improve maintainability
- Ensure data integrity
- Enable scalability


## Modules

### Inventory (Active Module)
- `inventory_service.py` → business logic (partially complete)
- `product_repo.py` → product data access (stable)
- `stock_movement_repo.py` → stock movement persistence (needs fixes)
- `inventory_module.py` → UI (still uses legacy DB calls)

### Database
- `core.py` → partially cleaned (legacy logic still exists)
- connection/schema separated

### Categories
- `category_repo.py` exists
- No `CategoryService` yet

### Untouched Modules
- POS
- Accounts / Ledger
- Reporting


## Current Status

- Product-related logic removed from Database layer
- ProductRepository implemented and stable
- InventoryService mostly correct but contains bugs
- StockMovementRepo implemented but incorrect
- UI still partially coupled to Database

System state:
- Backend architecture ~80% aligned with target
- UI not yet migrated
- System expected to partially break during transition

---

## Known Issues

### Critical

### Structural
UI still uses: self.db.*
Missing CategoryService
Category path simplified (breadcrumb removed)

### Design Risks
Atomicity depends on shared DB connection (not enforced globally)
ProductRepository accesses stock movements (cross-domain concern)

## Recent Changes
Removed product logic from Database (core.py)
Created:
ProductRepository
InventoryService
StockMovementRepo
Moved:
CRUD operations → ProductRepository
Business logic → InventoryService
Eliminated direct SQL from Service layer (partially enforced)
Simplified category representation in product queries

## Next Tasks

### Immediate

### Next Phase
Ensure all repositories share the same DB connection

Migrate UI (inventory_module.py):
Replace: self.db.*
With: self.app.inventory_service.*

### Later
Introduce CategoryService
Fully separate stock movement domain
Clean reporting architecture
Restore category breadcrumb logic (optional)

## Data Flow (Expected)

### Standard Flow
UI (inventory_module)
    ↓
InventoryService
    ↓
ProductRepository / StockMovementRepo
    ↓
Database (SQLite)

## Notes
Refactoring strategy: incremental, break-and-fix (no bridging layer)
Scope strictly limited to Inventory module at this stage
One responsibility moved at a time to maintain control
Repository layer must remain:
SQL-only
free of business logic
Service layer is the single source of truth
UI must not interact with Database directly

### Current phase is critical:
Structure is mostly correct, but behavior is still stabilizing.