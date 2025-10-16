import csv
import io
import pandas as pd
from typing import List, Dict
from datetime import datetime
import streamlit as st

def export_orders_to_csv_optimized(orders_with_items: Dict[int, Dict]) -> str:
    """
    将订单数据导出为CSV格式（优化版本）
    
    Args:
        orders_with_items: 包含订单及其商品信息的字典
    
    Returns:
        CSV格式的字符串
    """
    # 准备CSV数据
    csv_data = []
    total_orders = len(orders_with_items)
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (order_id, order_data) in enumerate(orders_with_items.items()):
        # 更新进度
        progress = (i + 1) / total_orders
        progress_bar.progress(progress)
        status_text.text(f"正在处理订单 {i + 1}/{total_orders}...")
        
        order_items = order_data.get('items', [])
        
        if not order_items:
            # 如果没有商品，仍然导出订单基本信息
            csv_data.append({
                '订单号': order_data['id'],
                '客户姓名': order_data['customer_name'],
                '订单状态': order_data['status'],
                '订单总金额': f"¥{order_data['total_amount']:.2f}",
                '创建时间': order_data['created_at'],
                '更新时间': order_data['updated_at'],
                '订单备注': order_data['notes'] or '',
                '商品类型': '',
                '商品名称': '',
                '商品数量': '',
                '单价': '',
                '小计': '',
                '表布': '',
                '里布': '',
                '商品备注': ''
            })
        else:
            # 为每个商品创建一行
            for item in order_items:
                csv_data.append({
                    '订单号': order_data['id'],
                    '客户姓名': order_data['customer_name'],
                    '订单状态': order_data['status'],
                    '订单总金额': f"¥{order_data['total_amount']:.2f}",
                    '创建时间': order_data['created_at'],
                    '更新时间': order_data['updated_at'],
                    '订单备注': order_data['notes'] or '',
                    '商品类型': item['item_type'],
                    '商品名称': item.get('inventory_name') or item.get('bag_type_name', ''),
                    '商品数量': item['quantity'],
                    '单价': f"¥{item['unit_price']:.2f}",
                    '小计': f"¥{item['unit_price'] * item['quantity']:.2f}",
                    '表布': item.get('outer_fabric_name', ''),
                    '里布': item.get('inner_fabric_name', ''),
                    '商品备注': item.get('notes', '')
                })
    
    # 更新进度为生成CSV
    status_text.text("正在生成CSV文件...")
    
    # 创建DataFrame并转换为CSV
    df = pd.DataFrame(csv_data)
    
    # 使用StringIO创建CSV字符串
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')  # 使用utf-8-sig确保中文正确显示
    csv_string = output.getvalue()
    output.close()
    
    # 清理进度显示
    progress_bar.empty()
    status_text.empty()
    
    return csv_string

def export_orders_to_csv(orders: List[Dict], order_items_dict: Dict[int, List[Dict]]) -> str:
    """
    将订单数据导出为CSV格式（原版本，保持兼容性）
    
    Args:
        orders: 订单列表
        order_items_dict: 订单商品字典，key为order_id，value为商品列表
    
    Returns:
        CSV格式的字符串
    """
    # 准备CSV数据
    csv_data = []
    
    for order in orders:
        order_id = order['id']
        order_items = order_items_dict.get(order_id, [])
        
        if not order_items:
            # 如果没有商品，仍然导出订单基本信息
            csv_data.append({
                '订单号': order['id'],
                '客户姓名': order['customer_name'],
                '订单状态': order['status'],
                '订单总金额': f"¥{order['total_amount']:.2f}",
                '创建时间': order['created_at'],
                '更新时间': order['updated_at'],
                '订单备注': order['notes'] or '',
                '商品类型': '',
                '商品名称': '',
                '商品数量': '',
                '单价': '',
                '小计': '',
                '表布': '',
                '里布': '',
                '商品备注': ''
            })
        else:
            # 为每个商品创建一行
            for item in order_items:
                csv_data.append({
                    '订单号': order['id'],
                    '客户姓名': order['customer_name'],
                    '订单状态': order['status'],
                    '订单总金额': f"¥{order['total_amount']:.2f}",
                    '创建时间': order['created_at'],
                    '更新时间': order['updated_at'],
                    '订单备注': order['notes'] or '',
                    '商品类型': item['item_type'],
                    '商品名称': item.get('inventory_name') or item.get('bag_type_name', ''),
                    '商品数量': item['quantity'],
                    '单价': f"¥{item['unit_price']:.2f}",
                    '小计': f"¥{item['unit_price'] * item['quantity']:.2f}",
                    '表布': item.get('outer_fabric_name', ''),
                    '里布': item.get('inner_fabric_name', ''),
                    '商品备注': item.get('notes', '')
                })
    
    # 创建DataFrame并转换为CSV
    df = pd.DataFrame(csv_data)
    
    # 使用StringIO创建CSV字符串
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')  # 使用utf-8-sig确保中文正确显示
    csv_string = output.getvalue()
    output.close()
    
    return csv_string

def generate_csv_filename() -> str:
    """生成CSV文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"订单导出_{timestamp}.csv"