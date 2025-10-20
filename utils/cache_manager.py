"""
缓存管理工具类

提供统一的缓存管理功能，包括缓存存储、获取、清理等操作。
支持基于时间的缓存过期和模式匹配的批量清理。
"""

import hashlib
import streamlit as st
from datetime import datetime
from typing import Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.cache_prefix = "cache_"
        self.time_prefix = "cache_time_"
    
    def generate_cache_key(self, func_name: str, key_prefix: str = "", *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            func_name: 函数名
            key_prefix: 缓存键前缀
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            生成的缓存键
        """
        cache_key = f"{key_prefix}_{func_name}" if key_prefix else func_name
        
        # 添加参数到缓存键
        if args or kwargs:
            params_str = str(args) + str(sorted(kwargs.items()))
            cache_key += f"_{hashlib.md5(params_str.encode()).hexdigest()[:8]}"
        
        return cache_key
    
    def get(self, cache_key: str, ttl: int = 300) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            cache_key: 缓存键
            ttl: 缓存时间（秒）
            
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        try:
            full_cache_key = f"{self.cache_prefix}{cache_key}"
            full_time_key = f"{self.time_prefix}{cache_key}"
            
            cached_result = st.session_state.get(full_cache_key)
            if cached_result is not None:
                cache_time = st.session_state.get(full_time_key, 0)
                if (datetime.now().timestamp() - cache_time) < ttl:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
                else:
                    # 缓存过期，清理
                    self._remove_cache_item(cache_key)
                    logger.debug(f"缓存过期: {cache_key}")
            
            return None
            
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
            return None
    
    def set(self, cache_key: str, value: Any) -> bool:
        """
        设置缓存数据
        
        Args:
            cache_key: 缓存键
            value: 要缓存的数据
            
        Returns:
            是否设置成功
        """
        try:
            full_cache_key = f"{self.cache_prefix}{cache_key}"
            full_time_key = f"{self.time_prefix}{cache_key}"
            
            st.session_state[full_cache_key] = value
            st.session_state[full_time_key] = datetime.now().timestamp()
            
            logger.debug(f"缓存存储: {cache_key}")
            return True
            
        except Exception as e:
            logger.warning(f"缓存存储失败: {e}")
            return False
    
    def _remove_cache_item(self, cache_key: str):
        """
        移除单个缓存项
        
        Args:
            cache_key: 缓存键
        """
        full_cache_key = f"{self.cache_prefix}{cache_key}"
        full_time_key = f"{self.time_prefix}{cache_key}"
        
        st.session_state.pop(full_cache_key, None)
        st.session_state.pop(full_time_key, None)
    
    def clear(self, cache_prefix: str = None) -> int:
        """
        清理缓存
        
        Args:
            cache_prefix: 缓存前缀，如果指定则只清理匹配的缓存
            
        Returns:
            清理的缓存项数量
        """
        try:
            keys_to_remove = []
            
            if cache_prefix:
                # 清理特定前缀的缓存
                target_cache_prefix = f"{self.cache_prefix}{cache_prefix}"
                target_time_prefix = f"{self.time_prefix}{cache_prefix}"
                
                for key in list(st.session_state.keys()):
                    if key.startswith(target_cache_prefix) or key.startswith(target_time_prefix):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del st.session_state[key]
                
                logger.debug(f"清理缓存: {cache_prefix} ({len(keys_to_remove)} 项)")
            else:
                # 清理所有查询缓存
                for key in list(st.session_state.keys()):
                    if key.startswith(self.cache_prefix) or key.startswith(self.time_prefix):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del st.session_state[key]
                
                logger.debug(f"清理所有缓存 ({len(keys_to_remove)} 项)")
            
            return len(keys_to_remove)
            
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        try:
            cache_items = 0
            time_items = 0
            total_size = 0
            
            for key, value in st.session_state.items():
                if key.startswith(self.cache_prefix):
                    cache_items += 1
                    # 估算大小（简单估算）
                    total_size += len(str(value))
                elif key.startswith(self.time_prefix):
                    time_items += 1
            
            return {
                'cache_items': cache_items,
                'time_items': time_items,
                'total_items': cache_items + time_items,
                'estimated_size_bytes': total_size,
                'estimated_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.warning(f"获取缓存统计失败: {e}")
            return {
                'cache_items': 0,
                'time_items': 0,
                'total_items': 0,
                'estimated_size_bytes': 0,
                'estimated_size_mb': 0
            }
    
    def cleanup_expired_cache(self, ttl: int = 300) -> int:
        """
        清理过期缓存
        
        Args:
            ttl: 缓存时间（秒）
            
        Returns:
            清理的过期缓存项数量
        """
        try:
            current_time = datetime.now().timestamp()
            expired_keys = []
            
            # 找出所有过期的缓存项
            for key in list(st.session_state.keys()):
                if key.startswith(self.time_prefix):
                    cache_time = st.session_state.get(key, 0)
                    if (current_time - cache_time) >= ttl:
                        # 过期了，添加到清理列表
                        cache_key = key.replace(self.time_prefix, "")
                        expired_keys.append(cache_key)
            
            # 清理过期的缓存项
            for cache_key in expired_keys:
                self._remove_cache_item(cache_key)
            
            logger.debug(f"清理过期缓存: {len(expired_keys)} 项")
            return len(expired_keys)
            
        except Exception as e:
            logger.warning(f"清理过期缓存失败: {e}")
            return 0


def cache_query(ttl: int = 300, key_prefix: str = ""):
    """
    查询缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            
            # 生成缓存键
            cache_key = cache_manager.generate_cache_key(
                func.__name__, key_prefix, *args, **kwargs
            )
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存储到缓存
            cache_manager.set(cache_key, result)
            
            return result
        
        return wrapper
    return decorator


# 全局缓存管理器实例
cache_manager = CacheManager()