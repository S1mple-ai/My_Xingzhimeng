"""
数据库优化模块
提供数据库查询优化、性能监控和缓存功能
"""

import sqlite3
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
from contextlib import contextmanager
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """查询性能监控器"""
    
    def __init__(self):
        self.query_stats = {}
        self.lock = threading.Lock()
    
    def record_query(self, query: str, execution_time: float, row_count: int = 0):
        """记录查询性能"""
        with self.lock:
            if query not in self.query_stats:
                self.query_stats[query] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0,
                    'total_rows': 0,
                    'last_execution': None
                }
            
            stats = self.query_stats[query]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['total_rows'] += row_count
            stats['last_execution'] = datetime.now().isoformat()
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        with self.lock:
            slow_queries = []
            for query, stats in self.query_stats.items():
                if stats['avg_time'] > threshold:
                    slow_queries.append({
                        'query': query[:100] + '...' if len(query) > 100 else query,
                        'avg_time': stats['avg_time'],
                        'max_time': stats['max_time'],
                        'count': stats['count']
                    })
            return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        with self.lock:
            if not self.query_stats:
                return {}
            
            total_queries = sum(stats['count'] for stats in self.query_stats.values())
            total_time = sum(stats['total_time'] for stats in self.query_stats.values())
            avg_time = total_time / total_queries if total_queries > 0 else 0
            
            return {
                'total_queries': total_queries,
                'unique_queries': len(self.query_stats),
                'total_time': total_time,
                'avg_time': avg_time,
                'slow_queries_count': len(self.get_slow_queries())
            }


class OptimizedQueries:
    """优化查询类"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.performance_monitor = QueryPerformanceMonitor()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_optimized_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """执行优化查询"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                
                execution_time = time.time() - start_time
                self.performance_monitor.record_query(query, execution_time, len(results))
                
                return results
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_monitor.record_query(query, execution_time, 0)
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_customers_optimized(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """优化的客户查询"""
        query = """
        SELECT id, name, phone, points, created_at, updated_at
        FROM customers 
        ORDER BY updated_at DESC 
        LIMIT ? OFFSET ?
        """
        return self.execute_optimized_query(query, (limit, offset))
    
    def get_orders_with_details_optimized(self, limit: int = 100) -> List[Dict[str, Any]]:
        """优化的订单详情查询"""
        query = """
        SELECT 
            o.id, o.customer_id, o.total_amount, o.status, o.created_at,
            c.name as customer_name, c.phone as customer_phone
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        ORDER BY o.created_at DESC
        LIMIT ?
        """
        return self.execute_optimized_query(query, (limit,))
    
    def get_inventory_summary_optimized(self) -> List[Dict[str, Any]]:
        """优化的库存摘要查询"""
        query = """
        SELECT 
            product_name,
            SUM(quantity) as total_quantity,
            AVG(price) as avg_price,
            COUNT(*) as variant_count
        FROM inventory
        GROUP BY product_name
        HAVING total_quantity > 0
        ORDER BY total_quantity DESC
        """
        return self.execute_optimized_query(query)
    
    def search_customers_optimized(self, search_term: str) -> List[Dict[str, Any]]:
        """优化的客户搜索"""
        query = """
        SELECT id, name, phone, points, created_at
        FROM customers 
        WHERE name LIKE ? OR phone LIKE ?
        ORDER BY name
        LIMIT 50
        """
        search_pattern = f"%{search_term}%"
        return self.execute_optimized_query(query, (search_pattern, search_pattern))


class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def create_indexes(self):
        """创建索引以提高查询性能"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_nickname ON customers(nickname)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone_suffix ON customers(phone_suffix)",
            "CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_product_name ON inventory(product_name)",
            "CREATE INDEX IF NOT EXISTS idx_fabrics_material_type ON fabrics(material_type)",
            "CREATE INDEX IF NOT EXISTS idx_fabrics_usage_type ON fabrics(usage_type)",
        ]
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for index_sql in indexes:
                    conn.execute(index_sql)
                conn.commit()
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def analyze_database(self):
        """分析数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("ANALYZE")
                conn.commit()
                logger.info("Database analysis completed")
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
    
    def vacuum_database(self):
        """清理数据库碎片"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuum completed")
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
    
    def get_table_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取表统计信息"""
        stats = {}
        tables = ['customers', 'orders', 'inventory', 'fabrics', 'bag_types']
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for table in tables:
                    try:
                        # 获取行数
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        
                        # 获取表大小（近似）
                        cursor = conn.execute(f"SELECT COUNT(*) * AVG(LENGTH(CAST(* AS TEXT))) FROM {table}")
                        size_estimate = cursor.fetchone()[0] or 0
                        
                        stats[table] = {
                            'row_count': row_count,
                            'size_estimate': size_estimate,
                            'last_updated': datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.warning(f"Failed to get stats for table {table}: {e}")
                        stats[table] = {'error': str(e)}
        
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
        
        return stats


def monitor_query_performance(func):
    """查询性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Query {func.__name__} executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query {func.__name__} failed after {execution_time:.4f}s: {e}")
            raise
    return wrapper


def initialize_database_optimization(db_path: str) -> Tuple[OptimizedQueries, Any]:
    """
    初始化数据库优化
    
    Args:
        db_path: 数据库路径
    
    Returns:
        优化查询实例和缓存指标实例
    """
    try:
        # 创建优化器并执行优化
        optimizer = DatabaseOptimizer(db_path)
        optimizer.create_indexes()
        optimizer.analyze_database()
        
        # 创建优化查询实例
        optimized_queries = OptimizedQueries(db_path)
        
        # 创建简单的缓存指标类
        class CacheMetrics:
            def __init__(self):
                self.hits = 0
                self.misses = 0
                self.total_requests = 0
            
            def record_hit(self):
                self.hits += 1
                self.total_requests += 1
            
            def record_miss(self):
                self.misses += 1
                self.total_requests += 1
            
            def get_hit_rate(self):
                return self.hits / self.total_requests if self.total_requests > 0 else 0
            
            def get_stats(self):
                return {
                    'hits': self.hits,
                    'misses': self.misses,
                    'total_requests': self.total_requests,
                    'hit_rate': self.get_hit_rate()
                }
        
        cache_metrics = CacheMetrics()
        
        logger.info("Database optimization initialized successfully")
        return optimized_queries, cache_metrics
        
    except Exception as e:
        logger.error(f"Failed to initialize database optimization: {e}")
        # 返回空实例以避免导入错误
        return None, None


# 示例使用
if __name__ == "__main__":
    # 测试数据库优化
    db_path = "test.db"
    optimized_queries, cache_metrics = initialize_database_optimization(db_path)
    
    if optimized_queries:
        # 获取性能统计
        stats = optimized_queries.performance_monitor.get_stats_summary()
        print(f"Performance stats: {stats}")
        
        # 获取慢查询
        slow_queries = optimized_queries.performance_monitor.get_slow_queries()
        print(f"Slow queries: {slow_queries}")
    
    if cache_metrics:
        print(f"Cache stats: {cache_metrics.get_stats()}")