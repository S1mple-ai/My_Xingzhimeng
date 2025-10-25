import sqlite3
import os
import logging
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from functools import wraps
import hashlib
import json

# 导入新的日志模块
from utils.logger import SystemLogger, log_exceptions, log_database_operation, log_performance
from utils.exception_handler import database_safe

# 初始化日志系统
logger = SystemLogger()

# 保持兼容性的传统logger
traditional_logger = logging.getLogger(__name__)

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
    @log_exceptions()
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
        logger.info(f"初始化数据库管理器: {db_path}", "database")
        self.init_database()
        logger.info(f"数据库管理器初始化完成: {db_path}", "database")
    
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
        
        # 为客户表添加软删除字段
        try:
            cursor.execute('ALTER TABLE customers ADD COLUMN deleted BOOLEAN DEFAULT FALSE')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        # 为面料表添加软删除字段
        try:
            cursor.execute('ALTER TABLE fabrics ADD COLUMN deleted BOOLEAN DEFAULT FALSE')
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
        
        # 为已存在的orders表添加points_awarded字段（如果不存在）
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN points_awarded BOOLEAN DEFAULT FALSE")
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        # 为库存表添加软删除字段
        try:
            cursor.execute('ALTER TABLE inventory ADD COLUMN deleted BOOLEAN DEFAULT FALSE')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        # 为订单表添加客户名称快照字段
        try:
            cursor.execute('ALTER TABLE orders ADD COLUMN customer_name_snapshot TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        # 积分历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                points_change INTEGER NOT NULL,
                points_before INTEGER NOT NULL,
                points_after INTEGER NOT NULL,
                change_type TEXT CHECK(change_type IN ('manual', 'order', 'formula')) NOT NULL,
                order_id INTEGER,
                reason TEXT,
                operator TEXT DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
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
        
        # 为订单商品表添加名称快照字段
        try:
            cursor.execute('ALTER TABLE order_items ADD COLUMN inventory_name_snapshot TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        try:
            cursor.execute('ALTER TABLE order_items ADD COLUMN outer_fabric_name_snapshot TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        try:
            cursor.execute('ALTER TABLE order_items ADD COLUMN inner_fabric_name_snapshot TEXT')
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass
        
        # 代加工人员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                phone TEXT,
                wechat TEXT,
                xiaohongshu TEXT,
                douyin TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 代加工订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processor_id INTEGER NOT NULL,
                fabric_id INTEGER,
                fabric_meters_main DECIMAL(10,2) DEFAULT 0,
                fabric_meters_lining DECIMAL(10,2) DEFAULT 0,
                product_name TEXT NOT NULL,
                product_quantity INTEGER DEFAULT 1,
                processing_days INTEGER DEFAULT 0,
                processing_cost DECIMAL(10,2) DEFAULT 0,
                selling_price DECIMAL(10,2) DEFAULT 0,
                status TEXT DEFAULT '待发货' CHECK(status IN ('待发货', '进行中', '已完成', '已取消')),
                start_date DATE,
                expected_finish_date DATE,
                actual_finish_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (processor_id) REFERENCES processors (id),
                FOREIGN KEY (fabric_id) REFERENCES fabrics (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== 代加工管理相关方法 ====================
    
    def add_processor(self, nickname: str, phone: str = None, wechat: str = None, 
                     xiaohongshu: str = None, douyin: str = None, notes: str = None):
        """添加代加工人员"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processors (nickname, phone, wechat, xiaohongshu, douyin, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nickname, phone, wechat, xiaohongshu, douyin, notes))
            processor_id = cursor.lastrowid
            conn.commit()
            conn.close()
            self.clear_cache("processors")
            logger.info(f"添加代加工人员成功: {nickname}")
            return processor_id
        except Exception as e:
            logger.error(f"添加代加工人员失败: {e}")
            raise e
    
    def get_processors(self) -> List[Dict]:
        """获取所有代加工人员"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processors ORDER BY created_at DESC")
        processors = []
        for row in cursor.fetchall():
            processors.append({
                'id': row[0], 'nickname': row[1], 'phone': row[2], 'wechat': row[3],
                'xiaohongshu': row[4], 'douyin': row[5], 'notes': row[6],
                'created_at': row[7], 'updated_at': row[8]
            })
        conn.close()
        return processors
    
    def get_processor_by_id(self, processor_id: int):
        """根据ID获取代加工人员"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processors WHERE id=?", (processor_id,))
        row = cursor.fetchone()
        
        if row:
            processor = {
                'id': row[0], 'nickname': row[1], 'phone': row[2], 'wechat': row[3],
                'xiaohongshu': row[4], 'douyin': row[5], 'notes': row[6],
                'created_at': row[7], 'updated_at': row[8]
            }
            conn.close()
            return processor
        
        conn.close()
        return None
    
    def update_processor(self, processor_id: int, nickname: str, phone: str = None, 
                        wechat: str = None, xiaohongshu: str = None, douyin: str = None, notes: str = None):
        """更新代加工人员信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE processors 
                SET nickname=?, phone=?, wechat=?, xiaohongshu=?, douyin=?, notes=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (nickname, phone, wechat, xiaohongshu, douyin, notes, processor_id))
            conn.commit()
            conn.close()
            self.clear_cache("processors")
            logger.info(f"更新代加工人员成功: {nickname}")
        except Exception as e:
            logger.error(f"更新代加工人员失败: {e}")
            raise e
    
    def delete_processor(self, processor_id: int, force_delete: bool = True):
        """删除代加工人员
        
        Args:
            processor_id: 处理器ID
            force_delete: 是否强制删除（忽略关联订单检查），默认为True
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 如果不是强制删除，检查是否有关联的代加工订单
            if not force_delete:
                cursor.execute("SELECT COUNT(*) FROM processing_orders WHERE processor_id=?", (processor_id,))
                order_count = cursor.fetchone()[0]
                
                if order_count > 0:
                    raise Exception(f"无法删除：该代加工人员还有 {order_count} 个关联订单")
            
            # 直接删除处理器（强制删除模式下忽略关联订单）
            cursor.execute("DELETE FROM processors WHERE id=?", (processor_id,))
            conn.commit()
            conn.close()
            self.clear_cache("processors")
            logger.info(f"删除代加工人员成功: ID {processor_id} (force_delete={force_delete})")
        except Exception as e:
            logger.error(f"删除代加工人员失败: {e}")
            raise e
    
    def add_processing_order(self, processor_id: int, fabric_id: int = None, 
                           fabric_meters_main: float = 0, fabric_meters_lining: float = 0,
                           product_name: str = "", product_quantity: int = 1, 
                           processing_days: int = 0, processing_cost: float = 0,
                           selling_price: float = 0, start_date: str = None,
                           expected_finish_date: str = None, notes: str = None):
        """添加代加工订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_orders 
                (processor_id, fabric_id, fabric_meters_main, fabric_meters_lining,
                 product_name, product_quantity, processing_days, processing_cost,
                 selling_price, start_date, expected_finish_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (processor_id, fabric_id, fabric_meters_main, fabric_meters_lining,
                  product_name, product_quantity, processing_days, processing_cost,
                  selling_price, start_date, expected_finish_date, notes))
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            self.clear_cache("processing_orders")
            logger.info(f"添加代加工订单成功: {product_name}")
            return order_id
        except Exception as e:
            logger.error(f"添加代加工订单失败: {e}")
            raise e
    
    def get_processing_orders(self) -> List[Dict]:
        """获取所有代加工订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.*, p.nickname as processor_name, f.name as fabric_name
            FROM processing_orders po
            LEFT JOIN processors p ON po.processor_id = p.id
            LEFT JOIN fabrics f ON po.fabric_id = f.id
            ORDER BY po.created_at DESC
        """)
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0], 'processor_id': row[1], 'fabric_id': row[2],
                'fabric_meters_main': row[3], 'fabric_meters_lining': row[4],
                'product_name': row[5], 'product_quantity': row[6],
                'processing_days': row[7], 'processing_cost': row[8],
                'selling_price': row[9], 'status': row[10],
                'start_date': row[11], 'expected_finish_date': row[12],
                'actual_finish_date': row[13], 'notes': row[14],
                'created_at': row[15], 'updated_at': row[16],
                'processor_name': row[17], 'fabric_name': row[18]
            })
        conn.close()
        return orders
    
    def get_processing_order_by_id(self, order_id: int):
        """根据ID获取代加工订单"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT po.*, p.nickname as processor_name, f.name as fabric_name
            FROM processing_orders po
            LEFT JOIN processors p ON po.processor_id = p.id
            LEFT JOIN fabrics f ON po.fabric_id = f.id
            WHERE po.id=?
        """, (order_id,))
        row = cursor.fetchone()
        
        if row:
            order = {
                'id': row[0], 'processor_id': row[1], 'fabric_id': row[2],
                'fabric_meters_main': row[3], 'fabric_meters_lining': row[4],
                'product_name': row[5], 'product_quantity': row[6],
                'processing_days': row[7], 'processing_cost': row[8],
                'selling_price': row[9], 'status': row[10],
                'start_date': row[11], 'expected_finish_date': row[12],
                'actual_finish_date': row[13], 'notes': row[14],
                'created_at': row[15], 'updated_at': row[16],
                'processor_name': row[17], 'fabric_name': row[18]
            }
            conn.close()
            return order
        
        conn.close()
        return None
    
    def update_processing_order(self, order_id: int, processor_id: int, fabric_id: int = None,
                              fabric_meters_main: float = 0, fabric_meters_lining: float = 0,
                              product_name: str = "", product_quantity: int = 1,
                              processing_days: int = 0, processing_cost: float = 0,
                              selling_price: float = 0, status: str = "待发货",
                              start_date: str = None, expected_finish_date: str = None,
                              actual_finish_date: str = None, notes: str = None):
        """更新代加工订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE processing_orders 
                SET processor_id=?, fabric_id=?, fabric_meters_main=?, fabric_meters_lining=?,
                    product_name=?, product_quantity=?, processing_days=?, processing_cost=?,
                    selling_price=?, status=?, start_date=?, expected_finish_date=?,
                    actual_finish_date=?, notes=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (processor_id, fabric_id, fabric_meters_main, fabric_meters_lining,
                  product_name, product_quantity, processing_days, processing_cost,
                  selling_price, status, start_date, expected_finish_date,
                  actual_finish_date, notes, order_id))
            conn.commit()
            conn.close()
            self.clear_cache("processing_orders")
            logger.info(f"更新代加工订单成功: {product_name}")
        except Exception as e:
            logger.error(f"更新代加工订单失败: {e}")
            raise e
    
    def delete_processing_order(self, order_id: int):
        """删除代加工订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM processing_orders WHERE id=?", (order_id,))
            conn.commit()
            conn.close()
            self.clear_cache("processing_orders")
            logger.info(f"删除代加工订单成功: ID {order_id}")
        except Exception as e:
            logger.error(f"删除代加工订单失败: {e}")
            raise e
    
    def get_processor_statistics(self, processor_id: int):
        """获取代加工人员统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取订单统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = '已完成' THEN 1 ELSE 0 END) as completed_orders,
                SUM(CASE WHEN status = '进行中' THEN 1 ELSE 0 END) as ongoing_orders,
                SUM(processing_cost) as total_cost,
                SUM(selling_price) as total_revenue,
                SUM(product_quantity) as total_products
            FROM processing_orders 
            WHERE processor_id = ?
        """, (processor_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats:
            return {
                'total_orders': stats[0] or 0,
                'completed_orders': stats[1] or 0,
                'ongoing_orders': stats[2] or 0,
                'total_cost': stats[3] or 0,
                'total_revenue': stats[4] or 0,
                'total_products': stats[5] or 0,
                'profit': (stats[4] or 0) - (stats[3] or 0)
            }
        
        return {
            'total_orders': 0, 'completed_orders': 0, 'ongoing_orders': 0,
            'total_cost': 0, 'total_revenue': 0, 'total_products': 0, 'profit': 0
        }
    
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
    

    
    @cache_query(ttl=300, key_prefix="unified_dashboard")
    def get_unified_dashboard_data(self, time_period: str):
        """获取统一时间段的仪表盘数据"""
        try:
            # 根据时间段计算日期范围
            date_filter = self._get_date_filter(time_period)
            
            # 获取汇总数据
            summary = self._get_summary_data(date_filter)
            
            # 获取每日销售数据
            daily_sales = self._get_daily_sales_data(date_filter)
            
            # 获取面料使用数据
            fabric_usage = self._get_fabric_usage_data(date_filter)
            
            # 获取商品销售数据
            product_sales = self._get_product_sales_data(date_filter)
            
            # 获取客户活跃度数据
            customer_activity = self._get_customer_activity_data(date_filter)
            
            return {
                'summary': summary,
                'daily_sales': daily_sales,
                'fabric_usage': fabric_usage,
                'product_sales': product_sales,
                'customer_activity': customer_activity
            }
            
        except Exception as e:
            logger.error(f"获取统一仪表盘数据时出错: {e}")
            return {
                'summary': {'total_orders': 0, 'total_amount': 0, 'active_customers': 0},
                'daily_sales': [],
                'fabric_usage': [],
                'product_sales': [],
                'customer_activity': [],
                'order_status': []
            }
    
    def _get_date_filter(self, time_period: str) -> str:
        """根据时间段获取日期过滤条件"""
        if time_period == "全部时间":
            return ""
        elif time_period == "近一周":
            return "AND DATE(created_at) >= DATE('now', '-7 days')"
        elif time_period == "近一月":
            return "AND DATE(created_at) >= DATE('now', '-30 days')"
        elif time_period == "近一季度":
            return "AND DATE(created_at) >= DATE('now', '-90 days')"
        elif time_period == "近一年":
            return "AND DATE(created_at) >= DATE('now', '-365 days')"
        else:
            return ""
    
    def _get_summary_data(self, date_filter: str) -> Dict:
        """获取汇总数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 订单总数和销售总额
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_amount), 0) as total_amount
                FROM orders 
                WHERE 1=1 {date_filter}
            """)
            result = cursor.fetchone()
            
            # 活跃客户数
            cursor.execute(f"""
                SELECT COUNT(DISTINCT customer_id) as active_customers
                FROM orders 
                WHERE 1=1 {date_filter}
            """)
            customer_result = cursor.fetchone()
            
            conn.close()
            return {
                'total_orders': result[0],
                'total_amount': float(result[1]) if result[1] else 0,
                'active_customers': customer_result[0]
            }
            
        except Exception as e:
            logger.error(f"获取汇总数据时出错: {e}")
            return {'total_orders': 0, 'total_amount': 0, 'active_customers': 0}
    
    def _get_daily_sales_data(self, date_filter: str) -> List[Dict]:
        """获取每日销售数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as order_count,
                    COALESCE(SUM(total_amount), 0) as amount
                FROM orders 
                WHERE 1=1 {date_filter}
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            results = cursor.fetchall()
            
            daily_sales = []
            for row in results:
                daily_sales.append({
                    'date': row[0],
                    'order_count': row[1],
                    'amount': float(row[2]) if row[2] else 0
                })
            
            conn.close()
            return daily_sales
            
        except Exception as e:
            logger.error(f"获取每日销售数据时出错: {e}")
            return []
    
    def _get_fabric_usage_data(self, date_filter: str) -> List[Dict]:
        """获取面料使用数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 表布使用情况
            cursor.execute(f"""
                SELECT 
                    f.name as fabric_name,
                    f.usage_type,
                    COUNT(oi.outer_fabric_id) as usage_count
                FROM fabrics f
                LEFT JOIN order_items oi ON f.id = oi.outer_fabric_id
                LEFT JOIN orders o ON oi.order_id = o.id
                WHERE f.usage_type = '表布' AND oi.id IS NOT NULL {date_filter.replace('created_at', 'o.created_at') if date_filter else ''}
                GROUP BY f.id, f.name, f.usage_type
                ORDER BY usage_count DESC
            """)
            outer_results = cursor.fetchall()
            
            # 里布使用情况
            cursor.execute(f"""
                SELECT 
                    f.name as fabric_name,
                    f.usage_type,
                    COUNT(oi.inner_fabric_id) as usage_count
                FROM fabrics f
                LEFT JOIN order_items oi ON f.id = oi.inner_fabric_id
                LEFT JOIN orders o ON oi.order_id = o.id
                WHERE f.usage_type = '里布' AND oi.id IS NOT NULL {date_filter.replace('created_at', 'o.created_at') if date_filter else ''}
                GROUP BY f.id, f.name, f.usage_type
                ORDER BY usage_count DESC
            """)
            inner_results = cursor.fetchall()
            
            fabric_usage = []
            for row in outer_results:
                fabric_usage.append({
                    'fabric_name': row[0],
                    'usage_type': row[1],
                    'usage_count': row[2]
                })
            
            for row in inner_results:
                fabric_usage.append({
                    'fabric_name': row[0],
                    'usage_type': row[1],
                    'usage_count': row[2]
                })
            
            conn.close()
            return fabric_usage
            
        except Exception as e:
            logger.error(f"获取面料使用数据时出错: {e}")
            return []
    
    def _get_product_sales_data(self, date_filter: str) -> List[Dict]:
        """获取商品销售数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 现货商品销售
            cursor.execute(f"""
                SELECT 
                    i.product_name,
                    SUM(oi.quantity) as quantity,
                    SUM(oi.quantity * oi.unit_price) as total_amount
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                LEFT JOIN inventory i ON oi.inventory_id = i.id
                WHERE oi.item_type = '现货' AND i.product_name IS NOT NULL {date_filter.replace('created_at', 'o.created_at') if date_filter else ''}
                GROUP BY i.product_name
                ORDER BY quantity DESC
            """)
            inventory_results = cursor.fetchall()
            
            # 定制商品销售
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
                WHERE oi.item_type = '定制' {date_filter.replace('created_at', 'o.created_at') if date_filter else ''}
                GROUP BY of.name, if.name
                ORDER BY quantity DESC
            """)
            custom_results = cursor.fetchall()
            
            product_sales = []
            for row in inventory_results:
                product_sales.append({
                    'product_name': row[0],
                    'quantity': row[1],
                    'total_amount': float(row[2]) if row[2] else 0
                })
            
            for row in custom_results:
                product_sales.append({
                    'product_name': row[0],
                    'quantity': row[1],
                    'total_amount': float(row[2]) if row[2] else 0
                })
            
            conn.close()
            return product_sales
            
        except Exception as e:
            logger.error(f"获取商品销售数据时出错: {e}")
            return []
    
    def _get_customer_activity_data(self, date_filter: str) -> List[Dict]:
        """获取客户活跃度数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    c.nickname,
                    COUNT(o.id) as order_count,
                    COALESCE(SUM(o.total_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                WHERE o.id IS NOT NULL {date_filter.replace('created_at', 'o.created_at') if date_filter else ''}
                GROUP BY c.id, c.nickname
                ORDER BY order_count DESC
            """)
            results = cursor.fetchall()
            
            customer_activity = []
            for row in results:
                customer_activity.append({
                    'nickname': row[0],
                    'order_count': row[1],
                    'total_spent': float(row[2]) if row[2] else 0
                })
            
            conn.close()
            return customer_activity
            
        except Exception as e:
            logger.error(f"获取客户活跃度数据时出错: {e}")
            return []
    

    
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
    
    def update_order(self, order_id: int, customer_id: int = None, notes: str = None, 
                    image_path: str = None, status: str = None, points_awarded: bool = None) -> bool:
        """更新订单信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 构建动态更新语句
        update_fields = []
        update_values = []
        
        if customer_id is not None:
            update_fields.append("customer_id=?")
            update_values.append(customer_id)
        if notes is not None:
            update_fields.append("notes=?")
            update_values.append(notes)
        if image_path is not None:
            update_fields.append("image_path=?")
            update_values.append(image_path)
        if status is not None:
            update_fields.append("status=?")
            update_values.append(status)
        if points_awarded is not None:
            update_fields.append("points_awarded=?")
            update_values.append(points_awarded)
        
        if not update_fields:
            return False  # 没有字段需要更新
        
        # 添加updated_at字段
        update_fields.append("updated_at=CURRENT_TIMESTAMP")
        update_values.append(order_id)
        
        sql = f"UPDATE orders SET {', '.join(update_fields)} WHERE id=?"
        cursor.execute(sql, update_values)
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
        cursor.execute("SELECT * FROM customers WHERE deleted = FALSE OR deleted IS NULL ORDER BY created_at DESC")
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
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"更新客户信息失败: {str(e)}")
    
    @log_exceptions()
    @log_database_operation("delete", "customers")
    @log_performance()
    def delete_customer(self, customer_id: int, force_delete: bool = True):
        """删除客户
        
        Args:
            customer_id: 客户ID
            force_delete: 是否强制删除（忽略关联订单检查），默认为True
        """
        try:
            logger.info(f"开始删除客户: {customer_id}, 强制删除: {force_delete}", "database")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查客户是否存在
            cursor.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
            if not cursor.fetchone():
                error_msg = f"客户ID {customer_id} 不存在"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 如果不是强制删除，检查是否有关联订单
            if not force_delete:
                cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id=?", (customer_id,))
                order_count = cursor.fetchone()[0]
                if order_count > 0:
                    error_msg = f"无法删除客户，该客户有 {order_count} 个关联订单"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            
            # 软删除客户（标记为已删除而不是物理删除）
            cursor.execute("UPDATE customers SET deleted = TRUE WHERE id=?", (customer_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"成功删除客户: {customer_id}, 强制删除: {force_delete}", "database")
            traditional_logger.info(f"Successfully deleted customer ID: {customer_id} (force_delete={force_delete})")
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
    
    def add_points_history(self, customer_id: int, points_change: int, points_before: int, 
                          points_after: int, change_type: str, order_id: int = None, 
                          reason: str = "", operator: str = "system"):
        """添加积分历史记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO points_history 
                (customer_id, points_change, points_before, points_after, change_type, order_id, reason, operator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, points_change, points_before, points_after, change_type, order_id, reason, operator))
            history_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Added points history for customer {customer_id}: {points_change} points")
            return history_id
        except sqlite3.Error as e:
            logger.error(f"Error adding points history for customer {customer_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"添加积分历史记录失败: {str(e)}")
    
    def get_customer_points_history(self, customer_id: int) -> List[Dict]:
        """获取客户积分历史记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ph.*, o.total_amount as order_amount
                FROM points_history ph
                LEFT JOIN orders o ON ph.order_id = o.id
                WHERE ph.customer_id = ?
                ORDER BY ph.created_at DESC
            ''', (customer_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'customer_id': row[1],
                    'points_change': row[2],
                    'points_before': row[3],
                    'points_after': row[4],
                    'change_type': row[5],
                    'order_id': row[6],
                    'reason': row[7],
                    'operator': row[8],
                    'created_at': row[9],
                    'order_amount': row[10] if row[10] else None
                })
            conn.close()
            return history
        except sqlite3.Error as e:
            logger.error(f"Error getting points history for customer {customer_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return []
    
    def update_customer_points_with_history(self, customer_id: int, points_change: int, 
                                          change_type: str, order_id: int = None, 
                                          reason: str = "", operator: str = "system"):
        """更新客户积分并记录历史"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 获取当前积分
            cursor.execute("SELECT points FROM customers WHERE id = ?", (customer_id,))
            result = cursor.fetchone()
            if not result:
                raise Exception(f"客户ID {customer_id} 不存在")
            
            points_before = result[0]
            points_after = points_before + points_change
            
            # 确保积分不为负数
            if points_after < 0:
                raise Exception(f"积分不能为负数，当前积分: {points_before}，尝试变化: {points_change}")
            
            # 更新客户积分
            cursor.execute(
                "UPDATE customers SET points = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (points_after, customer_id)
            )
            
            # 添加历史记录
            cursor.execute('''
                INSERT INTO points_history 
                (customer_id, points_change, points_before, points_after, change_type, order_id, reason, operator)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, points_change, points_before, points_after, change_type, order_id, reason, operator))
            
            conn.commit()
            conn.close()
            
            # 清理客户相关缓存
            self.clear_cache("customers")
            
            logger.info(f"Updated customer {customer_id} points: {points_before} -> {points_after} ({points_change:+d})")
            return points_after
            
        except sqlite3.Error as e:
            logger.error(f"Error updating customer points with history: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            raise Exception(f"更新客户积分失败: {str(e)}")
    
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
            cursor.execute("SELECT * FROM fabrics WHERE usage_type=? AND (deleted = FALSE OR deleted IS NULL) ORDER BY created_at DESC", (usage_type,))
        else:
            cursor.execute("SELECT * FROM fabrics WHERE deleted = FALSE OR deleted IS NULL ORDER BY created_at DESC")
        
        fabrics = []
        for row in cursor.fetchall():
            fabrics.append({
                'id': row[0], 'name': row[1], 'material_type': row[2],
                'usage_type': row[3], 'created_at': row[4], 'updated_at': row[5], 'image_path': row[6]
            })
        conn.close()
        return fabrics
    
    def get_fabric_by_id(self, fabric_id: int) -> Optional[Dict]:
        """根据ID获取单个面料"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fabrics WHERE id=? AND (deleted = FALSE OR deleted IS NULL)", (fabric_id,))
        row = cursor.fetchone()
        
        if row:
            fabric = {
                'id': row[0], 'name': row[1], 'material_type': row[2],
                'usage_type': row[3], 'created_at': row[4], 'updated_at': row[5], 'image_path': row[6]
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
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating fabric {fabric_id}: {e}")
            if 'conn' in locals():
                conn.close()
            raise Exception(f"更新面料失败: {str(e)}")
    
    def delete_fabric(self, fabric_id: int, force_delete: bool = True):
        """删除面料
        
        Args:
            fabric_id: 面料ID
            force_delete: 是否强制删除（忽略关联订单检查），默认为True
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 检查面料是否存在
            cursor.execute("SELECT id FROM fabrics WHERE id=?", (fabric_id,))
            if not cursor.fetchone():
                raise Exception(f"面料ID {fabric_id} 不存在")
            
            # 如果不是强制删除，检查是否有关联的订单项记录（作为外布或内布）
            if not force_delete:
                cursor.execute("""
                    SELECT COUNT(*) FROM order_items 
                    WHERE outer_fabric_id=? OR inner_fabric_id=?
                """, (fabric_id, fabric_id))
                order_items_count = cursor.fetchone()[0]
                if order_items_count > 0:
                    raise Exception(f"无法删除面料，该面料有 {order_items_count} 个关联订单记录")
            
            # 软删除面料（标记为已删除而不是物理删除）
            cursor.execute("UPDATE fabrics SET deleted = TRUE WHERE id=?", (fabric_id,))
            conn.commit()
            conn.close()
            logger.info(f"Successfully deleted fabric ID: {fabric_id} (force_delete={force_delete})")
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
        cursor.execute("SELECT * FROM inventory WHERE deleted = FALSE OR deleted IS NULL ORDER BY created_at DESC")
        
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
    
    def delete_inventory_item(self, item_id: int, force_delete: bool = True) -> bool:
        """删除库存商品
        
        Args:
            item_id: 商品ID
            force_delete: 是否强制删除（忽略关联订单检查）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 如果不是强制删除，检查是否有订单使用此商品
        if not force_delete:
            cursor.execute("SELECT COUNT(*) FROM order_items WHERE inventory_id=?", (item_id,))
            order_count = cursor.fetchone()[0]
            
            if order_count > 0:
                conn.close()
                return False  # 有订单使用，不能删除
        
        cursor.execute("UPDATE inventory SET deleted = TRUE WHERE id=?", (item_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        # 清理库存相关缓存
        if success:
            self.clear_cache("inventory")
        
        return success
    
    def get_inventory_item_by_id(self, item_id: int) -> Optional[Dict]:
        """根据ID获取库存商品"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE id=? AND (deleted = FALSE OR deleted IS NULL)", (item_id,))
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
        
        # 获取客户名称快照（只获取未删除的客户）
        cursor.execute("SELECT nickname FROM customers WHERE id = ? AND (deleted = FALSE OR deleted IS NULL)", (customer_id,))
        customer_result = cursor.fetchone()
        customer_name_snapshot = customer_result[0] if customer_result else None
        
        cursor.execute(
            "INSERT INTO orders (customer_id, notes, image_path, customer_name_snapshot) VALUES (?, ?, ?, ?)",
            (customer_id, notes, image_path, customer_name_snapshot)
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
        
        # 获取名称快照
        inventory_name_snapshot = None
        outer_fabric_name_snapshot = None
        inner_fabric_name_snapshot = None
        
        if inventory_id:
            cursor.execute("SELECT product_name FROM inventory WHERE id = ?", (inventory_id,))
            inventory_result = cursor.fetchone()
            inventory_name_snapshot = inventory_result[0] if inventory_result else None
            
        if outer_fabric_id:
            cursor.execute("SELECT name FROM fabrics WHERE id = ?", (outer_fabric_id,))
            outer_fabric_result = cursor.fetchone()
            outer_fabric_name_snapshot = outer_fabric_result[0] if outer_fabric_result else None
            
        if inner_fabric_id:
            cursor.execute("SELECT name FROM fabrics WHERE id = ?", (inner_fabric_id,))
            inner_fabric_result = cursor.fetchone()
            inner_fabric_name_snapshot = inner_fabric_result[0] if inner_fabric_result else None
        
        cursor.execute(
            """INSERT INTO order_items 
               (order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes,
                inventory_name_snapshot, outer_fabric_name_snapshot, inner_fabric_name_snapshot) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, item_type, inventory_id, outer_fabric_id, inner_fabric_id, quantity, unit_price, notes,
             inventory_name_snapshot, outer_fabric_name_snapshot, inner_fabric_name_snapshot)
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
            SELECT o.id, o.customer_id, o.total_amount, o.status, o.notes, o.image_path, 
                   o.created_at, o.updated_at, o.points_awarded, o.customer_name_snapshot,
                   c.nickname as customer_name, c.phone_suffix as customer_phone_suffix
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id AND (c.deleted = FALSE OR c.deleted IS NULL)
            ORDER BY o.created_at DESC
        """)
        
        orders = []
        for row in cursor.fetchall():
            # 优先使用快照名称，如果没有快照则使用当前名称
            customer_display_name = row[9] if row[9] else row[10]  # customer_name_snapshot 优先于 customer_name
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'points_awarded': row[8], 'customer_name_snapshot': row[9],
                'customer_name': customer_display_name, 'customer_phone_suffix': row[11]
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
            SELECT o.id, o.customer_id, o.total_amount, o.status, o.notes, o.image_path, 
                   o.created_at, o.updated_at, o.points_awarded, o.customer_name_snapshot,
                   c.nickname as customer_name, c.phone_suffix as customer_phone_suffix
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [page_size, offset])
        
        orders = []
        for row in cursor.fetchall():
            # 优先使用快照名称，如果没有快照则使用当前名称
            customer_display_name = row[9] if row[9] else row[10]  # customer_name_snapshot 优先于 customer_name
            orders.append({
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 'created_at': row[6], 'updated_at': row[7],
                'points_awarded': row[8], 'customer_name_snapshot': row[9],
                'customer_name': customer_display_name, 'customer_phone_suffix': row[11]
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
            SELECT o.id, o.customer_id, o.total_amount, o.status, o.notes, o.image_path, 
                   o.created_at, o.updated_at, o.points_awarded, o.customer_name_snapshot,
                   c.nickname as customer_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id IN ({placeholders})
        """, order_ids)
        
        orders_dict = {}
        for row in cursor.fetchall():
            # 优先使用快照名称，如果没有快照则使用当前名称
            customer_display_name = row[9] if row[9] else row[10]  # customer_name_snapshot 优先于 customer_name
            orders_dict[row[0]] = {
                'id': row[0], 'customer_id': row[1], 'total_amount': row[2],
                'status': row[3], 'notes': row[4], 'image_path': row[5], 
                'created_at': row[6], 'updated_at': row[7], 'points_awarded': row[8],
                'customer_name_snapshot': row[9], 'customer_name': customer_display_name,
                'items': []
            }
        
        # 获取所有订单的商品信息
        cursor.execute(f"""
            SELECT oi.id, oi.order_id, oi.item_type, oi.inventory_id, oi.outer_fabric_id, oi.inner_fabric_id,
                   oi.quantity, oi.unit_price, oi.notes, 
                   oi.inventory_name_snapshot, oi.outer_fabric_name_snapshot, oi.inner_fabric_name_snapshot,
                   i.product_name as inventory_name,
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
                # 优先使用快照名称，如果没有快照则使用当前名称
                inventory_display_name = row[9] if row[9] else row[12]  # inventory_name_snapshot 优先于 inventory_name
                outer_fabric_display_name = row[10] if row[10] else row[13]  # outer_fabric_name_snapshot 优先于 outer_fabric_name
                inner_fabric_display_name = row[11] if row[11] else row[14]  # inner_fabric_name_snapshot 优先于 inner_fabric_name
                
                orders_dict[order_id]['items'].append({
                    'id': row[0], 'order_id': row[1], 'item_type': row[2],
                    'inventory_id': row[3], 'outer_fabric_id': row[4], 'inner_fabric_id': row[5],
                    'quantity': row[6], 'unit_price': row[7], 'notes': row[8],
                    'inventory_name_snapshot': row[9], 'outer_fabric_name_snapshot': row[10], 'inner_fabric_name_snapshot': row[11],
                    'inventory_name': inventory_display_name, 'outer_fabric_name': outer_fabric_display_name, 'inner_fabric_name': inner_fabric_display_name
                })
        
        conn.close()
        return orders_dict
    
    def get_order_items(self, order_id: int) -> List[Dict]:
        """获取订单商品详情"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.id, oi.order_id, oi.item_type, oi.inventory_id, oi.outer_fabric_id, oi.inner_fabric_id,
                   oi.quantity, oi.unit_price, oi.notes, 
                   oi.inventory_name_snapshot, oi.outer_fabric_name_snapshot, oi.inner_fabric_name_snapshot,
                   i.product_name as inventory_name,
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
            # 优先使用快照名称，如果没有快照则使用当前名称
            inventory_display_name = row[9] if row[9] else row[12]  # inventory_name_snapshot 优先于 inventory_name
            outer_fabric_display_name = row[10] if row[10] else row[13]  # outer_fabric_name_snapshot 优先于 outer_fabric_name
            inner_fabric_display_name = row[11] if row[11] else row[14]  # inner_fabric_name_snapshot 优先于 inner_fabric_name
            
            items.append({
                'id': row[0], 'order_id': row[1], 'item_type': row[2],
                'inventory_id': row[3], 'outer_fabric_id': row[4], 'inner_fabric_id': row[5],
                'quantity': row[6], 'unit_price': row[7], 'notes': row[8],
                'inventory_name_snapshot': row[9], 'outer_fabric_name_snapshot': row[10], 'inner_fabric_name_snapshot': row[11],
                'inventory_name': inventory_display_name, 'outer_fabric_name': outer_fabric_display_name, 'inner_fabric_name': inner_fabric_display_name
            })
        conn.close()
        return items
    
    def complete_order_payment(self, order_id: int):
        """完成订单支付"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 更新订单状态为已完成
        cursor.execute(
            "UPDATE orders SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (order_id,)
        )
        
        conn.commit()
        conn.close()