import os
import random
import sqlite3
import statistics
import time
from datetime import datetime

# Temporary load/performance test for your SQLite backend.
# Writes results to a .txt log file.
#
# Example:
#   python temp_perf_test_large_db.py --db store.db --log perf_test_log.txt --products 50000 --categories 500 --invoices 20000


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def apply_performance_pragmas(conn: sqlite3.Connection) -> None:
    # Match database/connection.py behavior
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -10000")  # KB; matches your current code


def ensure_schema(conn: sqlite3.Connection) -> None:
    from database.schema import create_tables

    create_tables(conn)
    conn.commit()


def rand_name(prefix: str, i: int) -> str:
    return f"{prefix}_{i}"


def percentile(sorted_values: list[float], p: float) -> float:
    # sorted_values must be sorted ascending
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def time_block(fn, *args, **kwargs) -> tuple[object, float]:
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    end = time.perf_counter()
    return result, (end - start)


def run_timing_series(fn, repeats: int) -> dict:
    timings: list[float] = []
    last_result = None
    for _ in range(repeats):
        last_result, dt = time_block(fn)
        timings.append(dt)

    timings_sorted = sorted(timings)
    return {
        "n": repeats,
        "min": min(timings),
        "p50": percentile(timings_sorted, 50),
        "p90": percentile(timings_sorted, 90),
        "p95": percentile(timings_sorted, 95),
        "max": max(timings),
        "mean": statistics.mean(timings),
        "last_result": last_result,
    }


def _ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f} ms"


def _rating(p95: float) -> str:
    if p95 < 0.05:
        return "FAST"
    if p95 < 0.2:
        return "OK"
    if p95 < 1.0:
        return "SLOW"
    return "VERY SLOW"


_QUERY_LABELS = {
    "query_products_by_category": "Products by category (JOIN + GROUP BY)",
    "query_stock_movements_agg":  "Stock movements per product (aggregate)",
    "query_invoice_with_items":   "Single invoice + items (JOIN)",
    "query_invoices_filtered":    "Invoice count by type + date filter",
}


def format_timing_summary(name: str, timings: dict) -> str:
    label = _QUERY_LABELS.get(name, name)
    rating = _rating(timings["p95"])
    return (
        f"  {label}\n"
        f"    Typical (median) : {_ms(timings['p50'])}\n"
        f"    Worst 10%  (p90) : {_ms(timings['p90'])}\n"
        f"    Worst 5%   (p95) : {_ms(timings['p95'])}   <-- {rating}\n"
        f"    Absolute worst   : {_ms(timings['max'])}\n"
        f"    Runs             : {timings['n']}\n"
    )


def seed_categories(conn: sqlite3.Connection, categories: int) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM categories")
    existing = int(cur.fetchone()["c"])
    if existing >= categories:
        return f"existing_categories={existing} (no changes)"

    to_add = categories - existing
    start_idx = existing + 1

    rows = [(rand_name("Category", i), None) for i in range(start_idx, start_idx + to_add)]
    with conn:
        conn.executemany("INSERT INTO categories (name, parent_id) VALUES (?, ?)", rows)

    return f"added_categories={to_add}"


def seed_products(conn: sqlite3.Connection, products: int, categories: int) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM products")
    existing = int(cur.fetchone()["c"])
    if existing >= products:
        return f"existing_products={existing} (no changes)"

    to_add = products - existing
    cat_ids = list(range(1, categories + 1))
    start_idx = existing + 1

    batch_size = 2000
    added = 0
    with conn:
        for i0 in range(0, to_add, batch_size):
            i1 = min(i0 + batch_size, to_add)
            rows = []
            for j in range(i0, i1):
                idx = start_idx + j
                cat_id = random.choice(cat_ids)
                price = round(random.uniform(5, 5000), 2)
                cost = round(price * random.uniform(0.4, 0.9), 2)
                qty = random.randint(0, 500)
                min_th = random.randint(1, 50)
                rows.append((rand_name("Product", idx), price, cost, qty, min_th, cat_id))
            conn.executemany(
                "INSERT INTO products (name, price, cost, quantity, min_threshold, category_id) VALUES (?,?,?,?,?,?)",
                rows,
            )
            added += len(rows)

    return f"added_products={added}"


def seed_stock_movements(conn: sqlite3.Connection, movements: int, products: int) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM stock_movements")
    existing = int(cur.fetchone()["c"])
    if existing >= movements:
        return f"existing_stock_movements={existing} (no changes)"

    to_add = movements - existing
    product_ids = list(range(1, products + 1))
    types = ["IN", "OUT", "ADJUST", "TRANSFER"]
    reasons = ["sale", "purchase", "loss", "audit", "restock", "adjustment"]

    batch_size = 5000
    added = 0
    with conn:
        for i0 in range(0, to_add, batch_size):
            i1 = min(i0 + batch_size, to_add)
            rows = []
            for _ in range(i0, i1):
                product_id = random.choice(product_ids)
                movement_type = random.choice(types)
                qty = random.randint(1, 20)
                if movement_type == "OUT":
                    qty = -qty
                elif movement_type == "TRANSFER":
                    qty = random.choice([-qty, qty])
                reason = random.choice(reasons)
                rows.append((product_id, movement_type, qty, reason))

            conn.executemany(
                "INSERT INTO stock_movements (product_id, movement_type, quantity, reason) VALUES (?,?,?,?)",
                rows,
            )
            added += len(rows)

    return f"added_stock_movements={added}"


def seed_accounts(conn: sqlite3.Connection) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM accounts")
    existing = int(cur.fetchone()["c"])
    if existing > 0:
        return f"existing_accounts={existing} (no changes)"

    with conn:
        conn.executemany(
            "INSERT INTO accounts (name, phone, address, role, balance) VALUES (?,?,?,?,?)",
            [
                ("cash customer", "None", "None", "Customer", 0.0),
                ("random supplier", "None", "None", "Supplier", 0.0),
                ("wholesale customer", "None", "None", "Customer", 0.0),
                ("import supplier", "None", "None", "Supplier", 0.0),
            ],
        )
    return "added_accounts=4"


def seed_invoices_and_items(conn: sqlite3.Connection, invoices: int, products: int) -> str:
    cur = conn.execute("SELECT COUNT(*) AS c FROM invoices")
    existing = int(cur.fetchone()["c"])
    if existing >= invoices:
        return f"existing_invoices={existing} (no changes)"

    to_add = invoices - existing

    invoice_types = ["SALE", "PURCHASE", "MIXED_SALE"]
    payment_methods = ["cash", "card", "bank_transfer"]

    product_ids = list(range(1, products + 1))
    acc_ids = [r["id"] for r in conn.execute("SELECT id FROM accounts").fetchall()]
    if not acc_ids:
        raise RuntimeError("No accounts found; run seed_accounts first.")

    batch_size = 200  # keep transactions reasonable
    added_invoices = 0
    added_items = 0

    with conn:
        for i0 in range(0, to_add, batch_size):
            i1 = min(i0 + batch_size, to_add)

            for _ in range(i0, i1):
                inv_type = random.choice(invoice_types)
                partner_id = random.choice(acc_ids)
                status = "Paid"
                rate = round(random.uniform(14000, 16000), 2)
                tax = round(random.uniform(0, 50), 2)
                discount = round(random.uniform(0, 100), 2)
                payment_method = random.choice(payment_methods)

                item_count = random.randint(5, 20)
                chosen = random.sample(product_ids, k=min(item_count, len(product_ids)))

                placeholders = ",".join(["?"] * len(chosen))
                price_rows = conn.execute(
                    f"SELECT id, price, price_syp FROM products WHERE id IN ({placeholders})",
                    chosen,
                ).fetchall()
                price_map = {r["id"]: (float(r["price"]), float(r["price_syp"])) for r in price_rows}

                items = []
                total = 0.0
                total_syp = 0.0

                for pid in chosen:
                    qty = random.randint(1, 8)
                    unit_usd, unit_syp = price_map[pid]
                    item_discount = round(random.uniform(0, 10), 2)

                    line_usd = qty * unit_usd - item_discount
                    line_syp = qty * unit_syp - item_discount

                    total += line_usd
                    total_syp += line_syp
                    items.append((pid, qty, unit_usd, item_discount, unit_syp))

                cur2 = conn.execute(
                    """
                    INSERT INTO invoices
                    (type, partner_id, total, total_syp, rate_at_time, tax, discount, payment_method, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (inv_type, partner_id, round(total, 2), round(total_syp, 2), rate, tax, discount, payment_method, status),
                )
                invoice_id = int(cur2.lastrowid)

                conn.executemany(
                    """
                    INSERT INTO invoice_items
                    (invoice_id, product_id, quantity, price, item_discount, price_syp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [(invoice_id, pid, qty, unit_usd, item_discount, unit_syp) for (pid, qty, unit_usd, item_discount, unit_syp) in items],
                )

                added_invoices += 1
                added_items += len(items)

    return f"added_invoices={added_invoices}, added_invoice_items={added_items}"


# Bench queries (representative)
def query_products_by_category(conn: sqlite3.Connection):
    row = conn.execute("SELECT id FROM categories ORDER BY id DESC LIMIT 1").fetchone()
    category_id = int(row["id"]) if row else 1

    cur = conn.execute(
        """
        SELECT c.name, COUNT(p.id) AS product_count
        FROM categories c
        JOIN products p ON p.category_id = c.id
        WHERE c.id = ?
        GROUP BY c.name
        """,
        (category_id,),
    )
    cur.fetchall()
    return None


def query_stock_movements_agg(conn: sqlite3.Connection):
    row = conn.execute("SELECT id FROM products ORDER BY id DESC LIMIT 1").fetchone()
    product_id = int(row["id"]) if row else 1

    cur = conn.execute(
        """
        SELECT movement_type, SUM(quantity) AS qty_sum
        FROM stock_movements
        WHERE product_id = ?
        GROUP BY movement_type
        """,
        (product_id,),
    )
    cur.fetchall()
    return None


def query_invoice_with_items(conn: sqlite3.Connection):
    row = conn.execute("SELECT id FROM invoices ORDER BY id DESC LIMIT 1").fetchone()
    invoice_id = int(row["id"]) if row else 1

    cur = conn.execute(
        """
        SELECT i.id, i.type, i.date, COUNT(ii.id) AS items_count, SUM(ii.quantity) AS qty_sum
        FROM invoices i
        LEFT JOIN invoice_items ii ON ii.invoice_id = i.id
        WHERE i.id = ?
        GROUP BY i.id, i.type, i.date
        """,
        (invoice_id,),
    )
    cur.fetchone()
    return None


def query_invoices_filtered(conn: sqlite3.Connection):
    row = conn.execute("SELECT type FROM invoices LIMIT 1").fetchone()
    inv_type = row["type"] if row else "SALE"

    cur = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM invoices
        WHERE type = ?
        AND date >= datetime('now','-90 day')
        """,
        (inv_type,),
    )
    cur.fetchone()
    return None


def run_benchmark(db_path: str, log_path: str, products: int, categories: int, invoices: int) -> None:
    random.seed(42)

    if os.path.exists(log_path):
        os.remove(log_path)

    # Create log file early so we can confirm filesystem permissions
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"===== LOAD TEST START =====\n")
        log.write(f"Started: {now_iso()}\n")
        log.write(f"DB: {db_path}\n")
        log.write(f"Log: {log_path}\n")
        log.write(f"Params: products={products}, categories={categories}, invoices={invoices}\n")
        log.write(f"PID: {os.getpid()}\n")
        log.write(f"============================\n\n")

    conn = sqlite3.connect(db_path)
    try:
        apply_performance_pragmas(conn)
        conn.row_factory = sqlite3.Row
        ensure_schema(conn)

        movements_target = min(products * 2, max(products, 50_000))

        seed_steps = [
            ("Categories",          lambda: seed_categories(conn, categories)),
            ("Products",            lambda: seed_products(conn, products, categories)),
            (f"Stock movements (target: {movements_target:,})",
                                    lambda: seed_stock_movements(conn, movements_target, products)),
            ("Accounts",            lambda: seed_accounts(conn)),
            ("Invoices + items",    lambda: seed_invoices_and_items(conn, invoices, products)),
        ]

        with open(log_path, "a", encoding="utf-8") as log:

            log.write("=== PHASE 1 — DATA SEEDING ===\n")
            log.write(f"  (Skips rows that already exist — safe to re-run)\n\n")
            for i, (label, fn) in enumerate(seed_steps, 1):
                log.write(f"  [{i}/{len(seed_steps)}] {label} ... ")
                result, dt = time_block(fn)
                conn.commit()
                log.write(f"done in {dt:.1f}s  ({result})\n")
            log.write("\n")

            log.write("=== PHASE 2 — QUERY BENCHMARKS ===\n")
            log.write("  Each query is run 10 times. Times shown in milliseconds.\n")
            log.write("  Ratings: FAST < 50 ms | OK < 200 ms | SLOW < 1 s | VERY SLOW >= 1 s\n\n")

            results = {}
            bench_queries = [
                ("query_products_by_category", lambda: query_products_by_category(conn)),
                ("query_stock_movements_agg",  lambda: query_stock_movements_agg(conn)),
                ("query_invoice_with_items",   lambda: query_invoice_with_items(conn)),
                ("query_invoices_filtered",    lambda: query_invoices_filtered(conn)),
            ]
            for name, fn in bench_queries:
                timings = run_timing_series(fn, repeats=10)
                results[name] = timings
                log.write(format_timing_summary(name, timings))

            log.write("=== SUMMARY ===\n")
            log.write(f"  Finished : {now_iso()}\n")
            db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            log.write(f"  DB size  : {db_size_mb:.1f} MB\n")
            log.write(f"  DB file  : {db_path}\n\n")
            log.write("  Query results at a glance:\n")
            for name, timings in results.items():
                label = _QUERY_LABELS.get(name, name)
                rating = _rating(timings["p95"])
                log.write(f"    {rating:9s}  {_ms(timings['p95']):>10s} p95   {label}\n")
            log.write("\n")

    finally:
        conn.close()

    print(f"Load test done. Log written to: {log_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Temporary large DB performance/load test for SQLite backend.")
    parser.add_argument("--db", default="store.db", help="SQLite DB file path used by the app (default store.db)")
    parser.add_argument("--log", default="perf_test_log.txt", help="Output log file (txt)")
    parser.add_argument("--products", type=int, default=50000, help="How many products to generate")
    parser.add_argument("--categories", type=int, default=500, help="How many categories to generate")
    parser.add_argument("--invoices", type=int, default=20000, help="How many invoices to generate")
    args = parser.parse_args()

    run_benchmark(
        db_path=args.db,
        log_path=args.log,
        products=args.products,
        categories=args.categories,
        invoices=args.invoices,
    )
