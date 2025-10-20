import sqlite3
import os
import logging
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from functools import wraps
import hashlib
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 缓存装饰器
def cache_query(ttl: int = 300, key_prefix: str = ""):
    """
    查询缓存装饰器
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}_{func.__name__}"
            
            # 添加参数到缓存键
            if args or kwargs:
                params_str = json.dumps({"args": args[1:], "kwargs": kwargs}, sort_keys=True, default=str)
                cache_key += f"_{hashlib.md5(params_str.encode()).hexdigest()[:8]}"
            
            # 尝试从缓存获取
            try:
                cached_result = st.session_state.get(f"cache_{cache_key}")
                if cached_result is not None:
                    cache_time = st.session_state.get(f"cache_time_{cache_key}", 0)
                    if (datetime.now().timestamp() - cache_time) < ttl:
                        logger.debug(f"缓存命中: {cache_key}")
                        return cached_result
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 存储到缓存
            try:
                st.session_state[f"cache_{cache_key}"] = result
                st.session_state[f"cache_time_{cache_key}"] = datetime.now().timestamp()
                logger.debug(f"缓存存储: {cache_key}")
            except Exception as e:
                logger.warning(f"缓存存储失败: {e}")
            
            return result
        return wrapper
    return decorator

class DatabaseManager:
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
        self.init_database()
    
    def clear_cache(self, cache_prefix: str = None):
        """清理缓存"""
        try:
            if cache_prefix:
                # 清理特定前缀的缓存
                keys_to_remove = []
                for key in st.session_state.keys():
                    if key.startswith(f"cache_{cache_prefix}") or key.startswith(f"cache_time_{cache_prefix}"):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del st.session_state[key]
                
                logger.debug(f"清理缓存: {cache_prefix} ({len(keys_to_remove)} 项)")
            else:
                # 清理所有查询缓存
                keys_to_remove = []
                for key in st.session_state.keys():
                    if key.startswith("cache_") or key.startswith("cache_time_"):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del st.session_state[key]
                
                logger.debug(f"清理所有缓存 ({len(keys_to_remove)} 项)")
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
    
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
                outer_fabric_id INTEGER,
                inner_fabric_id INTEGER,
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2),
                notes TEXT,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (inventory_id) REFERENCES inventory (id),
                FOREIGN KEY (outer_fabric_id) REFERENCES fabrics (id),
                FOREIGN KEY (inner_fabric_id) REFERENCES fabrics (id)
            )
        ''')
        
        # 为现有的order_items表添加新字段（如果不存在）
        try:
            cursor.execute('ALTER TABLE order_items ADD COLUMN outer_fabric_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE order_items ADD COLUMN inner_fabric_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # 更新item_type的约束以支持定制商品
        try:
            # 创建新表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    item_type TEXT CHECK(item_type IN ('现货', '定制')),
                    inventory_id INTEGER,
                    outer_fabric_id INTEGER,
                    inner_fabric_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    unit_price DECIMAL(10,2),
                    notes TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (inventory_id) REFERENCES inventory (id),
                    FOREIGN KEY (outer_fabric_id) REFERENCES fabrics (id),
                    FOREIGN KEY (inner_fabric_id) REFERENCES fabrics (id)
                )
            ''')
            
            # 复制数据
            cursor.execute('''
                INSERT INTO order_items_new (id, order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes)
                SELECT id, order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes
                FROM order_items
            ''')
            
            # 删除旧表
            cursor.execute('DROP TABLE order_items')
            
            # 重命名新表
            cursor.execute('ALTER TABLE order_items_new RENAME TO order_items')
        except sqlite3.OperationalError:
            # 如果操作失败，说明表结构已经正确
            pass
        
        conn.commit()
        conn.close()
    
    @cache_query(ttl=300, key_prefix="fabric_analysis")
    def get_fabric_usage_analysis(self):
        """获取面料使用分析数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 查询表布使用情况
        cursor.execute("""
            SELECT f.name as fabric_name, f.usage_type, COUNT(oi.outer_fabric_id) as usage_count
            FROM fabrics f
            LEFT JOIN order_items oi ON f.id = oi.outer_fabric_id
            WHERE f.usage_type = '表布'
            GROUP BY f.id, f.name, f.usage_type
            HAVING usage_count > 0
            ORDER BY usage_count DESC
        """)
        outer_fabric_data = cursor.fetchall()
        
        # 查询里布使用情况
        cursor.execute("""
            SELECT f.name as fabric_name, f.usage_type, COUNT(oi.inner_fabric_id) as usage_count
            FROM fabrics f
            LEFT JOIN order_items oi ON f.id = oi.inner_fabric_id
            WHERE f.usage_type = '里布'
            GROUP BY f.id, f.name, f.usage_type
            HAVING usage_count > 0
            ORDER BY usage_count DESC
        """)
        inner_fabric_data = cursor.fetchall()
        
        # 合并数据
        fabric_usage = []
        for row in outer_fabric_data:
            fabric_usage.append({
                'fabric_name': row[0],
                'usage_type': row[1],
                'usage_count': row[2]
            })
        
        for row in inner_fabric_data:
            fabric_usage.append({
                'fabric_name': row[0],
                'usage_type': row[1],
                'usage_count': row[2]
            })
        
        conn.close()
        return fabric_usage
    
    @cache_query(ttl=300, key_prefix="sales_analysis")
    def get_sales_analysis(self, time_period: str):
        """获取销售分析数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 根据时间段确定日期范围
        if time_period == "近一周":
            date_filter = "DATE(o.created_at) >= DATE('now', '-7 days')"
        elif time_period == "近一月":
            date_filter = "DATE(o.created_at) >= DATE('now', '-30 days')"
        elif time_period == "近一季度":
            date_filter = "DATE(o.created_at) >= DATE('now', '-90 days')"
        elif time_period == "近一年":
            date_filter = "DATE(o.created_at) >= DATE('now', '-365 days')"
        else:
            date_filter = "1=1"  # 所有数据
        
        # 获取订单数据
        cursor.execute(f"""
            SELECT o.id, o.total_amount, DATE(o.created_at) as order_date
            FROM orders o
            WHERE {date_filter} AND o.status != 'cancelled'
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
        
        if not orders:
            conn.close()
            return {'orders': [], 'daily_sales': [], 'product_sales': [], 'total_orders': 0, 'total_amount': 0}
        
        # 计算每日销售额
        cursor.execute(f"""
            SELECT DATE(o.created_at) as date, SUM(o.total_amount) as amount, COUNT(*) as order_count
            FROM orders o
            WHERE {date_filter} AND o.status != 'cancelled'
            GROUP BY DATE(o.created_at)
            ORDER BY date
        """)
        daily_sales = []
        for row in cursor.fetchall():
            daily_sales.append({
                'date': row[0],
                'amount': float(row[1]) if row[1] else 0,
                'order_count': row[2]
            })
        
        # 获取商品销售排行（现货商品）
        cursor.execute(f"""
            SELECT i.product_name, SUM(oi.quantity) as quantity, SUM(oi.quantity * oi.unit_price) as total_amount
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN inventory i ON oi.inventory_id = i.id
            WHERE {date_filter} AND o.status != 'cancelled' AND oi.item_type = '现货' AND i.product_name IS NOT NULL
            GROUP BY i.product_name
            ORDER BY quantity DESC
        """)
        product_sales = []
        for row in cursor.fetchall():
            product_sales.append({
                'product_name': row[0],
                'quantity': row[1],
                'total_amount': float(row[2]) if row[2] else 0
            })
        
        # 获取定制商品销售情况
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN of.name IS NOT NULL AND if.name IS NOT NULL 
                    THEN '定制商品(' || of.name || '+' || if.name || ')'
                    ELSE '定制商品'
                END as product_name,
                SUM(oi.quantity) as quantity,
                SUM(oi.quantity * oi.unit_price) as total_amount
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN fabrics of ON oi.outer_fabric_id = of.id
            LEFT JOIN fabrics if ON oi.inner_fabric_id = if.id
            WHERE {date_filter} AND o.status != 'cancelled' AND oi.item_type = '定制'
            GROUP BY of.name, if.name
            ORDER BY quantity DESC
        """)
        
        for row in cursor.fetchall():
            product_sales.append({
                'product_name': row[0],
                'quantity': row[1],
                'total_amount': float(row[2]) if row[2] else 0
            })
        
        # 计算总计
        total_orders = len(orders)
        total_amount = sum([float(order[1]) if order[1] else 0 for order in orders])
        
        conn.close()
        
        return {
            'orders': orders,
            'daily_sales': daily_sales,
            'product_sales': product_sales,
            'total_orders': total_orders,
            'total_amount': total_amount
        }
    
    @cache_query(ttl=300, key_prefix="customer_analysis")
    def get_customer_analysis(self):
        """获取客户分析数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取客户积分分布
        cursor.execute("""
            SELECT points
            FROM customers
            WHERE points > 0
            ORDER BY points
        """)
        points_data = cursor.fetchall()
        points_distribution = [{'points': row[0]} for row in points_data]
        
        # 获取客户订单频次
        cursor.execute("""
            SELECT c.nickname, COUNT(o.id) as order_count, SUM(o.total_amount) as total_spent
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            WHERE o.id IS NOT NULL
            GROUP BY c.id, c.nickname
            ORDER BY order_count DESC
        """)
        order_frequency_data = cursor.fetchall()
        order_frequency = []
        for row in order_frequency_data:
            order_frequency.append({
                'nickname': row[0],
                'order_count': row[1],
                'total_spent': float(row[2]) if row[2] else 0
            })
        
        conn.close()
        
        return {
            'points_distribution': points_distribution,
            'order_frequency': order_frequency
        }
    
    @cache_query(ttl=300, key_prefix="order_status_analysis")
    def get_order_status_analysis(self):
        """获取订单状态分析数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 订单状态映射
        status_mapping = {
            'pending': '待处理',
            'processing': '处理中',
            'completed': '已完成',
            'cancelled': '已取消',
            'shipped': '已发货',
            'delivered': '已送达'
        }
        
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM orders
            GROUP BY status
            ORDER BY count DESC
        """)
        
        status_data = []
        for row in cursor.fetchall():
            status_data.append({
                'status': row[0],
                'status_name': status_mapping.get(row[0], row[0]),
                'count': row[1]
            })
        
        conn.close()
        return status_data
    
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
        """删除订单及其相关商品（支持删除所有状态的订单）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 删除订单商品
            cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
            
            # 删除订单（不再检查状态，允许删除所有状态的订单）
            cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
            success = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            conn.close()
            return False
    
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
            try:
                # 删除订单商品
                cursor.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
                
                # 删除订单（不再检查状态，允许删除所有状态的订单）
                cursor.execute("DELETE FROM orders WHERE id=?", (order_id,))
                
                if cursor.rowcount > 0:
                    success_count += 1
                else:
                    failed_ids.append(order_id)
            except Exception as e:
                # 如果删除过程中出现错误，记录失败的订单ID
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
            
            # 清理客户相关缓存
            self.clear_cache("customers")
            
            logger.info(f"Successfully added customer: {nickname}")
            return customer_id
        except sqlite3.Error as e:
            logger.error(f"Error adding customer {nickname}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"添加客户失败: {str(e)}")
    
    @cache_query(ttl=300, key_prefix="customers")
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
            
            # 清理面料相关缓存
            self.clear_cache("fabrics")
            
            logger.info(f"Successfully added fabric: {name}")
            return fabric_id
        except sqlite3.Error as e:
            logger.error(f"Error adding fabric {name}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"添加面料失败: {str(e)}")
    
    @cache_query(ttl=600, key_prefix="fabrics")
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
    
    def get_fabric_by_id(self, fabric_id: int) -> Optional[Dict]:
        """根据ID获取单个面料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fabrics WHERE id=?", (fabric_id,))
        row = cursor.fetchone()
        
        if row:
            fabric = {
                'id': row[0], 'name': row[1], 'material_type': row[2],
                'usage_type': row[3], 'created_at': row[4], 'updated_at': row[5]
            }
            conn.close()
            return fabric
        
        conn.close()
        return None
    
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
        
        # 清理库存相关缓存
        self.clear_cache("inventory")
        
        return item_id
    
    @cache_query(ttl=180, key_prefix="inventory")
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
        
        # 清理订单相关缓存
        self.clear_cache("orders_paginated")
        
        return order_id
    
    def add_order_item(self, order_id: int, item_type: str, quantity: int = 1, 
                      unit_price: float = 0, notes: str = "", **kwargs) -> int:
        """添加订单商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        inventory_id = kwargs.get('inventory_id')
        outer_fabric_id = kwargs.get('outer_fabric_id')
        inner_fabric_id = kwargs.get('inner_fabric_id')
        
        cursor.execute(
            """INSERT INTO order_items 
               (order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes)
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
            SELECT o.*, c.nickname as customer_name, c.phone_suffix as customer_phone_suffix
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC
        """)
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'customer_name': row[8], 'customer_phone_suffix': row[9]
            })
        conn.close()
        return orders
    
    @cache_query(ttl=60, key_prefix="orders_paginated")
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
            SELECT o.*, c.nickname as customer_name, c.phone_suffix as customer_phone_suffix
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
                'customer_name': row[8], 'customer_phone_suffix': row[9]
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
            SELECT o.*, c.nickname as customer_name, c.phone_suffix as customer_phone_suffix
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
                'customer_name': row[8], 'customer_phone_suffix': row[9]
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
            SELECT oi.*, i.product_name as inventory_name,
                   of.name as outer_fabric_name,
                   if.name as inner_fabric_name
            FROM order_items oi
            LEFT JOIN inventory i ON oi.inventory_id = i.id
            LEFT JOIN fabrics of ON oi.outer_fabric_id = of.id
            LEFT JOIN fabrics if ON oi.inner_fabric_id = if.id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id, oi.id
        """, order_ids)
        
        for row in cursor.fetchall():
            order_id = row[1]  # order_id is the second column
            if order_id in orders_dict:
                orders_dict[order_id]['items'].append({
                    'id': row[0], 'order_id': row[1], 'item_type': row[2],
                    'inventory_id': row[3], 'quantity': row[4], 'unit_price': row[5],
                    'notes': row[6], 'inventory_name': row[7],
                    'outer_fabric_name': row[8], 'inner_fabric_name': row[9]
                })
        
        conn.close()
        return orders_dict
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        """获取订单商品详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.*, i.product_name as inventory_name,
                   of.name as outer_fabric_name,
                   if.name as inner_fabric_name
            FROM order_items oi
            LEFT JOIN inventory i ON oi.inventory_id = i.id
            LEFT JOIN fabrics of ON oi.outer_fabric_id = of.id
            LEFT JOIN fabrics if ON oi.inner_fabric_id = if.id
            WHERE oi.order_id = ?
        """, (order_id,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0], 'order_id': row[1], 'item_type': row[2],
                'inventory_id': row[3], 'outer_fabric_id': row[4], 'inner_fabric_id': row[5],
                'quantity': row[6], 'unit_price': row[7], 'notes': row[8],
                'inventory_name': row[9], 'outer_fabric_name': row[10], 'inner_fabric_name': row[11]
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