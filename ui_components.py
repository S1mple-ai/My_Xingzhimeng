import streamlit as st
import time
from typing import Optional, List, Dict, Any

def show_loading_spinner(text: str = "加载中..."):
    """显示加载动画"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: 2rem;">
        <div class="loading-spinner"></div>
        <span style="margin-left: 1rem; font-size: 1.1rem; color: var(--text-dark);">{text}</span>
    </div>
    """, unsafe_allow_html=True)

def show_progress_bar(progress: float, text: str = ""):
    """显示进度条
    
    Args:
        progress: 进度值 (0-100)
        text: 进度文本
    """
    progress = max(0, min(100, progress))  # 确保在0-100范围内
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        {f'<div style="margin-bottom: 0.5rem; font-weight: 600;">{text}</div>' if text else ''}
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%;"></div>
        </div>
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-dark);">
            {progress:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_success_message(message: str, icon: str = "✅"):
    """显示成功消息"""
    st.markdown(f"""
    <div class="success-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_error_message(message: str, icon: str = "❌"):
    """显示错误消息"""
    st.markdown(f"""
    <div class="error-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_warning_message(message: str, icon: str = "⚠️"):
    """显示警告消息"""
    st.markdown(f"""
    <div class="warning-message">
        <strong>{icon} {message}</strong>
    </div>
    """, unsafe_allow_html=True)

def show_info_card(title: str, content: str, icon: str = "ℹ️"):
    """显示信息卡片"""
    st.markdown(f"""
    <div class="metric-card">
        <h4 style="margin: 0 0 1rem 0; color: var(--primary-color);">
            {icon} {title}
        </h4>
        <p style="margin: 0; color: var(--text-dark);">{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: Optional[str] = None, icon: str = "📊"):
    """创建指标卡片"""
    delta_html = ""
    if delta:
        delta_color = "var(--success-color)" if not delta.startswith("-") else "var(--error-color)"
        delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h4 style="margin: 0; color: var(--text-dark);">{title}</h4>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def create_action_button(text: str, key: str, icon: str = "", variant: str = "primary"):
    """创建动作按钮
    
    Args:
        text: 按钮文本
        key: 按钮key
        icon: 图标
        variant: 按钮变体 (primary, secondary, success, warning, error)
    """
    try:
        button_text = f"{icon} {text}" if icon else text
        
        # 根据变体设置样式
        if variant == "secondary":
            style = "background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));"
        elif variant == "success":
            style = "background: linear-gradient(135deg, var(--success-color), #00B894);"
        elif variant == "warning":
            style = "background: linear-gradient(135deg, var(--warning-color), #FDCB6E);"
        elif variant == "error":
            style = "background: linear-gradient(135deg, var(--error-color), #E84393);"
        else:
            style = ""
        
        if style:
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button[key="{key}"] {{
                {style}
            }}
            </style>
            """, unsafe_allow_html=True)
        
        return st.button(button_text, key=key)
    except Exception as e:
        st.error(f"按钮创建失败: {str(e)}")
        return False

def create_data_table(data: List[Dict[str, Any]], columns: List[str], title: str = ""):
    """创建数据表格
    
    Args:
        data: 数据列表
        columns: 列名列表
        title: 表格标题
    """
    if title:
        st.markdown(f"### 📋 {title}")
    
    if not data:
        st.info("暂无数据")
        return
    
    # 转换为DataFrame并显示
    import pandas as pd
    df = pd.DataFrame(data)
    
    # 只显示指定的列
    if columns:
        df = df[columns]
    
    st.dataframe(df, use_container_width=True)

def create_confirmation_dialog(message: str, key: str) -> bool:
    """创建确认对话框
    
    Args:
        message: 确认消息
        key: 组件key
        
    Returns:
        bool: 用户是否确认
    """
    st.markdown(f"""
    <div class="warning-message">
        <strong>⚠️ 确认操作</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = create_action_button("确认", f"confirm_{key}", "✅", "success")
    with col2:
        cancel = create_action_button("取消", f"cancel_{key}", "❌", "error")
    
    return confirm

def simulate_loading(duration: float = 2.0, steps: int = 10):
    """模拟加载过程
    
    Args:
        duration: 总持续时间（秒）
        steps: 进度步数
    """
    progress_placeholder = st.empty()
    
    for i in range(steps + 1):
        progress = (i / steps) * 100
        with progress_placeholder.container():
            show_progress_bar(progress, f"处理中... ({i}/{steps})")
        time.sleep(duration / steps)
    
    progress_placeholder.empty()

def create_tooltip(text: str, tooltip_text: str):
    """创建带工具提示的文本
    
    Args:
        text: 显示文本
        tooltip_text: 工具提示文本
    """
    st.markdown(f"""
    <div class="tooltip">
        {text}
        <span class="tooltiptext">{tooltip_text}</span>
    </div>
    """, unsafe_allow_html=True)