import streamlit as st
import time
import os
import base64
from typing import Optional, List, Dict, Any

def get_image_base64(image_path: str) -> str:
    """将图片文件转换为base64编码字符串
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的图片字符串
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"读取图片失败: {e}")
        return ""

def show_loading_spinner(text: str = "加载中..."):
    """显示加载动画"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 2rem;">
        <div class="loading-spinner"></div>
        <span style="margin-left: 1rem; font-size: 1.1rem; color: var(--text-dark);">{text}</span>
    </div>
    """, unsafe_allow_html=True)

def show_progress_bar(progress: float, text: str = ""):
    """显示进度条
    
    Args:
        progress: 进度值 (0-100)
        text: 进度文本
    """
    progress = max(0, min(100, progress))  # 确保在0-100范围内
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        {f'<div style="margin-bottom: 0.5rem; font-weight: 600;">{text}</div>' if text else ''}
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%;"></div>
        </div>
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-dark);">
            {progress:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_success_message(message: str, icon: str = "✅"):
    """显示成功消息"""
    st.markdown(f"""
    <div class="success-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_error_message(message: str, icon: str = "❌"):
    """显示错误消息"""
    st.markdown(f"""
    <div class="error-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_warning_message(message: str, icon: str = "⚠️"):
    """显示警告消息"""
    st.markdown(f"""
    <div class="warning-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_info_card(title: str, content: str, icon: str = "ℹ️"):
    """显示信息卡片"""
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="margin: 0 0 1rem 0; color: var(--primary-color);">
            {icon} {title}
        </h4>
        <p style="margin: 0; color: var(--text-dark);">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: Optional[str] = None, icon: str = "📊"):
    """创建指标卡片"""
    delta_html = ""
    if delta:
        delta_color = "var(--success-color)" if not delta.startswith("-") else "var(--error-color)"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: var(--text-dark);">{title}</h4>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def create_action_button(text: str, key: str, icon: str = "", variant: str = "primary"):
    """创建动作按钮
    
    Args:
        text: 按钮文本
        key: 按钮key
        icon: 图标
        variant: 按钮变体 (primary, secondary, success, warning, error)
    """
    try:
        button_text = f"{icon} {text}" if icon else text
        
        # 根据变体设置样式
        if variant == "secondary":
            style = "background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));"
        elif variant == "success":
            style = "background: linear-gradient(135deg, var(--success-color), #00B894);"
        elif variant == "warning":
            style = "background: linear-gradient(135deg, var(--warning-color), #FDCB6E);"
        elif variant == "error":
            style = "background: linear-gradient(135deg, var(--error-color), #E84393);"
        else:
            style = ""
        
        if style:
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button[key="{key}"] {{
                {style}
            }}
            </style>
            """, unsafe_allow_html=True)
        
        return st.button(button_text, key=key)
    except Exception as e:
        st.error(f"按钮创建失败: {str(e)}")
        return False

def create_data_table(data: List[Dict[str, Any]], columns: List[str], title: str = ""):
    """创建数据表格
    
    Args:
        data: 数据列表
        columns: 列名列表
        title: 表格标题
    """
    if title:
        st.markdown(f"### 📋 {title}")
    
    if not data:
        st.info("暂无数据")
        return
    
    # 转换为DataFrame并显示
    import pandas as pd
    df = pd.DataFrame(data)
    
    # 只显示指定的列
    if columns:
        df = df[columns]
    
    st.dataframe(df, use_container_width=True)

def create_confirmation_dialog(message: str, key: str) -> bool:
    """创建确认对话框
    
    Args:
        message: 确认消息
        key: 组件key
        
    Returns:
        bool: 用户是否确认
    """
    st.markdown(f"""
    <div class="warning-message">
        <strong>⚠️ 确认操作</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = create_action_button("确认", f"confirm_{key}", "✅", "success")
    with col2:
        cancel = create_action_button("取消", f"cancel_{key}", "❌", "error")
    
    return confirm

def simulate_loading(duration: float = 2.0, steps: int = 10):
    """模拟加载过程
    
    Args:
        duration: 总持续时间（秒）
        steps: 进度步数
    """
    progress_placeholder = st.empty()
    
    for i in range(steps + 1):
        progress = (i / steps) * 100
        with progress_placeholder.container():
            show_progress_bar(progress, f"处理中... ({i}/{steps})")
        time.sleep(duration / steps)
    
    progress_placeholder.empty()

def create_tooltip(text: str, tooltip_text: str):
    """创建带工具提示的文本
    
    Args:
        text: 显示文本
        tooltip_text: 工具提示文本
    """
    st.markdown(f"""
    <div class="tooltip">
        {text}
        <span class="tooltiptext">{tooltip_text}</span>
    </div>
    """, unsafe_allow_html=True)

def create_ecommerce_card(item_data: dict, card_type: str = "fabric", key_prefix: str = "", on_edit=None, on_view=None, on_delete=None):
    """创建电商风格的卡片预览
    
    Args:
        item_data: 项目数据字典
        card_type: 卡片类型 ("fabric" 或 "inventory")
        key_prefix: 组件key前缀
        on_edit: 编辑按钮回调函数
        on_view: 查看详情按钮回调函数
        on_delete: 删除按钮回调函数
    """
    # 增强的卡片样式CSS
    card_css = """
    <style>
    .ecommerce-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 24px;
        border: 1px solid #f0f0f0;
        position: relative;
        cursor: pointer;
    }
    .ecommerce-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        border-color: #e0e0e0;
    }
    .card-image-container {
        position: relative;
        width: 100%;
        height: 200px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .card-image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    .ecommerce-card:hover .card-image-container img {
        transform: scale(1.05);
    }
    .image-placeholder {
        color: #999;
        font-size: 48px;
        text-align: center;
    }
    .card-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(102,126,234,0.9);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        backdrop-filter: blur(10px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        z-index: 10;
    }
    .card-content {
        padding: 20px;
        background: white;
    }
    .card-title {
        font-size: 18px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 12px;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-field {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding: 6px 0;
        border-bottom: 1px solid #f8f9fa;
    }
    .card-field:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    .field-label {
        font-size: 14px;
        color: #666;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .field-value {
        font-size: 14px;
        color: #333;
        font-weight: 600;
        text-align: right;
        max-width: 60%;
        word-wrap: break-word;
    }
    .price-tag {
        background: linear-gradient(135deg, #00c851 0%, #007e33 100%);
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
        box-shadow: 0 2px 8px rgba(0,200,81,0.3);
    }
    .card-actions {
        padding: 16px 20px;
        background: #f8f9fa;
        border-top: 1px solid #e9ecef;
        display: flex;
        gap: 8px;
        justify-content: space-between;
    }
    .action-btn {
        flex: 1;
        padding: 8px 12px;
        border: none;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        text-decoration: none;
    }
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102,126,234,0.4);
    }
    .btn-secondary {
        background: white;
        color: #666;
        border: 1px solid #ddd;
    }
    .btn-secondary:hover {
        background: #f8f9fa;
        border-color: #ccc;
    }
    .btn-danger {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
    }
    .btn-danger:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,107,107,0.4);
    }
    .stock-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    .stock-high { background: #e8f5e8; color: #2e7d32; }
    .stock-medium { background: #fff3e0; color: #f57c00; }
    .stock-low { background: #ffebee; color: #d32f2f; }
    </style>
    """
    
    st.markdown(card_css, unsafe_allow_html=True)
    
    # 获取图片路径
    image_path = item_data.get('image_path', '')
    
    # 处理图片显示和徽章
    badge_html = ""
    
    # 根据卡片类型添加徽章
    if card_type == "fabric":
        badge_html = '<div class="card-badge">🧵 面料</div>'
    elif card_type == "inventory":
        stock_status = "有库存" if item_data.get('quantity', 0) > 0 else "缺货"
        badge_color = "#00c851" if item_data.get('quantity', 0) > 0 else "#ff6b6b"
        badge_html = f'<div class="card-badge" style="background: {badge_color}; color: white;">📦 {stock_status}</div>'
    
    # 构建内容部分
    content_html = ""  # 初始化变量
    
    if card_type == "fabric":
        # 面料卡片内容
        content_html = f"""
        <div class="card-content">
            <div class="card-title">{item_data.get('name', '未命名面料')}</div>
            <div class="card-field">
                <span class="field-label">🧵 材质类型</span>
                <span class="field-value">{item_data.get('material_type', '未指定')}</span>
            </div>
            <div class="card-field">
                <span class="field-label">🎯 用途类型</span>
                <span class="field-value">{item_data.get('usage_type', '未指定')}</span>
            </div>
            <div class="card-field">
                <span class="field-label">🏷️ 面料ID</span>
                <span class="field-value">#{item_data.get('id', 'N/A')}</span>
            </div>
        </div>
        """
    elif card_type == "inventory":
        # 库存卡片内容
        quantity = item_data.get('quantity', 0)
        price = item_data.get('price', 0)
        
        # 库存状态
        if quantity > 50:
            stock_class = "stock-high"
            stock_text = "库存充足"
            stock_emoji = "✅"
        elif quantity > 10:
            stock_class = "stock-medium"
            stock_text = "库存适中"
            stock_emoji = "⚠️"
        else:
            stock_class = "stock-low"
            stock_text = "库存不足"
            stock_emoji = "❌"
        
        content_html = f"""
        <div class="card-content">
            <div class="card-title">{item_data.get('product_name', '未命名商品')}</div>
            <div class="card-field">
                <span class="field-label">📝 商品描述</span>
                <span class="field-value">{item_data.get('description', '暂无描述')[:30]}{'...' if len(item_data.get('description', '')) > 30 else ''}</span>
            </div>
            <div class="card-field">
                <span class="field-label">💰 价格</span>
                <span class="field-value price-tag">¥{price:.2f}</span>
            </div>
            <div class="card-field">
                <span class="field-label">{stock_emoji} 库存状态</span>
                <span class="field-value stock-badge {stock_class}">{stock_text} ({quantity})</span>
            </div>
            <div class="card-field">
                <span class="field-label">🏷️ 商品ID</span>
                <span class="field-value">#{item_data.get('id', 'N/A')}</span>
            </div>
        </div>
        """
    else:
        # 默认内容
        content_html = f"""
        <div class="card-content">
            <div class="card-title">未知类型</div>
            <div class="card-field">
                <span class="field-label">类型</span>
                <span class="field-value">{card_type}</span>
            </div>
        </div>
        """
        
    # 使用容器来组织卡片布局
    with st.container():
        # 添加卡片容器的开始
        st.markdown(f'<div class="ecommerce-card">', unsafe_allow_html=True)
        
        # 图片部分 - 修复图片显示问题
        if image_path and os.path.exists(image_path):
            # 图片容器和图片一起显示
            st.markdown(f'''
            <div class="card-image-container" style="position: relative;">
                {badge_html}
            </div>
            ''', unsafe_allow_html=True)
            # 使用Streamlit原生图片组件，确保在容器内显示
            try:
                st.image(image_path, use_column_width=True)
            except Exception as e:
                # 如果图片加载失败，显示占位符
                st.markdown(f'''
                <div class="card-image-container">
                    <div class="image-placeholder">🖼️ 图片加载失败</div>
                    {badge_html}
                </div>
                ''', unsafe_allow_html=True)
        else:
            # 占位符
            st.markdown(f'''
            <div class="card-image-container">
                <div class="image-placeholder">📷 暂无图片</div>
                {badge_html}
            </div>
            ''', unsafe_allow_html=True)
        
        # 添加内容部分
        st.markdown(content_html, unsafe_allow_html=True)
        
        # 添加交互按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 编辑", key=f"{key_prefix}_edit_{item_data.get('id', 'unknown')}", use_container_width=True):
                st.session_state[f"show_edit_modal_{key_prefix}_{item_data.get('id')}"] = True
                st.session_state[f"edit_data_{key_prefix}_{item_data.get('id')}"] = item_data
                st.rerun()
        
        with col2:
            button_text = "👁️ 详情" if card_type == "fabric" else "📊 库存"
            if st.button(button_text, key=f"{key_prefix}_view_{item_data.get('id', 'unknown')}", use_container_width=True):
                st.session_state[f"show_view_modal_{key_prefix}_{item_data.get('id')}"] = True
                st.session_state[f"view_data_{key_prefix}_{item_data.get('id')}"] = item_data
                st.rerun()
        
        with col3:
            if st.button("🗑️ 删除", key=f"{key_prefix}_delete_{item_data.get('id', 'unknown')}", use_container_width=True):
                st.session_state[f"show_delete_modal_{key_prefix}_{item_data.get('id')}"] = True
                st.session_state[f"delete_data_{key_prefix}_{item_data.get('id')}"] = item_data
                st.rerun()
        
        # 处理编辑弹窗
        if st.session_state.get(f"show_edit_modal_{key_prefix}_{item_data.get('id')}", False):
            _show_edit_modal(item_data, card_type, key_prefix, on_edit)
        
        # 处理详情弹窗
        if st.session_state.get(f"show_view_modal_{key_prefix}_{item_data.get('id')}", False):
            _show_view_modal(item_data, card_type, key_prefix)
        
        # 处理删除弹窗
        if st.session_state.get(f"show_delete_modal_{key_prefix}_{item_data.get('id')}", False):
            _show_delete_modal(item_data, card_type, key_prefix, on_delete)
        
        # 关闭卡片容器
        st.markdown('</div>', unsafe_allow_html=True)

def create_card_grid(items: list, card_type: str = "fabric", columns: int = 3, on_edit=None, on_view=None, on_delete=None):
    """创建响应式卡片网格布局
    
    Args:
        items: 项目数据列表
        card_type: 卡片类型 ("fabric" 或 "inventory")
        columns: 列数
        on_edit: 编辑按钮回调函数
        on_view: 查看详情按钮回调函数
        on_delete: 删除按钮回调函数
    """
    if not items:
        # 美化的空状态显示
        empty_state_css = """
        <style>
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 16px;
            margin: 20px 0;
        }
        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.6;
        }
        .empty-title {
            font-size: 20px;
            font-weight: 600;
            color: #666;
            margin-bottom: 8px;
        }
        .empty-subtitle {
            font-size: 14px;
            color: #888;
        }
        </style>
        """
        
        empty_icon = "📦" if card_type == "inventory" else "🧵"
        empty_title = "暂无库存商品" if card_type == "inventory" else "暂无面料数据"
        empty_subtitle = "点击上方按钮添加新的商品" if card_type == "inventory" else "点击上方按钮添加新的面料"
        
        empty_html = f"""
        <div class="empty-state">
            <div class="empty-icon">{empty_icon}</div>
            <div class="empty-title">{empty_title}</div>
            <div class="empty-subtitle">{empty_subtitle}</div>
        </div>
        """
        
        st.markdown(empty_state_css + empty_html, unsafe_allow_html=True)
        return
    
    # 添加网格容器样式
    grid_css = """
    <style>
    .card-grid-container {
        display: grid;
        gap: 20px;
        margin: 20px 0;
    }
    @media (max-width: 768px) {
        .card-grid-container {
            grid-template-columns: 1fr;
        }
    }
    @media (min-width: 769px) and (max-width: 1024px) {
        .card-grid-container {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (min-width: 1025px) {
        .card-grid-container {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    .grid-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding: 0 4px;
    }
    .grid-title {
        font-size: 18px;
        font-weight: 600;
        color: #333;
    }
    .grid-count {
        background: #f0f2f6;
        color: #666;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
    }
    </style>
    """
    
    st.markdown(grid_css, unsafe_allow_html=True)
    
    # 显示网格标题和数量
    grid_title = "库存商品" if card_type == "inventory" else "面料库"
    grid_header = f"""
    <div class="grid-header">
        <div class="grid-title">{grid_title}</div>
        <div class="grid-count">共 {len(items)} 项</div>
    </div>
    """
    st.markdown(grid_header, unsafe_allow_html=True)
    
    # 创建响应式列布局
    cols = st.columns(columns)
    
    for i, item in enumerate(items):
        with cols[i % columns]:
            create_ecommerce_card(item, card_type, f"{card_type}_{i}", on_edit, on_view, on_delete)


def _show_edit_modal(item_data, card_type, key_prefix, on_edit):
    """显示编辑弹窗"""
    modal_key = f"edit_modal_{key_prefix}_{item_data.get('id')}"
    
    @st.dialog(f"📝 编辑{('面料' if card_type == 'fabric' else '库存')}")
    def edit_modal():
        if card_type == "fabric":
            # 面料编辑表单
            st.write(f"**编辑面料:** {item_data.get('name', '未知')}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("面料名称", value=item_data.get('name', ''), key=f"{modal_key}_name")
                new_material = st.selectbox("材质类型", 
                                          ["细帆", "细帆绗棉", "缎面绗棉"], 
                                          index=["细帆", "细帆绗棉", "缎面绗棉"].index(item_data.get('material_type', '细帆')) if item_data.get('material_type') in ["细帆", "细帆绗棉", "缎面绗棉"] else 0,
                                          key=f"{modal_key}_material")
            with col2:
                new_usage = st.selectbox("用途类型", 
                                       ["表布", "里布"], 
                                       index=["表布", "里布"].index(item_data.get('usage_type', '表布')) if item_data.get('usage_type') in ["表布", "里布"] else 0,
                                       key=f"{modal_key}_usage")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存修改", type="primary", key=f"{modal_key}_save"):
                    if on_edit:
                        # 创建更新后的数据
                        updated_data = item_data.copy()
                        updated_data.update({
                            'name': new_name,
                            'material_type': new_material,
                            'usage_type': new_usage
                        })
                        on_edit(updated_data)
                    st.session_state[f"show_edit_modal_{key_prefix}_{item_data.get('id')}"] = False
                    st.rerun()
            with col2:
                if st.button("❌ 取消", key=f"{modal_key}_cancel"):
                    st.session_state[f"show_edit_modal_{key_prefix}_{item_data.get('id')}"] = False
                    st.rerun()
        
        else:  # inventory
            # 库存编辑表单
            st.write(f"**编辑商品:** {item_data.get('product_name', '未知')}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("商品名称", value=item_data.get('product_name', ''), key=f"{modal_key}_name")
                new_price = st.number_input("价格", value=float(item_data.get('price', 0)), min_value=0.0, step=0.01, key=f"{modal_key}_price")
            with col2:
                new_quantity = st.number_input("库存数量", value=int(item_data.get('quantity', 0)), min_value=0, step=1, key=f"{modal_key}_quantity")
            
            new_description = st.text_area("商品描述", value=item_data.get('description', ''), key=f"{modal_key}_desc")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 保存修改", type="primary", key=f"{modal_key}_save"):
                    if on_edit:
                        # 创建更新后的数据
                        updated_data = item_data.copy()
                        updated_data.update({
                            'product_name': new_name,
                            'price': new_price,
                            'quantity': new_quantity,
                            'description': new_description
                        })
                        on_edit(updated_data)
                    st.session_state[f"show_edit_modal_{key_prefix}_{item_data.get('id')}"] = False
                    st.rerun()
            with col2:
                if st.button("❌ 取消", key=f"{modal_key}_cancel"):
                    st.session_state[f"show_edit_modal_{key_prefix}_{item_data.get('id')}"] = False
                    st.rerun()
    
    edit_modal()


def _show_view_modal(item_data, card_type, key_prefix):
    """显示详情弹窗"""
    modal_key = f"view_modal_{key_prefix}_{item_data.get('id')}"
    
    @st.dialog(f"👁️ {('面料' if card_type == 'fabric' else '库存')}详情")
    def view_modal():
        if card_type == "fabric":
            # 面料详情
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### 🧵 {item_data.get('name', '未知面料')}")
                st.write(f"**📋 面料ID:** #{item_data.get('id', 'N/A')}")
                st.write(f"**🏷️ 材质类型:** {item_data.get('material_type', '未指定')}")
                st.write(f"**🎯 用途类型:** {item_data.get('usage_type', '未指定')}")
                st.write(f"**📅 创建时间:** {item_data.get('created_at', '未知')}")
            
            with col2:
                if item_data.get('image_path'):
                    try:
                        st.image(item_data['image_path'], caption="面料图片", width=150)
                    except:
                        st.write("🖼️ 图片加载失败")
                else:
                    st.write("🖼️ 暂无图片")
        
        else:  # inventory
            # 库存详情
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### 📦 {item_data.get('product_name', '未知商品')}")
                st.write(f"**📋 商品ID:** #{item_data.get('id', 'N/A')}")
                st.write(f"**💰 价格:** ¥{item_data.get('price', 0):.2f}")
                st.write(f"**📊 库存数量:** {item_data.get('quantity', 0)} 件")
                st.write(f"**📝 描述:** {item_data.get('description', '暂无描述')}")
                st.write(f"**📅 创建时间:** {item_data.get('created_at', '未知')}")
            
            with col2:
                if item_data.get('image_path'):
                    try:
                        st.image(item_data['image_path'], caption="商品图片", width=150)
                    except:
                        st.write("🖼️ 图片加载失败")
                else:
                    st.write("🖼️ 暂无图片")
        
        if st.button("关闭", key=f"{modal_key}_close", type="primary"):
            st.session_state[f"show_view_modal_{key_prefix}_{item_data.get('id')}"] = False
            st.rerun()
    
    view_modal()


def _show_delete_modal(item_data, card_type, key_prefix, on_delete):
    """显示删除确认弹窗"""
    modal_key = f"delete_modal_{key_prefix}_{item_data.get('id')}"
    
    @st.dialog(f"🗑️ 删除确认")
    def delete_modal():
        item_name = item_data.get('name' if card_type == 'fabric' else 'product_name', '未知项目')
        st.warning(f"⚠️ 确定要删除 **{item_name}** 吗？")
        st.write("此操作不可撤销，请谨慎操作。")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 确认删除", type="primary", key=f"{modal_key}_confirm"):
                if on_delete:
                    on_delete(item_data)
                st.session_state[f"show_delete_modal_{key_prefix}_{item_data.get('id')}"] = False
                st.rerun()
        with col2:
            if st.button("❌ 取消", key=f"{modal_key}_cancel"):
                st.session_state[f"show_delete_modal_{key_prefix}_{item_data.get('id')}"] = False
                st.rerun()
    
    delete_modal()