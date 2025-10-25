"""
数据库性能增强器
提供高级索引优化、批量操作和查询性能监控
"""

import sqlite3
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

# 导入日志系统
from utils.logger import SystemLogger, log_performance, log_database_operation

logger = SystemLogger()


class DatabasePerformanceEnhancer:
    """数据库性能增强器"""
    
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
        self.query_stats = {}
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @log_performance
    def create_advanced_indexes(self) -> Dict[str, bool]:
        """创建高级复合索引"""
        advanced_indexes = {
            # 订单相关复合索引
            "idx_orders_customer_status": "CREATE INDEX IF NOT EXISTS idx_orders_customer_status ON orders(customer_id, status)",
            "idx_orders_status_date": "CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, created_at)",
            "idx_orders_customer_date": "CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, created_at)",
            "idx_orders_amount_date": "CREATE INDEX IF NOT EXISTS idx_orders_amount_date ON orders(total_amount, created_at)",
            
            # 订单项复合索引
            "idx_order_items_order_type": "CREATE INDEX IF NOT EXISTS idx_order_items_order_type ON order_items(order_id, item_type)",
            "idx_order_items_inventory_type": "CREATE INDEX IF NOT EXISTS idx_order_items_inventory_type ON order_items(inventory_id, item_type)",
            "idx_order_items_fabric_combo": "CREATE INDEX IF NOT EXISTS idx_order_items_fabric_combo ON order_items(outer_fabric_id, inner_fabric_id)",
            
            # 客户相关复合索引
            "idx_customers_points_date": "CREATE INDEX IF NOT EXISTS idx_customers_points_date ON customers(points, created_at)",
            "idx_customers_phone_nickname": "CREATE INDEX IF NOT EXISTS idx_customers_phone_nickname ON customers(phone_suffix, nickname)",
            
            # 库存复合索引
            "idx_inventory_quantity_name": "CREATE INDEX IF NOT EXISTS idx_inventory_quantity_name ON inventory(quantity, product_name)",
            "idx_inventory_price_quantity": "CREATE INDEX IF NOT EXISTS idx_inventory_price_quantity ON inventory(price, quantity)",
            
            # 面料复合索引
            "idx_fabrics_material_usage": "CREATE INDEX IF NOT EXISTS idx_fabrics_material_usage ON fabrics(material_type, usage_type)",
            "idx_fabrics_usage_name": "CREATE INDEX IF NOT EXISTS idx_fabrics_usage_name ON fabrics(usage_type, name)",
            
            # 积分历史索引
            "idx_points_customer_date": "CREATE INDEX IF NOT EXISTS idx_points_customer_date ON points_history(customer_id, created_at)",
            "idx_points_type_date": "CREATE INDEX IF NOT EXISTS idx_points_type_date ON points_history(change_type, created_at)",
            
            # 代加工相关索引
            "idx_processing_processor_status": "CREATE INDEX IF NOT EXISTS idx_processing_processor_status ON processing_orders(processor_id, status)",
            "idx_processing_status_date": "CREATE INDEX IF NOT EXISTS idx_processing_status_date ON processing_orders(status, created_at)",
        }
        
        results = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for index_name, index_sql in advanced_indexes.items():
                try:
                    start_time = time.time()
                    cursor.execute(index_sql)
                    execution_time = time.time() - start_time
                    
                    results[index_name] = True
                    logger.info(f"创建索引 {index_name} 成功，耗时: {execution_time:.3f}s")
                    
                except Exception as e:
                    results[index_name] = False
                    logger.error(f"创建索引 {index_name} 失败: {e}")
            
            conn.commit()
        
        return results
    
    @log_performance
    def analyze_query_performance(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        """分析查询性能"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取查询计划
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query, params)
            query_plan = cursor.fetchall()
            
            # 执行查询并测量时间
            start_time = time.time()
            cursor.execute(query, params)
            results = cursor.fetchall()
            execution_time = time.time() - start_time
            
            # 分析结果
            analysis = {
                'query': query,
                'execution_time': execution_time,
                'result_count': len(results),
                'query_plan': [dict(row) for row in query_plan],
                'uses_index': any('USING INDEX' in str(row) for row in query_plan),
                'scan_type': 'INDEX' if any('USING INDEX' in str(row) for row in query_plan) else 'TABLE',
                'timestamp': datetime.now().isoformat()
            }
            
            # 记录到统计中
            query_hash = str(hash(query))
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = []
            self.query_stats[query_hash].append(analysis)
            
            return analysis
    
    @log_database_operation
    def batch_insert(self, table: str, columns: List[str], data: List[Tuple], batch_size: int = 1000) -> int:
        """批量插入数据"""
        if not data:
            return 0
        
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        total_inserted = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 分批处理
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                try:
                    cursor.executemany(sql, batch)
                    total_inserted += len(batch)
                    logger.debug(f"批量插入 {table}: {len(batch)} 条记录")
                except Exception as e:
                    logger.error(f"批量插入 {table} 失败: {e}")
                    raise
            
            conn.commit()
        
        logger.info(f"批量插入 {table} 完成: {total_inserted} 条记录")
        return total_inserted
    
    @log_database_operation
    def batch_update(self, table: str, set_clause: str, where_clause: str, data: List[Tuple], batch_size: int = 1000) -> int:
        """批量更新数据"""
        if not data:
            return 0
        
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        total_updated = 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 分批处理
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                try:
                    cursor.executemany(sql, batch)
                    total_updated += cursor.rowcount
                    logger.debug(f"批量更新 {table}: {len(batch)} 条记录")
                except Exception as e:
                    logger.error(f"批量更新 {table} 失败: {e}")
                    raise
            
            conn.commit()
        
        logger.info(f"批量更新 {table} 完成: {total_updated} 条记录")
        return total_updated
    
    @log_performance
    def optimize_database(self) -> Dict[str, Any]:
        """优化数据库"""
        optimization_results = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 1. 分析数据库
                start_time = time.time()
                cursor.execute("ANALYZE")
                optimization_results['analyze_time'] = time.time() - start_time
                
                # 2. 重建索引
                start_time = time.time()
                cursor.execute("REINDEX")
                optimization_results['reindex_time'] = time.time() - start_time
                
                # 3. 清理数据库
                start_time = time.time()
                cursor.execute("VACUUM")
                optimization_results['vacuum_time'] = time.time() - start_time
                
                # 4. 获取数据库统计信息
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                optimization_results['database_size_mb'] = (page_count * page_size) / (1024 * 1024)
                optimization_results['page_count'] = page_count
                optimization_results['page_size'] = page_size
                
                conn.commit()
                
                logger.info(f"数据库优化完成: {optimization_results}")
                
            except Exception as e:
                logger.error(f"数据库优化失败: {e}")
                optimization_results['error'] = str(e)
        
        return optimization_results
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        if not self.query_stats:
            return {'message': '暂无查询统计数据'}
        
        stats = {
            'total_queries': sum(len(queries) for queries in self.query_stats.values()),
            'unique_queries': len(self.query_stats),
            'queries': []
        }
        
        for query_hash, executions in self.query_stats.items():
            if executions:
                avg_time = sum(e['execution_time'] for e in executions) / len(executions)
                max_time = max(e['execution_time'] for e in executions)
                min_time = min(e['execution_time'] for e in executions)
                
                stats['queries'].append({
                    'query': executions[0]['query'][:100] + '...' if len(executions[0]['query']) > 100 else executions[0]['query'],
                    'executions': len(executions),
                    'avg_time': avg_time,
                    'max_time': max_time,
                    'min_time': min_time,
                    'uses_index': executions[-1]['uses_index']
                })
        
        # 按平均执行时间排序
        stats['queries'].sort(key=lambda x: x['avg_time'], reverse=True)
        
        return stats
    
    @log_performance
    def create_cache_warming_queries(self) -> List[str]:
        """创建缓存预热查询"""
        warming_queries = [
            # 预热常用的客户查询
            "SELECT COUNT(*) FROM customers WHERE deleted = FALSE OR deleted IS NULL",
            "SELECT * FROM customers WHERE deleted = FALSE OR deleted IS NULL ORDER BY created_at DESC LIMIT 50",
            
            # 预热订单查询
            "SELECT COUNT(*) FROM orders",
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT 50",
            "SELECT status, COUNT(*) FROM orders GROUP BY status",
            
            # 预热库存查询
            "SELECT COUNT(*) FROM inventory WHERE deleted = FALSE OR deleted IS NULL",
            "SELECT * FROM inventory WHERE quantity > 0 AND (deleted = FALSE OR deleted IS NULL) LIMIT 50",
            
            # 预热面料查询
            "SELECT COUNT(*) FROM fabrics WHERE deleted = FALSE OR deleted IS NULL",
            "SELECT usage_type, COUNT(*) FROM fabrics WHERE deleted = FALSE OR deleted IS NULL GROUP BY usage_type",
            
            # 预热统计查询
            "SELECT DATE(created_at) as date, COUNT(*) FROM orders WHERE created_at >= date('now', '-30 days') GROUP BY DATE(created_at)",
            "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id ORDER BY order_count DESC LIMIT 20",
        ]
        
        return warming_queries
    
    @log_performance
    def warm_cache(self) -> Dict[str, Any]:
        """执行缓存预热"""
        warming_queries = self.create_cache_warming_queries()
        results = {
            'total_queries': len(warming_queries),
            'successful': 0,
            'failed': 0,
            'total_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for query in warming_queries:
                try:
                    query_start = time.time()
                    cursor.execute(query)
                    cursor.fetchall()  # 确保查询完全执行
                    query_time = time.time() - query_start
                    
                    results['successful'] += 1
                    logger.debug(f"缓存预热查询完成: {query[:50]}... (耗时: {query_time:.3f}s)")
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"查询失败: {query[:50]}... - {str(e)}")
                    logger.warning(f"缓存预热查询失败: {e}")
        
        results['total_time'] = time.time() - start_time
        logger.info(f"缓存预热完成: {results}")
        
        return results


# 全局性能增强器实例
performance_enhancer = DatabasePerformanceEnhancer()


def create_advanced_indexes():
    """创建高级索引的便捷函数"""
    return performance_enhancer.create_advanced_indexes()


def optimize_database():
    """优化数据库的便捷函数"""
    return performance_enhancer.optimize_database()


def warm_cache():
    """缓存预热的便捷函数"""
    return performance_enhancer.warm_cache()


def analyze_query(query: str, params: tuple = ()):
    """分析查询性能的便捷函数"""
    return performance_enhancer.analyze_query_performance(query, params)


if __name__ == "__main__":
    # 测试性能增强功能
    print("开始数据库性能优化...")
    
    # 创建高级索引
    print("\n1. 创建高级索引...")
    index_results = create_advanced_indexes()
    print(f"索引创建结果: {index_results}")
    
    # 优化数据库
    print("\n2. 优化数据库...")
    optimize_results = optimize_database()
    print(f"优化结果: {optimize_results}")
    
    # 缓存预热
    print("\n3. 缓存预热...")
    warm_results = warm_cache()
    print(f"预热结果: {warm_results}")
    
    # 获取统计信息
    print("\n4. 查询统计...")
    stats = performance_enhancer.get_query_statistics()
    print(f"统计信息: {stats}")
    
    print("\n数据库性能优化完成！")