"""
批量操作优化模块
提供高效的批量数据处理功能，优化大数据量操作性能
"""

import sqlite3
import time
import threading
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import json

# 导入日志系统
from utils.logger import SystemLogger, log_performance, log_database_operation
from database_performance_enhancer import DatabasePerformanceEnhancer

logger = SystemLogger()


class BatchOperationManager:
    """批量操作管理器"""
    
    def __init__(self, db_path: str = "business_management.db", max_workers: int = 4):
        self.db_path = db_path
        self.max_workers = max_workers
        self.performance_enhancer = DatabasePerformanceEnhancer(db_path)
        self._lock = threading.Lock()
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_records_processed': 0,
            'total_time': 0
        }
    
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
    def batch_insert_customers(self, customers_data: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """批量插入客户数据"""
        if not customers_data:
            return {'success': False, 'message': '没有数据需要插入'}
        
        # 准备数据
        columns = ['nickname', 'phone_suffix', 'points', 'notes', 'created_at']
        data_tuples = []
        
        for customer in customers_data:
            data_tuples.append((
                customer.get('nickname', ''),
                customer.get('phone_suffix', ''),
                customer.get('points', 0),
                customer.get('notes', ''),
                customer.get('created_at', datetime.now().isoformat())
            ))
        
        try:
            inserted_count = self.performance_enhancer.batch_insert(
                'customers', columns, data_tuples, batch_size
            )
            
            self._update_stats('insert', len(data_tuples), True)
            
            return {
                'success': True,
                'inserted_count': inserted_count,
                'message': f'成功批量插入 {inserted_count} 条客户记录'
            }
            
        except Exception as e:
            self._update_stats('insert', len(data_tuples), False)
            logger.error(f"批量插入客户失败: {e}")
            return {'success': False, 'message': f'批量插入失败: {str(e)}'}
    
    @log_performance
    def batch_update_customer_points(self, updates: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """批量更新客户积分"""
        if not updates:
            return {'success': False, 'message': '没有数据需要更新'}
        
        # 准备更新数据
        data_tuples = []
        for update in updates:
            data_tuples.append((
                update.get('points', 0),
                update.get('customer_id')
            ))
        
        try:
            updated_count = self.performance_enhancer.batch_update(
                'customers',
                'points = ?',
                'id = ?',
                data_tuples,
                batch_size
            )
            
            self._update_stats('update', len(data_tuples), True)
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'成功批量更新 {updated_count} 条客户积分'
            }
            
        except Exception as e:
            self._update_stats('update', len(data_tuples), False)
            logger.error(f"批量更新客户积分失败: {e}")
            return {'success': False, 'message': f'批量更新失败: {str(e)}'}
    
    @log_performance
    def batch_insert_orders(self, orders_data: List[Dict[str, Any]], batch_size: int = 500) -> Dict[str, Any]:
        """批量插入订单数据"""
        if not orders_data:
            return {'success': False, 'message': '没有订单数据需要插入'}
        
        results = {'orders': 0, 'order_items': 0, 'errors': []}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 分批处理订单
                for i in range(0, len(orders_data), batch_size):
                    batch = orders_data[i:i + batch_size]
                    
                    for order_data in batch:
                        try:
                            # 插入订单主记录
                            order_sql = """
                            INSERT INTO orders (customer_id, total_amount, status, notes, created_at)
                            VALUES (?, ?, ?, ?, ?)
                            """
                            cursor.execute(order_sql, (
                                order_data.get('customer_id'),
                                order_data.get('total_amount', 0),
                                order_data.get('status', 'pending'),
                                order_data.get('notes', ''),
                                order_data.get('created_at', datetime.now().isoformat())
                            ))
                            
                            order_id = cursor.lastrowid
                            results['orders'] += 1
                            
                            # 插入订单项
                            if 'items' in order_data and order_data['items']:
                                item_sql = """
                                INSERT INTO order_items (order_id, inventory_id, item_type, quantity, 
                                                       unit_price, outer_fabric_id, inner_fabric_id, notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """
                                
                                for item in order_data['items']:
                                    cursor.execute(item_sql, (
                                        order_id,
                                        item.get('inventory_id'),
                                        item.get('item_type', 'product'),
                                        item.get('quantity', 1),
                                        item.get('unit_price', 0),
                                        item.get('outer_fabric_id'),
                                        item.get('inner_fabric_id'),
                                        item.get('notes', '')
                                    ))
                                    results['order_items'] += 1
                            
                        except Exception as e:
                            results['errors'].append(f"订单处理失败: {str(e)}")
                            logger.warning(f"单个订单插入失败: {e}")
                
                conn.commit()
                self._update_stats('insert', results['orders'] + results['order_items'], True)
                
                return {
                    'success': True,
                    'orders_inserted': results['orders'],
                    'items_inserted': results['order_items'],
                    'errors': results['errors'],
                    'message': f"成功插入 {results['orders']} 个订单，{results['order_items']} 个订单项"
                }
                
            except Exception as e:
                conn.rollback()
                self._update_stats('insert', len(orders_data), False)
                logger.error(f"批量插入订单失败: {e}")
                return {'success': False, 'message': f'批量插入订单失败: {str(e)}'}
    
    @log_performance
    def batch_update_inventory_quantities(self, updates: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """批量更新库存数量"""
        if not updates:
            return {'success': False, 'message': '没有库存更新数据'}
        
        # 准备更新数据
        data_tuples = []
        for update in updates:
            data_tuples.append((
                update.get('quantity', 0),
                update.get('inventory_id')
            ))
        
        try:
            updated_count = self.performance_enhancer.batch_update(
                'inventory',
                'quantity = ?',
                'id = ?',
                data_tuples,
                batch_size
            )
            
            self._update_stats('update', len(data_tuples), True)
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'成功批量更新 {updated_count} 条库存记录'
            }
            
        except Exception as e:
            self._update_stats('update', len(data_tuples), False)
            logger.error(f"批量更新库存失败: {e}")
            return {'success': False, 'message': f'批量更新库存失败: {str(e)}'}
    
    @log_performance
    def batch_soft_delete(self, table: str, ids: List[int], batch_size: int = 1000) -> Dict[str, Any]:
        """批量软删除记录"""
        if not ids:
            return {'success': False, 'message': '没有需要删除的记录'}
        
        # 准备删除数据
        data_tuples = [(True, datetime.now().isoformat(), id_val) for id_val in ids]
        
        try:
            updated_count = self.performance_enhancer.batch_update(
                table,
                'deleted = ?, deleted_at = ?',
                'id = ?',
                data_tuples,
                batch_size
            )
            
            self._update_stats('delete', len(ids), True)
            
            return {
                'success': True,
                'deleted_count': updated_count,
                'message': f'成功批量删除 {updated_count} 条 {table} 记录'
            }
            
        except Exception as e:
            self._update_stats('delete', len(ids), False)
            logger.error(f"批量软删除 {table} 失败: {e}")
            return {'success': False, 'message': f'批量删除失败: {str(e)}'}
    
    @log_performance
    def parallel_data_processing(self, 
                                data_chunks: List[List[Any]], 
                                process_func: Callable,
                                max_workers: Optional[int] = None) -> Dict[str, Any]:
        """并行数据处理"""
        if not data_chunks:
            return {'success': False, 'message': '没有数据需要处理'}
        
        max_workers = max_workers or self.max_workers
        results = {'successful': 0, 'failed': 0, 'results': [], 'errors': []}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_chunk = {
                executor.submit(process_func, chunk): chunk 
                for chunk in data_chunks
            }
            
            # 收集结果
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    results['results'].append(result)
                    results['successful'] += 1
                    logger.debug(f"数据块处理成功: {len(chunk)} 条记录")
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"数据块处理失败: {str(e)}")
                    logger.warning(f"数据块处理失败: {e}")
        
        processing_time = time.time() - start_time
        
        return {
            'success': results['failed'] == 0,
            'successful_chunks': results['successful'],
            'failed_chunks': results['failed'],
            'total_chunks': len(data_chunks),
            'processing_time': processing_time,
            'results': results['results'],
            'errors': results['errors'],
            'message': f"并行处理完成: {results['successful']}/{len(data_chunks)} 成功"
        }
    
    def _update_stats(self, operation_type: str, record_count: int, success: bool):
        """更新操作统计"""
        with self._lock:
            self.operation_stats['total_operations'] += 1
            self.operation_stats['total_records_processed'] += record_count
            
            if success:
                self.operation_stats['successful_operations'] += 1
            else:
                self.operation_stats['failed_operations'] += 1
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """获取操作统计信息"""
        with self._lock:
            stats = self.operation_stats.copy()
            
            if stats['total_operations'] > 0:
                stats['success_rate'] = stats['successful_operations'] / stats['total_operations']
                stats['avg_records_per_operation'] = stats['total_records_processed'] / stats['total_operations']
            else:
                stats['success_rate'] = 0
                stats['avg_records_per_operation'] = 0
            
            return stats
    
    def reset_stats(self):
        """重置统计信息"""
        with self._lock:
            self.operation_stats = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'total_records_processed': 0,
                'total_time': 0
            }
    
    @log_performance
    def export_data_in_batches(self, 
                              table: str, 
                              output_format: str = 'json',
                              batch_size: int = 5000,
                              where_clause: str = "",
                              params: tuple = ()) -> Dict[str, Any]:
        """分批导出大量数据"""
        try:
            all_data = []
            offset = 0
            total_exported = 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取总记录数
                count_sql = f"SELECT COUNT(*) FROM {table}"
                if where_clause:
                    count_sql += f" WHERE {where_clause}"
                
                cursor.execute(count_sql, params)
                total_records = cursor.fetchone()[0]
                
                logger.info(f"开始分批导出 {table} 表，总记录数: {total_records}")
                
                # 分批查询和导出
                while offset < total_records:
                    query_sql = f"SELECT * FROM {table}"
                    if where_clause:
                        query_sql += f" WHERE {where_clause}"
                    query_sql += f" LIMIT {batch_size} OFFSET {offset}"
                    
                    cursor.execute(query_sql, params)
                    batch_data = cursor.fetchall()
                    
                    if not batch_data:
                        break
                    
                    # 转换为字典格式
                    batch_dict = [dict(row) for row in batch_data]
                    all_data.extend(batch_dict)
                    
                    total_exported += len(batch_data)
                    offset += batch_size
                    
                    logger.debug(f"已导出 {total_exported}/{total_records} 条记录")
            
            # 根据格式导出
            if output_format.lower() == 'json':
                output_data = json.dumps(all_data, ensure_ascii=False, indent=2, default=str)
            else:
                # 可以扩展支持其他格式
                output_data = all_data
            
            return {
                'success': True,
                'total_exported': total_exported,
                'data': output_data,
                'message': f'成功导出 {total_exported} 条 {table} 记录'
            }
            
        except Exception as e:
            logger.error(f"分批导出数据失败: {e}")
            return {'success': False, 'message': f'导出失败: {str(e)}'}


# 全局批量操作管理器实例
batch_manager = BatchOperationManager()


# 便捷函数
def batch_insert_customers(customers_data: List[Dict[str, Any]], batch_size: int = 1000):
    """批量插入客户的便捷函数"""
    return batch_manager.batch_insert_customers(customers_data, batch_size)


def batch_update_customer_points(updates: List[Dict[str, Any]], batch_size: int = 1000):
    """批量更新客户积分的便捷函数"""
    return batch_manager.batch_update_customer_points(updates, batch_size)


def batch_insert_orders(orders_data: List[Dict[str, Any]], batch_size: int = 500):
    """批量插入订单的便捷函数"""
    return batch_manager.batch_insert_orders(orders_data, batch_size)


def batch_update_inventory(updates: List[Dict[str, Any]], batch_size: int = 1000):
    """批量更新库存的便捷函数"""
    return batch_manager.batch_update_inventory_quantities(updates, batch_size)


def batch_soft_delete(table: str, ids: List[int], batch_size: int = 1000):
    """批量软删除的便捷函数"""
    return batch_manager.batch_soft_delete(table, ids, batch_size)


if __name__ == "__main__":
    # 测试批量操作功能
    print("开始测试批量操作功能...")
    
    # 测试批量插入客户
    test_customers = [
        {'nickname': f'测试客户{i}', 'phone_suffix': f'000{i}', 'points': i * 10}
        for i in range(1, 101)
    ]
    
    print("\n1. 测试批量插入客户...")
    result = batch_insert_customers(test_customers)
    print(f"结果: {result}")
    
    # 获取统计信息
    print("\n2. 获取操作统计...")
    stats = batch_manager.get_operation_stats()
    print(f"统计信息: {stats}")
    
    print("\n批量操作测试完成！")