#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能优化脚本
用于添加索引、优化查询性能
"""

import sqlite3
import time
import logging
from typing import List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self, db_path: str = "business_management.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def create_indexes(self):
        """创建性能优化索引"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 定义要创建的索引
        indexes = [
            # 订单表索引
            ("idx_orders_customer_id", "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)"),
            ("idx_orders_created_at", "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)"),
            ("idx_orders_status", "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)"),
            ("idx_orders_total_amount", "CREATE INDEX IF NOT EXISTS idx_orders_total_amount ON orders(total_amount)"),
            
            # 订单项表索引
            ("idx_order_items_order_id", "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"),
            ("idx_order_items_inventory_id", "CREATE INDEX IF NOT EXISTS idx_order_items_inventory_id ON order_items(inventory_id)"),
            ("idx_order_items_item_type", "CREATE INDEX IF NOT EXISTS idx_order_items_item_type ON order_items(item_type)"),
            
            # 客户表索引
            ("idx_customers_phone_suffix", "CREATE INDEX IF NOT EXISTS idx_customers_phone_suffix ON customers(phone_suffix)"),
            ("idx_customers_nickname", "CREATE INDEX IF NOT EXISTS idx_customers_nickname ON customers(nickname)"),
            ("idx_customers_points", "CREATE INDEX IF NOT EXISTS idx_customers_points ON customers(points)"),
            
            # 库存表索引
            ("idx_inventory_quantity", "CREATE INDEX IF NOT EXISTS idx_inventory_quantity ON inventory(quantity)"),
            ("idx_inventory_product_name", "CREATE INDEX IF NOT EXISTS idx_inventory_product_name ON inventory(product_name)"),
            
            # 面料表索引
            ("idx_fabrics_material_type", "CREATE INDEX IF NOT EXISTS idx_fabrics_material_type ON fabrics(material_type)"),
            ("idx_fabrics_usage_type", "CREATE INDEX IF NOT EXISTS idx_fabrics_usage_type ON fabrics(usage_type)"),
            
            # 复合索引（用于复杂查询优化）
            ("idx_orders_status_date", "CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, created_at)"),
            ("idx_orders_customer_date", "CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, created_at)"),
            ("idx_order_items_order_type", "CREATE INDEX IF NOT EXISTS idx_order_items_order_type ON order_items(order_id, item_type)"),
        ]
        
        created_count = 0
        for index_name, sql in indexes:
            try:
                start_time = time.time()
                cursor.execute(sql)
                end_time = time.time()
                
                logger.info(f"✅ 创建索引 {index_name} 成功 (耗时: {end_time - start_time:.3f}s)")
                created_count += 1
            except sqlite3.Error as e:
                logger.warning(f"⚠️ 创建索引 {index_name} 失败: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 索引创建完成！成功创建 {created_count}/{len(indexes)} 个索引")
        return created_count
    
    def analyze_query_performance(self):
        """分析查询性能"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 测试查询
        test_queries = [
            ("获取所有订单", "SELECT COUNT(*) FROM orders"),
            ("按客户查询订单", "SELECT COUNT(*) FROM orders WHERE customer_id = 1"),
            ("按状态查询订单", "SELECT COUNT(*) FROM orders WHERE status = 'pending'"),
            ("按日期范围查询", "SELECT COUNT(*) FROM orders WHERE created_at >= date('now', '-30 days')"),
            ("订单关联查询", """
                SELECT COUNT(*) FROM orders o 
                LEFT JOIN customers c ON o.customer_id = c.id 
                WHERE o.status = 'pending'
            """),
            ("复杂分页查询", """
                SELECT o.*, c.nickname 
                FROM orders o 
                LEFT JOIN customers c ON o.customer_id = c.id 
                ORDER BY o.created_at DESC 
                LIMIT 10 OFFSET 0
            """),
        ]
        
        logger.info("📊 开始性能测试...")
        results = []
        
        for query_name, sql in test_queries:
            try:
                start_time = time.time()
                cursor.execute(sql)
                cursor.fetchall()
                end_time = time.time()
                
                execution_time = end_time - start_time
                results.append((query_name, execution_time))
                
                status = "🟢" if execution_time < 0.1 else "🟡" if execution_time < 0.5 else "🔴"
                logger.info(f"{status} {query_name}: {execution_time:.3f}s")
                
            except sqlite3.Error as e:
                logger.error(f"❌ 查询 {query_name} 失败: {e}")
        
        conn.close()
        return results
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取表统计信息
        tables = ['customers', 'orders', 'order_items', 'inventory', 'fabrics']
        stats = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.Error as e:
                logger.error(f"获取表 {table} 统计失败: {e}")
                stats[table] = 0
        
        # 获取索引信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        logger.info("📈 数据库统计信息:")
        for table, count in stats.items():
            logger.info(f"   📋 {table}: {count} 条记录")
        
        logger.info(f"   🔍 自定义索引: {len(indexes)} 个")
        
        return stats, indexes
    
    def optimize_database(self):
        """执行完整的数据库优化"""
        logger.info("🚀 开始数据库性能优化...")
        
        # 1. 获取优化前统计
        logger.info("\n📊 优化前状态:")
        stats_before, indexes_before = self.get_database_stats()
        perf_before = self.analyze_query_performance()
        
        # 2. 创建索引
        logger.info("\n🔧 创建性能索引:")
        created_indexes = self.create_indexes()
        
        # 3. 获取优化后统计
        logger.info("\n📊 优化后状态:")
        stats_after, indexes_after = self.get_database_stats()
        perf_after = self.analyze_query_performance()
        
        # 4. 生成优化报告
        logger.info("\n📋 优化报告:")
        logger.info(f"   ✅ 新增索引: {len(indexes_after) - len(indexes_before)} 个")
        logger.info(f"   📈 总索引数: {len(indexes_after)} 个")
        
        # 性能对比
        if perf_before and perf_after:
            logger.info("\n⚡ 性能对比:")
            for i, (query_name, _) in enumerate(perf_before):
                if i < len(perf_after):
                    before_time = perf_before[i][1]
                    after_time = perf_after[i][1]
                    improvement = ((before_time - after_time) / before_time * 100) if before_time > 0 else 0
                    
                    if improvement > 0:
                        logger.info(f"   🚀 {query_name}: 提升 {improvement:.1f}%")
                    else:
                        logger.info(f"   ➡️ {query_name}: 无明显变化")
        
        logger.info("\n🎉 数据库优化完成！")
        return True

def main():
    """主函数"""
    optimizer = DatabaseOptimizer()
    optimizer.optimize_database()

if __name__ == "__main__":
    main()