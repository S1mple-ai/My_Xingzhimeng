import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

def clear_processing_cache():
    """清理加工管理相关的缓存"""
    try:
        # 清理Streamlit的缓存
        st.cache_data.clear()
        logger.info("加工管理缓存清理完成")
    except Exception as e:
        logger.error(f"加工管理缓存清理失败: {str(e)}")

def show_processing_management():
    """代加工管理主页面"""
    st.title("🏭 加工管理")
    
    # 初始化数据库
    db = DatabaseManager()
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["代加工人员管理", "代加工订单管理", "统计分析"])
    
    with tab1:
        show_processor_management(db)
    
    with tab2:
        show_processing_order_management(db)
    
    with tab3:
        show_processing_statistics(db)

def show_processor_management(db):
    """代加工人员管理"""
    st.header("👥 代加工人员管理")
    
    # 添加新代加工人员
    with st.expander("➕ 添加新代加工人员", expanded=False):
        with st.form("add_processor_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nickname = st.text_input("昵称*", placeholder="请输入代加工人员昵称")
                phone = st.text_input("手机号", placeholder="请输入手机号")
                wechat = st.text_input("微信号", placeholder="请输入微信号")
            
            with col2:
                xiaohongshu = st.text_input("小红书号", placeholder="请输入小红书号")
                douyin = st.text_input("抖音号", placeholder="请输入抖音号")
                notes = st.text_area("备注", placeholder="请输入备注信息")
            
            submitted = st.form_submit_button("添加代加工人员", type="primary")
            
            if submitted:
                if not nickname.strip():
                    st.error("昵称不能为空！")
                else:
                    try:
                        processor_id = db.add_processor(
                            nickname=nickname.strip(),
                            phone=phone.strip() if phone.strip() else None,
                            wechat=wechat.strip() if wechat.strip() else None,
                            xiaohongshu=xiaohongshu.strip() if xiaohongshu.strip() else None,
                            douyin=douyin.strip() if douyin.strip() else None,
                            notes=notes.strip() if notes.strip() else None
                        )
                        st.success(f"成功添加代加工人员：{nickname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败：{str(e)}")
    
    # 显示代加工人员列表
    st.subheader("📋 代加工人员列表")
    
    try:
        processors = db.get_processors()
        
        if not processors:
            st.info("暂无代加工人员数据")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(processors)
        
        # 显示表格
        for idx, processor in enumerate(processors):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{processor['nickname']}**")
                    if processor['phone']:
                        st.write(f"📱 {processor['phone']}")
                    if processor['wechat']:
                        st.write(f"💬 {processor['wechat']}")
                
                with col2:
                    if processor['xiaohongshu']:
                        st.write(f"📖 {processor['xiaohongshu']}")
                    if processor['douyin']:
                        st.write(f"🎵 {processor['douyin']}")
                
                with col3:
                    # 获取统计信息
                    stats = db.get_processor_statistics(processor['id'])
                    st.metric("总订单", stats['total_orders'])
                    st.metric("已完成", stats['completed_orders'])
                
                with col4:
                    # 使用不同的key来避免冲突
                    edit_key = f"editing_processor_{processor['id']}"
                    
                    if st.button("编辑", key=f"edit_btn_processor_{processor['id']}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    
                    if st.button("删除", key=f"delete_processor_{processor['id']}", type="secondary"):
                        try:
                            db.delete_processor(processor['id'], force_delete=True)
                            # 删除成功后清理缓存
                            clear_processing_cache()
                            st.success(f"成功删除代加工人员：{processor['nickname']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败：{str(e)}")
                
                # 编辑表单
                if st.session_state.get(edit_key, False):
                    with st.form(f"edit_processor_form_{processor['id']}"):
                        st.write(f"编辑代加工人员：{processor['nickname']}")
                        
                        edit_col1, edit_col2 = st.columns(2)
                        
                        with edit_col1:
                            edit_nickname = st.text_input("昵称*", value=processor['nickname'])
                            edit_phone = st.text_input("手机号", value=processor['phone'] or "")
                            edit_wechat = st.text_input("微信号", value=processor['wechat'] or "")
                        
                        with edit_col2:
                            edit_xiaohongshu = st.text_input("小红书号", value=processor['xiaohongshu'] or "")
                            edit_douyin = st.text_input("抖音号", value=processor['douyin'] or "")
                            edit_notes = st.text_area("备注", value=processor['notes'] or "")
                        
                        edit_col_btn1, edit_col_btn2 = st.columns(2)
                        
                        with edit_col_btn1:
                            if st.form_submit_button("保存修改", type="primary"):
                                if not edit_nickname.strip():
                                    st.error("昵称不能为空！")
                                else:
                                    try:
                                        db.update_processor(
                                            processor['id'],
                                            nickname=edit_nickname.strip(),
                                            phone=edit_phone.strip() if edit_phone.strip() else None,
                                            wechat=edit_wechat.strip() if edit_wechat.strip() else None,
                                            xiaohongshu=edit_xiaohongshu.strip() if edit_xiaohongshu.strip() else None,
                                            douyin=edit_douyin.strip() if edit_douyin.strip() else None,
                                            notes=edit_notes.strip() if edit_notes.strip() else None
                                        )
                                        st.success(f"成功更新代加工人员：{edit_nickname}")
                                        del st.session_state[edit_key]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"更新失败：{str(e)}")
                        
                        with edit_col_btn2:
                            if st.form_submit_button("取消"):
                                del st.session_state[edit_key]
                                st.rerun()
                
                st.divider()
    
    except Exception as e:
        st.error(f"获取代加工人员列表失败：{str(e)}")

def show_processing_order_management(db):
    """代加工订单管理"""
    st.header("📦 代加工订单管理")
    
    # 添加新代加工订单
    with st.expander("➕ 添加新代加工订单", expanded=False):
        with st.form("add_processing_order_form"):
            # 获取代加工人员和面料列表
            processors = db.get_processors()
            fabrics = db.get_fabrics()
            
            if not processors:
                st.warning("请先添加代加工人员！")
                st.form_submit_button("添加订单", disabled=True)
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 代加工人员选择
                processor_options = {p['id']: p['nickname'] for p in processors}
                processor_id = st.selectbox("选择代加工人员*", options=list(processor_options.keys()), 
                                          format_func=lambda x: processor_options[x])
                
                # 面料选择（可选）
                fabric_options = {0: "无关联面料"}
                fabric_options.update({f['id']: f['name'] for f in fabrics})
                fabric_id = st.selectbox("关联面料", options=list(fabric_options.keys()),
                                       format_func=lambda x: fabric_options[x])
                fabric_id = fabric_id if fabric_id != 0 else None
                
                fabric_meters_main = st.number_input("表布米数", min_value=0.0, step=0.1, value=0.0)
                fabric_meters_lining = st.number_input("里布米数", min_value=0.0, step=0.1, value=0.0)
                
                # 获取库存商品列表，实现商品联动
                inventory_items = db.get_inventory_items()
                product_options = {}
                product_prices = {}
                
                if inventory_items:
                    for item in inventory_items:
                        product_options[item['product_name']] = item['product_name']
                        product_prices[item['product_name']] = float(item['price'])
                    
                    # 添加自定义选项
                    product_options["自定义商品"] = "自定义商品"
                    
                    selected_product = st.selectbox("商品名称*", 
                                                  options=list(product_options.keys()),
                                                  format_func=lambda x: product_options[x])
                    
                    if selected_product == "自定义商品":
                        product_name = st.text_input("自定义商品名称*", placeholder="请输入商品名称")
                        auto_price = 0.0
                    else:
                        product_name = selected_product
                        auto_price = product_prices.get(selected_product, 0.0)
                        st.info(f"已选择商品：{product_name}，价格：¥{auto_price:.2f}")
                else:
                    st.warning("库存中暂无商品，请先添加库存商品或使用自定义商品名称")
                    product_name = st.text_input("商品名称*", placeholder="请输入商品名称")
                    auto_price = 0.0
                
                product_quantity = st.number_input("商品数量", min_value=1, value=1)
            
            with col2:
                processing_days = st.number_input("预计加工天数", min_value=0, value=0)
                processing_cost = st.number_input("代加工费用", min_value=0.0, step=0.01, value=0.0)
                
                # 销售价格自动同步或手动输入
                if 'auto_price' in locals() and auto_price > 0:
                    selling_price = st.number_input("销售价格", min_value=0.0, step=0.01, value=auto_price,
                                                   help="价格已从库存商品自动同步，可手动修改")
                else:
                    selling_price = st.number_input("销售价格", min_value=0.0, step=0.01, value=0.0)
                
                start_date = st.date_input("开始日期", value=datetime.now().date())
                
                # 预计完成日期自动计算
                if processing_days > 0:
                    auto_finish_date = start_date + timedelta(days=processing_days)
                    expected_finish_date = st.date_input("预计完成日期", 
                                                       value=auto_finish_date,
                                                       help=f"根据开始日期和预计加工天数({processing_days}天)自动计算")
                else:
                    expected_finish_date = st.date_input("预计完成日期", value=start_date)
                
                notes = st.text_area("备注", placeholder="请输入备注信息")
            
            submitted = st.form_submit_button("添加代加工订单", type="primary")
            
            if submitted:
                if not product_name.strip():
                    st.error("商品名称不能为空！")
                else:
                    try:
                        order_id = db.add_processing_order(
                            processor_id=processor_id,
                            fabric_id=fabric_id,
                            fabric_meters_main=fabric_meters_main,
                            fabric_meters_lining=fabric_meters_lining,
                            product_name=product_name.strip(),
                            product_quantity=product_quantity,
                            processing_days=processing_days,
                            processing_cost=processing_cost,
                            selling_price=selling_price,
                            start_date=start_date.strftime('%Y-%m-%d'),
                            expected_finish_date=expected_finish_date.strftime('%Y-%m-%d'),
                            notes=notes.strip() if notes.strip() else None
                        )
                        st.success(f"成功添加代加工订单：{product_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败：{str(e)}")
    
    # 显示代加工订单列表
    st.subheader("📋 代加工订单列表")
    
    try:
        orders = db.get_processing_orders()
        
        if not orders:
            st.info("暂无代加工订单数据")
            return
        
        # 状态筛选
        status_filter = st.selectbox("筛选状态", ["全部", "待发货", "进行中", "已完成", "已取消"])
        
        if status_filter != "全部":
            orders = [order for order in orders if order['status'] == status_filter]
        
        # 显示订单
        for order in orders:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{order['product_name']}** (数量: {order['product_quantity']})")
                    # 使用安全的字段访问
                    from utils.display_utils import format_processor_display, safe_get
                    processor_name = format_processor_display(order)
                    st.write(f"👤 {processor_name}")
                    fabric_name = safe_get(order, 'fabric_name', '未指定面料')
                    if fabric_name != '未指定面料':
                        st.write(f"🧵 {fabric_name}")
                
                with col2:
                    st.write(f"📏 表布: {order['fabric_meters_main']}m")
                    st.write(f"📏 里布: {order['fabric_meters_lining']}m")
                    st.write(f"⏱️ {order['processing_days']}天")
                
                with col3:
                    st.write(f"💰 加工费: ¥{order['processing_cost']}")
                    st.write(f"💵 售价: ¥{order['selling_price']}")
                    
                    # 状态标签
                    status_color = {
                        "待发货": "🟡", "进行中": "🔵", "已完成": "🟢", "已取消": "🔴"
                    }
                    st.write(f"{status_color.get(order['status'], '⚪')} {order['status']}")
                
                with col4:
                    # 使用不同的key来避免冲突
                    edit_key = f"editing_order_{order['id']}"
                    
                    if st.button("编辑", key=f"edit_btn_order_{order['id']}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    
                    if st.button("删除", key=f"delete_order_{order['id']}", type="secondary"):
                        try:
                            db.delete_processing_order(order['id'])
                            # 删除成功后清理缓存
                            clear_processing_cache()
                            st.success(f"成功删除订单：{order['product_name']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败：{str(e)}")
                
                # 编辑表单
                if st.session_state.get(edit_key, False):
                    with st.form(f"edit_order_form_{order['id']}"):
                        st.write(f"编辑代加工订单：{order['product_name']}")
                        
                        edit_col1, edit_col2 = st.columns(2)
                        
                        with edit_col1:
                            # 获取代加工人员列表
                            processors = db.get_processors()
                            processor_options = {p['id']: p['nickname'] for p in processors}
                            current_processor_idx = list(processor_options.keys()).index(order['processor_id']) if order['processor_id'] in processor_options else 0
                            
                            edit_processor_id = st.selectbox("代加工人员*", 
                                                           options=list(processor_options.keys()),
                                                           format_func=lambda x: processor_options[x],
                                                           index=current_processor_idx)
                            
                            # 获取面料列表
                            fabrics = db.get_fabrics()
                            fabric_options = {f['id']: f['name'] for f in fabrics}
                            fabric_options[None] = "无"
                            current_fabric_idx = list(fabric_options.keys()).index(order['fabric_id']) if order['fabric_id'] in fabric_options else 0
                            
                            edit_fabric_id = st.selectbox("面料", 
                                                        options=list(fabric_options.keys()),
                                                        format_func=lambda x: fabric_options[x],
                                                        index=current_fabric_idx)
                            if edit_fabric_id == "无":
                                edit_fabric_id = None
                            
                            edit_fabric_meters_main = st.number_input("表布米数", min_value=0.0, step=0.1, value=float(order['fabric_meters_main']))
                            edit_fabric_meters_lining = st.number_input("里布米数", min_value=0.0, step=0.1, value=float(order['fabric_meters_lining']))
                            edit_product_name = st.text_input("商品名称*", value=order['product_name'])
                            edit_product_quantity = st.number_input("商品数量", min_value=1, value=order['product_quantity'])
                        
                        with edit_col2:
                            edit_processing_days = st.number_input("预计加工天数", min_value=0, value=order['processing_days'])
                            edit_processing_cost = st.number_input("代加工费用", min_value=0.0, step=0.01, value=float(order['processing_cost']))
                            edit_selling_price = st.number_input("销售价格", min_value=0.0, step=0.01, value=float(order['selling_price']))
                            
                            edit_start_date = st.date_input("开始日期", value=datetime.strptime(order['start_date'], '%Y-%m-%d').date())
                            edit_expected_finish_date = st.date_input("预计完成日期", 
                                                                    value=datetime.strptime(order['expected_finish_date'], '%Y-%m-%d').date())
                            
                            edit_status = st.selectbox("订单状态", 
                                                     options=["待发货", "进行中", "已完成", "已取消"],
                                                     index=["待发货", "进行中", "已完成", "已取消"].index(order['status']))
                            
                            edit_notes = st.text_area("备注", value=order['notes'] or "")
                        
                        edit_col_btn1, edit_col_btn2 = st.columns(2)
                        
                        with edit_col_btn1:
                            if st.form_submit_button("保存修改", type="primary"):
                                if not edit_product_name.strip():
                                    st.error("商品名称不能为空！")
                                else:
                                    try:
                                        db.update_processing_order(
                                            order['id'],
                                            processor_id=edit_processor_id,
                                            fabric_id=edit_fabric_id,
                                            fabric_meters_main=edit_fabric_meters_main,
                                            fabric_meters_lining=edit_fabric_meters_lining,
                                            product_name=edit_product_name.strip(),
                                            product_quantity=edit_product_quantity,
                                            processing_days=edit_processing_days,
                                            processing_cost=edit_processing_cost,
                                            selling_price=edit_selling_price,
                                            status=edit_status,
                                            start_date=edit_start_date.strftime('%Y-%m-%d'),
                                            expected_finish_date=edit_expected_finish_date.strftime('%Y-%m-%d'),
                                            notes=edit_notes.strip() if edit_notes.strip() else None
                                        )
                                        st.success(f"成功更新订单：{edit_product_name}")
                                        del st.session_state[edit_key]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"更新失败：{str(e)}")
                        
                        with edit_col_btn2:
                            if st.form_submit_button("取消"):
                                del st.session_state[edit_key]
                                st.rerun()
                
                st.divider()
    
    except Exception as e:
        st.error(f"获取代加工订单列表失败：{str(e)}")

def show_processing_statistics(db):
    """统计分析"""
    st.header("📊 统计分析")
    
    try:
        # 获取所有数据
        processors = db.get_processors()
        orders = db.get_processing_orders()
        
        if not orders:
            st.info("暂无数据进行统计分析")
            return
        
        # 计算各种统计指标
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o['status'] == '已完成'])
        in_progress_orders = len([o for o in orders if o['status'] == '进行中'])
        pending_orders = len([o for o in orders if o['status'] == '待发货'])
        cancelled_orders = len([o for o in orders if o['status'] == '已取消'])
        
        total_cost = sum(order['processing_cost'] for order in orders)
        total_revenue = sum(order['selling_price'] for order in orders)
        total_profit = total_revenue - total_cost
        
        # 计算时间相关指标
        current_date = datetime.now().date()
        overdue_orders = 0
        total_processing_days = 0
        actual_processing_days = 0
        
        for order in orders:
            # 计算预计加工天数
            total_processing_days += order['processing_days']
            
            # 检查逾期订单
            expected_finish = datetime.strptime(order['expected_finish_date'], '%Y-%m-%d').date()
            if order['status'] in ['进行中', '待发货'] and expected_finish < current_date:
                overdue_orders += 1
            
            # 计算实际加工天数（已完成订单）
            if order['status'] == '已完成':
                start_date = datetime.strptime(order['start_date'], '%Y-%m-%d').date()
                # 假设完成日期为预计完成日期（实际项目中应该有实际完成日期字段）
                actual_days = (expected_finish - start_date).days
                actual_processing_days += actual_days
        
        # 总体统计
        st.subheader("📈 总体统计")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("总订单数", total_orders)
        with col2:
            st.metric("总加工费", f"¥{total_cost:.2f}")
        with col3:
            st.metric("总销售额", f"¥{total_revenue:.2f}")
        with col4:
            st.metric("总利润", f"¥{total_profit:.2f}", 
                     delta=f"{(total_profit/total_cost*100):.1f}%" if total_cost > 0 else "0%")
        with col5:
            completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
            st.metric("完成率", f"{completion_rate:.1f}%")
        
        # 效率与时间分析
        st.subheader("⏱️ 时间利用率与效率分析")
        
        time_col1, time_col2, time_col3, time_col4 = st.columns(4)
        
        with time_col1:
            st.metric("逾期订单", overdue_orders, 
                     delta=f"{(overdue_orders/total_orders*100):.1f}%" if total_orders > 0 else "0%")
        
        with time_col2:
            avg_processing_days = total_processing_days / total_orders if total_orders > 0 else 0
            st.metric("平均预计天数", f"{avg_processing_days:.1f}天")
        
        with time_col3:
            avg_actual_days = actual_processing_days / completed_orders if completed_orders > 0 else 0
            st.metric("平均实际天数", f"{avg_actual_days:.1f}天")
        
        with time_col4:
            time_efficiency = (avg_processing_days / avg_actual_days * 100) if avg_actual_days > 0 else 0
            st.metric("时间效率", f"{time_efficiency:.1f}%", 
                     help="预计天数与实际天数的比率，>100%表示提前完成")
        
        # 订单状态分布
        st.subheader("📊 订单状态分布")
        
        status_col1, status_col2 = st.columns([2, 1])
        
        with status_col1:
            status_counts = {
                '待发货': pending_orders,
                '进行中': in_progress_orders, 
                '已完成': completed_orders,
                '已取消': cancelled_orders
            }
            
            if any(status_counts.values()):
                status_df = pd.DataFrame(list(status_counts.items()), columns=['状态', '数量'])
                st.bar_chart(status_df.set_index('状态'))
        
        with status_col2:
            st.write("**详细数据:**")
            for status, count in status_counts.items():
                percentage = (count / total_orders * 100) if total_orders > 0 else 0
                st.write(f"• {status}: {count} ({percentage:.1f}%)")
        
        # 成本效益分析
        st.subheader("💰 成本效益分析")
        
        cost_col1, cost_col2, cost_col3 = st.columns(3)
        
        with cost_col1:
            avg_cost_per_order = total_cost / total_orders if total_orders > 0 else 0
            st.metric("平均订单成本", f"¥{avg_cost_per_order:.2f}")
        
        with cost_col2:
            avg_revenue_per_order = total_revenue / total_orders if total_orders > 0 else 0
            st.metric("平均订单收入", f"¥{avg_revenue_per_order:.2f}")
        
        with cost_col3:
            avg_profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            st.metric("平均利润率", f"{avg_profit_margin:.1f}%")
        
        # 代加工人员效率分析
        st.subheader("👥 代加工人员效率分析")
        
        processor_stats = []
        for processor in processors:
            stats = db.get_processor_statistics(processor['id'])
            
            # 计算该人员的效率指标
            processor_orders = [o for o in orders if o['processor_id'] == processor['id']]
            processor_completed = len([o for o in processor_orders if o['status'] == '已完成'])
            processor_overdue = 0
            processor_total_days = 0
            
            for order in processor_orders:
                processor_total_days += order['processing_days']
                expected_finish = datetime.strptime(order['expected_finish_date'], '%Y-%m-%d').date()
                if order['status'] in ['进行中', '待发货'] and expected_finish < current_date:
                    processor_overdue += 1
            
            completion_rate = (processor_completed / len(processor_orders) * 100) if processor_orders else 0
            avg_days = processor_total_days / len(processor_orders) if processor_orders else 0
            
            stats.update({
                'nickname': processor['nickname'],
                'completion_rate': completion_rate,
                'overdue_count': processor_overdue,
                'avg_processing_days': avg_days,
                'efficiency_score': completion_rate - (processor_overdue * 10)  # 简单的效率评分
            })
            processor_stats.append(stats)
        
        if processor_stats:
            stats_df = pd.DataFrame(processor_stats)
            display_columns = ['nickname', 'total_orders', 'completed_orders', 'completion_rate', 
                             'overdue_count', 'avg_processing_days', 'total_cost', 'total_revenue', 'profit']
            stats_df = stats_df[display_columns]
            stats_df.columns = ['代加工人员', '总订单', '已完成', '完成率(%)', '逾期数', 
                               '平均天数', '总成本', '总收入', '利润']
            
            # 格式化数值
            stats_df['完成率(%)'] = stats_df['完成率(%)'].round(1)
            stats_df['平均天数'] = stats_df['平均天数'].round(1)
            stats_df['总成本'] = stats_df['总成本'].apply(lambda x: f"¥{x:.2f}")
            stats_df['总收入'] = stats_df['总收入'].apply(lambda x: f"¥{x:.2f}")
            stats_df['利润'] = stats_df['利润'].apply(lambda x: f"¥{x:.2f}")
            
            st.dataframe(stats_df, use_container_width=True)
        
        # 商品类型分析
        st.subheader("📦 商品类型分析")
        
        product_stats = {}
        for order in orders:
            product = order['product_name']
            if product not in product_stats:
                product_stats[product] = {
                    'count': 0, 'total_cost': 0, 'total_revenue': 0, 
                    'total_quantity': 0, 'avg_days': 0
                }
            product_stats[product]['count'] += 1
            product_stats[product]['total_cost'] += order['processing_cost']
            product_stats[product]['total_revenue'] += order['selling_price']
            product_stats[product]['total_quantity'] += order['product_quantity']
            product_stats[product]['avg_days'] += order['processing_days']
        
        # 计算平均值
        for product in product_stats:
            count = product_stats[product]['count']
            product_stats[product]['avg_days'] = product_stats[product]['avg_days'] / count
            product_stats[product]['profit'] = (product_stats[product]['total_revenue'] - 
                                              product_stats[product]['total_cost'])
        
        if product_stats:
            product_df = pd.DataFrame.from_dict(product_stats, orient='index')
            product_df = product_df.reset_index()
            product_df.columns = ['商品名称', '订单数', '总成本', '总收入', '总数量', '平均天数', '利润']
            product_df = product_df.sort_values('订单数', ascending=False)
            
            # 显示前10个商品
            st.dataframe(product_df.head(10), use_container_width=True)
        
        # 月度趋势分析
        if len(orders) > 1:
            st.subheader("📅 月度趋势分析")
            
            # 按月统计
            monthly_data = {}
            for order in orders:
                if order['created_at']:
                    month = order['created_at'][:7]  # YYYY-MM
                    if month not in monthly_data:
                        monthly_data[month] = {
                            'orders': 0, 'cost': 0, 'revenue': 0, 'profit': 0,
                            'completed': 0, 'avg_days': 0, 'total_days': 0
                        }
                    monthly_data[month]['orders'] += 1
                    monthly_data[month]['cost'] += order['processing_cost']
                    monthly_data[month]['revenue'] += order['selling_price']
                    monthly_data[month]['profit'] += (order['selling_price'] - order['processing_cost'])
                    monthly_data[month]['total_days'] += order['processing_days']
                    
                    if order['status'] == '已完成':
                        monthly_data[month]['completed'] += 1
            
            # 计算平均天数
            for month in monthly_data:
                if monthly_data[month]['orders'] > 0:
                    monthly_data[month]['avg_days'] = (monthly_data[month]['total_days'] / 
                                                     monthly_data[month]['orders'])
            
            if monthly_data:
                monthly_df = pd.DataFrame.from_dict(monthly_data, orient='index')
                monthly_df.index = pd.to_datetime(monthly_df.index)
                monthly_df = monthly_df.sort_index()
                
                # 创建多个图表
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    st.line_chart(monthly_df[['orders', 'completed']], use_container_width=True)
                    st.caption("月度订单数量与完成数量")
                
                with chart_col2:
                    st.line_chart(monthly_df[['cost', 'revenue', 'profit']], use_container_width=True)
                    st.caption("月度成本、收入与利润")
                
                # 效率趋势
                st.line_chart(monthly_df[['avg_days']], use_container_width=True)
                st.caption("月度平均加工天数趋势")
    
    except Exception as e:
        st.error(f"统计分析失败：{str(e)}")