import streamlit as st
import pandas as pd
from datetime import datetime
from database import DatabaseManager
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from upload_components import drag_drop_image_uploader, drag_drop_media_uploader, display_uploaded_media
from ui_components import (
    show_loading_spinner, show_progress_bar, show_success_message, 
    show_error_message, show_warning_message, create_metric_card,
    create_action_button, create_confirmation_dialog, create_card_grid
)
from auto_backup import check_and_perform_backup

# 导入新的服务层和工具类
from config import config
from services import DashboardService, ExportService
from utils import CacheManager

# 导入页面组件
from pages import render_dashboard_page, render_order_page, render_customer_page, render_fabric_page, render_inventory_page, render_settings_page

# 页面配置
st.set_page_config(**config.get_page_config())

# 全局样式优化
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 主容器样式 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* 卡片样式 */
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    /* 按钮样式优化 */
    .stButton > button {
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* 表格样式 */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid #ddd;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库和服务层
@st.cache_resource
def init_database():
    return DatabaseManager()

@st.cache_resource
def init_services():
    """初始化服务层"""
    db = init_database()
    dashboard_service = DashboardService(db)
    export_service = ExportService(db)
    cache_manager = CacheManager()
    return db, dashboard_service, export_service, cache_manager

db, dashboard_service, export_service, cache_manager = init_services()

# 执行自动备份检查（仅在应用启动时执行一次）
if 'backup_checked' not in st.session_state:
    st.session_state.backup_checked = True
    with st.spinner("正在检查备份状态..."):
        check_and_perform_backup(db)

# 自定义CSS样式
st.markdown("""
<style>
    /* 主题色彩变量 */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --success-color: #06D6A0;
        --warning-color: #FFD23F;
        --error-color: #F72585;
        --background-light: #F8F9FA;
        --text-dark: #2D3748;
        --border-light: #E2E8F0;
    }
    
    /* 主标题样式 */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(46, 134, 171, 0.1);
        border: 1px solid var(--border-light);
    }
    
    /* 卡片样式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-light);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin: 0.75rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    /* 消息样式 */
    .success-message {
        background: linear-gradient(135deg, #06D6A0, #00B894);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(6, 214, 160, 0.3);
        border: none;
    }
    
    .error-message {
        background: linear-gradient(135deg, #F72585, #E84393);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(247, 37, 133, 0.3);
        border: none;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #FFD23F, #FDCB6E);
        color: var(--text-dark);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(255, 210, 63, 0.3);
        border: none;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(46, 134, 171, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.4);
        background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid var(--border-light);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(46, 134, 171, 0.1);
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid var(--border-light);
    }
    
    /* 数据表格样式 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: var(--background-light);
    }
    
    /* 加载动画 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(46, 134, 171, 0.3);
        border-radius: 50%;
        border-top-color: var(--primary-color);
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* 进度条样式 */
    .progress-bar {
        width: 100%;
        height: 8px;
        background-color: var(--border-light);
        border-radius: 4px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    /* 工具提示样式 */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: var(--text-dark);
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown('<div class="main-header">🏪 星之梦手作管理系统</div>', unsafe_allow_html=True)

# 处理按钮回调状态 - 完善版本

# 面料编辑对话框
if st.session_state.get('show_edit_fabric', False):
    with st.expander("📝 编辑面料", expanded=True):
        fabric_data = st.session_state.get('edit_fabric_data', {})
        if fabric_data:
            with st.form("edit_fabric_form"):
                st.write(f"**编辑面料:** {fabric_data.get('name', '未知')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("面料名称", value=fabric_data.get('name', ''))
                    new_material = st.selectbox("材质类型", 
                                              ["细帆", "细帆绗棉", "缎面绗棉"], 
                                              index=["细帆", "细帆绗棉", "缎面绗棉"].index(fabric_data.get('material_type', '细帆')) if fabric_data.get('material_type') in ["细帆", "细帆绗棉", "缎面绗棉"] else 0)
                with col2:
                    new_usage = st.selectbox("用途类型", 
                                           ["表布", "里布"], 
                                           index=["表布", "里布"].index(fabric_data.get('usage_type', '表布')) if fabric_data.get('usage_type') in ["表布", "里布"] else 0)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 保存修改", type="primary"):
                        try:
                            success = db.update_fabric(
                                fabric_data['id'],
                                new_name,
                                new_material,
                                new_usage,
                                fabric_data.get('image_path', '')
                            )
                            if success:
                                st.success("面料更新成功！")
                                st.session_state.show_edit_fabric = False
                                st.rerun()
                            else:
                                st.error("更新失败！")
                        except Exception as e:
                            st.error(f"更新失败: {str(e)}")
                with col2:
                    if st.form_submit_button("❌ 取消"):
                        st.session_state.show_edit_fabric = False
                        st.rerun()

# 面料详情对话框
if st.session_state.get('show_fabric_details', False):
    with st.expander("👁️ 面料详情", expanded=True):
        fabric_data = st.session_state.get('view_fabric_data', {})
        if fabric_data:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### 🧵 {fabric_data.get('name', '未知面料')}")
                st.write(f"**📋 面料ID:** #{fabric_data.get('id', 'N/A')}")
                st.write(f"**🏷️ 材质类型:** {fabric_data.get('material_type', '未指定')}")
                st.write(f"**🎯 用途类型:** {fabric_data.get('usage_type', '未指定')}")
                st.write(f"**📅 创建时间:** {fabric_data.get('created_at', '未知')}")
            
            with col2:
                if fabric_data.get('image_path'):
                    try:
                        st.image(fabric_data['image_path'], caption="面料图片", width=150)
                    except:
                        st.write("🖼️ 图片加载失败")
                else:
                    st.write("🖼️ 暂无图片")
            
            if st.button("关闭详情", key="close_fabric_details"):
                st.session_state.show_fabric_details = False
                st.rerun()

# 库存编辑对话框
if st.session_state.get('show_edit_inventory', False):
    with st.expander("📝 编辑库存", expanded=True):
        inventory_data = st.session_state.get('edit_inventory_data', {})
        if inventory_data:
            with st.form("edit_inventory_form"):
                st.write(f"**编辑商品:** {inventory_data.get('product_name', '未知')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("商品名称", value=inventory_data.get('product_name', ''))
                    new_price = st.number_input("价格", value=float(inventory_data.get('price', 0)), min_value=0.0, step=0.01)
                with col2:
                    new_quantity = st.number_input("库存数量", value=int(inventory_data.get('quantity', 0)), min_value=0, step=1)
                
                new_description = st.text_area("商品描述", value=inventory_data.get('description', ''))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 保存修改", type="primary"):
                        try:
                            success = db.update_inventory_item(
                                inventory_data['id'],
                                new_name,
                                new_description,
                                new_price,
                                new_quantity,
                                inventory_data.get('image_path', '')
                            )
                            if success:
                                st.success("库存更新成功！")
                                st.session_state.show_edit_inventory = False
                                st.rerun()
                            else:
                                st.error("更新失败！")
                        except Exception as e:
                            st.error(f"更新失败: {str(e)}")
                with col2:
                    if st.form_submit_button("❌ 取消"):
                        st.session_state.show_edit_inventory = False
                        st.rerun()

# 库存详情对话框
if st.session_state.get('show_inventory_details', False):
    with st.expander("📊 库存详情", expanded=True):
        inventory_data = st.session_state.get('view_inventory_data', {})
        if inventory_data:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"### 📦 {inventory_data.get('product_name', '未知商品')}")
                st.write(f"**📋 商品ID:** #{inventory_data.get('id', 'N/A')}")
                st.write(f"**💰 价格:** ¥{inventory_data.get('price', 0):.2f}")
                st.write(f"**📊 库存数量:** {inventory_data.get('quantity', 0)} 件")
                st.write(f"**📝 描述:** {inventory_data.get('description', '暂无描述')}")
                st.write(f"**📅 创建时间:** {inventory_data.get('created_at', '未知')}")
            
            with col2:
                if inventory_data.get('image_path'):
                    try:
                        st.image(inventory_data['image_path'], caption="商品图片", width=150)
                    except:
                        st.write("🖼️ 图片加载失败")
                else:
                    st.write("🖼️ 暂无图片")
            
            if st.button("关闭详情", key="close_inventory_details"):
                st.session_state.show_inventory_details = False
                st.rerun()

# 面料删除确认对话框
if st.session_state.get('show_delete_fabric_confirm', False):
    with st.expander("🗑️ 删除确认", expanded=True):
        fabric_id = st.session_state.get('delete_fabric_id')
        st.warning("确定要删除这个面料吗？此操作不可撤销！")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认删除", type="primary", key="confirm_delete_fabric"):
                try:
                    if db.delete_fabric(fabric_id):
                        st.success("面料删除成功！")
                        st.session_state.show_delete_fabric_confirm = False
                        st.rerun()
                    else:
                        st.error("删除失败！")
                except Exception as e:
                    st.error(f"删除失败: {str(e)}")
        with col2:
            if st.button("取消", key="cancel_delete_fabric"):
                st.session_state.show_delete_fabric_confirm = False
                st.rerun()



# 库存删除确认对话框
if st.session_state.get('show_delete_inventory_confirm', False):
    with st.expander("🗑️ 删除确认", expanded=True):
        inventory_id = st.session_state.get('delete_inventory_id')
        st.warning("确定要删除这个商品吗？此操作不可撤销！")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认删除", type="primary", key="confirm_delete_inventory"):
                if db.delete_inventory_item(inventory_id):
                    st.success("商品删除成功！")
                    st.session_state.show_delete_inventory_confirm = False
                    st.rerun()
                else:
                    st.error("删除失败！")
        with col2:
            if st.button("取消", key="cancel_delete_inventory"):
                st.session_state.show_delete_inventory_confirm = False
                st.rerun()

# 顶部导航栏
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-title {
        color: white;
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
        text-align: center;
    }
    .main-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        margin: 0;
        text-align: center;
    }
    .nav-container {
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown("""
<div class="main-header">
    <h1 class="main-title">🏪 星之梦手作管理系统</h1>
    <p class="main-subtitle">让生意管理更简单高效</p>
</div>
""", unsafe_allow_html=True)

# 顶部导航菜单
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
selected = option_menu(
    menu_title=None,
    options=["📊 仪表板", "👥 客户管理", "🧵 面料管理", "📦 库存管理", "📋 订单管理", "⚙️ 系统设置"],
    icons=["graph-up", "people", "palette", "box", "clipboard-check", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "icon": {"color": "#667eea", "font-size": "16px"},
        "nav-link": {
            "font-size": "14px", 
            "text-align": "center", 
            "margin": "0px",
            "padding": "0.5rem 1rem",
            "border-radius": "8px",
            "--hover-color": "#f0f2f6",
            "color": "#333"
        },
        "nav-link-selected": {
            "background-color": "#667eea",
            "color": "white",
            "font-weight": "bold"
        },
    }
)
st.markdown('</div>', unsafe_allow_html=True)

# 仪表板页面
if selected == "📊 仪表板":
    render_dashboard_page(db, dashboard_service)

# 客户管理页面
elif selected == "👥 客户管理":
    render_customer_page(db)

# 面料管理页面
elif selected == "🧵 面料管理":
    render_fabric_page(db)

# 库存管理页面
elif selected == "📦 库存管理":
    render_inventory_page(db)

# 订单管理页面
elif selected == "📋 订单管理":
    render_order_page(db, dashboard_service, export_service, cache_manager)

# 系统设置页面
elif selected == "⚙️ 系统设置":
    render_settings_page(db)

# 页脚
st.markdown("""
<style>
    .footer {
        margin-top: 3rem;
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        text-align: center;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
<div class="footer">
    © 2025 星之梦手作管理系统 | 专业的手工艺品管理解决方案
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass