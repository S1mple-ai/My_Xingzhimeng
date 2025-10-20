"""
面料管理页面组件
"""

import streamlit as st
import pandas as pd
from ui_components import (
    create_card_grid, show_success_message, show_error_message
)
from upload_components import drag_drop_image_uploader


def render_fabric_page(db):
    """
    渲染面料管理页面
    
    Args:
        db: 数据库管理器实例
    """
    st.markdown("## 🧵 面料管理")
    
    tab1, tab2 = st.tabs(["📋 面料列表", "➕ 添加面料"])
    
    with tab1:
        _render_fabric_list_tab(db)
    
    with tab2:
        _render_add_fabric_tab(db)


def _render_fabric_list_tab(db):
    """渲染面料列表标签页"""
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
                st.session_state.delete_fabric_id = fabric_data['id']
                st.session_state.show_delete_fabric_confirm = True
                st.rerun()
            
            create_card_grid(fabric_list, card_type="fabric", columns=3, 
                           on_edit=on_fabric_edit, on_view=on_fabric_view, on_delete=on_fabric_delete)
        else:
            st.info("暂无符合条件的面料数据")

    else:
        st.info("📝 暂无面料数据，请添加面料")


def _render_add_fabric_tab(db):
    """渲染添加面料标签页"""
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
            help_text="支持拖拽上传 PNG, JPG, JPEG, GIF 等格式的图片",
            category="fabric"
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