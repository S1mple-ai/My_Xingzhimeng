import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 客户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                phone_suffix TEXT,
                points INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 面料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fabrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                material_type TEXT CHECK(material_type IN ('细帆', '细帆绗棉', '缎面绗棉')),
                usage_type TEXT CHECK(usage_type IN ('表布', '里布')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 包型分类表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bag_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                level INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES bag_categories (id)
            )
        ''')
        
        # 包型表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bag_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                subcategory_id INTEGER,
                price DECIMAL(10,2),
                image_path TEXT,
                video_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES bag_categories (id),
                FOREIGN KEY (subcategory_id) REFERENCES bag_categories (id)
            )
        ''')
        
        # 库存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2),
                quantity INTEGER DEFAULT 0,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                total_amount DECIMAL(10,2) DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # 订单商品表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_type TEXT CHECK(item_type IN ('现货', '定制')),
                inventory_id INTEGER,
                bag_type_id INTEGER,
                outer_fabric_id INTEGER,
                inner_fabric_id INTEGER,
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2),
                notes TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (inventory_id) REFERENCES inventory (id),
                FOREIGN KEY (bag_type_id) REFERENCES bag_types (id),
                FOREIGN KEY (outer_fabric_id) REFERENCES fabrics (id),
                FOREIGN KEY (inner_fabric_id) REFERENCES fabrics (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # 客户管理方法
    def add_customer(self, nickname: str, phone_suffix: str = "", notes: str = "") -> int:
        """添加客户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (nickname, phone_suffix, notes) VALUES (?, ?, ?)",
            (nickname, phone_suffix, notes)
        )
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return customer_id
    
    def get_customers(self) -> List[Dict]:
        """获取所有客户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
        customers = []
        for row in cursor.fetchall():
            customers.append({
                'id': row[0], 'nickname': row[1], 'phone_suffix': row[2],
                'points': row[3], 'notes': row[4], 'created_at': row[5], 'updated_at': row[6]
            })
        conn.close()
        return customers
    
    def update_customer(self, customer_id: int, nickname: str, phone_suffix: str, notes: str):
        """更新客户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE customers SET nickname=?, phone_suffix=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (nickname, phone_suffix, notes, customer_id)
        )
        conn.commit()
        conn.close()
    
    def delete_customer(self, customer_id: int):
        """删除客户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
        conn.close()
    
    def update_customer_points(self, customer_id: int, points_to_add: int):
        """更新客户积分"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE customers SET points = points + ?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (points_to_add, customer_id)
        )
        conn.commit()
        conn.close()
    
    # 面料管理方法
    def add_fabric(self, name: str, material_type: str, usage_type: str) -> int:
        """添加面料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fabrics (name, material_type, usage_type) VALUES (?, ?, ?)",
            (name, material_type, usage_type)
        )
        fabric_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return fabric_id
    
    def get_fabrics(self, usage_type: str = None) -> List[Dict]:
        """获取面料列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if usage_type:
            cursor.execute("SELECT * FROM fabrics WHERE usage_type=? ORDER BY created_at DESC", (usage_type,))
        else:
            cursor.execute("SELECT * FROM fabrics ORDER BY created_at DESC")
        
        fabrics = []
        for row in cursor.fetchall():
            fabrics.append({
                'id': row[0], 'name': row[1], 'material_type': row[2],
                'usage_type': row[3], 'created_at': row[4], 'updated_at': row[5]
            })
        conn.close()
        return fabrics
    
    def update_fabric(self, fabric_id: int, name: str, material_type: str, usage_type: str):
        """更新面料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE fabrics SET name=?, material_type=?, usage_type=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (name, material_type, usage_type, fabric_id)
        )
        conn.commit()
        conn.close()
    
    def delete_fabric(self, fabric_id: int):
        """删除面料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fabrics WHERE id=?", (fabric_id,))
        conn.commit()
        conn.close()
    
    # 包型分类管理
    def add_bag_category(self, name: str, parent_id: int = None) -> int:
        """添加包型分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        level = 1
        if parent_id:
            cursor.execute("SELECT level FROM bag_categories WHERE id=?", (parent_id,))
            parent_level = cursor.fetchone()
            if parent_level:
                level = parent_level[0] + 1
        
        cursor.execute(
            "INSERT INTO bag_categories (name, parent_id, level) VALUES (?, ?, ?)",
            (name, parent_id, level)
        )
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return category_id
    
    def get_bag_categories(self, parent_id: int = None) -> List[Dict]:
        """获取包型分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute("SELECT * FROM bag_categories WHERE parent_id IS NULL ORDER BY created_at")
        else:
            cursor.execute("SELECT * FROM bag_categories WHERE parent_id=? ORDER BY created_at", (parent_id,))
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0], 'name': row[1], 'parent_id': row[2],
                'level': row[3], 'created_at': row[4]
            })
        conn.close()
        return categories
    
    # 包型管理
    def add_bag_type(self, name: str, category_id: int, subcategory_id: int = None, 
                     price: float = 0, image_path: str = "", video_path: str = "") -> int:
        """添加包型"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bag_types (name, category_id, subcategory_id, price, image_path, video_path) VALUES (?, ?, ?, ?, ?, ?)",
            (name, category_id, subcategory_id, price, image_path, video_path)
        )
        bag_type_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bag_type_id
    
    def get_bag_types(self) -> List[Dict]:
        """获取包型列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bt.*, bc1.name as category_name, bc2.name as subcategory_name
            FROM bag_types bt
            LEFT JOIN bag_categories bc1 ON bt.category_id = bc1.id
            LEFT JOIN bag_categories bc2 ON bt.subcategory_id = bc2.id
            ORDER BY bt.created_at DESC
        """)
        
        bag_types = []
        for row in cursor.fetchall():
            bag_types.append({
                'id': row[0], 'name': row[1], 'category_id': row[2], 'subcategory_id': row[3],
                'price': row[4], 'image_path': row[5], 'video_path': row[6],
                'created_at': row[7], 'updated_at': row[8],
                'category_name': row[9], 'subcategory_name': row[10]
            })
        conn.close()
        return bag_types
    
    # 库存管理
    def add_inventory_item(self, product_name: str, description: str = "", 
                          price: float = 0, quantity: int = 0, image_path: str = "") -> int:
        """添加库存商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (product_name, description, price, quantity, image_path) VALUES (?, ?, ?, ?, ?)",
            (product_name, description, price, quantity, image_path)
        )
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    def get_inventory_items(self) -> List[Dict]:
        """获取库存商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory ORDER BY created_at DESC")
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0], 'product_name': row[1], 'description': row[2],
                'price': row[3], 'quantity': row[4], 'image_path': row[5],
                'created_at': row[6], 'updated_at': row[7]
            })
        conn.close()
        return items
    
    def update_inventory_quantity(self, item_id: int, quantity_change: int):
        """更新库存数量"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET quantity = quantity + ?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (quantity_change, item_id)
        )
        conn.commit()
        conn.close()
    
    # 订单管理
    def create_order(self, customer_id: int, notes: str = "") -> int:
        """创建订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (customer_id, notes) VALUES (?, ?)",
            (customer_id, notes)
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def add_order_item(self, order_id: int, item_type: str, quantity: int = 1, 
                      unit_price: float = 0, notes: str = "", **kwargs) -> int:
        """添加订单商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        inventory_id = kwargs.get('inventory_id')
        bag_type_id = kwargs.get('bag_type_id')
        outer_fabric_id = kwargs.get('outer_fabric_id')
        inner_fabric_id = kwargs.get('inner_fabric_id')
        
        cursor.execute(
            """INSERT INTO order_items 
               (order_id, item_type, inventory_id, bag_type_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item_type, inventory_id, bag_type_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes)
        )
        
        item_id = cursor.lastrowid
        
        # 如果是现货商品，扣减库存
        if item_type == '现货' and inventory_id:
            cursor.execute(
                "UPDATE inventory SET quantity = quantity - ?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (quantity, inventory_id)
            )
        
        # 更新订单总金额
        cursor.execute(
            "UPDATE orders SET total_amount = total_amount + ?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (unit_price * quantity, order_id)
        )
        
        conn.commit()
        conn.close()
        return item_id
    
    def get_orders(self) -> List[Dict]:
        """获取订单列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC
        """)
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'created_at': row[5], 'updated_at': row[6],
                'customer_name': row[7]
            })
        conn.close()
        return orders
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        """获取订单商品详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.*, i.product_name as inventory_name, bt.name as bag_type_name,
                   f1.name as outer_fabric_name, f2.name as inner_fabric_name
            FROM order_items oi
            LEFT JOIN inventory i ON oi.inventory_id = i.id
            LEFT JOIN bag_types bt ON oi.bag_type_id = bt.id
            LEFT JOIN fabrics f1 ON oi.outer_fabric_id = f1.id
            LEFT JOIN fabrics f2 ON oi.inner_fabric_id = f2.id
            WHERE oi.order_id = ?
        """, (order_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0], 'order_id': row[1], 'item_type': row[2],
                'inventory_id': row[3], 'bag_type_id': row[4], 'outer_fabric_id': row[5],
                'inner_fabric_id': row[6], 'quantity': row[7], 'unit_price': row[8], 'notes': row[9],
                'inventory_name': row[10], 'bag_type_name': row[11],
                'outer_fabric_name': row[12], 'inner_fabric_name': row[13]
            })
        conn.close()
        return items
    
    def complete_order_payment(self, order_id: int):
        """完成订单支付，更新客户积分"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取订单信息
        cursor.execute("SELECT customer_id, total_amount FROM orders WHERE id=?", (order_id,))
        order_info = cursor.fetchone()
        
        if order_info:
            customer_id, total_amount = order_info
            points_to_add = int(total_amount)  # 每1元增加1积分
            
            # 更新客户积分
            cursor.execute(
                "UPDATE customers SET points = points + ?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (points_to_add, customer_id)
            )
            
            # 更新订单状态
            cursor.execute(
                "UPDATE orders SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (order_id,)
            )
        
        conn.commit()
        conn.close()