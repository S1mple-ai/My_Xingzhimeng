"""
客户管理页面组件
"""

import streamlit as st
import pandas as pd
from ui_components import (
    create_action_button, create_confirmation_dialog,
    show_success_message, show_error_message
)


def render_customer_page(db):
    """
    渲染客户管理页面
    
    Args:
        db: 数据库管理器实例
    """
    st.markdown("## 👥 客户管理")
    
    tab1, tab2 = st.tabs(["📋 客户列表", "➕ 添加客户"])
    
    with tab1:
        _render_customer_list_tab(db)
    
    with tab2:
        _render_add_customer_tab(db)


def _render_customer_list_tab(db):
    """渲染客户列表标签页"""
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
                    new_points = st.number_input("积分", value=customer['points'], min_value=0, step=1, key=f"points_{customer['id']}", format="%d")
                
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


def _render_add_customer_tab(db):
    """渲染添加客户标签页"""
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