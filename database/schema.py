# schema.py

import sqlite3
import logging
import hashlib
import os

logger = logging.getLogger(__name__)

# ── Schema version ────────────────────────────────────────────────────────────
# Bump this integer every time you add a migration step below.
# Rule: never edit an existing migration — only append new ones.
SCHEMA_VERSION = 3


def get_schema_version(conn) -> int:
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = 'schema_version'").fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def set_schema_version(conn, version: int) -> None:
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('schema_version', ?)",
            (str(version),),
        )


def run_migrations(conn) -> None:
    """
    Runs only the migrations that haven't been applied yet.
    Safe to call on every startup AND after every restore.

    HOW TO ADD A NEW MIGRATION:
      1. Write a new _migrate_vN function below.
      2. Append it to _MIGRATIONS list.
      3. Bump SCHEMA_VERSION by 1.
    Never edit or reorder existing migration functions.
    """
    # settings table must exist before we can read/write schema_version
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

    current = get_schema_version(conn)
    if current >= SCHEMA_VERSION:
        return

    for version, migrate_fn in enumerate(_MIGRATIONS, start=1):
        if version <= current:
            continue
        logger.info(f"Applying schema migration v{version}...")
        try:
            migrate_fn(conn)
            set_schema_version(conn, version)
            logger.info(f"Migration v{version} applied.")
        except Exception as e:
            logger.error(f"Migration v{version} failed: {e}")
            raise


# ── Migration functions ───────────────────────────────────────────────────────
# Each function applies exactly one version's changes.

def _migrate_v1(conn):
    """Initial schema — all base tables."""
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT UNIQUE NOT NULL,
            can_view_products BOOLEAN DEFAULT 0,
            can_edit_products BOOLEAN DEFAULT 0,
            can_delete_products BOOLEAN DEFAULT 0,
            can_view_invoices BOOLEAN DEFAULT 0,
            can_create_invoices BOOLEAN DEFAULT 0,
            can_edit_invoices BOOLEAN DEFAULT 0,
            can_delete_invoices BOOLEAN DEFAULT 0,
            can_view_accounts BOOLEAN DEFAULT 0,
            can_edit_accounts BOOLEAN DEFAULT 0,
            can_view_reports BOOLEAN DEFAULT 0,
            can_manage_users BOOLEAN DEFAULT 0,
            can_manage_settings BOOLEAN DEFAULT 0
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY(parent_id) REFERENCES categories(id) ON DELETE CASCADE
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            min_threshold INTEGER DEFAULT 5,
            category_id INTEGER,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            movement_type TEXT,
            quantity INTEGER,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            balance REAL DEFAULT 0.0
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            partner_id INTEGER,
            total REAL,
            total_syp REAL DEFAULT 0,
            rate_at_time REAL DEFAULT 1,
            tax REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            payment_method TEXT,
            status TEXT DEFAULT 'Paid',
            FOREIGN KEY(partner_id) REFERENCES accounts(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            item_discount REAL DEFAULT 0,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS accounts_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            reference_id INTEGER
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            account_id INTEGER,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES journal_entries(id),
            FOREIGN KEY(account_id) REFERENCES accounts_ledger(id)
        )""")
        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoice_partner ON invoices(partner_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoice_type ON invoices(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_type_date ON invoices(type, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_quantity ON products(quantity)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_products_min_threshold ON products(min_threshold)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product_date ON stock_movements(product_id, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id)")


def _migrate_v2(conn):
    """Add price_syp columns to products and invoice_items."""
    for sql in [
        "ALTER TABLE products ADD COLUMN price_syp REAL DEFAULT 0",
        "ALTER TABLE invoice_items ADD COLUMN price_syp REAL DEFAULT 0",
    ]:
        try:
            with conn:
                conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # column already exists — safe to ignore


def _migrate_v3(conn):
    """
    Placeholder for the next migration.
    Replace this body when you need to add tables/columns in the next version.
    """
    pass


# Ordered list — position+1 == version number. Never reorder.
_MIGRATIONS = [_migrate_v1, _migrate_v2, _migrate_v3]


# ── Public API (called from main.py — signatures unchanged) ───────────────────

def create_tables(conn):
    """Backward-compatible entry point — now delegates to run_migrations."""
    run_migrations(conn)


def seed_ledger_accounts(conn):
    accounts = [
        ("Cash", "Asset"),
        ("Accounts Receivable", "Asset"),
        ("Inventory", "Asset"),
        ("Accounts Payable", "Liability"),
        ("Owner Equity", "Equity"),
        ("Sales Revenue", "Revenue"),
        ("Cost of Goods Sold", "Expense"),
        ("General Expense", "Expense"),
    ]
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO accounts_ledger (name, type) VALUES (?, ?)", accounts
        )


def seed_permissions(conn):
    permissions = [
        ('admin',      1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        ('manager',    1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0),
        ('accountant', 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0),
        ('viewer',     1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0),
        ('user',       1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0),
    ]
    with conn:
        conn.executemany("""
            INSERT OR IGNORE INTO permissions
            (role, can_view_products, can_edit_products, can_delete_products,
             can_view_invoices, can_create_invoices, can_edit_invoices, can_delete_invoices,
             can_view_accounts, can_edit_accounts, can_view_reports,
             can_manage_users, can_manage_settings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, permissions)


def create_admin_user(conn):
    def hash_password(password: str) -> str:
        iterations = 200_000
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
        return f"pbkdf2${iterations}${salt.hex()}${dk.hex()}"

    with conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (username, password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", hash_password("123456"), "مدير النظام", "admin", 1))


def insert_dummy_data(conn):
    with conn:
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO products (name, price, cost, quantity, min_threshold, category_id) VALUES (?,?,?,?,?,?)",
                [("Laptop", 1200.00, 800, 10, 2, None), ("Mouse", 25.00, 10, 50, 5, None)],
            )
        if conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO accounts (name, phone, address, role, balance) VALUES (?,?,?,?,?)",
                [("cash customer", "None", "None", "Customer", 0.0),
                 ("random supplier", "None", "None", "Supplier", 0.0)],
            )


def initialize_database(db_path="store.db"):
    conn = sqlite3.connect(db_path)
    try:
        run_migrations(conn)
        seed_ledger_accounts(conn)
        seed_permissions(conn)
        create_admin_user(conn)
        insert_dummy_data(conn)
        logger.info("Database initialized successfully")
        return conn
    except Exception:
        logger.exception("Database initialization error")
        raise
    finally:
        conn.close()
