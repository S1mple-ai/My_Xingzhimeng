"""
统一状态管理和自动刷新机制
解决CRUD操作后数据不实时更新的问题
"""

import streamlit as st
import time
from typing import Dict, List, Callable, Any, Optional
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """统一状态管理器"""
    
    def __init__(self):
        self.cache_keys = set()
        self.data_dependencies = {
            'customers': ['customer_cache_data', 'customer_cache_key'],
            'orders': ['order_cache_data', 'order_cache_key'],
            'fabrics': ['fabric_cache_data', 'fabric_cache_key'],
            'inventory': ['inventory_cache_data', 'inventory_cache_key'],
            'processing': ['processing_cache_data', 'processing_cache_key'],
            'bag_types': ['bag_type_cache_data', 'bag_type_cache_key']
        }
        self.refresh_callbacks = {}
    
    def register_cache_key(self, key: str, data_type: str = None):
        """注册缓存键"""
        self.cache_keys.add(key)
        if data_type and data_type in self.data_dependencies:
            if key not in self.data_dependencies[data_type]:
                self.data_dependencies[data_type].append(key)
    
    def register_refresh_callback(self, data_type: str, callback: Callable):
        """注册数据刷新回调"""
        if data_type not in self.refresh_callbacks:
            self.refresh_callbacks[data_type] = []
        self.refresh_callbacks[data_type].append(callback)
    
    def clear_cache_by_type(self, data_type: str):
        """根据数据类型清理相关缓存"""
        try:
            # 清理Streamlit内置缓存
            st.cache_data.clear()
            
            # 清理session state中的相关缓存
            if data_type in self.data_dependencies:
                for cache_key in self.data_dependencies[data_type]:
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
            
            # 清理相关的UI状态
            self._clear_ui_state(data_type)
            
            logger.info(f"已清理 {data_type} 相关缓存")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
    
    def _clear_ui_state(self, data_type: str):
        """清理UI相关状态"""
        ui_patterns = {
            'customers': ['edit_customer_', 'show_customer_', 'customer_search'],
            'orders': ['edit_order_', 'show_details_', 'order_search', 'selected_orders'],
            'fabrics': ['edit_fabric_', 'show_fabric_', 'fabric_search'],
            'inventory': ['edit_inventory_', 'show_inventory_', 'inventory_search'],
            'processing': ['edit_processing_', 'show_processing_', 'processing_search']
        }
        
        if data_type in ui_patterns:
            keys_to_remove = []
            for key in st.session_state.keys():
                for pattern in ui_patterns[data_type]:
                    if key.startswith(pattern):
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del st.session_state[key]
    
    def clear_all_cache(self):
        """清理所有缓存"""
        try:
            # 清理Streamlit缓存
            st.cache_data.clear()
            
            # 清理所有注册的缓存键
            for cache_key in list(self.cache_keys):
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
            
            # 清理所有数据类型的缓存
            for data_type in self.data_dependencies:
                self.clear_cache_by_type(data_type)
            
            logger.info("已清理所有缓存")
            
        except Exception as e:
            logger.error(f"清理所有缓存失败: {str(e)}")
    
    def refresh_data(self, data_type: str):
        """刷新指定类型的数据"""
        try:
            # 清理缓存
            self.clear_cache_by_type(data_type)
            
            # 执行刷新回调
            if data_type in self.refresh_callbacks:
                for callback in self.refresh_callbacks[data_type]:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"执行刷新回调失败: {str(e)}")
            
            # 触发页面重新运行
            st.rerun()
            
        except Exception as e:
            logger.error(f"刷新数据失败: {str(e)}")


# 全局状态管理器实例
state_manager = StateManager()


def auto_refresh(data_types: List[str] = None, clear_cache: bool = True):
    """
    自动刷新装饰器
    用于CRUD操作后自动清理缓存和刷新页面
    
    Args:
        data_types: 需要刷新的数据类型列表
        clear_cache: 是否清理缓存
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 如果操作成功，进行刷新
                if result is not False and result is not None:
                    if clear_cache:
                        if data_types:
                            for data_type in data_types:
                                state_manager.clear_cache_by_type(data_type)
                        else:
                            # 如果没有指定类型，清理所有缓存
                            state_manager.clear_all_cache()
                    
                    # 触发页面重新运行
                    st.rerun()
                
                return result
                
            except Exception as e:
                logger.error(f"自动刷新装饰器执行失败: {str(e)}")
                # 即使出错也要返回原函数结果
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def smart_cache(key_prefix: str, data_type: str = None, ttl: int = 300):
    """
    智能缓存装饰器
    自动管理缓存键和过期时间
    
    Args:
        key_prefix: 缓存键前缀
        data_type: 数据类型
        ttl: 缓存过期时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}_{hash(str(args) + str(kwargs))}"
            timestamp_key = f"{cache_key}_timestamp"
            
            # 注册缓存键
            state_manager.register_cache_key(cache_key, data_type)
            
            # 检查缓存是否存在且未过期
            if (cache_key in st.session_state and 
                timestamp_key in st.session_state and
                time.time() - st.session_state[timestamp_key] < ttl):
                return st.session_state[cache_key]
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            st.session_state[timestamp_key] = time.time()
            
            return result
        
        return wrapper
    return decorator


def with_loading(message: str = "正在处理..."):
    """
    加载状态装饰器
    在操作期间显示加载状态
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def safe_operation(success_message: str = None, error_message: str = None):
    """
    安全操作装饰器
    自动处理异常并显示用户友好的消息
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                if result is not False and result is not None and success_message:
                    st.success(success_message)
                
                return result
                
            except Exception as e:
                logger.error(f"操作失败: {str(e)}")
                error_msg = error_message or f"操作失败: {str(e)}"
                st.error(error_msg)
                return False
        
        return wrapper
    return decorator


# 组合装饰器：完整的CRUD操作装饰器
def crud_operation(data_types: List[str], 
                  success_message: str = "操作成功", 
                  error_message: str = "操作失败",
                  loading_message: str = "正在处理..."):
    """
    完整的CRUD操作装饰器
    结合了自动刷新、安全操作和加载状态
    """
    def decorator(func: Callable) -> Callable:
        @with_loading(loading_message)
        @safe_operation(success_message, error_message)
        @auto_refresh(data_types)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷函数
def refresh_page():
    """刷新整个页面"""
    state_manager.clear_all_cache()
    st.rerun()


def refresh_module(data_type: str):
    """刷新指定模块"""
    state_manager.refresh_data(data_type)


def clear_module_cache(data_type: str):
    """清理指定模块的缓存"""
    state_manager.clear_cache_by_type(data_type)


# 初始化状态管理器
def init_state_manager():
    """初始化状态管理器"""
    if 'state_manager_initialized' not in st.session_state:
        st.session_state.state_manager_initialized = True
        logger.info("状态管理器已初始化")