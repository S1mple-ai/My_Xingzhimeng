import streamlit as st
import pandas as pd
from datetime import datetime
from database import DatabaseManager
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from upload_components import drag_drop_image_uploader, drag_drop_media_uploader, display_uploaded_media, enhanced_image_preview, save_uploaded_file
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
from performance_monitor import PerformanceMonitor, monitor_execution_time
from ui_components_extended import create_advanced_data_table, create_search_filter_panel, create_dashboard_stats
from database_optimizer import initialize_database_optimization, OptimizedQueries, monitor_query_performance
from cache_manager import cache_manager, smart_cache, CacheMetrics

# 导入代加工管理模块
from processing_management import show_processing_management

# 页面配置
st.set_page_config(**config.get_page_config())

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

@st.cache_resource
def init_optimizations():
    """初始化第二层优化组件"""
    # 获取数据库路径
    db_path = config.database.db_path
    
    # 初始化数据库优化
    initialize_database_optimization(db_path)
    
    # 初始化优化查询
    optimized_queries = OptimizedQueries(db_path)
    
    # 初始化缓存指标
    cache_metrics = CacheMetrics()
    
    return optimized_queries, cache_metrics

db, dashboard_service, export_service, cache_manager = init_services()
optimized_queries, cache_metrics = init_optimizations()

# 安全的图片显示函数
def safe_image_display(uploaded_file, width=200, caption="图片预览"):
    """安全地显示上传的图片，包含错误处理"""
    if uploaded_file is None:
        st.info("📷 暂无图片")
        return
    
    try:
        # 检查文件是否有效
        if hasattr(uploaded_file, 'read'):
            # 重置文件指针到开始位置
            uploaded_file.seek(0)
            st.image(uploaded_file, width=width, caption=caption)
        else:
            st.warning("⚠️ 图片文件格式不支持")
    except Exception as e:
        st.error(f"❌ 图片显示失败: {str(e)}")
        st.info("💡 请尝试上传 JPG、PNG 或 GIF 格式的图片")

# 积分公式解析函数
def parse_points_formula(formula, current_points):
    """
    解析积分公式，支持 +数字、-数字、=数字 三种格式
    
    Args:
        formula (str): 输入的公式字符串
        current_points (int): 当前积分
    
    Returns:
        tuple: (是否成功, 新积分值, 错误信息)
    """
    if not formula or not formula.strip():
        return False, current_points, "公式不能为空"
    
    formula = formula.strip()
    
    try:
        # 处理 =数字 格式（直接设置积分）
        if formula.startswith('='):
            new_points = int(formula[1:])
            if new_points < 0:
                return False, current_points, "积分不能为负数"
            return True, new_points, ""
        
        # 处理 +数字 格式（增加积分）
        elif formula.startswith('+'):
            points_to_add = int(formula[1:])
            new_points = current_points + points_to_add
            if new_points < 0:
                return False, current_points, "积分不能为负数"
            return True, new_points, ""
        
        # 处理 -数字 格式（减少积分）
        elif formula.startswith('-'):
            points_to_subtract = int(formula[1:])
            new_points = current_points - points_to_subtract
            if new_points < 0:
                return False, current_points, "积分不能为负数"
            return True, new_points, ""
        
        # 如果只是数字，当作 =数字 处理
        elif formula.isdigit():
            new_points = int(formula)
            if new_points < 0:
                return False, current_points, "积分不能为负数"
            return True, new_points, ""
        
        else:
            return False, current_points, "公式格式错误，请使用 +数字、-数字 或 =数字 格式"
    
    except ValueError:
        return False, current_points, "请输入有效的数字"
    except Exception as e:
        return False, current_points, f"公式解析错误: {str(e)}"

# 执行自动备份检查（仅在应用启动时执行一次）
if 'backup_checked' not in st.session_state:
    st.session_state.backup_checked = True
    with st.spinner("正在检查备份状态..."):
        check_and_perform_backup(db)

# 自定义CSS样式
# 加载外部CSS样式文件
def load_css():
    """加载外部CSS样式文件"""
    try:
        with open('static/css/main.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS样式文件未找到，使用默认样式")

# 加载CSS样式
load_css()

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
                
                # 图片上传区域
                st.markdown("---")
                st.markdown("**🖼️ 面料图片**")
                
                # 显示当前图片
                current_image_path = fabric_data.get('image_path', '')
                if current_image_path and os.path.exists(current_image_path):
                    st.markdown("**当前图片:**")
                    st.image(current_image_path, width=200)
                else:
                    st.markdown("*当前无图片*")
                
                # 上传新图片
                uploaded_file = drag_drop_image_uploader(
                    key=f"fabric_edit_image_{fabric_data.get('id', 'unknown')}",
                    label="拖拽新图片到此处或点击上传（可选）",
                    help_text="支持 JPG, PNG, GIF 格式"
                )
                
                # 显示新上传的图片预览
                if uploaded_file:
                    st.markdown("**新图片预览:**")
                    safe_image_display(uploaded_file, width=200, caption="新上传的面料图片")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 保存修改", type="primary"):
                        try:
                            # 处理图片上传
                            final_image_path = fabric_data.get('image_path', '')
                            if uploaded_file:
                                final_image_path = save_uploaded_file(uploaded_file, "fabric")
                            
                            success = db.update_fabric(
                                fabric_data['id'],
                                new_name,
                                new_material,
                                new_usage,
                                final_image_path
                            )
                            if success:
                                st.markdown('<div class="success-message">✅ 面料更新成功！</div>', unsafe_allow_html=True)
                                st.session_state.show_edit_fabric = False
                                st.rerun()
                            else:
                                st.markdown('<div class="error-message">❌ 更新失败！</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.markdown(f'<div class="error-message">❌ 更新失败: {str(e)}</div>', unsafe_allow_html=True)
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
                    
                    # 显示当前图片
                    current_image_path = inventory_data.get('image_path', '')
                    if current_image_path and os.path.exists(current_image_path):
                        st.markdown("**当前图片:**")
                        st.image(current_image_path, width=150)
                    
                    # 图片更换 - 支持拖拽上传
                    st.markdown("**🖼️ 更换图片**")
                    uploaded_file = drag_drop_image_uploader(
                        key=f"edit_inventory_image_{inventory_data.get('id', 0)}",
                        label="拖拽新图片到此处或点击上传",
                        help_text="支持 JPG, PNG, GIF 格式，留空则保持原图片"
                    )
                    
                    # 显示新上传的图片预览
                    if uploaded_file:
                        st.markdown("**新图片预览:**")
                        safe_image_display(uploaded_file, width=150, caption="新上传的商品图片")
                        
                with col2:
                    new_quantity = st.number_input("库存数量", value=int(inventory_data.get('quantity', 0)), min_value=0, step=1)
                
                new_description = st.text_area("商品描述", value=inventory_data.get('description', ''))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.form_submit_button("💾 保存修改", type="primary"):
                        try:
                            # 处理图片更新
                            final_image_path = inventory_data.get('image_path', '')
                            if uploaded_file:
                                # 保存新图片
                                final_image_path = save_uploaded_file(uploaded_file, "inventory")
                            
                            success = db.update_inventory_item(
                                inventory_data['id'],
                                new_name,
                                new_description,
                                new_price,
                                new_quantity,
                                final_image_path
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

# 面料删除确认对话框已移至ui_components.py中的弹窗系统



# 库存删除确认对话框已移至ui_components.py中的弹窗系统

# 侧边栏导航
with st.sidebar:
    # 优化的菜单栏标题
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2E86AB, #A23B72);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.2);
    ">
        <h3 style="
            color: white;
            margin: 0;
            font-weight: 600;
            font-size: 1.2rem;
            text-align: center;
        ">📋 系统导航</h3>
        <p style="
            color: rgba(255, 255, 255, 0.8);
            margin: 0.5rem 0 0 0;
            font-size: 0.85rem;
            text-align: center;
        ">选择功能模块进行操作</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title=None,
        options=["📊 仪表板", "👥 客户管理", "🧵 面料管理", "📦 库存管理", "📋 订单管理", "🏭 加工管理", "⚙️ 系统设置"],
        icons=None,  # 移除重复图标，统一使用emoji
        menu_icon=None,
        default_index=0,
        styles={
            "container": {
                "padding": "0.5rem 0",
                "background-color": "transparent",
                "border-radius": "10px"
            },
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "3px 0",
                "padding": "14px 18px",
                "border-radius": "10px",
                "background-color": "white",
                "border": "1px solid #E2E8F0",
                "box-shadow": "0 2px 6px rgba(0,0,0,0.08)",
                "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                "display": "flex",
                "align-items": "center",
                "font-weight": "500",
                "letter-spacing": "0.3px",
                "--hover-color": "transparent"
            },
            "nav-link:hover": {
                "background-color": "#F8FAFC",
                "border-color": "#2E86AB",
                "transform": "translateX(6px) scale(1.02)",
                "box-shadow": "0 6px 20px rgba(46, 134, 171, 0.2)",
                "color": "#2E86AB"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #2E86AB, #A23B72)",
                "color": "white",
                "border": "1px solid #2E86AB",
                "box-shadow": "0 6px 20px rgba(46, 134, 171, 0.4)",
                "transform": "translateX(6px) scale(1.02)",
                "font-weight": "600"
            },
            "nav-link-selected:hover": {
                "background": "linear-gradient(135deg, #A23B72, #2E86AB)",
                "transform": "translateX(8px) scale(1.03)",
                "box-shadow": "0 8px 25px rgba(46, 134, 171, 0.5)"
            }
        }
    )

# 仪表板页面
if selected == "📊 仪表板":
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
    
    # 销售趋势分析
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
    
    # 面料使用分析
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
    
    # 商品销售分析
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
    
    # 客户活跃度分析
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
    

    
    # 库存预警 - 使用新的UI组件
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

# 客户管理页面
elif selected == "👥 客户管理":
    st.markdown("## 👥 客户管理")
    
    tab1, tab2 = st.tabs(["📋 客户列表", "➕ 添加客户"])
    
    with tab1:
        st.markdown("### 📋 客户列表")
        customers = db.get_customers()
        
        if customers:
            df_customers = pd.DataFrame(customers)
            
            # 搜索和筛选区域
            st.markdown("#### 🔍 搜索与筛选")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 搜索客户", placeholder="输入客户昵称、手机尾号或备注...", key="customer_search")
            
            with col2:
                points_filter = st.selectbox("积分范围", ["全部", "0-100", "100-500", "500-1000", "1000以上"], key="points_filter")
            
            with col3:
                has_notes_filter = st.selectbox("备注状态", ["全部", "有备注", "无备注"], key="notes_filter")
            
            # 排序选项
            col4, col5 = st.columns(2)
            with col4:
                sort_by = st.selectbox("排序方式", ["创建时间", "客户昵称", "积分", "更新时间"], key="customer_sort")
            with col5:
                sort_order = st.selectbox("排序顺序", ["降序", "升序"], key="customer_order")
            
            # 应用搜索筛选
            if search_term:
                df_customers = df_customers[
                    df_customers['nickname'].str.contains(search_term, case=False, na=False) |
                    df_customers['phone_suffix'].str.contains(search_term, case=False, na=False) |
                    df_customers['notes'].str.contains(search_term, case=False, na=False)
                ]
            
            # 积分范围筛选
            if points_filter != "全部":
                if points_filter == "0-100":
                    df_customers = df_customers[(df_customers['points'] >= 0) & (df_customers['points'] <= 100)]
                elif points_filter == "100-500":
                    df_customers = df_customers[(df_customers['points'] > 100) & (df_customers['points'] <= 500)]
                elif points_filter == "500-1000":
                    df_customers = df_customers[(df_customers['points'] > 500) & (df_customers['points'] <= 1000)]
                elif points_filter == "1000以上":
                    df_customers = df_customers[df_customers['points'] > 1000]
            
            # 备注状态筛选
            if has_notes_filter != "全部":
                if has_notes_filter == "有备注":
                    df_customers = df_customers[df_customers['notes'].notna() & (df_customers['notes'] != "")]
                elif has_notes_filter == "无备注":
                    df_customers = df_customers[df_customers['notes'].isna() | (df_customers['notes'] == "")]
            
            # 排序
            sort_column_map = {
                "创建时间": "created_at",
                "客户昵称": "nickname",
                "积分": "points",
                "更新时间": "updated_at"
            }
            sort_column = sort_column_map[sort_by]
            ascending = sort_order == "升序"
            df_customers = df_customers.sort_values(by=sort_column, ascending=ascending)
            
            # 显示筛选结果统计
            total_count = len(customers)
            filtered_count = len(df_customers)
            if filtered_count != total_count:
                st.info(f"📊 显示 {filtered_count} / {total_count} 个客户")
            else:
                st.info(f"📊 共 {total_count} 个客户")
            
            # 客户统计信息
            if len(customers) > 0:
                total_points = sum(customer['points'] for customer in customers)
                avg_points = total_points / len(customers)
                high_value_customers = len([c for c in customers if c['points'] > 500])
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("总积分", f"{total_points:,}")
                with col_stat2:
                    st.metric("平均积分", f"{avg_points:.0f}")
                with col_stat3:
                    st.metric("高价值客户(>500积分)", high_value_customers)
            
            # 显示客户列表
            for _, customer in df_customers.iterrows():
                with st.expander(f"👤 {customer['nickname']} - 积分: {customer['points']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        new_nickname = st.text_input("昵称", value=customer['nickname'], key=f"nickname_{customer['id']}")
                        new_phone = st.text_input("手机尾号", value=customer['phone_suffix'] or "", key=f"phone_{customer['id']}")
                    
                    with col2:
                        new_notes = st.text_area("备注", value=customer['notes'] or "", key=f"notes_{customer['id']}")
                        st.write(f"当前积分: **{customer['points']}**")
                        points_formula = st.text_input(
                            "积分公式", 
                            placeholder="输入 +数字、-数字 或 =数字", 
                            key=f"points_formula_{customer['id']}",
                            help="例如: +50 (增加50分), -20 (减少20分), =100 (设为100分)"
                        )
                        
                        # 积分历史查看按钮
                        if st.button("📊 查看积分历史", key=f"history_{customer['id']}"):
                            st.session_state[f"show_history_{customer['id']}"] = not st.session_state.get(f"show_history_{customer['id']}", False)
                        
                        # 显示积分历史
                        if st.session_state.get(f"show_history_{customer['id']}", False):
                            history = db.get_customer_points_history(customer['id'])
                            if history:
                                st.write("**积分历史记录:**")
                                for record in history[:5]:  # 只显示最近5条
                                    change_text = f"+{record['points_change']}" if record['points_change'] > 0 else str(record['points_change'])
                                    st.write(f"• {record['created_at'][:16]} | {change_text} | {record['reason']} | 操作者: {record['operator']}")
                                if len(history) > 5:
                                    st.write(f"... 还有 {len(history) - 5} 条记录")
                            else:
                                st.write("暂无积分历史记录")
                    
                    with col3:
                        if create_action_button("💾 更新", f"update_{customer['id']}", "primary"):
                            try:
                                # 更新基本信息
                                db.update_customer(customer['id'], new_nickname, new_phone, new_notes)
                                
                                # 处理积分更新
                                if points_formula and points_formula.strip():
                                    success, new_points, error_msg = parse_points_formula(points_formula, customer['points'])
                                    if success:
                                        points_change = new_points - customer['points']
                                        if points_change != 0:
                                            db.update_customer_points_with_history(
                                                customer['id'], 
                                                points_change,
                                                change_type="manual",
                                                reason=f"手动调整: {points_formula}",
                                                operator="管理员"
                                            )
                                            show_success_message(f"客户信息已更新，积分从 {customer['points']} 变更为 {new_points}")
                                        else:
                                            show_success_message("客户信息已更新")
                                    else:
                                        show_error_message(f"积分公式错误: {error_msg}")
                                        continue
                                else:
                                    show_success_message("客户信息已更新")
                                
                                st.rerun()
                            except Exception as e:
                                show_error_message(f"更新客户信息失败: {str(e)}")
                        
                        # 删除客户功能
                        delete_key = f"delete_customer_{customer['id']}"
                        confirm_key = f"confirm_delete_{customer['id']}"
                        
                        # 如果还没有点击删除按钮，显示删除按钮
                        if not st.session_state.get(delete_key, False):
                            if st.button("🗑️ 删除", key=f"btn_delete_{customer['id']}", type="secondary"):
                                st.session_state[delete_key] = True
                                st.rerun()
                        else:
                            # 显示确认对话框
                            st.warning(f"⚠️ 确认删除客户 '{customer['nickname']}' 吗？此操作不可撤销！")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ 确认删除", key=f"confirm_{customer['id']}", type="primary"):
                                    try:
                                        db.delete_customer(customer['id'])
                                        show_success_message("客户已删除")
                                        # 清理状态
                                        st.session_state[delete_key] = False
                                        if confirm_key in st.session_state:
                                            del st.session_state[confirm_key]
                                        st.rerun()
                                    except Exception as e:
                                        show_error_message(f"删除客户失败: {str(e)}")
                                        st.session_state[delete_key] = False
                            with col2:
                                if st.button("❌ 取消", key=f"cancel_{customer['id']}"):
                                    st.session_state[delete_key] = False
                                    st.rerun()
        else:
            st.info("📝 暂无客户数据，请添加客户")
    
    with tab2:
        st.markdown("### ➕ 添加新客户")
        
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nickname = st.text_input("👤 客户昵称*", placeholder="请输入客户昵称")
                phone_suffix = st.text_input("📱 手机尾号", placeholder="例如：1234")
            
            with col2:
                notes = st.text_area("📝 备注信息", placeholder="客户偏好、特殊要求等")
            
            submitted = st.form_submit_button("➕ 添加客户", use_container_width=True)
            
            if submitted:
                if nickname:
                    try:
                        customer_id = db.add_customer(nickname, phone_suffix, notes)
                        show_success_message(f'客户 "{nickname}" 添加成功！客户ID: {customer_id}')
                        st.rerun()
                    except Exception as e:
                        show_error_message(f"添加客户失败: {str(e)}")
                else:
                    show_error_message("请输入客户昵称")

# 面料管理页面
elif selected == "🧵 面料管理":
    st.markdown("## 🧵 面料管理")
    
    tab1, tab2 = st.tabs(["📋 面料列表", "➕ 添加面料"])
    
    with tab1:
        st.markdown("### 📋 面料列表")
        
        # 搜索和筛选区域
        st.markdown("#### 🔍 搜索与筛选")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 搜索面料", placeholder="输入面料名称进行搜索...", key="fabric_search")
        
        with col2:
            material_filter = st.selectbox("材质类型", ["全部", "细帆", "细帆绗棉", "缎面绗棉"], key="material_filter")
        
        with col3:
            usage_filter = st.selectbox("用途类型", ["全部", "表布", "里布"], key="usage_filter")
        
        # 排序选项
        col4, col5 = st.columns(2)
        with col4:
            sort_by = st.selectbox("排序方式", ["创建时间", "名称", "材质类型", "用途类型"], key="fabric_sort")
        with col5:
            sort_order = st.selectbox("排序顺序", ["降序", "升序"], key="fabric_order")
        
        # 添加加载状态
        with st.spinner("正在加载面料数据..."):
            fabrics = db.get_fabrics()
        
        if fabrics:
            df_fabrics = pd.DataFrame(fabrics)
            
            # 应用搜索筛选
            if search_term:
                df_fabrics = df_fabrics[df_fabrics['name'].str.contains(search_term, case=False, na=False)]
            
            if material_filter != "全部":
                df_fabrics = df_fabrics[df_fabrics['material_type'] == material_filter]
            
            if usage_filter != "全部":
                df_fabrics = df_fabrics[df_fabrics['usage_type'] == usage_filter]
            
            # 应用排序
            sort_column_map = {
                "创建时间": "created_at",
                "名称": "name", 
                "材质类型": "material_type",
                "用途类型": "usage_type"
            }
            sort_column = sort_column_map[sort_by]
            ascending = sort_order == "升序"
            df_fabrics = df_fabrics.sort_values(by=sort_column, ascending=ascending)
            
            # 显示筛选结果统计
            total_count = len(fabrics)
            filtered_count = len(df_fabrics)
            if filtered_count != total_count:
                st.info(f"📊 显示 {filtered_count} / {total_count} 个面料")
            else:
                st.info(f"📊 共 {total_count} 个面料")
            
            # 卡片视图显示
            st.markdown("#### 🎴 面料卡片")
            st.markdown("---")
            if not df_fabrics.empty:
                # 转换为字典列表以便卡片组件使用
                fabric_list = df_fabrics.to_dict('records')
                
                # 定义回调函数
                def on_fabric_edit(fabric_data):
                    st.session_state.edit_fabric_id = fabric_data['id']
                    st.session_state.edit_fabric_data = fabric_data
                    st.session_state.show_edit_fabric = True
                    st.rerun()
                
                def on_fabric_view(fabric_data):
                    st.session_state.view_fabric_data = fabric_data
                    st.session_state.show_fabric_details = True
                    st.rerun()
                
                def on_fabric_delete(fabric_data):
                    """删除面料的回调函数"""
                    try:
                        if db.delete_fabric(fabric_data['id']):
                            st.success("面料删除成功！")
                            st.rerun()
                        else:
                            st.error("删除失败！")
                    except Exception as e:
                        st.error(f"删除失败: {str(e)}")
                
                create_card_grid(fabric_list, card_type="fabric", columns=3, 
                               on_edit=on_fabric_edit, on_view=on_fabric_view, on_delete=on_fabric_delete)
            else:
                st.info("暂无符合条件的面料数据")

        else:
            st.info("📝 暂无面料数据，请添加面料")
    
    with tab2:
        st.markdown("### ➕ 添加新面料")
        
        # 基本信息表单
        with st.form("add_fabric_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("🧵 面料名称*", placeholder="请输入面料名称")
                material_type = st.selectbox("🏷️ 材质类型*", ["细帆", "细帆绗棉", "缎面绗棉"])
            
            with col2:
                usage_type = st.selectbox("🎯 用途*", ["表布", "里布"])
            
            # 图片上传区域
            st.markdown("---")
            st.markdown("**🖼️ 面料图片**")
            uploaded_file, _ = drag_drop_image_uploader(
                key="fabric_image_upload",
                label="拖拽图片到此处或点击上传",
                help_text="支持 JPG, PNG, GIF 格式",
                form_safe=True
            )
            
            submitted = st.form_submit_button("➕ 添加面料", use_container_width=True)
            
            if submitted:
                if name:
                    try:
                        # 处理图片上传
                        image_path = ""
                        if uploaded_file:
                            image_path = save_uploaded_file(uploaded_file, "fabric")
                        
                        fabric_id = db.add_fabric(name, material_type, usage_type, image_path)
                        st.markdown(f'<div class="success-message">✅ 面料 "{name}" 添加成功！面料ID: {fabric_id}</div>', unsafe_allow_html=True)
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<div class="error-message">❌ 添加面料失败: {str(e)}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ 请输入面料名称</div>', unsafe_allow_html=True)

# 库存管理页面
elif selected == "📦 库存管理":
    st.markdown("## 📦 库存管理")
    
    tab1, tab2 = st.tabs(["📋 库存列表", "➕ 添加商品"])
    
    with tab1:
        st.markdown("### 📋 库存列表")
        inventory_items = db.get_inventory_items()
        
        if inventory_items:
            # 搜索和筛选区域
            st.markdown("#### 🔍 搜索与筛选")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 搜索商品", placeholder="输入商品名称或描述...", key="inventory_search")
            
            with col2:
                stock_filter = st.selectbox("库存状态", ["全部", "充足(>10)", "偏少(1-10)", "缺货(0)"], key="stock_filter")
            
            with col3:
                price_filter = st.selectbox("价格范围", ["全部", "0-50元", "50-100元", "100-200元", "200元以上"], key="price_filter")
            
            # 排序选项
            col4, col5 = st.columns(2)
            with col4:
                sort_by = st.selectbox("排序方式", ["创建时间", "商品名称", "价格", "库存量"], key="inventory_sort")
            with col5:
                sort_order = st.selectbox("排序顺序", ["降序", "升序"], key="inventory_order")
            
            # 应用筛选
            filtered_items = inventory_items.copy()
            
            # 搜索筛选
            if search_term:
                filtered_items = [item for item in filtered_items 
                                if search_term.lower() in item['product_name'].lower() 
                                or (item['description'] and search_term.lower() in item['description'].lower())]
            
            # 库存状态筛选
            if stock_filter != "全部":
                if stock_filter == "充足(>10)":
                    filtered_items = [item for item in filtered_items if item['quantity'] > 10]
                elif stock_filter == "偏少(1-10)":
                    filtered_items = [item for item in filtered_items if 1 <= item['quantity'] <= 10]
                elif stock_filter == "缺货(0)":
                    filtered_items = [item for item in filtered_items if item['quantity'] == 0]
            
            # 价格范围筛选
            if price_filter != "全部":
                if price_filter == "0-50元":
                    filtered_items = [item for item in filtered_items if 0 <= item['price'] <= 50]
                elif price_filter == "50-100元":
                    filtered_items = [item for item in filtered_items if 50 < item['price'] <= 100]
                elif price_filter == "100-200元":
                    filtered_items = [item for item in filtered_items if 100 < item['price'] <= 200]
                elif price_filter == "200元以上":
                    filtered_items = [item for item in filtered_items if item['price'] > 200]
            
            # 排序
            sort_key_map = {
                "创建时间": "created_at",
                "商品名称": "product_name",
                "价格": "price",
                "库存量": "quantity"
            }
            sort_key = sort_key_map[sort_by]
            reverse = sort_order == "降序"
            filtered_items = sorted(filtered_items, key=lambda x: x[sort_key], reverse=reverse)
            
            # 显示筛选结果统计
            total_count = len(inventory_items)
            filtered_count = len(filtered_items)
            if filtered_count != total_count:
                st.info(f"📊 显示 {filtered_count} / {total_count} 个商品")
            else:
                st.info(f"📊 共 {total_count} 个商品")
            
            # 库存状态统计
            stock_stats = {"充足": 0, "偏少": 0, "缺货": 0}
            for item in inventory_items:
                if item['quantity'] > 10:
                    stock_stats["充足"] += 1
                elif item['quantity'] > 0:
                    stock_stats["偏少"] += 1
                else:
                    stock_stats["缺货"] += 1
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("🟢 库存充足", stock_stats["充足"])
            with col_stat2:
                st.metric("🟡 库存偏少", stock_stats["偏少"])
            with col_stat3:
                st.metric("🔴 库存缺货", stock_stats["缺货"])
            
            # 卡片视图显示
            st.markdown("#### 🎴 库存卡片")
            st.markdown("---")
            if filtered_items:
                # 定义回调函数
                def on_inventory_edit(inventory_data):
                    st.session_state.edit_inventory_id = inventory_data['id']
                    st.session_state.edit_inventory_data = inventory_data
                    st.session_state.show_edit_inventory = True
                    st.rerun()
                
                def on_inventory_view(inventory_data):
                    st.session_state.view_inventory_data = inventory_data
                    st.session_state.show_inventory_details = True
                    st.rerun()
                
                def on_inventory_delete(inventory_data):
                    """删除库存商品的回调函数"""
                    try:
                        if db.delete_inventory_item(inventory_data['id']):
                            st.success("商品删除成功！")
                            st.rerun()
                        else:
                            st.error("删除失败！")
                    except Exception as e:
                        st.error(f"删除失败: {str(e)}")
                
                create_card_grid(filtered_items, card_type="inventory", columns=3,
                               on_edit=on_inventory_edit, on_view=on_inventory_view, on_delete=on_inventory_delete)
            else:
                st.info("暂无符合条件的库存数据")
        else:
            st.info("📝 暂无库存数据，请添加商品")
    
    with tab2:
        st.markdown("### ➕ 添加新商品")
        
        with st.form("add_inventory_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                product_name = st.text_input("📦 商品名称*", placeholder="请输入商品名称")
                description = st.text_area("📝 商品描述", placeholder="商品详细描述")
                
                # 图片上传 - 支持拖拽上传
                st.markdown("**🖼️ 商品图片**")
                uploaded_file = drag_drop_image_uploader(
                    key="inventory_image_upload",
                    label="拖拽图片到此处或点击上传",
                    help_text="支持 JPG, PNG, GIF 格式"
                )
                
                # 显示上传的图片预览
                if uploaded_file:
                    safe_image_display(uploaded_file, width=200, caption="商品图片预览")
            
            with col2:
                price = st.number_input("💰 价格*", min_value=0.0, step=0.01, format="%.2f")
                quantity = st.number_input("📊 初始库存*", min_value=0, step=1, format="%d")
            
            submitted = st.form_submit_button("➕ 添加商品", use_container_width=True)
            
            if submitted:
                if product_name:
                    # 处理图片上传
                    image_path = ""
                    if uploaded_file:
                        image_path = save_uploaded_file(uploaded_file, "inventory")
                    
                    item_id = db.add_inventory_item(product_name, description, price, quantity, image_path)
                    st.markdown(f'<div class="success-message">✅ 商品 "{product_name}" 添加成功！</div>', unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.markdown('<div class="error-message">❌ 请输入商品名称</div>', unsafe_allow_html=True)

# 订单管理页面
elif selected == "📋 订单管理":
    st.markdown("## 📋 订单管理")
    
    tab1, tab2 = st.tabs(["📋 订单列表", "➕ 创建订单"])
    
    with tab1:
        st.markdown("### 📋 订单列表")
        
        # 初始化分页和搜索状态
        if 'order_page' not in st.session_state:
            st.session_state.order_page = 1
        if 'order_search' not in st.session_state:
            st.session_state.order_search = ""
        if 'order_status_filter' not in st.session_state:
            st.session_state.order_status_filter = "all"
        if 'selected_orders' not in st.session_state:
            st.session_state.selected_orders = set()
        
        # 搜索和筛选区域
        st.markdown("#### 🔍 搜索与筛选")
        
        # 第一行：搜索框和状态筛选
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            search_term = st.text_input("🔍 搜索订单", 
                                      value=st.session_state.order_search,
                                      placeholder="输入客户名称、订单ID或备注...")
            if search_term != st.session_state.order_search:
                st.session_state.order_search = search_term
                st.session_state.order_page = 1  # 重置到第一页
                st.rerun()
        
        with col2:
            status_filter = st.selectbox("📊 状态筛选", 
                                       ["all", "pending", "completed"],
                                       format_func=lambda x: {"all": "全部", "pending": "待完成", "completed": "已完成"}[x],
                                       index=["all", "pending", "completed"].index(st.session_state.order_status_filter))
            if status_filter != st.session_state.order_status_filter:
                st.session_state.order_status_filter = status_filter
                st.session_state.order_page = 1  # 重置到第一页
                st.rerun()
        
        with col3:
            page_size = st.selectbox("📄 每页显示", [10, 20, 50], index=0)
        
        # 第二行：日期筛选和金额筛选
        col4, col5, col6 = st.columns(3)
        
        with col4:
            # 日期筛选
            date_filter = st.selectbox("📅 创建时间", 
                                     ["全部", "今天", "本周", "本月", "最近7天", "最近30天"],
                                     key="order_date_filter")
        
        with col5:
            # 金额范围筛选
            amount_filter = st.selectbox("💰 订单金额", 
                                       ["全部", "0-100", "100-500", "500-1000", "1000以上"],
                                       key="order_amount_filter")
        
        with col6:
            # 排序选项
            sort_by = st.selectbox("📊 排序方式", 
                                 ["创建时间(新到旧)", "创建时间(旧到新)", "金额(高到低)", "金额(低到高)"],
                                 key="order_sort")
        
        # 缓存机制 - 避免重复查询
        cache_key = f"orders_{st.session_state.order_page}_{page_size}_{st.session_state.order_search}_{st.session_state.order_status_filter}_{date_filter}_{amount_filter}_{sort_by}"
        
        # 检查缓存
        if ('order_cache_key' not in st.session_state or 
            st.session_state.order_cache_key != cache_key or
            'order_cache_data' not in st.session_state):
            
            # 显示加载状态
            with st.spinner("🔄 正在加载订单数据..."):
                # 获取分页数据
                orders, total_count = db.get_orders_paginated(
                    page=st.session_state.order_page,
                    page_size=page_size,
                    search_term=st.session_state.order_search,
                    status_filter=st.session_state.order_status_filter if st.session_state.order_status_filter != "all" else None,
                    date_filter=date_filter,
                    amount_filter=amount_filter,
                    sort_by=sort_by
                )
            
            # 缓存数据
            st.session_state.order_cache_key = cache_key
            st.session_state.order_cache_data = (orders, total_count)
        else:
            # 使用缓存数据
            orders, total_count = st.session_state.order_cache_data
        
        if total_count > 0:
            # 订单统计信息
            if orders:
                total_amount = sum(order['total_amount'] for order in orders)
                completed_orders = len([order for order in orders if order['status'] == 'completed'])
                pending_orders = len([order for order in orders if order['status'] == 'pending'])
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("当前页订单数", len(orders))
                with col_stat2:
                    st.metric("当前页总金额", f"¥{total_amount:.2f}")
                with col_stat3:
                    st.metric("已完成", completed_orders)
                with col_stat4:
                    st.metric("待完成", pending_orders)
            
            # 分页和批量操作区域
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            total_pages = (total_count + page_size - 1) // page_size
            current_order_ids = {order['id'] for order in orders}
            selected_count = len(st.session_state.selected_orders)
            
            with col1:
                # 分页控制
                st.markdown(f"**第 {st.session_state.order_page} / {total_pages} 页**")
                page_col1, page_col2 = st.columns(2)
                with page_col1:
                    if st.button("⏪ 上页", disabled=st.session_state.order_page == 1, use_container_width=True):
                        st.session_state.order_page -= 1
                        st.rerun()
                with page_col2:
                    if st.button("下页 ⏩", disabled=st.session_state.order_page == total_pages, use_container_width=True):
                        st.session_state.order_page += 1
                        st.rerun()
            
            with col2:
                # 批量选择
                st.markdown("**批量选择**")
                select_col1, select_col2 = st.columns(2)
                with select_col1:
                    if st.button("全选", use_container_width=True):
                        st.session_state.selected_orders.update(current_order_ids)
                        st.rerun()
                with select_col2:
                    if st.button("取消", use_container_width=True):
                        st.session_state.selected_orders -= current_order_ids
                        st.rerun()
            
            with col3:
                # 导出功能
                st.markdown(f"**已选择: {selected_count} 个**")
                
                # CSV导出
                if st.button("📊 导出CSV", use_container_width=True, disabled=selected_count == 0):
                    if selected_count > 0:
                        try:
                            # 使用导出服务
                            csv_content, filename = export_service.export_orders_to_csv(
                                list(st.session_state.selected_orders)
                            )
                            
                            # 提供下载
                            st.download_button(
                                label="💾 下载CSV文件",
                                data=csv_content,
                                file_name=filename,
                                mime="text/csv",
                                use_container_width=True,
                                key="download_csv_btn"
                            )
                            
                            st.success(f"✅ 已生成 {selected_count} 个订单的CSV文件")
                        except Exception as e:
                            st.error(f"❌ CSV导出失败: {str(e)}")
                
                # PDF导出
                if st.button("📄 导出PDF", use_container_width=True, disabled=selected_count == 0):
                    if selected_count > 0:
                        try:
                            # 使用导出服务
                            pdf_data, pdf_filename = export_service.export_orders_to_pdf(
                                list(st.session_state.selected_orders)
                            )
                            
                            # 提供下载
                            st.download_button(
                                label="💾 下载PDF文件",
                                data=pdf_data,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_pdf_btn"
                            )
                            
                            st.success(f"✅ 已生成 {selected_count} 个订单的PDF文件")
                        except Exception as e:
                            st.error(f"❌ PDF导出失败: {str(e)}")
                
                # 批量打印 (76mm*130mm)
                if st.button("🖨️ 批量打印", use_container_width=True, disabled=selected_count == 0):
                    if selected_count > 0:
                        try:
                            # 使用导出服务的批量打印功能
                            print_data, print_filename = export_service.batch_print_orders(
                                list(st.session_state.selected_orders)
                            )
                            
                            # 提供下载
                            st.download_button(
                                label="💾 下载打印文件",
                                data=print_data,
                                file_name=print_filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_print_btn"
                            )
                            
                            st.success(f"✅ 已生成 {selected_count} 个订单的打印文件 (76mm×130mm)")
                        except Exception as e:
                            st.error(f"❌ 批量打印失败: {str(e)}")
            
            with col4:
                # 批量删除
                st.markdown("**批量操作**")
                if st.button("🗑️ 批量删除", use_container_width=True, disabled=selected_count == 0, type="secondary"):
                    if selected_count > 0:
                        # 确认删除
                        if st.session_state.get('confirm_batch_delete', False):
                            try:
                                deleted_count, failed_ids = db.delete_orders_batch(list(st.session_state.selected_orders))
                                
                                if deleted_count > 0:
                                    st.success(f"✅ 成功删除 {deleted_count} 个订单")
                                    st.session_state.selected_orders = set()
                                    st.session_state.confirm_batch_delete = False
                                    # 清理缓存
                                    if 'order_cache_key' in st.session_state:
                                        del st.session_state.order_cache_key
                                    if 'order_cache_data' in st.session_state:
                                        del st.session_state.order_cache_data
                                    st.rerun()
                                
                                if failed_ids:
                                    st.warning(f"⚠️ {len(failed_ids)} 个订单删除失败（可能是已完成状态）")
                            except Exception as e:
                                st.error(f"❌ 批量删除失败: {str(e)}")
                        else:
                            st.session_state.confirm_batch_delete = True
                            st.warning(f"⚠️ 确认要删除 {selected_count} 个订单吗？再次点击确认删除。")
            
            st.markdown("---")
            
            # 订单列表显示
            for order in orders:
                status_icon = "✅" if order['status'] == 'completed' else "⏳"
                
                # 订单卡片
                with st.container():
                    col_checkbox, col_content = st.columns([1, 20])
                    
                    with col_checkbox:
                        is_selected = st.checkbox(
                            "选择",
                            value=order['id'] in st.session_state.selected_orders,
                            key=f"select_order_{order['id']}",
                            label_visibility="collapsed"
                        )
                        
                        # 更新选中状态
                        if is_selected:
                            st.session_state.selected_orders.add(order['id'])
                        else:
                            st.session_state.selected_orders.discard(order['id'])
                    
                    with col_content:
                        # 订单基本信息
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                        
                        with col1:
                            st.markdown(f"**{status_icon} 订单 #{order['id']}**")
                            st.write(f"客户: {order['customer_name']}")
                        
                        with col2:
                            st.write(f"金额: ¥{order['total_amount']:.2f}")
                            st.write(f"状态: {order['status']}")
                        
                        with col3:
                            st.write(f"创建: {order['created_at']}")
                            if order['notes']:
                                st.write(f"备注: {order['notes'][:20]}...")
                        
                        with col4:
                            # 快速操作按钮
                            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                            
                            with btn_col1:
                                if st.button("👁️", key=f"view_{order['id']}", help="查看详情"):
                                    st.session_state[f"show_details_{order['id']}"] = not st.session_state.get(f"show_details_{order['id']}", False)
                                    st.rerun()
                            
                            with btn_col2:
                                if st.button("✏️", key=f"edit_{order['id']}", help="编辑"):
                                    st.session_state[f"edit_order_{order['id']}"] = True
                                    st.rerun()
                            
                            with btn_col3:
                                if order['status'] != 'completed':
                                    if st.button("💳", key=f"complete_{order['id']}", help="完成支付"):
                                        db.complete_order_payment(order['id'])
                                        st.success("✅ 订单支付完成")
                                        # 清理缓存
                                        if 'order_cache_key' in st.session_state:
                                            del st.session_state.order_cache_key
                                        if 'order_cache_data' in st.session_state:
                                            del st.session_state.order_cache_data
                                        st.rerun()
                            
                            with btn_col4:
                                if order['status'] != 'completed':
                                    if st.button("🗑️", key=f"delete_{order['id']}", help="删除", type="secondary"):
                                        success = db.delete_order(order['id'])
                                        if success:
                                            st.success("✅ 订单已删除")
                                            # 清理缓存
                                            if 'order_cache_key' in st.session_state:
                                                del st.session_state.order_cache_key
                                            if 'order_cache_data' in st.session_state:
                                                del st.session_state.order_cache_data
                                            st.rerun()
                                        else:
                                            st.error("❌ 删除失败")
                        
                        # 详细信息展开
                        if st.session_state.get(f"show_details_{order['id']}", False):
                            st.markdown("---")
                            
                            detail_col1, detail_col2 = st.columns(2)
                            
                            with detail_col1:
                                st.markdown("**订单详情:**")
                                st.write(f"客户: {order['customer_name']}")
                                st.write(f"总金额: ¥{order['total_amount']:.2f}")
                                st.write(f"状态: {order['status']}")
                                st.write(f"创建时间: {order['created_at']}")
                                st.write(f"备注: {order['notes'] or '无'}")
                            
                            with detail_col2:
                                # 显示订单图片
                                if order.get('image_path'):
                                    st.markdown("**订单图片:**")
                                    display_uploaded_media(order['image_path'])
                            
                            # 显示订单商品详情
                            st.markdown("**订单商品:**")
                            order_items = db.get_order_items(order['id'])
                            
                            if order_items:
                                for item in order_items:
                                    if item['item_type'] == '现货':
                                        st.write(f"• 现货: {item['inventory_name']} × {item['quantity']} = ¥{item['unit_price'] * item['quantity']:.2f}")
                                    else:  # 定制商品
                                        st.write(f"• 定制: {item['inventory_name']} × {item['quantity']} = ¥{item['unit_price'] * item['quantity']:.2f}")
                                        if item.get('outer_fabric_name'):
                                            st.write(f"  表布: {item['outer_fabric_name']}")
                                        if item.get('inner_fabric_name'):
                                            st.write(f"  里布: {item['inner_fabric_name']}")
                                    if item['notes']:
                                        st.write(f"  备注: {item['notes']}")
                            
                            # 积分操作区域
                            st.markdown("---")
                            st.markdown("**💰 积分操作:**")
                            
                            # 检查订单是否已完成且未加过积分
                            points_awarded = order.get('points_awarded', False)
                            order_completed = order['status'] == 'completed'
                            
                            if order_completed and not points_awarded:
                                # 计算建议积分（订单金额的1%，向下取整）
                                suggested_points = int(order['total_amount'] * 0.01)
                                
                                col_points1, col_points2 = st.columns([2, 1])
                                
                                with col_points1:
                                    points_to_award = st.number_input(
                                        f"给客户加积分 (建议: {suggested_points}分)", 
                                        min_value=0, 
                                        value=suggested_points, 
                                        step=1,
                                        key=f"points_input_{order['id']}"
                                    )
                                
                                with col_points2:
                                    if st.button(f"🎁 加积分", key=f"award_points_{order['id']}"):
                                        if points_to_award > 0:
                                            try:
                                                # 获取客户当前积分
                                                customer = db.get_customer_by_id(order['customer_id'])
                                                if customer:
                                                    current_points = customer['points']
                                                    
                                                    # 使用新的积分更新方法，记录历史
                                                    success = db.update_customer_points_with_history(
                                                        customer_id=order['customer_id'],
                                                        points_change=points_to_award,
                                                        change_type='order_reward',
                                                        order_id=order['id'],
                                                        reason=f"订单#{order['id']}完成奖励",
                                                        operator='系统'
                                                    )
                                                    
                                                    if success:
                                                        # 标记订单已加积分
                                                        db.execute_query(
                                                            "UPDATE orders SET points_awarded = 1 WHERE id = ?",
                                                            (order['id'],)
                                                        )
                                                        
                                                        st.success(f"✅ 成功给客户 {order['customer_name']} 加了 {points_to_award} 积分！")
                                                        
                                                        # 清理缓存
                                                        if 'order_cache_key' in st.session_state:
                                                            del st.session_state.order_cache_key
                                                        if 'order_cache_data' in st.session_state:
                                                            del st.session_state.order_cache_data
                                                        
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ 加积分失败，请重试")
                                                else:
                                                    st.error("❌ 找不到客户信息")
                                            except Exception as e:
                                                st.error(f"❌ 操作失败: {str(e)}")
                                        else:
                                            st.warning("⚠️ 请输入大于0的积分数量")
                            
                            elif order_completed and points_awarded:
                                st.info("ℹ️ 该订单已经给客户加过积分了")
                            
                            elif not order_completed:
                                st.info("ℹ️ 订单完成后可给客户加积分")
                        
                        # 编辑订单表单（弹窗式）
                        if st.session_state.get(f"edit_order_{order['id']}", False):
                            st.markdown("---")
                            st.markdown("**✏️ 编辑订单信息:**")
                            
                            with st.form(f"edit_order_form_{order['id']}"):
                                edit_col1, edit_col2 = st.columns(2)
                                
                                with edit_col1:
                                    # 客户选择
                                    customers = db.get_customers()
                                    customer_options = [f"{c['nickname']} ({c['phone_suffix']})" for c in customers]
                                    current_customer_index = next((i for i, c in enumerate(customers) if c['id'] == order['customer_id']), 0)
                                    selected_customer_index = st.selectbox("选择客户", range(len(customer_options)), 
                                                                         format_func=lambda x: customer_options[x],
                                                                         index=current_customer_index)
                                    
                                    new_notes = st.text_area("订单备注", value=order['notes'] or "")
                                
                                with edit_col2:
                                    new_status = st.selectbox("订单状态", ["pending", "completed"], 
                                                            index=0 if order['status'] == 'pending' else 1)
                                    new_image_path = st.text_input("图片路径", value=order['image_path'] or "")
                                
                                col_save, col_cancel = st.columns(2)
                                
                                with col_save:
                                    if st.form_submit_button("💾 保存修改", use_container_width=True):
                                        selected_customer = customers[selected_customer_index]
                                        success = db.update_order(order['id'], selected_customer['id'], 
                                                                new_notes, new_image_path, new_status)
                                        if success:
                                            st.success("✅ 订单信息已更新")
                                            st.session_state[f"edit_order_{order['id']}"] = False
                                            # 清理缓存
                                            if 'order_cache_key' in st.session_state:
                                                del st.session_state.order_cache_key
                                            if 'order_cache_data' in st.session_state:
                                                del st.session_state.order_cache_data
                                            st.rerun()
                                        else:
                                            st.error("❌ 更新失败")
                                
                                with col_cancel:
                                    if st.form_submit_button("❌ 取消", use_container_width=True):
                                        st.session_state[f"edit_order_{order['id']}"] = False
                                        st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("📝 暂无订单数据，请创建订单或调整搜索条件")
    
    with tab2:
        st.markdown("### ➕ 创建新订单")
        
        # 步骤1：选择客户
        st.markdown("#### 步骤1: 选择客户")
        customers = db.get_customers()
        
        if not customers:
            st.warning("⚠️ 请先在客户管理中添加客户")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                customer_options = [f"{customer['nickname']} (ID: {customer['id']})" for customer in customers]
                selected_customer = st.selectbox("选择客户", customer_options)
                customer_id = int(selected_customer.split("ID: ")[1].split(")")[0])
            
            with col2:
                if st.button("➕ 新建客户"):
                    st.info("请前往客户管理页面添加新客户")
            
            # 步骤2：添加商品
            st.markdown("#### 步骤2: 添加商品")
            
            if 'order_items' not in st.session_state:
                st.session_state.order_items = []
            
            # 添加现货商品
            inventory_items = db.get_inventory_items()
            available_items = [item for item in inventory_items if item['quantity'] > 0]
            
            if available_items:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    item_options = [f"{item['product_name']} (库存: {item['quantity']}, ¥{item['price']:.2f})" for item in available_items]
                    selected_item = st.selectbox("选择现货商品", item_options)
                    item_index = item_options.index(selected_item)
                    selected_inventory = available_items[item_index]
                
                with col2:
                    quantity = st.number_input("数量", min_value=1, max_value=selected_inventory['quantity'], value=1, step=1, format="%d")
                
                with col3:
                    if st.button("➕ 添加到订单"):
                        order_item = {
                            'type': '现货',
                            'inventory_id': selected_inventory['id'],
                            'name': selected_inventory['product_name'],
                            'quantity': quantity,
                            'unit_price': selected_inventory['price'],
                            'total_price': selected_inventory['price'] * quantity
                        }
                        st.session_state.order_items.append(order_item)
                        st.success("✅ 商品已添加到订单")
            else:
                st.warning("⚠️ 暂无可用现货商品")
            
            # 添加定制商品
            st.markdown("---")
            st.markdown("##### 🎨 添加定制商品")
            
            # 获取面料数据
            fabrics = db.get_fabrics()
            
            if available_items and fabrics:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                
                with col1:
                    # 选择基础商品
                    custom_item_options = [f"{item['product_name']} (¥{item['price']:.2f})" for item in available_items]
                    selected_custom_item = st.selectbox("选择基础商品", custom_item_options, key="custom_base_item")
                    custom_item_index = custom_item_options.index(selected_custom_item)
                    selected_custom_inventory = available_items[custom_item_index]
                
                with col2:
                    # 选择表布 - 只显示用途类型为"表布"的面料
                    outer_fabrics = [fabric for fabric in fabrics if fabric['usage_type'] == '表布']
                    if outer_fabrics:
                        outer_fabric_options = [f"{fabric['name']} ({fabric['material_type']})" for fabric in outer_fabrics]
                        selected_outer_fabric = st.selectbox("选择表布", outer_fabric_options, key="outer_fabric")
                        outer_fabric_index = outer_fabric_options.index(selected_outer_fabric)
                        selected_outer_fabric_data = outer_fabrics[outer_fabric_index]
                    else:
                        st.warning("⚠️ 暂无表布面料")
                        selected_outer_fabric_data = None
                
                with col3:
                    # 选择里布 - 只显示用途类型为"里布"的面料
                    inner_fabrics = [fabric for fabric in fabrics if fabric['usage_type'] == '里布']
                    if inner_fabrics:
                        inner_fabric_options = [f"{fabric['name']} ({fabric['material_type']})" for fabric in inner_fabrics]
                        selected_inner_fabric = st.selectbox("选择里布", inner_fabric_options, key="inner_fabric")
                        inner_fabric_index = inner_fabric_options.index(selected_inner_fabric)
                        selected_inner_fabric_data = inner_fabrics[inner_fabric_index]
                    else:
                        st.warning("⚠️ 暂无里布面料")
                        selected_inner_fabric_data = None
                
                with col4:
                    custom_quantity = st.number_input("数量", min_value=1, value=1, step=1, format="%d", key="custom_quantity")
                
                with col5:
                    price_value = selected_custom_inventory['price'] if selected_custom_inventory['price'] is not None else 0
                    custom_price = st.number_input("定制价格", min_value=0.0, value=float(price_value), step=0.01, format="%.2f", key="custom_price")
                
                # 定制商品备注
                custom_notes = st.text_area("定制备注", placeholder="特殊要求、工艺说明等", key="custom_notes")
                
                if st.button("🎨 添加定制商品到订单"):
                    # 验证面料选择
                    if selected_outer_fabric_data is None or selected_inner_fabric_data is None:
                        st.error("❌ 请确保选择了表布和里布")
                    else:
                        custom_order_item = {
                            'type': '定制',
                            'inventory_id': selected_custom_inventory['id'],
                            'outer_fabric_id': selected_outer_fabric_data['id'],
                            'inner_fabric_id': selected_inner_fabric_data['id'],
                            'name': f"定制-{selected_custom_inventory['product_name']}",
                            'outer_fabric_name': selected_outer_fabric_data['name'],
                            'inner_fabric_name': selected_inner_fabric_data['name'],
                            'quantity': custom_quantity,
                            'unit_price': custom_price,
                            'total_price': custom_price * custom_quantity,
                            'notes': custom_notes
                        }
                        st.session_state.order_items.append(custom_order_item)
                        st.success("✅ 定制商品已添加到订单")
            else:
                if not available_items:
                    st.warning("⚠️ 暂无可用商品作为定制基础")
                if not fabrics:
                    st.warning("⚠️ 暂无可用面料，请先添加面料")
            
            # 显示当前订单商品
            if st.session_state.order_items:
                st.markdown("#### 当前订单商品")
                total_amount = 0
                
                for i, item in enumerate(st.session_state.order_items):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if item['type'] == '现货':
                            st.write(f"• 现货: {item['name']} × {item['quantity']} = ¥{item['total_price']:.2f}")
                        else:  # 定制商品
                            st.write(f"• 定制: {item['name']} × {item['quantity']} = ¥{item['total_price']:.2f}")
                            st.write(f"  表布: {item['outer_fabric_name']}, 里布: {item['inner_fabric_name']}")
                            if item.get('notes'):
                                st.write(f"  备注: {item['notes']}")
                    
                    with col2:
                        if st.button("🗑️", key=f"remove_item_{i}"):
                            st.session_state.order_items.pop(i)
                            st.rerun()
                    
                    total_amount += item['total_price']
                
                st.markdown(f"**订单总金额: ¥{total_amount:.2f}**")
                
                # 步骤3：订单备注和图片上传
                st.markdown("#### 步骤3: 订单备注和图片")
                order_notes = st.text_area("订单备注", placeholder="特殊要求、交货时间等")
                
                # 图片上传区域
                st.markdown("##### 📸 订单图片上传")
                uploaded_file, order_image_path = drag_drop_image_uploader("order_image", "订单相关图片（可选）", category="order")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 创建订单", use_container_width=True):
                        # 创建订单
                        # 确保order_image_path是字符串
                        image_path = order_image_path if isinstance(order_image_path, str) else ""
                        order_id = db.create_order(customer_id, order_notes, image_path)
                        
                        # 添加订单商品
                        for item in st.session_state.order_items:
                            if item['type'] == '现货':
                                db.add_order_item(
                                    order_id, '现货', item['quantity'], item['unit_price'],
                                    inventory_id=item['inventory_id']
                                )
                            else:  # 定制商品
                                db.add_order_item(
                                    order_id, '定制', item['quantity'], item['unit_price'],
                                    notes=item.get('notes', ''),
                                    inventory_id=item['inventory_id'],
                                    outer_fabric_id=item['outer_fabric_id'],
                                    inner_fabric_id=item['inner_fabric_id']
                                )
                        
                        # 自动完成支付
                        db.complete_order_payment(order_id)
                        
                        # 获取订单总金额用于显示
                        orders = db.get_orders()
                        created_order = next((o for o in orders if o['id'] == order_id), None)
                        total_amount = created_order['total_amount'] if created_order else 0
                        
                        st.session_state.order_items = []  # 清空订单商品
                        # 清理缓存
                        if 'order_cache_key' in st.session_state:
                            del st.session_state.order_cache_key
                        if 'order_cache_data' in st.session_state:
                            del st.session_state.order_cache_data
                        
                        # 保存新创建的订单信息到session_state，用于积分奖励
                        st.session_state.newly_created_order = {
                            'id': order_id,
                            'customer_id': customer_id,
                            'total_amount': total_amount,
                            'customer_name': next((c['nickname'] for c in customers if c['id'] == customer_id), '未知客户')
                        }
                        
                        st.success(f"✅ 订单创建成功！订单号: {order_id}")
                        st.success(f"💰 订单金额: ¥{total_amount:.2f}")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ 清空订单", use_container_width=True):
                        st.session_state.order_items = []
                        st.rerun()
            
            # 积分奖励区域 - 在订单创建成功后显示
            if 'newly_created_order' in st.session_state:
                order_info = st.session_state.newly_created_order
                
                # 检查订单是否已经加过积分
                orders = db.get_orders()
                current_order = next((o for o in orders if o['id'] == order_info['id']), None)
                
                if current_order and not current_order.get('points_awarded', False):
                    st.markdown("---")
                    st.markdown("### 🎁 积分奖励")
                    
                    # 计算建议积分（等于订单金额）
                    suggested_points = max(1, int(order_info['total_amount']))
                    
                    st.info(f"💡 为客户 **{order_info['customer_name']}** 奖励积分？")
                    st.write(f"📊 订单金额: ¥{order_info['total_amount']:.2f}")
                    st.write(f"⭐ 建议积分: {suggested_points} 分（等于订单金额）")
                    
                    col1, col2, col3 = st.columns([2, 2, 2])
                    
                    with col1:
                        # 积分数量输入
                        points_to_award = st.number_input(
                            "积分数量", 
                            min_value=0, 
                            value=suggested_points, 
                            step=1,
                            key=f"points_award_{order_info['id']}"
                        )
                    
                    with col2:
                        if st.button("🎁 奖励积分", use_container_width=True, key=f"award_points_{order_info['id']}"):
                            if points_to_award > 0:
                                try:
                                    # 使用积分历史记录功能更新客户积分
                                    success = db.update_customer_points_with_history(
                                        order_info['customer_id'], 
                                        points_to_award, 
                                        'order',  # change_type
                                        order_info['id'],  # order_id
                                        f"订单奖励 - 订单号: {order_info['id']}"  # reason
                                    )
                                    
                                    if success:
                                        # 标记订单已加积分
                                        db.update_order(order_info['id'], points_awarded=True)
                                        
                                        st.success(f"✅ 成功为客户 {order_info['customer_name']} 奖励 {points_to_award} 积分！")
                                        
                                        # 清理session_state
                                        del st.session_state.newly_created_order
                                        
                                        # 清理缓存
                                        if 'customer_cache_key' in st.session_state:
                                            del st.session_state.customer_cache_key
                                        if 'customer_cache_data' in st.session_state:
                                            del st.session_state.customer_cache_data
                                        
                                        st.rerun()
                                    else:
                                        st.error("❌ 积分奖励失败，请重试")
                                except Exception as e:
                                    st.error(f"❌ 积分奖励失败: {str(e)}")
                            else:
                                st.warning("⚠️ 积分数量必须大于0")
                    
                    with col3:
                        if st.button("⏭️ 跳过奖励", use_container_width=True, key=f"skip_points_{order_info['id']}"):
                            # 标记订单已处理积分（跳过）
                            db.update_order(order_info['id'], points_awarded=True)
                            
                            # 清理session_state
                            del st.session_state.newly_created_order
                            st.info("已跳过积分奖励")
                            st.rerun()
                elif current_order and current_order.get('points_awarded', False):
                    # 如果已经加过积分，清理session_state
                    del st.session_state.newly_created_order

# 代加工管理页面
elif selected == "🏭 加工管理":
    show_processing_management()

# 系统设置页面
elif selected == "⚙️ 系统设置":
    st.markdown("## ⚙️ 系统设置")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["🗄️ 自动备份", "📊 系统信息", "🔧 高级设置"])
    
    with tab1:
        st.markdown("### 🗄️ 自动备份管理")
        
        # 备份状态信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📋 备份状态")
            from auto_backup import AutoBackup
            backup_manager = AutoBackup(db)
            
            # 检查今日备份状态
            data_types = ["customers", "fabrics", "orders", "inventory"]
            backup_status = {}
            for data_type in data_types:
                backup_status[data_type] = backup_manager.is_backup_exists_today(data_type)
            
            # 显示备份状态
            for data_type, exists in backup_status.items():
                type_names = {
                    "customers": "👥 客户数据",
                    "fabrics": "🧵 面料数据", 
                    "orders": "📋 订单数据",
                    "inventory": "📦 库存数据"
                }
                status_icon = "✅" if exists else "❌"
                st.write(f"{status_icon} {type_names[data_type]}: {'已备份' if exists else '未备份'}")
        
        with col2:
            st.markdown("#### 🔄 备份操作")
            
            if st.button("🔄 立即执行完整备份", use_container_width=True):
                with st.spinner("正在执行备份..."):
                    from auto_backup import check_and_perform_backup
                    check_and_perform_backup(db, force_backup=True)
                st.rerun()
            
            st.markdown("---")
            
            # 备份历史
            st.markdown("#### 📁 备份文件管理")
            import os
            backup_dir = "backups"
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
                backup_files.sort(reverse=True)  # 最新的在前
                
                if backup_files:
                    st.write(f"📂 共找到 {len(backup_files)} 个备份文件：")
                    
                    # 显示最近的备份文件
                    for i, file in enumerate(backup_files[:10]):  # 只显示最近10个
                        file_path = os.path.join(backup_dir, file)
                        file_size = os.path.getsize(file_path)
                        file_size_kb = file_size / 1024
                        
                        col_file, col_size, col_action = st.columns([3, 1, 1])
                        with col_file:
                            st.write(f"📄 {file}")
                        with col_size:
                            st.write(f"{file_size_kb:.1f}KB")
                        with col_action:
                            if st.button("📥", key=f"download_{i}", help="下载备份文件"):
                                with open(file_path, 'rb') as f:
                                    st.download_button(
                                        label="下载",
                                        data=f.read(),
                                        file_name=file,
                                        mime="application/json",
                                        key=f"download_btn_{i}"
                                    )
                else:
                    st.info("📭 暂无备份文件")
            else:
                st.info("📁 备份目录不存在")
    
    with tab2:
        st.markdown("### 📊 系统信息")
        
        # 数据统计
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 数据统计")
            customers = db.get_customers()
            orders = db.get_orders()
            inventory_items = db.get_inventory_items()
            fabrics = db.get_fabrics()
            
            st.metric("👥 客户总数", len(customers))
            st.metric("📋 订单总数", len(orders))
            st.metric("📦 库存商品", len(inventory_items))
            st.metric("🧵 面料种类", len(fabrics))
        
        with col2:
            st.markdown("#### 💾 数据库信息")
            import sqlite3
            import os
            
            db_path = "handmade_shop.db"
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                db_size_mb = db_size / (1024 * 1024)
                st.metric("💾 数据库大小", f"{db_size_mb:.2f} MB")
                
                # 获取数据库表信息
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                st.metric("📋 数据表数量", len(tables))
                
                # 显示表名
                st.markdown("**数据表列表：**")
                for table in tables:
                    st.write(f"• {table[0]}")
            else:
                st.error("❌ 数据库文件不存在")
    
    with tab3:
        st.markdown("### 🔧 高级设置")
        
        st.markdown("#### ⚠️ 危险操作")
        st.warning("以下操作可能影响系统数据，请谨慎使用！")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清理旧备份文件", use_container_width=True):
                st.info("此功能将在后续版本中实现")
        
        with col2:
            if st.button("🔄 重置缓存", use_container_width=True):
                # 清理所有缓存
                cache_keys = [key for key in st.session_state.keys() if 'cache' in key]
                for key in cache_keys:
                    del st.session_state[key]
                st.success("✅ 缓存已清理")
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📋 系统版本信息")
        st.info("星之梦手作管理系统 v1.0.0")
        st.info("最后更新：2025-10-17")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🏪 星之梦手作管理系统 | 让生意管理更简单高效
    </div>
    """, 
    unsafe_allow_html=True
)

if __name__ == "__main__":
    pass