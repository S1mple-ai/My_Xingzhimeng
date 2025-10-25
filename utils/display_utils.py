"""
显示工具函数 - 统一处理NULL值和已删除数据的显示
提供安全的字段访问和格式化功能，确保用户界面的一致性
"""

def safe_get(item, field, default="未知"):
    """
    安全获取字典字段值，处理None和缺失字段
    
    Args:
        item: 字典对象
        field: 字段名
        default: 默认值
    
    Returns:
        字段值或默认值
    """
    if not item:
        return default
    
    value = item.get(field)
    return value if value is not None else default


def format_item_display(item, item_type="商品"):
    """
    格式化商品显示名称
    
    Args:
        item: 订单项字典
        item_type: 商品类型（"现货"、"定制"等）
    
    Returns:
        格式化后的商品名称
    """
    if not item:
        return f"未知{item_type}"
    
    # 优先使用inventory_name，如果为空则使用备用显示
    name = item.get('inventory_name')
    if name:
        return name
    
    # 如果有inventory_id但没有name，说明商品已被删除
    if item.get('inventory_id'):
        return f"已删除的{item_type}"
    
    # 完全没有关联，可能是纯定制商品
    return f"定制{item_type}" if item_type == "商品" else item_type


def format_fabric_display(item, fabric_type):
    """
    格式化面料显示名称
    
    Args:
        item: 订单项字典
        fabric_type: 面料类型（"outer"表布 或 "inner"里布）
    
    Returns:
        格式化后的面料名称，如果没有面料则返回None
    """
    if not item:
        return None
    
    fabric_name_field = f"{fabric_type}_fabric_name"
    fabric_id_field = f"{fabric_type}_fabric_id"
    
    fabric_name = item.get(fabric_name_field)
    fabric_id = item.get(fabric_id_field)
    
    # 如果有面料名称，直接返回
    if fabric_name:
        return fabric_name
    
    # 如果有面料ID但没有名称，说明面料已被删除
    if fabric_id:
        return "已删除的面料"
    
    # 没有面料信息
    return None


def format_customer_display(order):
    """
    格式化客户显示名称
    
    Args:
        order: 订单字典
    
    Returns:
        格式化后的客户名称
    """
    if not order:
        return "未知客户"
    
    # 优先使用客户名称快照（订单创建时的客户名称）
    customer_name_snapshot = order.get('customer_name_snapshot')
    if customer_name_snapshot and customer_name_snapshot != 'None':
        return customer_name_snapshot
    
    # 如果没有快照，使用当前客户名称
    customer_name = order.get('customer_name')
    if customer_name and customer_name != 'None':
        return customer_name
    
    # 如果有customer_id但没有name，说明客户已被删除
    if order.get('customer_id'):
        return "已删除的客户"
    
    return "未知客户"


def format_order_item_line(item):
    """
    格式化订单项的完整显示行
    
    Args:
        item: 订单项字典
    
    Returns:
        格式化后的订单项显示字符串
    """
    if not item:
        return "• 无效商品项"
    
    # 获取商品名称
    item_name = format_item_display(item)
    quantity = item.get('quantity', 0)
    unit_price = item.get('unit_price', 0)
    total_price = quantity * unit_price
    item_type = item.get('item_type', '未知')
    
    # 基础信息行
    base_line = f"• {item_type}: {item_name} × {quantity} = ¥{total_price:.2f}"
    
    # 面料信息（仅定制商品）
    fabric_lines = []
    if item_type == '定制':
        outer_fabric = format_fabric_display(item, 'outer')
        inner_fabric = format_fabric_display(item, 'inner')
        
        if outer_fabric:
            fabric_lines.append(f"  表布: {outer_fabric}")
        if inner_fabric:
            fabric_lines.append(f"  里布: {inner_fabric}")
    
    # 备注信息
    notes = item.get('notes')
    if notes:
        fabric_lines.append(f"  备注: {notes}")
    
    # 组合所有行
    all_lines = [base_line] + fabric_lines
    return '\n'.join(all_lines)


def format_processor_display(order):
    """
    格式化代加工商显示名称
    
    Args:
        order: 代加工订单字典
    
    Returns:
        格式化后的代加工商名称
    """
    if not order:
        return "未知代加工商"
    
    processor_name = order.get('processor_name')
    if processor_name:
        return processor_name
    
    # 如果有processor_id但没有name，说明代加工商已被删除
    if order.get('processor_id'):
        return "已删除的代加工商"
    
    return "未知代加工商"


# 常用的默认值常量
DEFAULT_VALUES = {
    'item_name': '已删除的商品',
    'fabric_name': '已删除的面料',
    'customer_name': '已删除的客户',
    'processor_name': '已删除的代加工商',
    'unknown_item': '未知商品',
    'unknown_fabric': '未知面料',
    'unknown_customer': '未知客户',
    'unknown_processor': '未知代加工商'
}