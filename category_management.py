import streamlit as st
from typing import List, Dict, Optional

def render_category_tree(categories: List[Dict], db, key_prefix: str = "cat"):
    """渲染分类树形结构"""
    
    def build_tree(categories: List[Dict]) -> Dict:
        """构建树形结构"""
        tree = {}
        for cat in categories:
            if cat['parent_id'] is None:
                if 'children' not in tree:
                    tree['children'] = []
                tree['children'].append(cat)
            else:
                # 找到父分类并添加子分类
                parent = find_category_by_id(categories, cat['parent_id'])
                if parent:
                    if 'children' not in parent:
                        parent['children'] = []
                    parent['children'].append(cat)
        return tree
    
    def find_category_by_id(categories: List[Dict], category_id: int) -> Optional[Dict]:
        """根据ID查找分类"""
        for cat in categories:
            if cat['id'] == category_id:
                return cat
        return None
    
    def render_category_node(category: Dict, level: int = 0):
        """渲染单个分类节点"""
        indent = "　" * level  # 使用全角空格缩进
        level_icon = "📁" if level == 0 else "📂"
        
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"{indent}{level_icon} **{category['name']}** (Level {category['level']})")
        
        with col2:
            if st.button("✏️", key=f"{key_prefix}_edit_{category['id']}", help="编辑分类"):
                st.session_state[f"edit_category_{category['id']}"] = True
        
        with col3:
            if st.button("🗑️", key=f"{key_prefix}_delete_{category['id']}", help="删除分类"):
                if db.delete_bag_category(category['id']):
                    st.success(f"✅ 分类 \"{category['name']}\" 删除成功！")
                    st.rerun()
                else:
                    st.error("❌ 无法删除该分类，可能存在子分类或关联的包型")
        
        with col4:
            if st.button("➕", key=f"{key_prefix}_add_child_{category['id']}", help="添加子分类"):
                st.session_state[f"add_child_to_{category['id']}"] = True
        
        # 编辑分类表单
        if st.session_state.get(f"edit_category_{category['id']}", False):
            with st.expander(f"编辑分类: {category['name']}", expanded=True):
                with st.form(f"edit_category_form_{category['id']}"):
                    new_name = st.text_input("分类名称", value=category['name'])
                    
                    # 获取可选的父分类（排除自己和子分类）
                    all_categories = db.get_all_bag_categories_tree()
                    parent_options = ["无（顶级分类）"]
                    for cat in all_categories:
                        if cat['id'] != category['id'] and cat['level'] <= category['level']:
                            parent_options.append(cat['name'])
                    
                    current_parent = "无（顶级分类）"
                    if category['parent_id']:
                        parent_cat = find_category_by_id(all_categories, category['parent_id'])
                        if parent_cat:
                            current_parent = parent_cat['name']
                    
                    new_parent = st.selectbox("父分类", parent_options, 
                                            index=parent_options.index(current_parent) if current_parent in parent_options else 0)
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 保存"):
                            parent_id = None
                            if new_parent != "无（顶级分类）":
                                parent_id = next((cat['id'] for cat in all_categories if cat['name'] == new_parent), None)
                            
                            if db.update_bag_category(category['id'], new_name, parent_id):
                                st.success(f"✅ 分类更新成功！")
                                st.session_state[f"edit_category_{category['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ 更新失败")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ 取消"):
                            st.session_state[f"edit_category_{category['id']}"] = False
                            st.rerun()
        
        # 添加子分类表单
        if st.session_state.get(f"add_child_to_{category['id']}", False):
            with st.expander(f"为 \"{category['name']}\" 添加子分类", expanded=True):
                with st.form(f"add_child_form_{category['id']}"):
                    child_name = st.text_input("子分类名称", placeholder="输入子分类名称")
                    
                    col_add, col_cancel = st.columns(2)
                    with col_add:
                        if st.form_submit_button("➕ 添加"):
                            if child_name:
                                child_id = db.add_bag_category(child_name, category['id'])
                                st.success(f"✅ 子分类 \"{child_name}\" 添加成功！")
                                st.session_state[f"add_child_to_{category['id']}"] = False
                                st.rerun()
                    
                    with col_cancel:
                        if st.form_submit_button("❌ 取消"):
                            st.session_state[f"add_child_to_{category['id']}"] = False
                            st.rerun()
        
        # 渲染子分类
        if 'children' in category:
            for child in category['children']:
                render_category_node(child, level + 1)
    
    # 构建并渲染树形结构
    tree = build_tree(categories)
    if 'children' in tree:
        for category in tree['children']:
            render_category_node(category)
    else:
        st.info("📝 暂无分类，请添加第一个分类")

def render_category_management(db):
    """渲染完整的分类管理界面"""
    st.markdown("### 🗂️ 分类管理")
    
    # 添加新分类区域
    with st.expander("➕ 添加新分类", expanded=False):
        with st.form("add_new_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category_name = st.text_input("分类名称*", placeholder="例如：手提包")
            
            with col2:
                # 获取现有分类作为父分类选项
                categories = db.get_all_bag_categories_tree()
                parent_options = ["无（顶级分类）"] + [cat['name'] for cat in categories]
                parent_choice = st.selectbox("父分类", parent_options)
            
            if st.form_submit_button("➕ 添加分类", use_container_width=True):
                if category_name:
                    parent_id = None
                    if parent_choice != "无（顶级分类）":
                        parent_id = next((cat['id'] for cat in categories if cat['name'] == parent_choice), None)
                    
                    category_id = db.add_bag_category(category_name, parent_id)
                    st.success(f"✅ 分类 \"{category_name}\" 添加成功！")
                    st.rerun()
                else:
                    st.error("❌ 请输入分类名称")
    
    # 分类树形显示
    st.markdown("#### 📂 分类结构")
    categories = db.get_all_bag_categories_tree()
    
    if categories:
        # 添加搜索功能
        search_term = st.text_input("🔍 搜索分类", placeholder="输入分类名称进行搜索...")
        
        if search_term:
            filtered_categories = [cat for cat in categories if search_term.lower() in cat['name'].lower()]
            st.markdown(f"**搜索结果：** 找到 {len(filtered_categories)} 个匹配的分类")
            render_category_tree(filtered_categories, db, "search")
        else:
            render_category_tree(categories, db, "main")
        
        # 统计信息
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总分类数", len(categories))
        with col2:
            top_level_count = len([cat for cat in categories if cat['parent_id'] is None])
            st.metric("顶级分类", top_level_count)
        with col3:
            max_level = max([cat['level'] for cat in categories]) if categories else 0
            st.metric("最大层级", max_level)
    else:
        st.info("📝 暂无分类，请添加第一个分类")