"""
扩展UI组件模块
提供高级数据表格、搜索过滤面板和仪表板统计组件
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta


def create_advanced_data_table(
    data: pd.DataFrame,
    title: str = "数据表格",
    searchable: bool = True,
    sortable: bool = True,
    paginated: bool = True,
    page_size: int = 10,
    actions: Optional[List[Dict[str, Any]]] = None,
    key: str = "advanced_table"
) -> Dict[str, Any]:
    """
    创建高级数据表格
    
    Args:
        data: 数据DataFrame
        title: 表格标题
        searchable: 是否可搜索
        sortable: 是否可排序
        paginated: 是否分页
        page_size: 每页显示数量
        actions: 操作按钮列表
        key: 组件唯一键
    
    Returns:
        包含用户操作结果的字典
    """
    result = {
        'selected_rows': [],
        'action_clicked': None,
        'search_query': '',
        'filtered_data': data.copy()
    }
    
    if data.empty:
        st.warning("暂无数据")
        return result
    
    # 标题
    st.markdown(f"### {title}")
    
    # 搜索功能
    if searchable:
        search_query = st.text_input(
            "🔍 搜索",
            placeholder="输入关键词搜索...",
            key=f"{key}_search"
        )
        result['search_query'] = search_query
        
        if search_query:
            # 在所有文本列中搜索
            text_columns = data.select_dtypes(include=['object']).columns
            mask = pd.Series([False] * len(data))
            
            for col in text_columns:
                mask |= data[col].astype(str).str.contains(search_query, case=False, na=False)
            
            data = data[mask]
            result['filtered_data'] = data
    
    # 排序功能
    if sortable and not data.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            sort_column = st.selectbox(
                "排序字段",
                options=data.columns.tolist(),
                key=f"{key}_sort_col"
            )
        with col2:
            sort_order = st.selectbox(
                "排序方式",
                options=["升序", "降序"],
                key=f"{key}_sort_order"
            )
        
        if sort_column:
            ascending = sort_order == "升序"
            data = data.sort_values(by=sort_column, ascending=ascending)
            result['filtered_data'] = data
    
    # 分页功能
    if paginated and not data.empty:
        total_rows = len(data)
        total_pages = (total_rows - 1) // page_size + 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input(
                    f"页码 (共 {total_pages} 页)",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    key=f"{key}_page"
                )
            
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            data = data.iloc[start_idx:end_idx]
            
            st.caption(f"显示第 {start_idx + 1}-{end_idx} 条，共 {total_rows} 条记录")
    
    # 显示数据表格
    if not data.empty:
        # 使用streamlit的数据编辑器
        edited_data = st.data_editor(
            data,
            use_container_width=True,
            hide_index=True,
            key=f"{key}_editor"
        )
        
        # 操作按钮
        if actions:
            st.markdown("---")
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(
                        action.get('label', '操作'),
                        key=f"{key}_action_{i}",
                        type=action.get('type', 'secondary')
                    ):
                        result['action_clicked'] = action.get('name', f'action_{i}')
    
    return result


def create_search_filter_panel(
    filters: Dict[str, Dict[str, Any]],
    key: str = "search_filter"
) -> Dict[str, Any]:
    """
    创建搜索过滤面板
    
    Args:
        filters: 过滤器配置字典
        key: 组件唯一键
    
    Returns:
        用户选择的过滤条件
    """
    result = {}
    
    with st.expander("🔍 搜索与过滤", expanded=False):
        for filter_name, filter_config in filters.items():
            filter_type = filter_config.get('type', 'text')
            label = filter_config.get('label', filter_name)
            
            if filter_type == 'text':
                result[filter_name] = st.text_input(
                    label,
                    value=filter_config.get('default', ''),
                    key=f"{key}_{filter_name}"
                )
            
            elif filter_type == 'select':
                options = filter_config.get('options', [])
                result[filter_name] = st.selectbox(
                    label,
                    options=options,
                    index=0 if options else 0,
                    key=f"{key}_{filter_name}"
                )
            
            elif filter_type == 'multiselect':
                options = filter_config.get('options', [])
                result[filter_name] = st.multiselect(
                    label,
                    options=options,
                    default=filter_config.get('default', []),
                    key=f"{key}_{filter_name}"
                )
            
            elif filter_type == 'date_range':
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        f"{label} - 开始日期",
                        value=filter_config.get('default_start', datetime.now().date()),
                        key=f"{key}_{filter_name}_start"
                    )
                with col2:
                    end_date = st.date_input(
                        f"{label} - 结束日期",
                        value=filter_config.get('default_end', datetime.now().date()),
                        key=f"{key}_{filter_name}_end"
                    )
                result[filter_name] = {'start': start_date, 'end': end_date}
            
            elif filter_type == 'number_range':
                col1, col2 = st.columns(2)
                with col1:
                    min_val = st.number_input(
                        f"{label} - 最小值",
                        value=filter_config.get('min_default', 0),
                        key=f"{key}_{filter_name}_min"
                    )
                with col2:
                    max_val = st.number_input(
                        f"{label} - 最大值",
                        value=filter_config.get('max_default', 100),
                        key=f"{key}_{filter_name}_max"
                    )
                result[filter_name] = {'min': min_val, 'max': max_val}
    
    return result


def create_dashboard_stats(
    stats: List[Dict[str, Any]],
    columns: int = 4,
    key: str = "dashboard_stats"
) -> None:
    """
    创建仪表板统计卡片
    
    Args:
        stats: 统计数据列表
        columns: 列数
        key: 组件唯一键
    """
    if not stats:
        st.warning("暂无统计数据")
        return
    
    # 创建列布局
    cols = st.columns(columns)
    
    for i, stat in enumerate(stats):
        col_index = i % columns
        
        with cols[col_index]:
            # 创建统计卡片
            title = stat.get('title', '统计项')
            value = stat.get('value', 0)
            delta = stat.get('delta', None)
            delta_color = stat.get('delta_color', 'normal')
            icon = stat.get('icon', '📊')
            
            # 卡片样式
            card_style = f"""
            <div style="
                background: white;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #2E86AB;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 0.5rem;
                ">
                    <span style="
                        font-size: 0.9rem;
                        color: #666;
                        font-weight: 500;
                    ">{title}</span>
                    <span style="font-size: 1.2rem;">{icon}</span>
                </div>
                <div style="
                    font-size: 1.8rem;
                    font-weight: bold;
                    color: #2E86AB;
                    margin-bottom: 0.5rem;
                ">{value}</div>
            """
            
            if delta is not None:
                delta_symbol = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                delta_color_code = "#28a745" if delta > 0 else "#dc3545" if delta < 0 else "#6c757d"
                
                card_style += f"""
                <div style="
                    font-size: 0.8rem;
                    color: {delta_color_code};
                    font-weight: 500;
                ">
                    {delta_symbol} {abs(delta)}
                </div>
                """
            
            card_style += "</div>"
            
            st.markdown(card_style, unsafe_allow_html=True)


def create_chart_container(
    chart_type: str,
    data: pd.DataFrame,
    title: str = "图表",
    **kwargs
) -> None:
    """
    创建图表容器
    
    Args:
        chart_type: 图表类型 ('line', 'bar', 'pie', 'scatter')
        data: 数据
        title: 图表标题
        **kwargs: 其他图表参数
    """
    if data.empty:
        st.warning("暂无数据可显示")
        return
    
    st.markdown(f"### {title}")
    
    try:
        if chart_type == 'line':
            x_col = kwargs.get('x', data.columns[0])
            y_col = kwargs.get('y', data.columns[1] if len(data.columns) > 1 else data.columns[0])
            fig = px.line(data, x=x_col, y=y_col, title=title)
            
        elif chart_type == 'bar':
            x_col = kwargs.get('x', data.columns[0])
            y_col = kwargs.get('y', data.columns[1] if len(data.columns) > 1 else data.columns[0])
            fig = px.bar(data, x=x_col, y=y_col, title=title)
            
        elif chart_type == 'pie':
            names_col = kwargs.get('names', data.columns[0])
            values_col = kwargs.get('values', data.columns[1] if len(data.columns) > 1 else data.columns[0])
            fig = px.pie(data, names=names_col, values=values_col, title=title)
            
        elif chart_type == 'scatter':
            x_col = kwargs.get('x', data.columns[0])
            y_col = kwargs.get('y', data.columns[1] if len(data.columns) > 1 else data.columns[0])
            fig = px.scatter(data, x=x_col, y=y_col, title=title)
            
        else:
            st.error(f"不支持的图表类型: {chart_type}")
            return
        
        # 更新图表布局
        fig.update_layout(
            height=400,
            showlegend=True,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"图表生成失败: {str(e)}")


def create_data_export_panel(
    data: pd.DataFrame,
    filename_prefix: str = "export",
    key: str = "export_panel"
) -> None:
    """
    创建数据导出面板
    
    Args:
        data: 要导出的数据
        filename_prefix: 文件名前缀
        key: 组件唯一键
    """
    if data.empty:
        st.warning("暂无数据可导出")
        return
    
    with st.expander("📤 数据导出", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("导出 CSV", key=f"{key}_csv"):
                csv = data.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载 CSV 文件",
                    data=csv,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("导出 Excel", key=f"{key}_excel"):
                # 注意：这里需要安装openpyxl库
                try:
                    excel_buffer = data.to_excel(index=False, engine='openpyxl')
                    st.download_button(
                        label="下载 Excel 文件",
                        data=excel_buffer,
                        file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ImportError:
                    st.error("请安装 openpyxl 库以支持 Excel 导出")
        
        with col3:
            if st.button("导出 JSON", key=f"{key}_json"):
                json_data = data.to_json(orient='records', force_ascii=False, indent=2)
                st.download_button(
                    label="下载 JSON 文件",
                    data=json_data,
                    file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )