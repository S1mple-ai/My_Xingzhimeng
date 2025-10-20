"""
库存管理页面组件
"""
import streamlit as st
from ui_components import create_card_grid


def render_inventory_page(db):
    """渲染库存管理页面"""
    st.markdown("## 📦 库存管理")
    
    tab1, tab2 = st.tabs(["📋 库存列表", "➕ 添加商品"])
    
    with tab1:
        _render_inventory_list_tab(db)
    
    with tab2:
        _render_add_inventory_tab(db)


def _render_inventory_list_tab(db):
    """渲染库存列表标签页"""
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
                st.session_state.delete_inventory_id = inventory_data['id']
                st.session_state.show_delete_inventory_confirm = True
                st.rerun()
            
            create_card_grid(filtered_items, card_type="inventory", columns=3,
                           on_edit=on_inventory_edit, on_view=on_inventory_view, on_delete=on_inventory_delete)
        else:
            st.info("暂无符合条件的库存数据")
    else:
        st.info("📝 暂无库存数据，请添加商品")


def _render_add_inventory_tab(db):
    """渲染添加商品标签页"""
    st.markdown("### ➕ 添加新商品")
    
    with st.form("add_inventory_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("📦 商品名称*", placeholder="请输入商品名称")
            description = st.text_area("📝 商品描述", placeholder="商品详细描述")
            image_path = st.text_input("🖼️ 图片路径", placeholder="可选")
        
        with col2:
            price = st.number_input("💰 价格*", min_value=0.0, step=0.01, format="%.2f")
            quantity = st.number_input("📊 初始库存*", min_value=0, step=1, format="%d")
        
        submitted = st.form_submit_button("➕ 添加商品", use_container_width=True)
        
        if submitted:
            if product_name:
                item_id = db.add_inventory_item(product_name, description, price, quantity, image_path)
                st.markdown(f'<div class="success-message">✅ 商品 "{product_name}" 添加成功！</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown('<div class="error-message">❌ 请输入商品名称</div>', unsafe_allow_html=True)