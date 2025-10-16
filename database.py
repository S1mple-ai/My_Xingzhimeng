import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            return conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise Exception(f"数据库连接失败: {e}")
    
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
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 为现有的面料表添加image_path字段（如果不存在）
        try:
            cursor.execute('ALTER TABLE fabrics ADD COLUMN image_path TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
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
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # 为已存在的orders表添加image_path字段（如果不存在）
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN image_path TEXT")
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
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
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """根据ID获取订单详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        
        row = cursor.fetchone()
        if row:
            order = {
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 
                'created_at': row[6], 'updated_at': row[7], 'customer_name': row[8]
            }
            conn.close()
            return order
        
        conn.close()
        return None
    
    def update_order(self, order_id: int, customer_id: int, notes: str = "", 
                    image_path: str = "", status: str = "pending") -> bool:
        """更新订单信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET customer_id=?, notes=?, image_path=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (customer_id, notes, image_path, status, order_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_order(self, order_id: int) -> bool:
        """删除订单及其相关商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查订单状态，已完成的订单不能删除
        cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,))
        order_status = cursor.fetchone()
        
        if order_status and order_status[0] == 'completed':
            conn.close()
            return False  # 已完成的订单不能删除
        
        # 删除订单商品
        cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
        
        # 删除订单
        cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
    
    def delete_orders_batch(self, order_ids: List[int]) -> Tuple[int, List[int]]:
        """批量删除订单
        
        Returns:
            Tuple[int, List[int]]: (成功删除的数量, 无法删除的订单ID列表)
        """
        if not order_ids:
            return 0, []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        success_count = 0
        failed_ids = []
        
        for order_id in order_ids:
            # 检查订单状态
            cursor.execute("SELECT status FROM orders WHERE id=?", (order_id,))
            order_status = cursor.fetchone()
            
            if order_status and order_status[0] == 'completed':
                failed_ids.append(order_id)
                continue
            
            # 删除订单商品
            cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
            
            # 删除订单
            cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
            
            if cursor.rowcount > 0:
                success_count += 1
            else:
                failed_ids.append(order_id)
        
        conn.commit()
        conn.close()
        return success_count, failed_ids
    
    def update_order_item(self, item_id: int, quantity: int, unit_price: float, notes: str = "") -> bool:
        """更新订单商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE order_items SET quantity=?, unit_price=?, notes=? WHERE id=?",
            (quantity, unit_price, notes, item_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_order_item(self, item_id: int) -> bool:
        """删除订单商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE id=?", (item_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # 客户管理方法
    def add_customer(self, nickname: str, phone_suffix: str = "", notes: str = "") -> int:
        """添加客户"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO customers (nickname, phone_suffix, notes) VALUES (?, ?, ?)",
                (nickname, phone_suffix, notes)
            )
            customer_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Successfully added customer: {nickname}")
            return customer_id
        except sqlite3.Error as e:
            logger.error(f"Error adding customer {nickname}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"添加客户失败: {str(e)}")
    
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE customers SET nickname=?, phone_suffix=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (nickname, phone_suffix, notes, customer_id)
            )
            if cursor.rowcount == 0:
                raise Exception(f"客户ID {customer_id} 不存在")
            conn.commit()
            conn.close()
            logger.info(f"Successfully updated customer ID: {customer_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"更新客户信息失败: {str(e)}")
    
    def delete_customer(self, customer_id: int):
        """删除客户"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查客户是否存在
            cursor.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
            if not cursor.fetchone():
                raise Exception(f"客户ID {customer_id} 不存在")
            
            # 检查是否有关联订单
            cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id=?", (customer_id,))
            order_count = cursor.fetchone()[0]
            if order_count > 0:
                raise Exception(f"无法删除客户，该客户有 {order_count} 个关联订单")
            
            cursor.execute("DELETE FROM customers WHERE id=?", (customer_id,))
            conn.commit()
            conn.close()
            logger.info(f"Successfully deleted customer ID: {customer_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"删除客户失败: {str(e)}")
    
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
    def add_fabric(self, name: str, material_type: str, usage_type: str, image_path: str = None) -> int:
        """添加面料"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查是否已存在同名面料
            cursor.execute("SELECT id FROM fabrics WHERE name=?", (name,))
            if cursor.fetchone():
                raise Exception(f"面料名称 '{name}' 已存在")
            
            cursor.execute(
                "INSERT INTO fabrics (name, material_type, usage_type, image_path) VALUES (?, ?, ?, ?)",
                (name, material_type, usage_type, image_path)
            )
            fabric_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Successfully added fabric: {name}")
            return fabric_id
        except sqlite3.Error as e:
            logger.error(f"Error adding fabric {name}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"添加面料失败: {str(e)}")
    
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
    
    def update_fabric(self, fabric_id: int, name: str, material_type: str, usage_type: str, image_path: str = None):
        """更新面料"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查面料是否存在
            cursor.execute("SELECT id FROM fabrics WHERE id=?", (fabric_id,))
            if not cursor.fetchone():
                raise Exception(f"面料ID {fabric_id} 不存在")
            
            # 检查是否有其他面料使用相同名称
            cursor.execute("SELECT id FROM fabrics WHERE name=? AND id!=?", (name, fabric_id))
            if cursor.fetchone():
                raise Exception(f"面料名称 '{name}' 已被其他面料使用")
            
            cursor.execute(
                "UPDATE fabrics SET name=?, material_type=?, usage_type=?, image_path=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (name, material_type, usage_type, image_path, fabric_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"Successfully updated fabric ID: {fabric_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating fabric {fabric_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"更新面料失败: {str(e)}")
    
    def delete_fabric(self, fabric_id: int):
        """删除面料"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查面料是否存在
            cursor.execute("SELECT id FROM fabrics WHERE id=?", (fabric_id,))
            if not cursor.fetchone():
                raise Exception(f"面料ID {fabric_id} 不存在")
            
            # 检查是否有关联的订单项记录（作为外布或内布）
            cursor.execute("""
                SELECT COUNT(*) FROM order_items 
                WHERE outer_fabric_id=? OR inner_fabric_id=?
            """, (fabric_id, fabric_id))
            order_items_count = cursor.fetchone()[0]
            if order_items_count > 0:
                raise Exception(f"无法删除面料，该面料有 {order_items_count} 个关联订单记录")
            
            cursor.execute("DELETE FROM fabrics WHERE id=?", (fabric_id,))
            conn.commit()
            conn.close()
            logger.info(f"Successfully deleted fabric ID: {fabric_id}")
        except sqlite3.Error as e:
            logger.error(f"Error deleting fabric {fabric_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"删除面料失败: {str(e)}")
    
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
    
    def update_bag_category(self, category_id: int, name: str, parent_id: int = None) -> bool:
        """更新包型分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 计算新的层级
        level = 1
        if parent_id:
            cursor.execute("SELECT level FROM bag_categories WHERE id=?", (parent_id,))
            parent_level = cursor.fetchone()
            if parent_level:
                level = parent_level[0] + 1
        
        cursor.execute(
            "UPDATE bag_categories SET name=?, parent_id=?, level=? WHERE id=?",
            (name, parent_id, level, category_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_bag_category(self, category_id: int) -> bool:
        """删除包型分类（级联删除子分类）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否有子分类
        cursor.execute("SELECT COUNT(*) FROM bag_categories WHERE parent_id=?", (category_id,))
        child_count = cursor.fetchone()[0]
        
        # 检查是否有包型使用此分类
        cursor.execute("SELECT COUNT(*) FROM bag_types WHERE main_category_id=? OR subcategory_id=?", 
                      (category_id, category_id))
        bag_count = cursor.fetchone()[0]
        
        if child_count > 0 or bag_count > 0:
            conn.close()
            return False  # 有子分类或包型使用，不能删除
        
        cursor.execute("DELETE FROM bag_categories WHERE id=?", (category_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_all_bag_categories_tree(self) -> List[Dict]:
        """获取所有分类的树形结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bag_categories ORDER BY level, created_at")
        
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
    
    def get_bag_type_by_id(self, bag_type_id: int) -> Optional[Dict]:
        """根据ID获取包型信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bt.*, bc1.name as category_name, bc2.name as subcategory_name
            FROM bag_types bt
            LEFT JOIN bag_categories bc1 ON bt.category_id = bc1.id
            LEFT JOIN bag_categories bc2 ON bt.subcategory_id = bc2.id
            WHERE bt.id = ?
        """, (bag_type_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0], 'name': row[1], 'category_id': row[2], 'subcategory_id': row[3],
                'price': row[4], 'image_path': row[5], 'video_path': row[6],
                'created_at': row[7], 'updated_at': row[8],
                'category_name': row[9], 'subcategory_name': row[10]
            }
        return None
    
    def update_bag_type(self, bag_type_id: int, name: str, category_id: int, 
                       subcategory_id: int = None, price: float = 0, 
                       image_path: str = "", video_path: str = "") -> bool:
        """更新包型信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bag_types 
            SET name=?, category_id=?, subcategory_id=?, price=?, 
                image_path=?, video_path=?, updated_at=CURRENT_TIMESTAMP 
            WHERE id=?
        """, (name, category_id, subcategory_id, price, image_path, video_path, bag_type_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_bag_type(self, bag_type_id: int) -> bool:
        """删除包型（检查是否有关联的订单项）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否有订单项使用此包型
        cursor.execute("""
            SELECT COUNT(*) FROM order_items 
            WHERE item_type = '定制' AND bag_type_id = ?
        """, (bag_type_id,))
        order_count = cursor.fetchone()[0]
        
        if order_count > 0:
            conn.close()
            return False  # 有订单使用，不能删除
        
        cursor.execute("DELETE FROM bag_types WHERE id=?", (bag_type_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
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
    
    def update_inventory_item(self, item_id: int, product_name: str, description: str = "", 
                             price: float = 0, quantity: int = 0, image_path: str = "") -> bool:
        """更新库存商品完整信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET product_name=?, description=?, price=?, quantity=?, image_path=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (product_name, description, price, quantity, image_path, item_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_inventory_item(self, item_id: int) -> bool:
        """删除库存商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否有订单使用此商品
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE inventory_id=?", (item_id,))
        order_count = cursor.fetchone()[0]
        
        if order_count > 0:
            conn.close()
            return False  # 有订单使用，不能删除
        
        cursor.execute("DELETE FROM inventory WHERE id=?", (item_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_inventory_item_by_id(self, item_id: int) -> Optional[Dict]:
        """根据ID获取库存商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE id=?", (item_id,))
        row = cursor.fetchone()
        
        if row:
            item = {
                'id': row[0], 'product_name': row[1], 'description': row[2],
                'price': row[3], 'quantity': row[4], 'image_path': row[5],
                'created_at': row[6], 'updated_at': row[7]
            }
            conn.close()
            return item
        
        conn.close()
        return None
    
    # 订单管理
    def create_order(self, customer_id: int, notes: str = "", image_path: str = "") -> int:
        """创建订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (customer_id, notes, image_path) VALUES (?, ?, ?)",
            (customer_id, notes, image_path)
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
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'customer_name': row[8]
            })
        conn.close()
        return orders
    
    def get_orders_paginated(self, page: int = 1, page_size: int = 10, search_term: str = "", status_filter: str = "", 
                           date_filter: str = "", amount_filter: str = "", sort_by: str = "创建时间(新到旧)") -> Tuple[List[Dict], int]:
        """获取分页订单列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建WHERE条件
        where_conditions = []
        params = []
        
        if search_term:
            where_conditions.append("(c.nickname LIKE ? OR o.notes LIKE ? OR CAST(o.id AS TEXT) LIKE ?)")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        if status_filter:
            where_conditions.append("o.status = ?")
            params.append(status_filter)
        
        # 日期筛选
        if date_filter and date_filter != "全部":
            if date_filter == "今天":
                where_conditions.append("DATE(o.created_at) = DATE('now')")
            elif date_filter == "本周":
                where_conditions.append("DATE(o.created_at) >= DATE('now', 'weekday 0', '-7 days')")
            elif date_filter == "本月":
                where_conditions.append("DATE(o.created_at) >= DATE('now', 'start of month')")
            elif date_filter == "最近7天":
                where_conditions.append("DATE(o.created_at) >= DATE('now', '-7 days')")
            elif date_filter == "最近30天":
                where_conditions.append("DATE(o.created_at) >= DATE('now', '-30 days')")
        
        # 金额筛选
        if amount_filter and amount_filter != "全部":
            if amount_filter == "0-100":
                where_conditions.append("o.total_amount >= 0 AND o.total_amount <= 100")
            elif amount_filter == "100-500":
                where_conditions.append("o.total_amount > 100 AND o.total_amount <= 500")
            elif amount_filter == "500-1000":
                where_conditions.append("o.total_amount > 500 AND o.total_amount <= 1000")
            elif amount_filter == "1000以上":
                where_conditions.append("o.total_amount > 1000")
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # 排序条件
        order_clause = "ORDER BY "
        if sort_by == "创建时间(新到旧)":
            order_clause += "o.created_at DESC"
        elif sort_by == "创建时间(旧到新)":
            order_clause += "o.created_at ASC"
        elif sort_by == "金额(高到低)":
            order_clause += "o.total_amount DESC"
        elif sort_by == "金额(低到高)":
            order_clause += "o.total_amount ASC"
        else:
            order_clause += "o.created_at DESC"
        
        # 获取总数
        count_query = f"""
            SELECT COUNT(*)
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            {where_clause}
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT o.*, c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [page_size, offset])
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'customer_name': row[8]
            })
        
        conn.close()
        return orders, total_count
    
    def get_orders_by_ids(self, order_ids: List[int]) -> List[Dict]:
        """根据ID列表获取订单"""
        if not order_ids:
            return []
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in order_ids])
        cursor.execute(f"""
            SELECT o.*, c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id IN ({placeholders})
            ORDER BY o.created_at DESC
        """, order_ids)
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'customer_name': row[8]
            })
        
        conn.close()
        return orders
    
    def get_orders_with_items_for_export(self, order_ids: List[int]) -> Dict[int, Dict]:
        """获取订单及其商品信息用于CSV导出（优化版本）"""
        if not order_ids:
            return {}
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取订单基本信息
        placeholders = ','.join(['?' for _ in order_ids])
        cursor.execute(f"""
            SELECT o.*, c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id IN ({placeholders})
        """, order_ids)
        
        orders_dict = {}
        for row in cursor.fetchall():
            orders_dict[row[0]] = {
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 
                'created_at': row[6], 'updated_at': row[7], 'customer_name': row[8],
                'items': []
            }
        
        # 获取所有订单的商品信息
        cursor.execute(f"""
            SELECT oi.*, i.product_name as inventory_name, bt.name as bag_type_name,
                   f1.name as outer_fabric_name, f2.name as inner_fabric_name
            FROM order_items oi
            LEFT JOIN inventory i ON oi.inventory_id = i.id
            LEFT JOIN bag_types bt ON oi.bag_type_id = bt.id
            LEFT JOIN fabrics f1 ON oi.outer_fabric_id = f1.id
            LEFT JOIN fabrics f2 ON oi.inner_fabric_id = f2.id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id, oi.id
        """, order_ids)
        
        for row in cursor.fetchall():
            order_id = row[1]  # order_id is the second column
            if order_id in orders_dict:
                orders_dict[order_id]['items'].append({
                    'id': row[0], 'order_id': row[1], 'item_type': row[2],
                    'inventory_id': row[3], 'bag_type_id': row[4], 'outer_fabric_id': row[5],
                    'inner_fabric_id': row[6], 'quantity': row[7], 'unit_price': row[8],
                    'notes': row[9], 'inventory_name': row[10], 'bag_type_name': row[11],
                    'outer_fabric_name': row[12], 'inner_fabric_name': row[13]
                })
        
        conn.close()
        return orders_dict
    
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