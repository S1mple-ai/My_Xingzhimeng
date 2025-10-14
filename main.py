import streamlit as st
import pandas as pd
from datetime import datetime
from database import DatabaseManager
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from upload_components import drag_drop_image_uploader, drag_drop_media_uploader, display_uploaded_media
from category_management import render_category_management
from ui_components import (
    show_loading_spinner, show_progress_bar, show_success_message, 
    show_error_message, show_warning_message, create_metric_card,
    create_action_button, create_confirmation_dialog
)

# 页面配置
st.set_page_config(
    page_title="生意管理系统",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据库
@st.cache_resource
def init_database():
    return DatabaseManager()

db = init_database()

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
st.markdown('<div class="main-header">🏪 生意管理系统</div>', unsafe_allow_html=True)

# 侧边栏导航
with st.sidebar:
    st.markdown("### 📋 系统导航")
    selected = option_menu(
        menu_title=None,
        options=["📊 仪表板", "👥 客户管理", "🧵 面料管理", "👜 包型管理", "📦 库存管理", "📋 订单管理"],
        icons=["graph-up", "people", "palette", "bag", "box", "clipboard-check"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#1f77b4", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#1f77b4"},
        }
    )

# 仪表板页面
if selected == "📊 仪表板":
    st.markdown("## 📊 业务概览")
    
    # 显示加载状态
    with st.spinner("正在加载数据..."):
        # 获取统计数据
        customers = db.get_customers()
        orders = db.get_orders()
        inventory_items = db.get_inventory_items()
        fabrics = db.get_fabrics()
        bag_types = db.get_bag_types()
    
    # 显示关键指标 - 使用新的UI组件
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card("客户总数", str(len(customers)), icon="👥")
    
    with col2:
        create_metric_card("订单总数", str(len(orders)), icon="📋")
    
    with col3:
        total_revenue = sum([order['total_amount'] for order in orders if order['total_amount']])
        # 计算收入变化（这里简化为示例）
        revenue_delta = "+12.5%" if total_revenue > 0 else "0%"
        create_metric_card("总收入", f"¥{total_revenue:.2f}", revenue_delta, "💰")
    
    with col4:
        total_inventory_value = sum([item['price'] * item['quantity'] for item in inventory_items])
        create_metric_card("库存价值", f"¥{total_inventory_value:.2f}", icon="📦")
    
    # 图表展示
    if orders:
        st.markdown("### 📈 订单趋势")
        df_orders = pd.DataFrame(orders)
        df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
        df_orders['date'] = df_orders['created_at'].dt.date
        
        daily_orders = df_orders.groupby('date').agg({
            'id': 'count',
            'total_amount': 'sum'
        }).reset_index()
        daily_orders.columns = ['日期', '订单数量', '销售额']
        
        col1, col2 = st.columns(2)
        with col1:
            # 现代化的线图样式
            fig1 = px.line(daily_orders, x='日期', y='订单数量', title='每日订单数量')
            fig1.update_traces(
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=8, color='#2E86AB')
            )
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # 现代化的柱状图样式
            fig2 = px.bar(daily_orders, x='日期', y='销售额', title='每日销售额')
            fig2.update_traces(
                marker_color='#F18F01',
                marker_line_color='#F18F01',
                marker_line_width=1
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#2D3748',
                font=dict(color='#2D3748'),
                xaxis=dict(showgrid=True, gridcolor='#E2E8F0'),
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("📊 暂无订单数据，无法显示趋势图表")
    
    # 库存预警 - 使用新的UI组件
    st.markdown("### ⚠️ 库存预警")
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
            
            # 搜索功能
            search_term = st.text_input("🔍 搜索客户", placeholder="输入客户昵称或手机尾号")
            if search_term:
                df_customers = df_customers[
                    df_customers['nickname'].str.contains(search_term, case=False, na=False) |
                    df_customers['phone_suffix'].str.contains(search_term, case=False, na=False)
                ]
            
            # 显示客户列表
            for _, customer in df_customers.iterrows():
                with st.expander(f"👤 {customer['nickname']} - 积分: {customer['points']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        new_nickname = st.text_input("昵称", value=customer['nickname'], key=f"nickname_{customer['id']}")
                        new_phone = st.text_input("手机尾号", value=customer['phone_suffix'] or "", key=f"phone_{customer['id']}")
                    
                    with col2:
                        new_notes = st.text_area("备注", value=customer['notes'] or "", key=f"notes_{customer['id']}")
                        new_points = st.number_input("积分", value=customer['points'], key=f"points_{customer['id']}")
                    
                    with col3:
                        if create_action_button("💾 更新", f"update_{customer['id']}", "primary"):
                            try:
                                db.update_customer(customer['id'], new_nickname, new_phone, new_notes)
                                # 更新积分
                                points_diff = new_points - customer['points']
                                if points_diff != 0:
                                    db.update_customer_points(customer['id'], points_diff)
                                show_success_message("客户信息已更新")
                                st.rerun()
                            except Exception as e:
                                show_error_message(f"更新客户信息失败: {str(e)}")
                        
                        # 使用确认对话框进行删除操作
                        if create_action_button("🗑️ 删除", f"delete_{customer['id']}", "danger"):
                            if create_confirmation_dialog(
                                f"确认删除客户 '{customer['nickname']}' 吗？",
                                f"delete_confirm_{customer['id']}"
                            ):
                                try:
                                    db.delete_customer(customer['id'])
                                    show_success_message("客户已删除")
                                    st.rerun()
                                except Exception as e:
                                    show_error_message(f"删除客户失败: {str(e)}")
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
        
        # 筛选选项
        col1, col2 = st.columns(2)
        with col1:
            material_filter = st.selectbox("材质类型筛选", ["全部", "细帆", "细帆绗棉", "缎面绗棉"])
        with col2:
            usage_filter = st.selectbox("用途筛选", ["全部", "表布", "里布"])
        
        # 添加加载状态
        with st.spinner("正在加载面料数据..."):
            fabrics = db.get_fabrics()
        
        if fabrics:
            df_fabrics = pd.DataFrame(fabrics)
            
            # 应用筛选
            if material_filter != "全部":
                df_fabrics = df_fabrics[df_fabrics['material_type'] == material_filter]
            if usage_filter != "全部":
                df_fabrics = df_fabrics[df_fabrics['usage_type'] == usage_filter]
            
            # 显示面料列表
            for _, fabric in df_fabrics.iterrows():
                with st.expander(f"🧵 {fabric['name']} - {fabric['material_type']} ({fabric['usage_type']})"):
                    # 显示现有图片
                    if fabric.get('image_path'):
                        display_uploaded_media(image_path=fabric['image_path'])
                    
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        new_name = st.text_input("面料名称", value=fabric['name'], key=f"fabric_name_{fabric['id']}")
                        new_material = st.selectbox("材质类型", ["细帆", "细帆绗棉", "缎面绗棉"], 
                                                  index=["细帆", "细帆绗棉", "缎面绗棉"].index(fabric['material_type']),
                                                  key=f"fabric_material_{fabric['id']}")
                    
                    with col2:
                        new_usage = st.selectbox("用途", ["表布", "里布"], 
                                                index=["表布", "里布"].index(fabric['usage_type']),
                                                key=f"fabric_usage_{fabric['id']}")
                        
                        # 图片更新
                        st.markdown("**更新图片:**")
                        uploaded_file, new_image_path = drag_drop_image_uploader(
                            key=f"fabric_update_image_{fabric['id']}", 
                            label="", 
                            help_text="上传新图片以替换现有图片"
                        )
                    
                    with col3:
                        if create_action_button("💾 更新", f"update_fabric_{fabric['id']}", "primary"):
                            try:
                                # 如果有新图片，使用新图片路径，否则保持原有路径
                                final_image_path = new_image_path if new_image_path else fabric.get('image_path')
                                db.update_fabric(fabric['id'], new_name, new_material, new_usage, final_image_path)
                                show_success_message("面料信息已更新")
                                st.rerun()
                            except Exception as e:
                                show_error_message(f"更新面料信息失败: {str(e)}")
                        
                        # 删除按钮和确认逻辑
                        delete_key = f"delete_fabric_{fabric['id']}"
                        confirm_key = f"confirm_delete_fabric_{fabric['id']}"
                        
                        if create_action_button("🗑️ 删除", delete_key, "danger"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                        
                        # 显示确认对话框
                        if st.session_state.get(confirm_key, False):
                            st.markdown(f"""
                            <div class="warning-message">
                                <strong>⚠️ 确认删除</strong><br>
                                确认删除面料 '{fabric['name']}' 吗？此操作不可撤销。
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ 确认删除", key=f"confirm_yes_{fabric['id']}", type="primary"):
                                    try:
                                        db.delete_fabric(fabric['id'])
                                        show_success_message(f"面料 '{fabric['name']}' 已删除")
                                        del st.session_state[confirm_key]
                                        st.rerun()
                                    except Exception as e:
                                        show_error_message(f"删除面料失败: {str(e)}")
                                        del st.session_state[confirm_key]
                            with col2:
                                if st.button("❌ 取消", key=f"confirm_no_{fabric['id']}"):
                                    del st.session_state[confirm_key]
                                    st.rerun()
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
            uploaded_file, image_path = drag_drop_image_uploader(
                key="fabric_image", 
                label="📷 面料图片", 
                help_text="支持拖拽上传 PNG, JPG, JPEG, GIF 等格式的图片"
            )
            
            submitted = st.form_submit_button("➕ 添加面料", use_container_width=True)
            
            if submitted:
                if name:
                    try:
                        fabric_id = db.add_fabric(name, material_type, usage_type, image_path)
                        show_success_message(f'面料 "{name}" 添加成功！面料ID: {fabric_id}')
                        st.rerun()
                    except Exception as e:
                        show_error_message(f"添加面料失败: {str(e)}")
                else:
                    show_error_message("请输入面料名称")

# 包型管理页面
elif selected == "👜 包型管理":
    st.markdown("## 👜 包型管理")
    
    # 初始化编辑状态
    if 'bag_type_edit_states' not in st.session_state:
        st.session_state.bag_type_edit_states = {}
    
    tab1, tab2, tab3 = st.tabs(["📋 包型列表", "🗂️ 分类管理", "➕ 添加包型"])
    
    with tab1:
        st.markdown("### 📋 包型列表")
        bag_types = db.get_bag_types()
        
        if bag_types:
            for bag_type in bag_types:
                with st.expander(f"👜 {bag_type['name']} - ¥{bag_type['price']:.2f}"):
                    # 显示媒体文件
                    if bag_type['image_path'] or bag_type['video_path']:
                        display_uploaded_media(
                            image_path=bag_type['image_path'], 
                            video_path=bag_type['video_path']
                        )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**大分类:** {bag_type['category_name'] or '未分类'}")
                        st.write(f"**子分类:** {bag_type['subcategory_name'] or '无'}")
                        st.write(f"**价格:** ¥{bag_type['price']:.2f}")
                    
                    with col2:
                        if bag_type['image_path']:
                            st.write(f"**图片路径:** {bag_type['image_path']}")
                        if bag_type['video_path']:
                            st.write(f"**视频路径:** {bag_type['video_path']}")
                    
                    # 编辑和删除按钮
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        edit_button = st.button("✏️ 编辑", key=f"edit_bag_type_{bag_type['id']}", use_container_width=True)
                    
                    with col_delete:
                        if st.button("🗑️ 删除", key=f"delete_bag_type_{bag_type['id']}", use_container_width=True):
                            if db.delete_bag_type(bag_type['id']):
                                st.success(f"✅ 包型 \"{bag_type['name']}\" 删除成功！")
                                st.rerun()
                            else:
                                st.error("❌ 无法删除该包型，可能有订单正在使用")
                    
                    # 处理编辑状态
                    bag_type_id = bag_type['id']
                    if edit_button:
                        st.session_state.bag_type_edit_states[bag_type_id] = True
                    
                    # 编辑表单
                    if st.session_state.bag_type_edit_states.get(bag_type_id, False):
                        st.markdown("---")
                        st.markdown("#### ✏️ 编辑包型")
                        
                        with st.form(f"edit_bag_type_form_{bag_type['id']}"):
                            edit_col1, edit_col2 = st.columns(2)
                            
                            with edit_col1:
                                edit_name = st.text_input("包型名称", value=bag_type['name'])
                                edit_price = st.number_input("价格", value=float(bag_type['price']), min_value=0.0, step=0.01, format="%.2f")
                                
                                # 获取分类选项
                                categories = db.get_bag_categories()
                                main_categories = [cat for cat in categories if cat['level'] == 1]
                                category_names = [cat['name'] for cat in main_categories]
                                
                                current_category_name = bag_type['category_name'] or ""
                                category_index = category_names.index(current_category_name) if current_category_name in category_names else 0
                                edit_category_choice = st.selectbox("大分类", category_names, index=category_index)
                            
                            with edit_col2:
                                # 子分类选择
                                selected_main_category = next((cat for cat in main_categories if cat['name'] == edit_category_choice), None)
                                subcategories = []
                                if selected_main_category:
                                    subcategories = [cat for cat in categories if cat['parent_id'] == selected_main_category['id']]
                                
                                subcategory_names = ["无"] + [cat['name'] for cat in subcategories]
                                current_subcategory_name = bag_type['subcategory_name'] or "无"
                                subcategory_index = subcategory_names.index(current_subcategory_name) if current_subcategory_name in subcategory_names else 0
                                edit_subcategory_choice = st.selectbox("子分类", subcategory_names, index=subcategory_index)
                            
                            # 媒体文件上传
                            st.markdown("##### 📸 更新图片")
                            edit_uploaded_file, edit_image_path = drag_drop_image_uploader(f"edit_bag_image_{bag_type['id']}", "包型图片（可选）")
                            
                            st.markdown("##### 🎥 更新视频")
                            edit_video_file, edit_video_path = drag_drop_media_uploader(f"edit_bag_video_{bag_type['id']}", "包型视频（可选）")
                            
                            # 保存和取消按钮
                            save_col, cancel_col = st.columns(2)
                            
                            with save_col:
                                if st.form_submit_button("💾 保存修改", use_container_width=True):
                                    # 获取分类ID
                                    category_id = selected_main_category['id'] if selected_main_category else None
                                    subcategory_id = None
                                    if edit_subcategory_choice != "无":
                                        subcategory_id = next((cat['id'] for cat in subcategories if cat['name'] == edit_subcategory_choice), None)
                                    
                                    # 使用新上传的文件路径，如果没有则保持原有路径
                                    final_image_path = edit_image_path if edit_image_path else bag_type['image_path']
                                    final_video_path = edit_video_path if edit_video_path else bag_type['video_path']
                                    
                                    if db.update_bag_type(bag_type['id'], edit_name, category_id, subcategory_id, edit_price, final_image_path, final_video_path):
                                        st.success(f"✅ 包型 \"{edit_name}\" 更新成功！")
                                        st.session_state.bag_type_edit_states[bag_type_id] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ 更新失败")
                            
                            with cancel_col:
                                if st.form_submit_button("❌ 取消", use_container_width=True):
                                    st.session_state.bag_type_edit_states[bag_type_id] = False
                                    st.rerun()
        else:
            st.info("📝 暂无包型数据，请先创建分类并添加包型")
    
    with tab2:
        render_category_management(db)
    
    with tab3:
        st.markdown("### ➕ 添加新包型")
        
        categories = db.get_bag_categories()
        
        if not categories:
            st.warning("⚠️ 请先在分类管理中创建包型分类")
        else:
            with st.form("add_bag_type_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("👜 包型名称*", placeholder="请输入包型名称")
                    price = st.number_input("💰 价格*", min_value=0.0, step=0.01, format="%.2f")
                    
                    # 大分类选择
                    main_categories = [cat for cat in categories if cat['level'] == 1]
                    category_names = [cat['name'] for cat in main_categories]
                    category_choice = st.selectbox("🗂️ 大分类*", category_names)
                
                with col2:
                    # 子分类选择
                    selected_category = next((cat for cat in main_categories if cat['name'] == category_choice), None)
                    subcategories = db.get_bag_categories(selected_category['id']) if selected_category else []
                    
                    if subcategories:
                        subcategory_options = ["无"] + [subcat['name'] for subcat in subcategories]
                        subcategory_choice = st.selectbox("📂 子分类", subcategory_options)
                    else:
                        subcategory_choice = "无"
                        st.info("该分类下暂无子分类")
                
                # 媒体文件上传区域
                st.markdown("---")
                media_uploads = drag_drop_media_uploader(
                    key="bag_type_media", 
                    label="📁 包型媒体文件", 
                    help_text="支持拖拽上传图片和视频文件"
                )
                
                submitted = st.form_submit_button("➕ 添加包型", use_container_width=True)
                
                if submitted:
                    if name and selected_category:
                        subcategory_id = None
                        if subcategory_choice != "无":
                            subcategory_id = next((subcat['id'] for subcat in subcategories if subcat['name'] == subcategory_choice), None)
                        
                        # 获取上传的文件路径
                        image_path = media_uploads["image"][1]  # 获取图片路径
                        video_path = media_uploads["video"][1]  # 获取视频路径
                        
                        bag_type_id = db.add_bag_type(name, selected_category['id'], subcategory_id, price, image_path, video_path)
                        st.markdown(f'<div class="success-message">✅ 包型 "{name}" 添加成功！</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-message">❌ 请填写必填项</div>', unsafe_allow_html=True)

# 库存管理页面
elif selected == "📦 库存管理":
    st.markdown("## 📦 库存管理")
    
    tab1, tab2 = st.tabs(["📋 库存列表", "➕ 添加商品"])
    
    with tab1:
        st.markdown("### 📋 库存列表")
        inventory_items = db.get_inventory_items()
        
        if inventory_items:
            # 搜索功能
            search_term = st.text_input("🔍 搜索商品", placeholder="输入商品名称")
            
            filtered_items = inventory_items
            if search_term:
                filtered_items = [item for item in inventory_items if search_term.lower() in item['product_name'].lower()]
            
            # 显示库存列表
            for item in filtered_items:
                status_color = "🟢" if item['quantity'] > 10 else "🟡" if item['quantity'] > 0 else "🔴"
                
                with st.expander(f"{status_color} {item['product_name']} - 库存: {item['quantity']} - ¥{item['price']:.2f}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        new_name = st.text_input("商品名称", value=item['product_name'], key=f"item_name_{item['id']}")
                        new_description = st.text_area("商品描述", value=item['description'] or "", key=f"item_desc_{item['id']}")
                    
                    with col2:
                        new_price = st.number_input("价格", value=float(item['price']), min_value=0.0, step=0.01, key=f"item_price_{item['id']}")
                        quantity_change = st.number_input("库存调整", value=0, step=1, key=f"item_qty_{item['id']}", 
                                                        help="正数增加库存，负数减少库存")
                        new_image = st.text_input("图片路径", value=item['image_path'] or "", key=f"item_image_{item['id']}")
                    
                    with col3:
                        if st.button("💾 更新", key=f"update_item_{item['id']}"):
                            # 更新商品完整信息
                            new_quantity = item['quantity'] + quantity_change
                            success = db.update_inventory_item(
                                item['id'], new_name, new_description, 
                                new_price, new_quantity, new_image
                            )
                            if success:
                                st.success("✅ 商品信息已更新")
                                st.rerun()
                            else:
                                st.error("❌ 更新失败")
                        
                        if st.button("🗑️ 删除", key=f"delete_item_{item['id']}", type="secondary"):
                            success = db.delete_inventory_item(item['id'])
                            if success:
                                st.success("✅ 商品已删除")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败，该商品可能已被订单使用")
        else:
            st.info("📝 暂无库存数据，请添加商品")
    
    with tab2:
        st.markdown("### ➕ 添加新商品")
        
        with st.form("add_inventory_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                product_name = st.text_input("📦 商品名称*", placeholder="请输入商品名称")
                description = st.text_area("📝 商品描述", placeholder="商品详细描述")
                image_path = st.text_input("🖼️ 图片路径", placeholder="可选")
            
            with col2:
                price = st.number_input("💰 价格*", min_value=0.0, step=0.01, format="%.2f")
                quantity = st.number_input("📊 初始库存*", min_value=0, step=1)
            
            submitted = st.form_submit_button("➕ 添加商品", use_container_width=True)
            
            if submitted:
                if product_name:
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
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            search_term = st.text_input("🔍 搜索订单 (客户名称/订单ID)", 
                                      value=st.session_state.order_search,
                                      placeholder="输入客户名称或订单ID...")
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
        
        # 获取分页数据
        orders, total_count = db.get_orders_paginated(
            page=st.session_state.order_page,
            page_size=page_size,
            search_term=st.session_state.order_search,
            status_filter=st.session_state.order_status_filter if st.session_state.order_status_filter != "all" else None
        )
        
        if total_count > 0:
            # 分页信息
            total_pages = (total_count + page_size - 1) // page_size
            st.markdown(f"**共 {total_count} 个订单，第 {st.session_state.order_page} / {total_pages} 页**")
            
            # 分页控制
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ 首页", disabled=st.session_state.order_page == 1):
                    st.session_state.order_page = 1
                    st.rerun()
            
            with col2:
                if st.button("⏪ 上页", disabled=st.session_state.order_page == 1):
                    st.session_state.order_page -= 1
                    st.rerun()
            
            with col3:
                # 页码跳转
                new_page = st.number_input("跳转到页", min_value=1, max_value=total_pages, 
                                         value=st.session_state.order_page, key="page_jump")
                if new_page != st.session_state.order_page:
                    st.session_state.order_page = new_page
                    st.rerun()
            
            with col4:
                if st.button("⏩ 下页", disabled=st.session_state.order_page == total_pages):
                    st.session_state.order_page += 1
                    st.rerun()
            
            with col5:
                if st.button("⏭️ 末页", disabled=st.session_state.order_page == total_pages):
                    st.session_state.order_page = total_pages
                    st.rerun()
            
            st.markdown("---")
            
            # 批量操作区域
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
            
            current_order_ids = {order['id'] for order in orders}
            
            with col1:
                if st.button("🔲 全选当页", use_container_width=True):
                    st.session_state.selected_orders.update(current_order_ids)
                    st.rerun()
            
            with col2:
                if st.button("⬜ 取消当页", use_container_width=True):
                    st.session_state.selected_orders -= current_order_ids
                    st.rerun()
            
            with col3:
                selected_count = len(st.session_state.selected_orders)
                st.write(f"已选择: {selected_count} 个")
            
            with col4:
                if st.button("📊 导出CSV", use_container_width=True, disabled=selected_count == 0):
                    if selected_count > 0:
                        # 使用优化的CSV导出
                        from csv_export import export_orders_to_csv_optimized, generate_csv_filename
                        
                        # 获取选中订单的完整数据
                        orders_with_items = db.get_orders_with_items_for_export(list(st.session_state.selected_orders))
                        
                        # 生成CSV
                        csv_content = export_orders_to_csv_optimized(orders_with_items)
                        filename = generate_csv_filename()
                        
                        # 提供下载
                        st.download_button(
                            label="💾 下载CSV文件",
                            data=csv_content,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                        st.success(f"✅ 已生成 {selected_count} 个订单的CSV文件")
            
            with col5:
                if st.button("🗑️ 批量删除", use_container_width=True, disabled=selected_count == 0, type="secondary"):
                    if selected_count > 0:
                        # 确认删除
                        if st.session_state.get('confirm_batch_delete', False):
                            deleted_count, failed_ids = db.delete_orders_batch(list(st.session_state.selected_orders))
                            
                            if deleted_count > 0:
                                st.success(f"✅ 成功删除 {deleted_count} 个订单")
                                st.session_state.selected_orders = set()
                                st.session_state.confirm_batch_delete = False
                                st.rerun()
                            
                            if failed_ids:
                                st.warning(f"⚠️ {len(failed_ids)} 个订单删除失败（可能是已完成状态）")
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
                                        st.rerun()
                            
                            with btn_col4:
                                if order['status'] != 'completed':
                                    if st.button("🗑️", key=f"delete_{order['id']}", help="删除", type="secondary"):
                                        success = db.delete_order(order['id'])
                                        if success:
                                            st.success("✅ 订单已删除")
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
                                    else:
                                        st.write(f"• 定制: {item['bag_type_name']} × {item['quantity']} = ¥{item['unit_price'] * item['quantity']:.2f}")
                                        if item['outer_fabric_name']:
                                            st.write(f"  表布: {item['outer_fabric_name']}")
                                        if item['inner_fabric_name']:
                                            st.write(f"  里布: {item['inner_fabric_name']}")
                                    if item['notes']:
                                        st.write(f"  备注: {item['notes']}")
                        
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
            
            # 商品类型选择
            item_type = st.radio("商品类型", ["现货", "定制"], horizontal=True)
            
            if item_type == "现货":
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
                        quantity = st.number_input("数量", min_value=1, max_value=selected_inventory['quantity'], value=1)
                    
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
            
            else:  # 定制商品
                bag_types = db.get_bag_types()
                fabrics = db.get_fabrics()
                
                if not bag_types:
                    st.warning("⚠️ 请先在包型管理中添加包型")
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 选择包型
                        bag_options = [f"{bag['name']} - ¥{bag['price']:.2f}" for bag in bag_types]
                        selected_bag = st.selectbox("选择包型", bag_options)
                        bag_index = bag_options.index(selected_bag)
                        selected_bag_type = bag_types[bag_index]
                        
                        # 选择表布
                        outer_fabrics = [fabric for fabric in fabrics if fabric['usage_type'] == '表布']
                        if outer_fabrics:
                            outer_fabric_options = [fabric['name'] for fabric in outer_fabrics]
                            selected_outer_fabric = st.selectbox("选择表布", outer_fabric_options)
                            outer_fabric_id = next(fabric['id'] for fabric in outer_fabrics if fabric['name'] == selected_outer_fabric)
                        else:
                            st.warning("⚠️ 请先添加表布面料")
                            outer_fabric_id = None
                    
                    with col2:
                        # 选择里布
                        inner_fabrics = [fabric for fabric in fabrics if fabric['usage_type'] == '里布']
                        if inner_fabrics:
                            inner_fabric_options = [fabric['name'] for fabric in inner_fabrics]
                            selected_inner_fabric = st.selectbox("选择里布", inner_fabric_options)
                            inner_fabric_id = next(fabric['id'] for fabric in inner_fabrics if fabric['name'] == selected_inner_fabric)
                        else:
                            st.warning("⚠️ 请先添加里布面料")
                            inner_fabric_id = None
                        
                        quantity = st.number_input("数量", min_value=1, value=1)
                        custom_notes = st.text_input("定制备注", placeholder="特殊要求等")
                    
                    if st.button("➕ 添加定制商品到订单"):
                        if outer_fabric_id and inner_fabric_id:
                            order_item = {
                                'type': '定制',
                                'bag_type_id': selected_bag_type['id'],
                                'name': f"定制 {selected_bag_type['name']}",
                                'outer_fabric_id': outer_fabric_id,
                                'outer_fabric_name': selected_outer_fabric,
                                'inner_fabric_id': inner_fabric_id,
                                'inner_fabric_name': selected_inner_fabric,
                                'quantity': quantity,
                                'unit_price': selected_bag_type['price'],
                                'total_price': selected_bag_type['price'] * quantity,
                                'notes': custom_notes
                            }
                            st.session_state.order_items.append(order_item)
                            st.success("✅ 定制商品已添加到订单")
                        else:
                            st.error("❌ 请选择表布和里布")
            
            # 显示当前订单商品
            if st.session_state.order_items:
                st.markdown("#### 当前订单商品")
                total_amount = 0
                
                for i, item in enumerate(st.session_state.order_items):
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        if item['type'] == '现货':
                            st.write(f"• {item['name']} × {item['quantity']} = ¥{item['total_price']:.2f}")
                        else:
                            st.write(f"• {item['name']} × {item['quantity']} = ¥{item['total_price']:.2f}")
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
                uploaded_file, order_image_path = drag_drop_image_uploader("order_image", "订单相关图片（可选）")
                
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
                            else:
                                db.add_order_item(
                                    order_id, '定制', item['quantity'], item['unit_price'],
                                    notes=item.get('notes', ''),
                                    bag_type_id=item['bag_type_id'],
                                    outer_fabric_id=item['outer_fabric_id'],
                                    inner_fabric_id=item['inner_fabric_id']
                                )
                        
                        # 自动完成支付并更新客户积分
                        db.complete_order_payment(order_id)
                        
                        # 获取订单总金额用于显示
                        orders = db.get_orders()
                        created_order = next((o for o in orders if o['id'] == order_id), None)
                        total_amount = created_order['total_amount'] if created_order else 0
                        points_earned = int(total_amount)
                        
                        st.session_state.order_items = []  # 清空订单商品
                        st.success(f"✅ 订单创建成功！订单号: {order_id}")
                        st.success(f"💰 订单金额: ¥{total_amount:.2f}，客户获得 {points_earned} 积分")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ 清空订单", use_container_width=True):
                        st.session_state.order_items = []
                        st.rerun()

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🏪 生意管理系统 | 让生意管理更简单高效
    </div>
    """, 
    unsafe_allow_html=True
)

if __name__ == "__main__":
    pass