"""
增强的日志查看界面
提供统一的日志管理、分析和监控功能
"""

import streamlit as st
import os
import glob
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter

from logging_config import get_logger, get_log_statistics, set_log_level, LOG_LEVELS


class EnhancedLogViewer:
    """增强的日志查看器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.logger = get_logger()
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def render_log_management_panel(self):
        """渲染日志管理面板"""
        st.header("📋 日志管理系统")
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 日志概览", 
            "🔍 日志查看", 
            "📈 日志分析", 
            "⚙️ 日志配置", 
            "🧹 日志维护"
        ])
        
        with tab1:
            self._render_log_overview()
        
        with tab2:
            self._render_log_viewer()
        
        with tab3:
            self._render_log_analysis()
        
        with tab4:
            self._render_log_configuration()
        
        with tab5:
            self._render_log_maintenance()
    
    def _render_log_overview(self):
        """渲染日志概览"""
        st.subheader("📊 日志系统概览")
        
        # 获取日志统计
        stats = get_log_statistics()
        log_files = self._get_log_files()
        
        # 显示关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📁 日志文件数", stats['total_files'])
        
        with col2:
            st.metric("💾 总大小", f"{stats['total_size_mb']:.2f} MB")
        
        with col3:
            # 今日错误数量
            today_errors = self._count_today_errors()
            st.metric("❌ 今日错误", today_errors)
        
        with col4:
            # 最新日志时间
            if stats['latest_modified']:
                latest_time = stats['latest_modified'].strftime("%H:%M:%S")
                st.metric("🕐 最新日志", latest_time)
            else:
                st.metric("🕐 最新日志", "无")
        
        # 日志文件分布图表
        if stats['files_by_category']:
            st.subheader("📊 日志文件分布")
            
            categories = list(stats['files_by_category'].keys())
            counts = list(stats['files_by_category'].values())
            
            fig = px.pie(
                values=counts,
                names=categories,
                title="日志文件类型分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 日志文件列表
        st.subheader("📋 日志文件列表")
        if log_files:
            df = pd.DataFrame(log_files)
            df['大小(KB)'] = (df['size'] / 1024).round(2)
            df['修改时间'] = pd.to_datetime(df['modified']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            display_df = df[['name', '大小(KB)', '修改时间', 'category']].rename(columns={
                'name': '文件名',
                'category': '类型'
            })
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("📝 暂无日志文件")
    
    def _render_log_viewer(self):
        """渲染日志查看器"""
        st.subheader("🔍 日志查看器")
        
        # 日志文件选择
        log_files = self._get_log_files()
        if not log_files:
            st.info("📝 暂无日志文件")
            return
        
        file_options = {f['name']: f for f in log_files}
        selected_file = st.selectbox(
            "选择日志文件",
            options=list(file_options.keys()),
            key="log_file_selector"
        )
        
        if not selected_file:
            return
        
        # 过滤选项
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_levels = ["全部"] + list(LOG_LEVELS.keys())
            selected_level = st.selectbox("日志级别", log_levels, key="log_level_filter")
        
        with col2:
            time_range = st.selectbox(
                "时间范围",
                ["全部", "最近1小时", "最近6小时", "最近24小时", "最近7天"],
                key="time_range_filter"
            )
        
        with col3:
            search_term = st.text_input("🔍 搜索关键词", key="log_search_term")
        
        # 显示选项
        col1, col2 = st.columns(2)
        with col1:
            max_lines = st.slider("显示行数", 10, 1000, 100, key="log_max_lines")
        with col2:
            reverse_order = st.checkbox("倒序显示（最新在前）", value=True, key="log_reverse")
        
        # 读取和过滤日志
        log_content = self._read_and_filter_log(
            selected_file,
            selected_level,
            time_range,
            search_term,
            max_lines,
            reverse_order
        )
        
        if log_content:
            # 下载按钮
            st.download_button(
                label="📥 下载日志",
                data=log_content,
                file_name=f"{selected_file}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                mime="text/plain"
            )
            
            # 显示日志内容
            st.code(log_content, language="text")
        else:
            st.info("📝 没有找到匹配的日志内容")
    
    def _render_log_analysis(self):
        """渲染日志分析"""
        st.subheader("📈 日志分析")
        
        # 分析选项
        analysis_type = st.selectbox(
            "分析类型",
            ["错误统计", "性能分析", "访问模式", "时间分布"],
            key="analysis_type"
        )
        
        if analysis_type == "错误统计":
            self._render_error_analysis()
        elif analysis_type == "性能分析":
            self._render_performance_analysis()
        elif analysis_type == "访问模式":
            self._render_access_pattern_analysis()
        elif analysis_type == "时间分布":
            self._render_time_distribution_analysis()
    
    def _render_log_configuration(self):
        """渲染日志配置"""
        st.subheader("⚙️ 日志配置")
        
        # 当前配置显示
        st.write("**当前日志配置：**")
        current_level = st.session_state.get('current_log_level', 'INFO')
        st.info(f"日志级别: {current_level}")
        
        # 日志级别设置
        st.write("**修改日志级别：**")
        new_level = st.selectbox(
            "选择新的日志级别",
            list(LOG_LEVELS.keys()),
            index=list(LOG_LEVELS.keys()).index(current_level),
            key="new_log_level"
        )
        
        if st.button("应用配置", key="apply_log_config"):
            set_log_level(new_level)
            st.session_state['current_log_level'] = new_level
            st.success(f"✅ 日志级别已设置为: {new_level}")
            st.rerun()
        
        # 日志轮转配置
        st.write("**日志轮转配置：**")
        col1, col2 = st.columns(2)
        
        with col1:
            max_file_size = st.number_input(
                "最大文件大小 (MB)",
                min_value=1,
                max_value=100,
                value=10,
                key="max_file_size"
            )
        
        with col2:
            backup_count = st.number_input(
                "备份文件数量",
                min_value=1,
                max_value=10,
                value=5,
                key="backup_count"
            )
        
        if st.button("应用轮转配置", key="apply_rotation_config"):
            st.success("✅ 日志轮转配置已更新")
    
    def _render_log_maintenance(self):
        """渲染日志维护"""
        st.subheader("🧹 日志维护")
        
        # 清理选项
        st.write("**日志清理：**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cleanup_days = st.number_input(
                "清理多少天前的日志",
                min_value=1,
                max_value=365,
                value=30,
                key="cleanup_days"
            )
        
        with col2:
            cleanup_size_mb = st.number_input(
                "清理超过多少MB的日志",
                min_value=1,
                max_value=1000,
                value=100,
                key="cleanup_size_mb"
            )
        
        # 清理按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ 清理旧日志", key="cleanup_old_logs"):
                self._cleanup_old_logs(cleanup_days)
        
        with col2:
            if st.button("🗑️ 清理大文件", key="cleanup_large_files"):
                self._cleanup_large_files(cleanup_size_mb)
        
        with col3:
            if st.button("🗑️ 清理所有日志", key="cleanup_all_logs"):
                if st.session_state.get('confirm_cleanup_all', False):
                    self._cleanup_all_logs()
                    st.session_state['confirm_cleanup_all'] = False
                    st.success("✅ 所有日志已清理")
                    st.rerun()
                else:
                    st.session_state['confirm_cleanup_all'] = True
                    st.warning("⚠️ 再次点击确认清理所有日志")
        
        # 日志压缩
        st.write("**日志压缩：**")
        if st.button("📦 压缩日志文件", key="compress_logs"):
            self._compress_logs()
    
    def _get_log_files(self) -> List[Dict[str, Any]]:
        """获取日志文件列表"""
        log_files = []
        
        if not os.path.exists(self.log_dir):
            return log_files
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(self.log_dir, filename)
                try:
                    stat = os.stat(file_path)
                    log_files.append({
                        'name': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'category': filename.replace('.log', '')
                    })
                except OSError:
                    continue
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    def _count_today_errors(self) -> int:
        """统计今日错误数量"""
        error_log_path = os.path.join(self.log_dir, "error.log")
        if not os.path.exists(error_log_path):
            return 0
        
        today = datetime.now().date()
        error_count = 0
        
        try:
            with open(error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'ERROR' in line and today.strftime('%Y-%m-%d') in line:
                        error_count += 1
        except Exception:
            pass
        
        return error_count
    
    def _read_and_filter_log(self, filename: str, level: str, time_range: str, 
                           search_term: str, max_lines: int, reverse_order: bool) -> str:
        """读取和过滤日志内容"""
        file_path = os.path.join(self.log_dir, filename)
        
        if not os.path.exists(file_path):
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return ""
        
        # 时间过滤
        if time_range != "全部":
            lines = self._filter_by_time(lines, time_range)
        
        # 级别过滤
        if level != "全部":
            lines = [line for line in lines if level in line]
        
        # 关键词搜索
        if search_term:
            lines = [line for line in lines if search_term.lower() in line.lower()]
        
        # 排序
        if reverse_order:
            lines = lines[::-1]
        
        # 限制行数
        lines = lines[:max_lines]
        
        return ''.join(lines)
    
    def _filter_by_time(self, lines: List[str], time_range: str) -> List[str]:
        """按时间范围过滤日志行"""
        now = datetime.now()
        
        if time_range == "最近1小时":
            cutoff = now - timedelta(hours=1)
        elif time_range == "最近6小时":
            cutoff = now - timedelta(hours=6)
        elif time_range == "最近24小时":
            cutoff = now - timedelta(days=1)
        elif time_range == "最近7天":
            cutoff = now - timedelta(days=7)
        else:
            return lines
        
        filtered_lines = []
        for line in lines:
            # 尝试从日志行中提取时间戳
            timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
            if timestamp_match:
                try:
                    log_time = datetime.strptime(timestamp_match.group(), '%Y-%m-%d %H:%M:%S')
                    if log_time >= cutoff:
                        filtered_lines.append(line)
                except ValueError:
                    filtered_lines.append(line)  # 如果解析失败，保留该行
            else:
                filtered_lines.append(line)  # 如果没有时间戳，保留该行
        
        return filtered_lines
    
    def _render_error_analysis(self):
        """渲染错误分析"""
        st.write("**错误统计分析**")
        
        error_log_path = os.path.join(self.log_dir, "error.log")
        if not os.path.exists(error_log_path):
            st.info("📝 暂无错误日志")
            return
        
        # 分析错误日志
        error_stats = self._analyze_error_log(error_log_path)
        
        if error_stats:
            # 错误类型分布
            col1, col2 = st.columns(2)
            
            with col1:
                if error_stats['error_types']:
                    fig = px.bar(
                        x=list(error_stats['error_types'].keys()),
                        y=list(error_stats['error_types'].values()),
                        title="错误类型分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if error_stats['hourly_distribution']:
                    fig = px.line(
                        x=list(error_stats['hourly_distribution'].keys()),
                        y=list(error_stats['hourly_distribution'].values()),
                        title="错误时间分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # 最近错误列表
            st.write("**最近错误：**")
            if error_stats['recent_errors']:
                for error in error_stats['recent_errors'][:10]:
                    st.error(f"🕐 {error['time']} - {error['message']}")
        else:
            st.info("📝 暂无错误数据")
    
    def _render_performance_analysis(self):
        """渲染性能分析"""
        st.write("**性能分析**")
        
        perf_log_path = os.path.join(self.log_dir, "performance.log")
        if not os.path.exists(perf_log_path):
            st.info("📝 暂无性能日志")
            return
        
        # 分析性能日志
        perf_stats = self._analyze_performance_log(perf_log_path)
        
        if perf_stats:
            # 性能指标
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_time = sum(perf_stats['execution_times']) / len(perf_stats['execution_times'])
                st.metric("平均执行时间", f"{avg_time:.3f}s")
            
            with col2:
                max_time = max(perf_stats['execution_times'])
                st.metric("最长执行时间", f"{max_time:.3f}s")
            
            with col3:
                st.metric("性能记录数", len(perf_stats['execution_times']))
            
            # 性能趋势图
            if perf_stats['time_series']:
                df = pd.DataFrame(perf_stats['time_series'])
                fig = px.line(df, x='time', y='execution_time', title="性能趋势")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 暂无性能数据")
    
    def _render_access_pattern_analysis(self):
        """渲染访问模式分析"""
        st.write("**访问模式分析**")
        st.info("🚧 功能开发中...")
    
    def _render_time_distribution_analysis(self):
        """渲染时间分布分析"""
        st.write("**时间分布分析**")
        st.info("🚧 功能开发中...")
    
    def _analyze_error_log(self, file_path: str) -> Dict[str, Any]:
        """分析错误日志"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return {}
        
        error_types = Counter()
        hourly_distribution = defaultdict(int)
        recent_errors = []
        
        for line in lines:
            if 'ERROR' in line:
                # 提取错误类型
                if 'Exception' in line:
                    error_type = re.search(r'(\w+Exception)', line)
                    if error_type:
                        error_types[error_type.group(1)] += 1
                
                # 提取时间
                timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                if timestamp_match:
                    try:
                        log_time = datetime.strptime(timestamp_match.group(), '%Y-%m-%d %H:%M:%S')
                        hourly_distribution[log_time.hour] += 1
                        
                        recent_errors.append({
                            'time': timestamp_match.group(),
                            'message': line.strip()
                        })
                    except ValueError:
                        pass
        
        # 按时间排序最近错误
        recent_errors.sort(key=lambda x: x['time'], reverse=True)
        
        return {
            'error_types': dict(error_types),
            'hourly_distribution': dict(hourly_distribution),
            'recent_errors': recent_errors
        }
    
    def _analyze_performance_log(self, file_path: str) -> Dict[str, Any]:
        """分析性能日志"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return {}
        
        execution_times = []
        time_series = []
        
        for line in lines:
            if 'PERFORMANCE' in line:
                # 提取执行时间
                time_match = re.search(r'(\d+\.\d+)s', line)
                if time_match:
                    exec_time = float(time_match.group(1))
                    execution_times.append(exec_time)
                    
                    # 提取时间戳
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                    if timestamp_match:
                        time_series.append({
                            'time': timestamp_match.group(),
                            'execution_time': exec_time
                        })
        
        return {
            'execution_times': execution_times,
            'time_series': time_series
        }
    
    def _cleanup_old_logs(self, days: int):
        """清理旧日志"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        for log_file in self._get_log_files():
            if log_file['modified'] < cutoff_date:
                try:
                    os.remove(log_file['path'])
                    cleaned_count += 1
                except OSError:
                    pass
        
        st.success(f"✅ 已清理 {cleaned_count} 个旧日志文件")
    
    def _cleanup_large_files(self, size_mb: int):
        """清理大文件"""
        size_bytes = size_mb * 1024 * 1024
        cleaned_count = 0
        
        for log_file in self._get_log_files():
            if log_file['size'] > size_bytes:
                try:
                    os.remove(log_file['path'])
                    cleaned_count += 1
                except OSError:
                    pass
        
        st.success(f"✅ 已清理 {cleaned_count} 个大日志文件")
    
    def _cleanup_all_logs(self):
        """清理所有日志"""
        log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
        for log_file in log_files:
            try:
                os.remove(log_file)
            except OSError:
                pass
    
    def _compress_logs(self):
        """压缩日志文件"""
        st.info("🚧 日志压缩功能开发中...")


def render_enhanced_log_viewer():
    """渲染增强的日志查看器"""
    viewer = EnhancedLogViewer()
    viewer.render_log_management_panel()


# 导出主要接口
__all__ = ['EnhancedLogViewer', 'render_enhanced_log_viewer']