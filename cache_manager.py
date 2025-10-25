"""
缓存管理模块
提供智能缓存功能和缓存指标监控
"""

import time
import hashlib
import pickle
import threading
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheMetrics:
    """缓存指标监控"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_requests = 0
        self.total_size = 0
        self.lock = threading.Lock()
        self.start_time = datetime.now()
    
    def record_hit(self, size: int = 0):
        """记录缓存命中"""
        with self.lock:
            self.hits += 1
            self.total_requests += 1
    
    def record_miss(self, size: int = 0):
        """记录缓存未命中"""
        with self.lock:
            self.misses += 1
            self.total_requests += 1
            self.total_size += size
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        with self.lock:
            return self.hits / self.total_requests if self.total_requests > 0 else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            uptime = datetime.now() - self.start_time
            return {
                'hits': self.hits,
                'misses': self.misses,
                'total_requests': self.total_requests,
                'hit_rate': self.get_hit_rate(),
                'total_size_mb': self.total_size / (1024 * 1024),
                'uptime_seconds': uptime.total_seconds()
            }
    
    def reset(self):
        """重置统计"""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.total_requests = 0
            self.total_size = 0
            self.start_time = datetime.now()


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl else None
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """访问缓存项"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    def get_size(self) -> int:
        """获取缓存项大小（字节）"""
        try:
            return len(pickle.dumps(self.value))
        except:
            return 0


class SmartCacheManager:
    """智能缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.cache: Dict[str, CacheItem] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        self.metrics = CacheMetrics()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if item.is_expired()
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if len(self.cache) >= self.max_size:
            # 按最后访问时间排序，删除最久未访问的
            lru_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].last_accessed
            )
            del self.cache[lru_key]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        with self.lock:
            self._cleanup_expired()
            
            if key in self.cache:
                item = self.cache[key]
                if not item.is_expired():
                    self.metrics.record_hit()
                    return item.access()
                else:
                    del self.cache[key]
            
            self.metrics.record_miss()
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值"""
        with self.lock:
            self._cleanup_expired()
            self._evict_lru()
            
            ttl = ttl or self.default_ttl
            item = CacheItem(value, ttl)
            self.cache[key] = item
            
            # 记录缓存大小
            self.metrics.record_miss(item.get_size())
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.metrics.reset()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            cache_size = len(self.cache)
            total_memory = sum(item.get_size() for item in self.cache.values())
            
            stats = self.metrics.get_stats()
            stats.update({
                'cache_size': cache_size,
                'max_size': self.max_size,
                'memory_usage_mb': total_memory / (1024 * 1024),
                'fill_rate': cache_size / self.max_size
            })
            
            return stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取详细缓存信息"""
        with self.lock:
            items_info = []
            for key, item in self.cache.items():
                items_info.append({
                    'key': key[:20] + '...' if len(key) > 20 else key,
                    'size_bytes': item.get_size(),
                    'access_count': item.access_count,
                    'created_at': datetime.fromtimestamp(item.created_at).isoformat(),
                    'last_accessed': datetime.fromtimestamp(item.last_accessed).isoformat(),
                    'expires_at': datetime.fromtimestamp(item.expires_at).isoformat() if item.expires_at else None,
                    'is_expired': item.is_expired()
                })
            
            return {
                'items': sorted(items_info, key=lambda x: x['last_accessed'], reverse=True),
                'stats': self.get_stats()
            }


# 全局缓存管理器实例
cache_manager = SmartCacheManager()


def smart_cache(ttl: Optional[float] = None, key_func: Optional[Callable] = None):
    """
    智能缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        key_func: 自定义键生成函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{cache_manager._generate_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda: cache_manager.clear()
        wrapper.cache_info = lambda: cache_manager.get_stats()
        
        return wrapper
    return decorator


def cache_key_generator(*args, **kwargs) -> str:
    """生成缓存键"""
    return cache_manager._generate_key(*args, **kwargs)


def invalidate_cache_pattern(pattern: str) -> int:
    """
    根据模式删除缓存
    
    Args:
        pattern: 键模式（支持简单的通配符）
    
    Returns:
        删除的缓存项数量
    """
    deleted_count = 0
    with cache_manager.lock:
        keys_to_delete = []
        for key in cache_manager.cache.keys():
            if pattern in key:  # 简单的包含匹配
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            cache_manager.delete(key)
            deleted_count += 1
    
    return deleted_count


# 便捷函数
def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return cache_manager.get_stats()


def clear_all_cache() -> None:
    """清空所有缓存"""
    cache_manager.clear()


def get_cache_info() -> Dict[str, Any]:
    """获取详细缓存信息"""
    return cache_manager.get_cache_info()


# 示例使用
if __name__ == "__main__":
    # 测试缓存功能
    @smart_cache(ttl=60)
    def expensive_function(x: int, y: int) -> int:
        time.sleep(0.1)  # 模拟耗时操作
        return x + y
    
    # 测试缓存
    print("First call:")
    start = time.time()
    result1 = expensive_function(1, 2)
    print(f"Result: {result1}, Time: {time.time() - start:.4f}s")
    
    print("Second call (cached):")
    start = time.time()
    result2 = expensive_function(1, 2)
    print(f"Result: {result2}, Time: {time.time() - start:.4f}s")
    
    # 获取缓存统计
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
    
    # 获取详细信息
    info = get_cache_info()
    print(f"Cache info: {info}")