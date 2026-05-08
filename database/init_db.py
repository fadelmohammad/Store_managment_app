# init_db.py
import sqlite3
from schema import initialize_database

if __name__ == "__main__":
    DB_NAME = "POS.db"
    
    print(" بدء تهيئة قاعدة بيانات POS...")
    print("=" * 50)
    
    conn = initialize_database(DB_NAME)
    
    print("\n" + "=" * 50)
    print(" اكتملت التهيئة!")
    print("\n محتويات قاعدة البيانات:")
    

    conn_check = sqlite3.connect(DB_NAME)
    try:
        cursor = conn_check.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nعدد الجداول المنشأة: {len(tables)}")
        print("الجداول:")
        for table in tables:
            print(f"   - {table[0]}")
        

        cursor.execute("SELECT id, username, full_name, role FROM users")
        users = cursor.fetchall()
        print(f"\n المستخدمين ({len(users)}):")
        for user in users:
            print(f"   - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Role: {user[3]}")
        

        cursor.execute("SELECT role, can_manage_users, can_create_invoices FROM permissions")
        perms = cursor.fetchall()
        print(f"\n الصلاحيات ({len(perms)}):")
        for perm in perms:
            print(f"   - {perm[0]}: Manage Users={perm[1]}, Create Invoices={perm[2]}")
    finally:
        conn_check.close()
    
    print("\n" + "=" * 50)
    print(" يمكنك الآن تشغيل البرنامج الرئيسي")
