"""
系统设置页面组件
"""
import streamlit as st
import os
import sqlite3


def render_settings_page(db):
    """渲染系统设置页面"""
    st.markdown("## ⚙️ 系统设置")
    
    # 创建选项卡
    tab1, tab2, tab3 = st.tabs(["🗄️ 自动备份", "📊 系统信息", "🔧 高级设置"])
    
    with tab1:
        _render_backup_tab(db)
    
    with tab2:
        _render_system_info_tab(db)
    
    with tab3:
        _render_advanced_settings_tab()


def _render_backup_tab(db):
    """渲染自动备份标签页"""
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


def _render_system_info_tab(db):
    """渲染系统信息标签页"""
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


def _render_advanced_settings_tab():
    """渲染高级设置标签页"""
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