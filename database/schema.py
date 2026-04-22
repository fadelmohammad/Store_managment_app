# schema.py


def create_tables(conn):
    # Using context manager to ensure all tables are created safely
    with conn:
        # 1. INVENTORY MGT
        conn.execute(
            """CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            min_threshold INTEGER DEFAULT 5,
            category_id INTEGER,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )"""
        )
        try:
            conn.execute("ALTER TABLE products ADD COLUMN price_syp REAL DEFAULT 0")
        except:
            pass

        conn.execute(
            """CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY(parent_id) REFERENCES categories(id) ON DELETE CASCADE
        )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            movement_type TEXT,
            quantity INTEGER,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )"""
        )

        # 2. UNIFIED PARTNER ACCOUNTS
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0.0
            )
        """
        )

        # 3. INVOICING
        conn.execute(
            """CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,           -- SALE, RETURN, MIXED_SALE, PURCHASE, etc.
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            partner_id INTEGER,
            total REAL,                   -- USD Total
            total_syp REAL DEFAULT 0,     -- SYP Total
            rate_at_time REAL DEFAULT 1,  -- Exchange rate used
            tax REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            payment_method TEXT,
            status TEXT DEFAULT 'Paid',
            FOREIGN KEY(partner_id) REFERENCES accounts(id)
        )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_invoice_partner ON invoices(partner_id)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_invoice_type ON invoices(type)")

        conn.execute(
            """CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            item_discount REAL DEFAULT 0,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )"""
        )
        try:
            conn.execute(
                "ALTER TABLE invoice_items ADD COLUMN price_syp REAL DEFAULT 0"
            )
        except:
            pass

        # 4. ACCOUNTING LEDGER (Double-Entry System)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS accounts_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT
        )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            reference_id INTEGER
        )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            account_id INTEGER,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES journal_entries(id),
            FOREIGN KEY(account_id) REFERENCES accounts_ledger(id)
        )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
            )"""
        )


def seed_ledger_accounts(conn):
    """Initializes the Chart of Accounts."""
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


def insert_dummy_data(conn):
    with conn:
        # Check products
        res_products = conn.execute("SELECT COUNT(*) FROM products")
        if res_products.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO products (name, price, cost, quantity, min_threshold, category_id) VALUES (?,?,?,?,?,?)",
                [
                    ("Laptop", 1200.00, 800, 10, 2, None),
                    ("Mouse", 25.00, 10, 50, 5, None),
                ],
            )

        # Check accounts
        res_accounts = conn.execute("SELECT COUNT(*) FROM accounts")
        if res_accounts.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO accounts (name, phone, address, role, balance) VALUES (?,?,?,?,?)",
                [
                    ("cash customer", "None", "None", "Customer", 0.0),
                    ("random supplier", "None", "None", "Supplier", 0.0),
                ],
            )
