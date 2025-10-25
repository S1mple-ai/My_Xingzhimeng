"""
订单打印服务

专门用于生成小尺寸（76mm*130mm）的订单打印PDF
适用于热敏打印机或标签打印机
"""

import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class PrintService:
    """订单打印服务类"""
    
    # 页面尺寸：76mm x 130mm
    PAGE_WIDTH = 76 * mm
    PAGE_HEIGHT = 130 * mm
    
    # 边距
    MARGIN = 5 * mm
    
    # 可用区域
    CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
    CONTENT_HEIGHT = PAGE_HEIGHT - 2 * MARGIN
    
    def __init__(self, db_manager):
        """
        初始化打印服务
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
        self._setup_fonts()
    
    def _setup_fonts(self):
        """设置中文字体"""
        try:
            # 尝试注册系统中文字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.chinese_font = 'ChineseFont'
                        return
                    except:
                        continue
            
            # 如果没有找到中文字体，使用默认字体
            self.chinese_font = 'Helvetica'
            
        except Exception as e:
            print(f"字体设置失败: {e}")
            self.chinese_font = 'Helvetica'
    
    def generate_orders_print_pdf(self, order_ids: List[int]) -> bytes:
        """
        生成批量订单打印PDF
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            PDF文件的字节数据
        """
        if not order_ids:
            raise ValueError("订单ID列表不能为空")
        
        # 创建内存中的PDF
        buffer = io.BytesIO()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(self.PAGE_WIDTH, self.PAGE_HEIGHT),
            leftMargin=self.MARGIN,
            rightMargin=self.MARGIN,
            topMargin=self.MARGIN,
            bottomMargin=self.MARGIN
        )
        
        # 获取订单数据
        orders_data = self._get_orders_print_data(order_ids)
        
        # 构建PDF内容
        story = []
        
        for i, order_data in enumerate(orders_data):
            if i > 0:
                # 添加分页符（除了第一页）
                story.append(PageBreak())
            
            # 添加单个订单的内容
            order_content = self._create_order_print_content(order_data)
            story.extend(order_content)
        
        # 生成PDF
        doc.build(story)
        
        # 获取PDF数据
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def _get_orders_print_data(self, order_ids: List[int]) -> List[Dict[str, Any]]:
        """
        获取订单打印数据
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            订单数据列表
        """
        orders_data = []
        
        for order_id in order_ids:
            # 获取订单基本信息
            order = self.db.get_order_by_id(order_id)
            if not order:
                continue
            
            # 获取客户信息
            customers = self.db.get_customers()
            customer = next((c for c in customers if c['id'] == order['customer_id']), None)
            
            # 获取订单商品
            order_items = self.db.get_order_items(order_id)
            
            # 分类商品
            inventory_items = []
            custom_items = []
            
            for item in order_items:
                if item['item_type'] == '现货':
                    inventory_items.append(item)
                else:
                    custom_items.append(item)
            
            orders_data.append({
                'order': order,
                'customer': customer,
                'inventory_items': inventory_items,
                'custom_items': custom_items
            })
        
        return orders_data
    
    def _create_order_print_content(self, order_data: Dict[str, Any]) -> List:
        """
        创建单个订单的打印内容
        
        Args:
            order_data: 订单数据
            
        Returns:
            PDF内容元素列表
        """
        content = []
        order = order_data['order']
        customer = order_data['customer']
        inventory_items = order_data['inventory_items']
        custom_items = order_data['custom_items']
        
        # 样式设置
        styles = getSampleStyleSheet()
        
        # 标题
        title_style = styles['Title'].clone('TitleStyle')
        title_style.fontName = self.chinese_font
        title_style.fontSize = 12
        title_style.alignment = 1  # 居中
        
        content.append(Paragraph("订单详情", title_style))
        content.append(Spacer(1, 3 * mm))
        
        # 客户信息
        customer_style = styles['Normal'].clone('CustomerStyle')
        customer_style.fontName = self.chinese_font
        customer_style.fontSize = 9
        
        # 使用安全的客户信息显示
        from utils.display_utils import safe_get
        customer_name = safe_get(customer, 'nickname', '未知客户') if customer else '未知客户'
        customer_phone = safe_get(customer, 'phone_suffix', '无') if customer else '无'
        
        content.append(Paragraph(f"客户：{customer_name}", customer_style))
        content.append(Paragraph(f"手机尾号：{customer_phone}", customer_style))
        content.append(Spacer(1, 2 * mm))
        
        # 订单基本信息
        order_style = styles['Normal'].clone('OrderStyle')
        order_style.fontName = self.chinese_font
        order_style.fontSize = 8
        
        order_date = order['created_at'][:10] if order['created_at'] else '未知'
        content.append(Paragraph(f"订单号：{order['id']}", order_style))
        content.append(Paragraph(f"日期：{order_date}", order_style))
        content.append(Spacer(1, 3 * mm))
        
        # 导入统一显示工具
        from utils.display_utils import format_item_display, format_fabric_display
        
        # 现货商品
        if inventory_items:
            content.append(Paragraph("现货商品：", order_style))
            
            for item in inventory_items:
                item_name = format_item_display(item, "现货")
                quantity = item['quantity']
                unit_price = item['unit_price']
                subtotal = quantity * unit_price
                
                item_text = f"• {item_name} × {quantity} = ¥{subtotal:.2f}"
                content.append(Paragraph(item_text, order_style))
            
            content.append(Spacer(1, 2 * mm))
        
        # 定制商品
        if custom_items:
            content.append(Paragraph("定制商品：", order_style))
            
            for item in custom_items:
                item_name = format_item_display(item, "定制")
                quantity = item['quantity']
                unit_price = item['unit_price']
                subtotal = quantity * unit_price
                
                item_text = f"• {item_name} × {quantity} = ¥{subtotal:.2f}"
                content.append(Paragraph(item_text, order_style))
                
                # 面料信息
                outer_fabric = format_fabric_display(item, 'outer')
                if outer_fabric:
                    content.append(Paragraph(f"  表布：{outer_fabric}", order_style))
                    
                inner_fabric = format_fabric_display(item, 'inner')
                if inner_fabric:
                    content.append(Paragraph(f"  里布：{inner_fabric}", order_style))
                
                # 定制备注
                if item.get('notes'):
                    content.append(Paragraph(f"  备注：{item['notes']}", order_style))
            
            content.append(Spacer(1, 2 * mm))
        
        # 订单备注
        if order.get('notes'):
            content.append(Paragraph(f"订单备注：{order['notes']}", order_style))
            content.append(Spacer(1, 2 * mm))
        
        # 订单总价
        total_style = styles['Normal'].clone('TotalStyle')
        total_style.fontName = self.chinese_font
        total_style.fontSize = 10
        total_style.alignment = 1  # 居中
        
        total_amount = order['total_amount']
        content.append(Paragraph(f"总价：¥{total_amount:.2f}", total_style))
        
        return content
    
    def get_print_filename(self, order_ids: List[int]) -> str:
        """
        生成打印文件名
        
        Args:
            order_ids: 订单ID列表
            
        Returns:
            文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if len(order_ids) == 1:
            return f"订单打印_{order_ids[0]}_{timestamp}.pdf"
        else:
            return f"批量订单打印_{len(order_ids)}个订单_{timestamp}.pdf"