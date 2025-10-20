"""
订单管理页面组件

包含订单列表、搜索筛选、分页、批量操作、详情展示、编辑功能和创建订单等功能。
"""

import streamlit as st
from upload_components import drag_drop_image_uploader, display_uploaded_media


def render_order_page(db, dashboard_service, export_service, cache_manager):
    """渲染订单管理页面"""
    st.markdown("## 📋 订单管理")
    
    tab1, tab2 = st.tabs(["📋 订单列表", "➕ 创建订单"])
    
    with tab1:
        _render_order_list_tab(db, export_service)
    
    with tab2:
        _render_create_order_tab(db)


def _render_order_list_tab(db, export_service):
    """渲染订单列表标签页"""
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
        _render_order_list_controls(db, export_service, orders, total_count, page_size)
        
        st.markdown("---")
        
        # 订单列表显示
        for order in orders:
            _render_order_item(db, order)
    else:
        st.info("📝 暂无订单数据，请创建订单或调整搜索条件")


def _render_order_list_controls(db, export_service, orders, total_count, page_size):
    """渲染订单列表控制区域（分页、批量操作等）"""
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
                            _clear_order_cache()
                            st.rerun()
                        
                        if failed_ids:
                            st.warning(f"⚠️ {len(failed_ids)} 个订单删除失败（可能是已完成状态）")
                    except Exception as e:
                        st.error(f"❌ 批量删除失败: {str(e)}")
                else:
                    st.session_state.confirm_batch_delete = True
                    st.warning(f"⚠️ 确认要删除 {selected_count} 个订单吗？再次点击确认删除。")


def _render_order_item(db, order):
    """渲染单个订单项"""
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
                _render_order_action_buttons(db, order)
            
            # 详细信息展开
            if st.session_state.get(f"show_details_{order['id']}", False):
                _render_order_details(db, order)
            
            # 编辑订单表单（弹窗式）
            if st.session_state.get(f"edit_order_{order['id']}", False):
                _render_order_edit_form(db, order)
        
        st.markdown("---")


def _render_order_action_buttons(db, order):
    """渲染订单操作按钮"""
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
                _clear_order_cache()
                st.rerun()
    
    with btn_col4:
        if order['status'] != 'completed':
            if st.button("🗑️", key=f"delete_{order['id']}", help="删除", type="secondary"):
                success = db.delete_order(order['id'])
                if success:
                    st.success("✅ 订单已删除")
                    _clear_order_cache()
                    st.rerun()
                else:
                    st.error("❌ 删除失败")


def _render_order_details(db, order):
    """渲染订单详细信息"""
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


def _render_order_edit_form(db, order):
    """渲染订单编辑表单"""
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
                    _clear_order_cache()
                    st.rerun()
                else:
                    st.error("❌ 更新失败")
        
        with col_cancel:
            if st.form_submit_button("❌ 取消", use_container_width=True):
                st.session_state[f"edit_order_{order['id']}"] = False
                st.rerun()


def _render_create_order_tab(db):
    """渲染创建订单标签页"""
    st.markdown("### ➕ 创建新订单")
    
    # 步骤1：选择客户
    st.markdown("#### 步骤1: 选择客户")
    customers = db.get_customers()
    
    if not customers:
        st.warning("⚠️ 请先在客户管理中添加客户")
        return
    
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
    _render_add_inventory_item(db)
    
    # 添加定制商品
    _render_add_custom_item(db)
    
    # 显示当前订单商品
    if st.session_state.order_items:
        _render_current_order_items(db, customer_id)


def _render_add_inventory_item(db):
    """渲染添加现货商品区域"""
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


def _render_add_custom_item(db):
    """渲染添加定制商品区域"""
    st.markdown("---")
    st.markdown("##### 🎨 添加定制商品")
    
    # 获取面料数据
    fabrics = db.get_fabrics()
    inventory_items = db.get_inventory_items()
    available_items = [item for item in inventory_items if item['quantity'] > 0]
    
    if available_items and fabrics:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
        
        with col1:
            # 选择基础商品
            custom_item_options = [f"{item['product_name']} (¥{item['price']:.2f})" for item in available_items]
            selected_custom_item = st.selectbox("选择基础商品", custom_item_options, key="custom_base_item")
            custom_item_index = custom_item_options.index(selected_custom_item)
            selected_custom_inventory = available_items[custom_item_index]
        
        with col2:
            # 选择表布
            outer_fabric_options = [f"{fabric['name']} ({fabric['material_type']})" for fabric in fabrics]
            selected_outer_fabric = st.selectbox("选择表布", outer_fabric_options, key="outer_fabric")
            outer_fabric_index = outer_fabric_options.index(selected_outer_fabric)
            selected_outer_fabric_data = fabrics[outer_fabric_index]
        
        with col3:
            # 选择里布
            inner_fabric_options = [f"{fabric['name']} ({fabric['material_type']})" for fabric in fabrics]
            selected_inner_fabric = st.selectbox("选择里布", inner_fabric_options, key="inner_fabric")
            inner_fabric_index = inner_fabric_options.index(selected_inner_fabric)
            selected_inner_fabric_data = fabrics[inner_fabric_index]
        
        with col4:
            custom_quantity = st.number_input("数量", min_value=1, value=1, step=1, format="%d", key="custom_quantity")
        
        with col5:
            price_value = selected_custom_inventory['price'] if selected_custom_inventory['price'] is not None else 0
            custom_price = st.number_input("定制价格", min_value=0.0, value=float(price_value), step=0.01, format="%.2f", key="custom_price")
        
        # 定制商品备注
        custom_notes = st.text_area("定制备注", placeholder="特殊要求、工艺说明等", key="custom_notes")
        
        if st.button("🎨 添加定制商品到订单"):
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


def _render_current_order_items(db, customer_id):
    """渲染当前订单商品列表"""
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
            _create_order(db, customer_id, order_notes, order_image_path, total_amount)
    
    with col2:
        if st.button("🗑️ 清空订单", use_container_width=True):
            st.session_state.order_items = []
            st.rerun()


def _create_order(db, customer_id, order_notes, order_image_path, total_amount):
    """创建订单"""
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
    
    # 自动完成支付并更新客户积分
    db.complete_order_payment(order_id)
    
    # 获取订单总金额用于显示
    orders = db.get_orders()
    created_order = next((o for o in orders if o['id'] == order_id), None)
    total_amount = created_order['total_amount'] if created_order else 0
    points_earned = int(total_amount)
    
    st.session_state.order_items = []  # 清空订单商品
    _clear_order_cache()
    st.success(f"✅ 订单创建成功！订单号: {order_id}")
    st.success(f"💰 订单金额: ¥{total_amount:.2f}，客户获得 {points_earned} 积分")
    st.rerun()


def _clear_order_cache():
    """清理订单缓存"""
    if 'order_cache_key' in st.session_state:
        del st.session_state.order_cache_key
    if 'order_cache_data' in st.session_state:
        del st.session_state.order_cache_data