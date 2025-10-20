#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化性能测试脚本
测试数据库索引和查询优化效果
"""

import time
import sqlite3
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePerformanceTester:
    def __init__(self):
        self.db_path = "business_management.db"
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def test_query_performance(self):
        """测试查询性能"""
        logger.info("🔍 开始数据库查询性能测试...")
        
        queries = [
            ("获取所有客户", "SELECT * FROM customers"),
            ("获取所有面料", "SELECT * FROM fabrics"),
            ("获取库存信息", "SELECT * FROM inventory"),
            ("获取订单列表", "SELECT * FROM orders LIMIT 50"),
            ("按客户查询订单", "SELECT * FROM orders WHERE customer_id = 1"),
            ("按状态查询订单", "SELECT * FROM orders WHERE status = 'pending'"),
            ("按日期范围查询", "SELECT * FROM orders WHERE created_at >= date('now', '-30 days')"),
            ("订单关联查询", """
                SELECT o.*, c.nickname, c.phone_suffix 
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                LIMIT 20
            """),
            ("复杂分页查询", """
                SELECT o.*, c.nickname, 
                       COUNT(oi.id) as item_count,
                       SUM(oi.quantity * oi.unit_price) as total_amount
                FROM orders o 
                LEFT JOIN customers c ON o.customer_id = c.id 
                LEFT JOIN order_items oi ON o.id = oi.order_id 
                GROUP BY o.id 
                ORDER BY o.created_at DESC 
                LIMIT 10 OFFSET 0
            """),
        ]
        
        results = []
        conn = self.get_connection()
        
        for query_name, query in queries:
            # 执行多次取平均值
            times = []
            for i in range(3):
                start_time = time.time()
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            row_count = len(rows) if 'rows' in locals() else 0
            
            # 性能评级
            if avg_time < 0.001:
                status = "🟢 极快"
            elif avg_time < 0.01:
                status = "🟢 很快"
            elif avg_time < 0.1:
                status = "🟡 正常"
            elif avg_time < 0.5:
                status = "🟠 较慢"
            else:
                status = "🔴 慢"
            
            results.append({
                'name': query_name,
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'row_count': row_count,
                'status': status
            })
            
            logger.info(f"{status}: {query_name} - 平均 {avg_time:.4f}s ({row_count} 行)")
        
        conn.close()
        return results
    
    def test_index_effectiveness(self):
        """测试索引有效性"""
        logger.info("📊 开始索引有效性测试...")
        
        conn = self.get_connection()
        
        # 获取索引信息
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"🔍 发现 {len(indexes)} 个自定义索引:")
        for idx in indexes:
            logger.info(f"   - {idx}")
        
        # 测试索引使用情况
        test_queries = [
            ("客户ID索引", "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 1"),
            ("状态索引", "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE status = 'pending'"),
            ("日期索引", "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE created_at >= date('now', '-30 days')"),
            ("复合索引", "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 1 AND status = 'pending'"),
        ]
        
        for test_name, query in test_queries:
            cursor = conn.execute(query)
            plan = cursor.fetchall()
            
            # 检查是否使用了索引
            plan_text = ' '.join([str(row) for row in plan])
            uses_index = 'USING INDEX' in plan_text.upper()
            
            status = "✅ 使用索引" if uses_index else "❌ 全表扫描"
            logger.info(f"{status}: {test_name}")
        
        conn.close()
        return indexes
    
    def test_database_stats(self):
        """测试数据库统计信息"""
        logger.info("📈 开始数据库统计测试...")
        
        conn = self.get_connection()
        
        tables = ['customers', 'orders', 'order_items', 'inventory', 'fabrics']
        stats = {}
        
        for table in tables:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
                logger.info(f"📋 {table}: {count} 条记录")
            except sqlite3.Error as e:
                logger.warning(f"⚠️ 无法获取 {table} 统计: {e}")
        
        # 数据库文件大小
        import os
        if os.path.exists(self.db_path):
            file_size = os.path.getsize(self.db_path) / 1024 / 1024  # MB
            logger.info(f"💾 数据库文件大小: {file_size:.2f} MB")
            stats['file_size_mb'] = file_size
        
        conn.close()
        return stats
    
    def generate_performance_report(self):
        """生成性能报告"""
        logger.info("📋 生成性能优化报告...")
        
        # 数据库统计
        stats = self.test_database_stats()
        
        # 索引测试
        indexes = self.test_index_effectiveness()
        
        # 查询性能测试
        query_results = self.test_query_performance()
        
        # 分析结果
        fast_queries = [r for r in query_results if r['avg_time'] < 0.01]
        slow_queries = [r for r in query_results if r['avg_time'] > 0.1]
        
        logger.info("\n" + "="*60)
        logger.info("📊 性能优化报告摘要")
        logger.info("="*60)
        logger.info(f"🔍 数据库索引: {len(indexes)} 个")
        logger.info(f"📋 数据表记录: {sum(stats.get(table, 0) for table in ['customers', 'orders', 'order_items', 'inventory', 'fabrics'])} 条")
        logger.info(f"💾 数据库大小: {stats.get('file_size_mb', 0):.2f} MB")
        logger.info(f"🚀 快速查询: {len(fast_queries)}/{len(query_results)} ({len(fast_queries)/len(query_results)*100:.1f}%)")
        logger.info(f"🐌 慢查询: {len(slow_queries)}/{len(query_results)} ({len(slow_queries)/len(query_results)*100:.1f}%)")
        
        if len(fast_queries) >= len(query_results) * 0.8:
            logger.info("✅ 性能优化效果: 优秀")
        elif len(fast_queries) >= len(query_results) * 0.6:
            logger.info("🟡 性能优化效果: 良好")
        else:
            logger.info("🔴 性能优化效果: 需要改进")
        
        logger.info("="*60)
        
        return {
            'stats': stats,
            'indexes': indexes,
            'query_results': query_results,
            'fast_queries': len(fast_queries),
            'slow_queries': len(slow_queries),
            'total_queries': len(query_results)
        }
    
    def run_test(self):
        """运行性能测试"""
        logger.info("🚀 开始性能测试...")
        
        start_time = time.time()
        report = self.generate_performance_report()
        total_time = time.time() - start_time
        
        logger.info(f"✅ 性能测试完成！总耗时: {total_time:.2f}s")
        logger.info("🎉 数据库性能优化验证完成！")
        
        return report

def main():
    """主函数"""
    try:
        tester = SimplePerformanceTester()
        tester.run_test()
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        raise

if __name__ == "__main__":
    main()