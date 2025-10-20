"""
页面组件模块

这个模块包含了应用程序的所有页面组件，每个页面都被提取为独立的组件函数。
这样的设计提高了代码的可维护性和可读性。
"""

# 页面组件导入（将在实现后逐步添加）
from .dashboard_page import render_dashboard_page
from .customer_page import render_customer_page
from .fabric_page import render_fabric_page
from .inventory_page import render_inventory_page
from .order_page import render_order_page
from .settings_page import render_settings_page

__all__ = [
    'render_dashboard_page', 
    'render_customer_page', 
    'render_fabric_page',
    'render_inventory_page',
    'render_order_page',
    'render_settings_page'
]