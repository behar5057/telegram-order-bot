import sqlite3
import os

class Database:
    def __init__(self):
        # استخدم مساراً مطلقاً لـ Render
        self.db_path = '/tmp/orders.db' if 'RENDER' in os.environ else 'orders.db'
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول البائعين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            store_name TEXT NOT NULL,
            store_code TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول المنتجات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES sellers (id)
        )
        ''')
        
        # جدول الطلبيات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT,
            quantity INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    # دوال البائعين
    def add_seller(self, telegram_id, store_name, store_code, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO sellers (telegram_id, store_name, store_code, password)
            VALUES (?, ?, ?, ?)
            ''', (telegram_id, store_name, store_code, password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_seller_by_code(self, store_code):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sellers WHERE store_code = ?', (store_code,))
        seller = cursor.fetchone()
        conn.close()
        return seller
    
    # دوال المنتجات
    def add_product(self, seller_id, name, price, description=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO products (seller_id, name, price, description)
        VALUES (?, ?, ?, ?)
        ''', (seller_id, name, price, description))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        return product_id
    
    def get_products_by_seller(self, seller_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE seller_id = ?', (seller_id,))
        products = cursor.fetchall()
        conn.close()
        return products
    
    # دوال الطلبيات
    def add_order(self, product_id, customer_name, customer_phone, customer_address, quantity=1):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO orders (product_id, customer_name, customer_phone, customer_address, quantity)
        VALUES (?, ?, ?, ?, ?)
        ''', (product_id, customer_name, customer_phone, customer_address, quantity))
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return order_id
    
    def get_orders_for_seller(self, seller_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT o.*, p.name as product_name, p.price
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE p.seller_id = ?
        ORDER BY o.created_at DESC
        ''', (seller_id,))
        orders = cursor.fetchall()
        conn.close()
        return orders

db = Database()
