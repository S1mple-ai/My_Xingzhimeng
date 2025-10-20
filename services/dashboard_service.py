"""
仪表盘业务服务层

负责处理仪表盘相关的业务逻辑，包括数据获取、处理和格式化。
将业务逻辑从UI层分离，提高代码的可维护性和可测试性。
"""

import pandas as pd
import plotly.express as px
from typing import Dict, List, Any, Optional
from database import DatabaseManager


class DashboardService:
    """仪表盘业务服务类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化仪表盘服务
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def get_dashboard_data(self, time_period: str) -> Dict[str, Any]:
        """
        获取仪表盘数据
        
        Args:
            time_period: 时间段选择
            
        Returns:
            包含所有仪表盘数据的字典
        """
        return self.db.get_unified_dashboard_data(time_period)
    
    def calculate_key_metrics(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算关键指标
        
        Args:
            dashboard_data: 仪表盘原始数据
            
        Returns:
            格式化后的关键指标数据
        """
        summary = dashboard_data['summary']
        
        # 计算平均订单价值
        avg_order_value = (
            summary['total_amount'] / summary['total_orders'] 
            if summary['total_orders'] > 0 else 0
        )
        
        return {
            'total_orders': summary['total_orders'],
            'total_amount': summary['total_amount'],
            'active_customers': summary['active_customers'],
            'avg_order_value': avg_order_value
        }
    
    def create_sales_trend_chart(self, daily_sales_data: List[Dict], time_period: str):
        """
        创建销售趋势图表
        
        Args:
            daily_sales_data: 每日销售数据
            time_period: 时间段
            
        Returns:
            Plotly图表对象
        """
        if not daily_sales_data:
            return None
            
        df_sales = pd.DataFrame(daily_sales_data)
        
        fig_trend = px.line(
            df_sales, 
            x='date', 
            y='amount',
            title=f'{time_period} - 每日销售额趋势',
            markers=True
        )
        
        fig_trend.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_size=16,
            title_font_color='#2D3748',
            font=dict(color='#2D3748'),
            xaxis_title="日期",
            yaxis_title="销售额 (¥)"
        )
        
        return fig_trend
    
    def create_daily_orders_chart(self, daily_sales_data: List[Dict], time_period: str):
        """
        创建每日订单数图表
        
        Args:
            daily_sales_data: 每日销售数据
            time_period: 时间段
            
        Returns:
            Plotly图表对象
        """
        if not daily_sales_data:
            return None
            
        df_sales = pd.DataFrame(daily_sales_data)
        
        fig_orders = px.bar(
            df_sales, 
            x='date', 
            y='order_count',
            title=f'{time_period} - 每日订单数',
            color_discrete_sequence=['#4299E1']
        )
        
        fig_orders.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_size=16,
            title_font_color='#2D3748',
            font=dict(color='#2D3748'),
            xaxis_title="日期",
            yaxis_title="订单数"
        )
        
        return fig_orders
    
    def create_fabric_usage_charts(self, fabric_data: List[Dict], time_period: str) -> Dict[str, Any]:
        """
        创建面料使用分析图表
        
        Args:
            fabric_data: 面料使用数据
            time_period: 时间段
            
        Returns:
            包含表布和里布图表的字典
        """
        if not fabric_data:
            return {'face_fabric_chart': None, 'lining_chart': None}
        
        df_fabric = pd.DataFrame(fabric_data)
        
        # 表布使用分析
        face_fabric_data = df_fabric[df_fabric['usage_type'] == '表布']
        face_fabric_chart = None
        if not face_fabric_data.empty:
            face_fabric_chart = px.pie(
                face_fabric_data, 
                values='usage_count', 
                names='fabric_name',
                title=f'{time_period} - 表布使用分布',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            face_fabric_chart.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748')
            )
        
        # 里布使用分析
        lining_data = df_fabric[df_fabric['usage_type'] == '里布']
        lining_chart = None
        if not lining_data.empty:
            lining_chart = px.pie(
                lining_data, 
                values='usage_count', 
                names='fabric_name',
                title=f'{time_period} - 里布使用分布',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            lining_chart.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748')
            )
        
        return {
            'face_fabric_chart': face_fabric_chart,
            'lining_chart': lining_chart
        }
    
    def create_product_sales_charts(self, product_data: List[Dict], time_period: str) -> Dict[str, Any]:
        """
        创建商品销售分析图表
        
        Args:
            product_data: 商品销售数据
            time_period: 时间段
            
        Returns:
            包含现货和定制商品图表的字典
        """
        if not product_data:
            return {'inventory_chart': None, 'custom_chart': None}
        
        df_product = pd.DataFrame(product_data)
        
        # 现货商品销售排行
        inventory_data = df_product[df_product['product_type'] == 'inventory']
        inventory_chart = None
        if not inventory_data.empty:
            inventory_chart = px.bar(
                inventory_data.head(10), 
                x='sales_count', 
                y='product_name',
                title=f'{time_period} - 现货商品销售排行 (Top 10)',
                orientation='h',
                color_discrete_sequence=['#48BB78']
            )
            inventory_chart.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis_title="销售数量",
                yaxis_title="商品名称"
            )
        
        # 定制商品销售排行
        custom_data = df_product[df_product['product_type'] == 'custom']
        custom_chart = None
        if not custom_data.empty:
            custom_chart = px.bar(
                custom_data.head(10), 
                x='sales_count', 
                y='product_name',
                title=f'{time_period} - 定制商品销售排行 (Top 10)',
                orientation='h',
                color_discrete_sequence=['#ED8936']
            )
            custom_chart.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis_title="销售数量",
                yaxis_title="商品名称"
            )
        
        return {
            'inventory_chart': inventory_chart,
            'custom_chart': custom_chart
        }
    
    def create_customer_activity_charts(self, customer_data: List[Dict], time_period: str) -> Dict[str, Any]:
        """
        创建客户活跃度分析图表
        
        Args:
            customer_data: 客户活跃度数据
            time_period: 时间段
            
        Returns:
            包含客户活跃度图表的字典
        """
        if not customer_data:
            return {'activity_chart': None}
        
        df_customer = pd.DataFrame(customer_data)
        
        # 客户订单频率分析
        activity_chart = px.bar(
            df_customer, 
            x='order_count', 
            y='customer_name',
            title=f'{time_period} - 客户订单频率分析',
            orientation='h',
            color_discrete_sequence=['#9F7AEA']
        )
        
        activity_chart.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title_font_size=16,
            title_font_color='#2D3748',
            font=dict(color='#2D3748'),
            xaxis_title="订单数量",
            yaxis_title="客户姓名"
        )
        
        return {'activity_chart': activity_chart}
    
    def refresh_cache(self):
        """刷新缓存"""
        self.db.clear_cache()