"""
仪表板页面组件
提供业务数据分析和可视化功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui_components import create_metric_card, show_warning_message, show_success_message


def render_dashboard_page(db, dashboard_service):
    """
    渲染仪表板页面
    
    Args:
        db: 数据库服务实例
        dashboard_service: 仪表板服务实例
    """
    st.markdown("## 📊 业务数据分析中心")
    
    # 统一时间段选择器 - 放在最顶部
    st.markdown("### ⏰ 分析时间段")
    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = st.selectbox(
            "选择分析时间段",
            ["全部时间", "近一周", "近一月", "近一季度", "近一年"],
            key="global_time_period",
            help="选择时间段后，下方所有分析数据都会基于该时间段进行统计"
        )
    with col2:
        if st.button("🔄 刷新数据", help="重新加载所有分析数据"):
            dashboard_service.refresh_cache()  # 使用服务层刷新缓存
            st.rerun()
    
    # 显示加载状态
    with st.spinner(f"正在加载{time_period}的数据..."):
        # 使用仪表盘服务获取数据
        unified_data = dashboard_service.get_dashboard_data(time_period)
    
    # 关键指标概览
    _render_key_metrics(dashboard_service, unified_data, time_period)
    
    # 销售趋势分析
    _render_sales_trends(dashboard_service, unified_data, time_period)
    
    # 面料使用分析
    _render_fabric_analysis(unified_data, time_period)
    
    # 商品销售分析
    _render_product_analysis(unified_data, time_period)
    
    # 客户活跃度分析
    _render_customer_analysis(unified_data, time_period)
    
    # 库存预警
    _render_inventory_alerts(db)


def _render_key_metrics(dashboard_service, unified_data, time_period):
    """渲染关键指标概览"""
    st.markdown("### 📊 关键指标概览")
    
    # 使用服务层计算关键指标
    key_metrics = dashboard_service.calculate_key_metrics(unified_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            f"{time_period}订单数", 
            str(key_metrics['total_orders']), 
            icon="📋"
        )
    
    with col2:
        create_metric_card(
            f"{time_period}销售额", 
            f"¥{key_metrics['total_amount']:.2f}", 
            icon="💰"
        )
    
    with col3:
        create_metric_card(
            "活跃客户数", 
            str(key_metrics['active_customers']), 
            icon="👥"
        )
    
    with col4:
        create_metric_card(
            "平均订单价值", 
            f"¥{key_metrics['avg_order_value']:.2f}", 
            icon="📊"
        )


def _render_sales_trends(dashboard_service, unified_data, time_period):
    """渲染销售趋势分析"""
    st.markdown("### 📈 销售趋势分析")
    if unified_data['daily_sales']:
        col1, col2 = st.columns(2)
        
        with col1:
            # 使用服务层生成销售趋势图
            fig_trend = dashboard_service.create_sales_trend_chart(
                unified_data['daily_sales'], 
                f'{time_period} - 每日销售额趋势'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with col2:
            # 使用服务层生成订单数量趋势图
            fig_orders = dashboard_service.create_daily_orders_chart(
                unified_data['daily_sales'], 
                f'{time_period} - 每日订单数量'
            )
            st.plotly_chart(fig_orders, use_container_width=True)
    else:
        st.info(f"📊 {time_period}暂无销售数据")


def _render_fabric_analysis(unified_data, time_period):
    """渲染面料使用分析"""
    st.markdown("### 🧵 面料使用分析")
    if unified_data['fabric_usage']:
        col1, col2 = st.columns(2)
        
        with col1:
            # 表布使用情况
            outer_fabric_data = [item for item in unified_data['fabric_usage'] if item['usage_type'] == '表布']
            if outer_fabric_data:
                df_outer = pd.DataFrame(outer_fabric_data)
                fig_outer = px.pie(
                    df_outer, 
                    values='usage_count', 
                    names='fabric_name',
                    title=f'{time_period} - 表布使用分布',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_outer.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=16,
                    title_font_color='#2D3748',
                    font=dict(color='#2D3748')
                )
                st.plotly_chart(fig_outer, use_container_width=True)
            else:
                st.info(f"{time_period}暂无表布使用数据")
        
        with col2:
            # 里布使用情况
            inner_fabric_data = [item for item in unified_data['fabric_usage'] if item['usage_type'] == '里布']
            if inner_fabric_data:
                df_inner = pd.DataFrame(inner_fabric_data)
                fig_inner = px.pie(
                    df_inner, 
                    values='usage_count', 
                    names='fabric_name',
                    title=f'{time_period} - 里布使用分布',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_inner.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=16,
                    title_font_color='#2D3748',
                    font=dict(color='#2D3748')
                )
                st.plotly_chart(fig_inner, use_container_width=True)
            else:
                st.info(f"{time_period}暂无里布使用数据")
    else:
        st.info(f"{time_period}暂无面料使用数据")


def _render_product_analysis(unified_data, time_period):
    """渲染商品销售分析"""
    st.markdown("### 🛍️ 商品销售分析")
    if unified_data['product_sales']:
        col1, col2 = st.columns(2)
        
        with col1:
            # 商品销售排行
            df_products = pd.DataFrame(unified_data['product_sales'])
            fig_products = px.bar(
                df_products.head(10), 
                x='quantity', 
                y='product_name',
                title=f'{time_period} - 商品销售排行',
                orientation='h'
            )
            fig_products.update_traces(
                marker_color='#10B981',
                marker_line_color='#10B981',
                marker_line_width=1
            )
            fig_products.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig_products, use_container_width=True)
        
        with col2:
            # 商品销售额排行
            df_products_amount = df_products.copy()
            df_products_amount = df_products_amount.sort_values('total_amount', ascending=True)
            fig_amount = px.bar(
                df_products_amount.tail(10), 
                x='total_amount', 
                y='product_name',
                title=f'{time_period} - 商品销售额排行',
                orientation='h'
            )
            fig_amount.update_traces(
                marker_color='#8B5CF6',
                marker_line_color='#8B5CF6',
                marker_line_width=1
            )
            fig_amount.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig_amount, use_container_width=True)
    else:
        st.info(f"{time_period}暂无商品销售数据")


def _render_customer_analysis(unified_data, time_period):
    """渲染客户活跃度分析"""
    st.markdown("### 👥 客户活跃度分析")
    if unified_data['customer_activity']:
        col1, col2 = st.columns(2)
        
        with col1:
            # 客户订单频次
            df_customers = pd.DataFrame(unified_data['customer_activity'])
            if not df_customers.empty:
                fig_customers = px.bar(
                    df_customers.head(10), 
                    x='order_count', 
                    y='nickname',
                    title=f'{time_period} - 客户活跃度排行',
                    orientation='h'
                )
                fig_customers.update_traces(
                    marker_color='#EF4444',
                    marker_line_color='#EF4444',
                    marker_line_width=1
                )
                fig_customers.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=16,
                    title_font_color='#2D3748',
                    font=dict(color='#2D3748'),
                    xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                    yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
                )
                st.plotly_chart(fig_customers, use_container_width=True)
            else:
                st.info(f"{time_period}暂无客户活跃数据")
        
        with col2:
            # 客户消费金额排行
            df_customers_amount = df_customers.copy()
            df_customers_amount = df_customers_amount.sort_values('total_spent', ascending=True)
            fig_customer_amount = px.bar(
                df_customers_amount.tail(10), 
                x='total_spent', 
                y='nickname',
                title=f'{time_period} - 客户消费金额排行',
                orientation='h'
            )
            fig_customer_amount.update_traces(
                marker_color='#F59E0B',
                marker_line_color='#F59E0B',
                marker_line_width=1
            )
            fig_customer_amount.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig_customer_amount, use_container_width=True)
    else:
        st.info(f"{time_period}暂无客户活跃数据")


def _render_inventory_alerts(db):
    """渲染库存预警"""
    st.markdown("### ⚠️ 库存预警")
    inventory_items = db.get_inventory_items()
    low_stock_items = [item for item in inventory_items if item['quantity'] < 5]
    if low_stock_items:
        show_warning_message(f"发现 {len(low_stock_items)} 个商品库存不足！")
        df_low_stock = pd.DataFrame(low_stock_items)
        st.dataframe(
            df_low_stock[['product_name', 'quantity', 'price']], 
            use_container_width=True,
            column_config={
                "product_name": "商品名称",
                "quantity": st.column_config.NumberColumn(
                    "库存数量",
                    help="当前库存数量",
                    format="%d 件"
                ),
                "price": st.column_config.NumberColumn(
                    "单价",
                    help="商品单价",
                    format="¥%.2f"
                )
            }
        )
    else:
        show_success_message("所有商品库存充足")