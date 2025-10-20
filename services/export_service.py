"""
导出业务服务层

负责处理各种导出功能的业务逻辑，包括CSV导出、PDF导出等。
将导出相关的业务逻辑从UI层分离，提高代码的可维护性和可测试性。
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
from database import DatabaseManager


class ExportService:
    """导出业务服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化导出服务
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def export_orders_to_csv(self, order_ids: List[int]) -> Tuple[str, str]:
        """
        导出订单为CSV格式
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            元组 (CSV内容, 文件名)
            
        Raises:
            Exception: 导出过程中的任何错误
        """
        try:
            # 导入CSV导出模块
            from csv_export import export_orders_to_csv_optimized, generate_csv_filename
            
            # 获取订单完整数据
            orders_with_items = self.db.get_orders_with_items_for_export(order_ids)
            
            # 生成CSV内容
            csv_content = export_orders_to_csv_optimized(orders_with_items)
            filename = generate_csv_filename()
            
            return csv_content, filename
            
        except Exception as e:
            raise Exception(f"CSV导出失败: {str(e)}")
    
    def export_orders_to_pdf(self, order_ids: List[int]) -> Tuple[bytes, str]:
        """
        导出订单为PDF格式
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            元组 (PDF数据, 文件名)
            
        Raises:
            Exception: 导出过程中的任何错误
        """
        try:
            # 导入PDF导出模块
            from pdf_export import export_orders_to_pdf
            
            # 获取订单数据
            orders = self.db.get_orders_by_ids(order_ids)
            
            # 获取订单项数据
            order_items_dict = {}
            for order_id in order_ids:
                items = self.db.get_order_items(order_id)
                order_items_dict[order_id] = items
            
            # 生成PDF数据
            pdf_data = export_orders_to_pdf(orders, order_items_dict)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"订单详情_{timestamp}.pdf"
            
            return pdf_data, filename
            
        except Exception as e:
            raise Exception(f"PDF导出失败: {str(e)}")
    
    def get_export_summary(self, order_ids: List[int]) -> Dict[str, Any]:
        """
        获取导出摘要信息
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            包含导出摘要的字典
        """
        try:
            orders = self.db.get_orders_by_ids(order_ids)
            
            total_amount = sum(order.get('total_amount', 0) for order in orders)
            customer_count = len(set(order.get('customer_id') for order in orders if order.get('customer_id')))
            
            return {
                'order_count': len(orders),
                'total_amount': total_amount,
                'customer_count': customer_count,
                'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {
                'order_count': 0,
                'total_amount': 0,
                'customer_count': 0,
                'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': str(e)
            }
    
    def validate_export_data(self, order_ids: List[int]) -> Dict[str, Any]:
        """
        验证导出数据的完整性
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            验证结果字典
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            if not order_ids:
                validation_result['is_valid'] = False
                validation_result['errors'].append("未选择任何订单")
                return validation_result
            
            # 检查订单是否存在
            orders = self.db.get_orders_by_ids(order_ids)
            found_order_ids = [order['id'] for order in orders]
            missing_order_ids = set(order_ids) - set(found_order_ids)
            
            if missing_order_ids:
                validation_result['warnings'].append(f"以下订单不存在: {list(missing_order_ids)}")
            
            # 检查订单数据完整性
            incomplete_orders = []
            for order in orders:
                if not order.get('customer_id'):
                    incomplete_orders.append(order['id'])
            
            if incomplete_orders:
                validation_result['warnings'].append(f"以下订单缺少客户信息: {incomplete_orders}")
            
            # 检查订单项数据
            orders_without_items = []
            for order_id in found_order_ids:
                items = self.db.get_order_items(order_id)
                if not items:
                    orders_without_items.append(order_id)
            
            if orders_without_items:
                validation_result['warnings'].append(f"以下订单没有商品项: {orders_without_items}")
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"数据验证失败: {str(e)}")
        
        return validation_result
    
    def get_supported_export_formats(self) -> List[Dict[str, str]]:
        """
        获取支持的导出格式列表
        
        Returns:
            支持的导出格式列表
        """
        return [
            {
                'format': 'csv',
                'name': 'CSV表格',
                'description': '适合在Excel中打开的表格格式',
                'mime_type': 'text/csv',
                'extension': '.csv'
            },
            {
                'format': 'pdf',
                'name': 'PDF文档',
                'description': '适合打印的文档格式 (76mm×130mm)',
                'mime_type': 'application/pdf',
                'extension': '.pdf'
            }
        ]