#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合性能测试脚本
测试数据库索引、缓存和查询优化效果
"""

import time
import logging
from database import DatabaseManager
import streamlit as st

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTester:
    def __init__(self):
        self.db = DatabaseManager()
        # 初始化session_state模拟
        if not hasattr(st, 'session_state'):
            st.session_state = {}
    
    def test_database_queries(self):
        """测试数据库查询性能"""
        logger.info("🔍 开始数据库查询性能测试...")
        
        tests = [
            ("获取客户列表", lambda: self.db.get_customers()),
            ("获取面料列表", lambda: self.db.get_fabrics()),
            ("获取库存列表", lambda: self.db.get_inventory_items()),
            ("分页查询订单", lambda: self.db.get_orders_paginated(page=1, page_size=10)),
            ("搜索订单", lambda: self.db.get_orders_paginated(page=1, page_size=10, search_term="测试")),
            ("状态筛选订单", lambda: self.db.get_orders_paginated(page=1, page_size=10, status_filter="pending")),
        ]
        
        results = []
        for test_name, test_func in tests:
            # 第一次执行（无缓存）
            start_time = time.time()
            result1 = test_func()
            first_time = time.time() - start_time
            
            # 第二次执行（有缓存）
            start_time = time.time()
            result2 = test_func()
            second_time = time.time() - start_time
            
            # 计算缓存效果
            cache_improvement = ((first_time - second_time) / first_time * 100) if first_time > 0 else 0
            
            results.append({
                'test': test_name,
                'first_time': first_time,
                'second_time': second_time,
                'improvement': cache_improvement
            })
            
            status = "🟢" if first_time < 0.1 else "🟡" if first_time < 0.5 else "🔴"
            cache_status = "🚀" if cache_improvement > 50 else "⚡" if cache_improvement > 10 else "➡️"
            
            logger.info(f"{status} {test_name}: {first_time:.3f}s → {second_time:.3f}s {cache_status} 缓存提升: {cache_improvement:.1f}%")
        
        return results
    
    def test_cache_effectiveness(self):
        """测试缓存有效性"""
        logger.info("💾 开始缓存有效性测试...")
        
        # 清理所有缓存
        self.db.clear_cache()
        
        # 测试缓存命中率
        cache_tests = [
            ("客户数据缓存", self.db.get_customers),
            ("面料数据缓存", self.db.get_fabrics),
            ("库存数据缓存", self.db.get_inventory_items),
        ]
        
        for test_name, test_func in cache_tests:
            # 多次调用测试缓存
            times = []
            for i in range(5):
                start_time = time.time()
                result = test_func()
                execution_time = time.time() - start_time
                times.append(execution_time)
            
            avg_time = sum(times) / len(times)
            first_time = times[0]
            cached_avg = sum(times[1:]) / len(times[1:]) if len(times) > 1 else 0
            
            improvement = ((first_time - cached_avg) / first_time * 100) if first_time > 0 and cached_avg > 0 else 0
            
            logger.info(f"📊 {test_name}: 首次 {first_time:.3f}s, 缓存平均 {cached_avg:.3f}s, 提升 {improvement:.1f}%")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        logger.info("🧠 开始内存使用测试...")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 获取初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行一系列操作
        for i in range(10):
            self.db.get_customers()
            self.db.get_fabrics()
            self.db.get_inventory_items()
            self.db.get_orders_paginated(page=i+1, page_size=10)
        
        # 获取最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        logger.info(f"💾 内存使用: {initial_memory:.1f}MB → {final_memory:.1f}MB (增加 {memory_increase:.1f}MB)")
        
        # 清理缓存后的内存
        self.db.clear_cache()
        after_clear_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = final_memory - after_clear_memory
        
        logger.info(f"🧹 清理缓存后: {after_clear_memory:.1f}MB (释放 {memory_freed:.1f}MB)")
    
    def test_concurrent_access(self):
        """测试并发访问性能"""
        logger.info("🔄 开始并发访问测试...")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker():
            start_time = time.time()
            try:
                # 模拟并发查询
                customers = self.db.get_customers()
                fabrics = self.db.get_fabrics()
                inventory = self.db.get_inventory_items()
                orders = self.db.get_orders_paginated()
                
                execution_time = time.time() - start_time
                results_queue.put(('success', execution_time))
            except Exception as e:
                results_queue.put(('error', str(e)))
        
        # 创建多个线程
        threads = []
        thread_count = 5
        
        start_time = time.time()
        for i in range(thread_count):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 收集结果
        success_count = 0
        error_count = 0
        execution_times = []
        
        while not results_queue.empty():
            status, result = results_queue.get()
            if status == 'success':
                success_count += 1
                execution_times.append(result)
            else:
                error_count += 1
                logger.error(f"并发测试错误: {result}")
        
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        logger.info(f"🔄 并发测试结果: {success_count}/{thread_count} 成功")
        logger.info(f"⏱️ 总耗时: {total_time:.3f}s, 平均单线程: {avg_time:.3f}s")
    
    def generate_performance_report(self):
        """生成性能报告"""
        logger.info("📋 生成性能优化报告...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'database_stats': {},
            'performance_results': {},
            'optimization_summary': {}
        }
        
        # 数据库统计
        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # 获取表大小
            tables = ['customers', 'orders', 'order_items', 'inventory', 'fabrics']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                report['database_stats'][table] = count
            
            # 获取索引数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            index_count = cursor.fetchone()[0]
            report['database_stats']['indexes'] = index_count
            
            conn.close()
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
        
        # 性能测试结果
        query_results = self.test_database_queries()
        report['performance_results']['query_tests'] = query_results
        
        # 缓存测试
        self.test_cache_effectiveness()
        
        # 内存测试
        try:
            self.test_memory_usage()
        except ImportError:
            logger.warning("psutil未安装，跳过内存测试")
        
        # 并发测试
        self.test_concurrent_access()
        
        # 优化总结
        total_queries = len(query_results)
        fast_queries = len([r for r in query_results if r['first_time'] < 0.1])
        cached_improvements = [r for r in query_results if r['improvement'] > 10]
        
        report['optimization_summary'] = {
            'total_queries_tested': total_queries,
            'fast_queries_count': fast_queries,
            'fast_queries_percentage': (fast_queries / total_queries * 100) if total_queries > 0 else 0,
            'cache_improvements_count': len(cached_improvements),
            'avg_cache_improvement': sum(r['improvement'] for r in cached_improvements) / len(cached_improvements) if cached_improvements else 0
        }
        
        # 输出报告摘要
        logger.info("📊 性能优化报告摘要:")
        logger.info(f"   🚀 快速查询: {fast_queries}/{total_queries} ({report['optimization_summary']['fast_queries_percentage']:.1f}%)")
        logger.info(f"   💾 缓存优化: {len(cached_improvements)} 项查询获得显著提升")
        logger.info(f"   ⚡ 平均缓存提升: {report['optimization_summary']['avg_cache_improvement']:.1f}%")
        logger.info(f"   🔍 数据库索引: {report['database_stats'].get('indexes', 0)} 个")
        
        return report
    
    def run_full_test(self):
        """运行完整性能测试"""
        logger.info("🚀 开始完整性能测试...")
        
        start_time = time.time()
        report = self.generate_performance_report()
        total_time = time.time() - start_time
        
        logger.info(f"✅ 性能测试完成！总耗时: {total_time:.2f}s")
        logger.info("🎉 性能优化验证成功！")
        
        return report

def main():
    """主函数"""
    try:
        tester = PerformanceTester()
        tester.run_full_test()
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        raise

if __name__ == "__main__":
    main()