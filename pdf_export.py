"""
PDF导出功能模块
支持将订单数据导出为PDF格式，尺寸为76mm*130mm，适合打印
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from typing import List, Dict

# 自定义页面尺寸 76mm x 130mm
CUSTOM_PAGE_SIZE = (76 * mm, 130 * mm)

def register_chinese_font():
    """注册中文字体"""
    try:
        # 尝试注册系统中的中文字体
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
        
        # 如果没有找到中文字体，使用默认字体
        return 'Helvetica'
    except Exception:
        return 'Helvetica'

def safe_format_currency(value):
    """安全格式化货币值"""
    if value is None:
        return "0.00"
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"

def safe_multiply(price, quantity):
    """安全计算乘积"""
    if price is None or quantity is None:
        return 0.0
    try:
        return float(price) * float(quantity)
    except (ValueError, TypeError):
        return 0.0

def create_order_pdf(orders: List[Dict], order_items_dict: Dict) -> bytes:
    """
    创建订单PDF
    
    Args:
        orders: 订单列表
        order_items_dict: 订单项字典，key为order_id，value为订单项列表
    
    Returns:
        PDF文件的字节数据
    """
    buffer = io.BytesIO()
    
    # 创建PDF文档，使用自定义页面尺寸
    doc = SimpleDocTemplate(
        buffer,
        pagesize=CUSTOM_PAGE_SIZE,
        rightMargin=5*mm,
        leftMargin=5*mm,
        topMargin=5*mm,
        bottomMargin=5*mm
    )
    
    # 注册中文字体
    font_name = register_chinese_font()
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=3*mm
    )
    
    # 正文样式
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=7,
        alignment=TA_LEFT,
        leading=8
    )
    
    # 小字体样式
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=6,
        alignment=TA_LEFT,
        leading=7
    )
    
    story = []
    
    for order in orders:
        # 添加标题
        title = Paragraph("订单详情", title_style)
        story.append(title)
        story.append(Spacer(1, 2*mm))
        
        # 基本信息表格
        basic_info_data = [
            ['客户昵称:', order.get('customer_name', '未知')],
            ['手机尾号:', order.get('customer_phone_suffix', '未知')],
            ['订单号:', f"#{order.get('id', 'N/A')}"],
            ['订单备注:', order.get('notes', '无') or '无']
        ]
        
        basic_info_table = Table(basic_info_data, colWidths=[15*mm, 45*mm])
        basic_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        
        story.append(basic_info_table)
        story.append(Spacer(1, 3*mm))
        
        # 商品信息
        items = order_items_dict.get(order['id'], [])
        if items:
            # 商品表格标题
            items_title = Paragraph("商品明细", normal_style)
            story.append(items_title)
            story.append(Spacer(1, 1*mm))
            
            # 分类商品
            spot_items = []
            custom_items = []
            
            for item in items:
                if item.get('item_type') == '现货':
                    spot_items.append(item)
                elif item.get('item_type') == '定制':
                    custom_items.append(item)
            
            # 现货商品
            if spot_items:
                spot_title = Paragraph("现货商品:", small_style)
                story.append(spot_title)
                
                for item in spot_items:
                    item_data = [
                        ['商品:', item.get('inventory_name', '未知商品')],
                        ['数量:', str(item.get('quantity', 0))],
                        ['单价:', f"¥{safe_format_currency(item.get('unit_price'))}"],
                        ['小计:', f"¥{safe_format_currency(safe_multiply(item.get('unit_price'), item.get('quantity')))}"]
                    ]
                    
                    item_table = Table(item_data, colWidths=[12*mm, 48*mm])
                    item_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), 6),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 1),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
                    ]))
                    
                    story.append(item_table)
                    story.append(Spacer(1, 1*mm))
            
            # 定制商品
            if custom_items:
                custom_title = Paragraph("定制商品:", small_style)
                story.append(custom_title)
                
                for item in custom_items:
                    item_data = [
                        ['商品:', item.get('inventory_name', '定制商品')],
                        ['数量:', str(item.get('quantity', 0))],
                        ['单价:', f"¥{safe_format_currency(item.get('unit_price'))}"],
                        ['表布:', item.get('outer_fabric_name', '无')],
                        ['里布:', item.get('inner_fabric_name', '无')],
                        ['备注:', item.get('notes', '无') or '无'],
                        ['小计:', f"¥{safe_format_currency(safe_multiply(item.get('unit_price'), item.get('quantity')))}"]
                    ]
                    
                    item_table = Table(item_data, colWidths=[12*mm, 48*mm])
                    item_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), font_name),
                        ('FONTSIZE', (0, 0), (-1, -1), 6),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 1),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
                    ]))
                    
                    story.append(item_table)
                    story.append(Spacer(1, 1*mm))
        
        # 总价
        total_data = [
            ['订单总价:', f"¥{safe_format_currency(order.get('total_amount'))}"]
        ]
        
        total_table = Table(total_data, colWidths=[20*mm, 40*mm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        story.append(Spacer(1, 2*mm))
        story.append(total_table)
        
        # 如果不是最后一个订单，添加分页符
        if order != orders[-1]:
            story.append(Spacer(1, 10*mm))  # 添加更多空间来分隔订单
    
    # 构建PDF
    doc.build(story)
    
    # 获取PDF数据
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def export_orders_to_pdf(orders: List[Dict], order_items_dict: Dict) -> bytes:
    """
    导出订单到PDF
    
    Args:
        orders: 订单列表
        order_items_dict: 订单项字典
    
    Returns:
        PDF文件的字节数据
    """
    return create_order_pdf(orders, order_items_dict)