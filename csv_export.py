import csv
import io
import pandas as pd
from typing import List, Dict
from datetime import datetime
import streamlit as st

def safe_format_currency(value, default=0.0):
    """安全的货币格式化函数，处理None值"""
    if value is None:
        value = default
    try:
        return f"¥{float(value):.2f}"
    except (ValueError, TypeError):
        return f"¥{default:.2f}"

def safe_multiply(a, b, default=0.0):
    """安全的乘法运算，处理None值"""
    if a is None or b is None:
        return default
    try:
        return float(a) * float(b)
    except (ValueError, TypeError):
        return default

def export_orders_to_csv_optimized(orders_with_items: Dict[int, Dict]) -> str:
    """
    将订单数据导出为CSV格式（优化版本）
    字段：客户昵称、手机尾号、订单号、现货商品、数量、单价、定制商品、数量、单价、定制商品备注、订单备注、订单总价
    
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
        
        # 分离现货和定制商品
        stock_items = [item for item in order_items if item.get('item_type') == '现货']
        custom_items = [item for item in order_items if item.get('item_type') == '定制']
        
        # 获取客户信息
        customer_name = order_data.get('customer_name', '')
        phone_suffix = order_data.get('customer_phone_suffix', '')  # 需要从数据库获取
        order_notes = order_data.get('notes', '')
        total_amount = safe_format_currency(order_data.get('total_amount'))
        
        # 如果没有任何商品，创建一行空记录
        if not order_items:
            csv_data.append({
                '客户昵称': customer_name,
                '手机尾号': phone_suffix,
                '订单号': order_data['id'],
                '现货商品': '',
                '现货数量': '',
                '现货单价': '',
                '定制商品': '',
                '定制数量': '',
                '定制单价': '',
                '定制商品备注': '',
                '订单备注': order_notes,
                '订单总价': total_amount
            })
        else:
            # 计算需要的行数（取现货和定制商品的最大数量）
            max_rows = max(len(stock_items), len(custom_items), 1)
            
            for j in range(max_rows):
                # 现货商品信息
                stock_name = stock_items[j].get('inventory_name', '') if j < len(stock_items) else ''
                stock_quantity = stock_items[j].get('quantity', '') if j < len(stock_items) else ''
                stock_price = safe_format_currency(stock_items[j].get('unit_price')) if j < len(stock_items) else ''
                
                # 定制商品信息
                if j < len(custom_items):
                    custom_item = custom_items[j]
                    custom_name = custom_item.get('inventory_name', '')
                    # 如果有面料信息，添加到商品名称中
                    if custom_item.get('outer_fabric_name') or custom_item.get('inner_fabric_name'):
                        fabric_info = []
                        if custom_item.get('outer_fabric_name'):
                            fabric_info.append(f"表布:{custom_item['outer_fabric_name']}")
                        if custom_item.get('inner_fabric_name'):
                            fabric_info.append(f"里布:{custom_item['inner_fabric_name']}")
                        custom_name += f"({','.join(fabric_info)})"
                    
                    custom_quantity = custom_item.get('quantity', '')
                    custom_price = safe_format_currency(custom_item.get('unit_price'))
                    custom_notes = custom_item.get('notes', '')
                else:
                    custom_name = custom_quantity = custom_price = custom_notes = ''
                
                # 只在第一行显示订单信息
                row_customer_name = customer_name if j == 0 else ''
                row_phone_suffix = phone_suffix if j == 0 else ''
                row_order_id = order_data['id'] if j == 0 else ''
                row_order_notes = order_notes if j == 0 else ''
                row_total_amount = total_amount if j == 0 else ''
                
                csv_data.append({
                    '客户昵称': row_customer_name,
                    '手机尾号': row_phone_suffix,
                    '订单号': row_order_id,
                    '现货商品': stock_name,
                    '现货数量': stock_quantity,
                    '现货单价': stock_price,
                    '定制商品': custom_name,
                    '定制数量': custom_quantity,
                    '定制单价': custom_price,
                    '定制商品备注': custom_notes,
                    '订单备注': row_order_notes,
                    '订单总价': row_total_amount
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
    将订单数据导出为CSV格式（按照新的字段要求）
    字段：客户昵称、手机尾号、订单号、现货商品、数量、单价、定制商品、数量、单价、定制商品备注、订单备注、订单总价
    
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
        
        # 分离现货和定制商品
        stock_items = [item for item in order_items if item.get('item_type') == '现货']
        custom_items = [item for item in order_items if item.get('item_type') == '定制']
        
        # 获取客户信息
        customer_name = order.get('customer_name', '')
        phone_suffix = order.get('customer_phone_suffix', '')  # 需要从数据库获取
        order_notes = order.get('notes', '')
        total_amount = safe_format_currency(order.get('total_amount'))
        
        # 如果没有任何商品，创建一行空记录
        if not order_items:
            csv_data.append({
                '客户昵称': customer_name,
                '手机尾号': phone_suffix,
                '订单号': order['id'],
                '现货商品': '',
                '现货数量': '',
                '现货单价': '',
                '定制商品': '',
                '定制数量': '',
                '定制单价': '',
                '定制商品备注': '',
                '订单备注': order_notes,
                '订单总价': total_amount
            })
        else:
            # 计算需要的行数（取现货和定制商品的最大数量）
            max_rows = max(len(stock_items), len(custom_items), 1)
            
            for j in range(max_rows):
                # 现货商品信息
                stock_name = stock_items[j].get('inventory_name', '') if j < len(stock_items) else ''
                stock_quantity = stock_items[j].get('quantity', '') if j < len(stock_items) else ''
                stock_price = safe_format_currency(stock_items[j].get('unit_price')) if j < len(stock_items) else ''
                
                # 定制商品信息
                if j < len(custom_items):
                    custom_item = custom_items[j]
                    custom_name = custom_item.get('inventory_name', '')
                    # 如果有面料信息，添加到商品名称中
                    if custom_item.get('outer_fabric_name') or custom_item.get('inner_fabric_name'):
                        fabric_info = []
                        if custom_item.get('outer_fabric_name'):
                            fabric_info.append(f"表布:{custom_item['outer_fabric_name']}")
                        if custom_item.get('inner_fabric_name'):
                            fabric_info.append(f"里布:{custom_item['inner_fabric_name']}")
                        custom_name += f"({','.join(fabric_info)})"
                    
                    custom_quantity = custom_item.get('quantity', '')
                    custom_price = safe_format_currency(custom_item.get('unit_price'))
                    custom_notes = custom_item.get('notes', '')
                else:
                    custom_name = custom_quantity = custom_price = custom_notes = ''
                
                # 只在第一行显示订单信息
                row_customer_name = customer_name if j == 0 else ''
                row_phone_suffix = phone_suffix if j == 0 else ''
                row_order_id = order['id'] if j == 0 else ''
                row_order_notes = order_notes if j == 0 else ''
                row_total_amount = total_amount if j == 0 else ''
                
                csv_data.append({
                    '客户昵称': row_customer_name,
                    '手机尾号': row_phone_suffix,
                    '订单号': row_order_id,
                    '现货商品': stock_name,
                    '现货数量': stock_quantity,
                    '现货单价': stock_price,
                    '定制商品': custom_name,
                    '定制数量': custom_quantity,
                    '定制单价': custom_price,
                    '定制商品备注': custom_notes,
                    '订单备注': row_order_notes,
                    '订单总价': row_total_amount
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