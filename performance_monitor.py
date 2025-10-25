"""
性能监控模块
提供性能监控和执行时间跟踪功能
"""

import time
import functools
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading
import psutil
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器类"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.lock = threading.Lock()
        
    def start_timer(self, name: str) -> None:
        """开始计时"""
        with self.lock:
            self.start_times[name] = time.time()
            
    def end_timer(self, name: str) -> float:
        """结束计时并返回执行时间"""
        with self.lock:
            if name not in self.start_times:
                logger.warning(f"Timer '{name}' was not started")
                return 0.0
                
            execution_time = time.time() - self.start_times[name]
            del self.start_times[name]
            
            # 记录到metrics
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append({
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })
            
            return execution_time
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {'rss': 0, 'vms': 0, 'percent': 0}
    
    def get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取性能指标摘要"""
        with self.lock:
            summary = {}
            for name, records in self.metrics.items():
                if records:
                    times = [r['execution_time'] for r in records]
                    summary[name] = {
                        'count': len(times),
                        'total_time': sum(times),
                        'avg_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                        'last_execution': records[-1]['timestamp']
                    }
            
            # 添加系统资源信息
            summary['system'] = {
                'memory': self.get_memory_usage(),
                'cpu': self.get_cpu_usage(),
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
    
    def clear_metrics(self) -> None:
        """清空性能指标"""
        with self.lock:
            self.metrics.clear()
            self.start_times.clear()
    
    def log_performance(self, name: str, execution_time: float) -> None:
        """记录性能日志"""
        logger.info(f"Performance [{name}]: {execution_time:.4f}s")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_execution_time(name: Optional[str] = None, log_result: bool = True):
    """
    装饰器：监控函数执行时间
    
    Args:
        name: 监控名称，默认使用函数名
        log_result: 是否记录日志
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor_name = name or f"{func.__module__}.{func.__name__}"
            
            # 开始计时
            performance_monitor.start_timer(monitor_name)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 结束计时
                execution_time = performance_monitor.end_timer(monitor_name)
                
                if log_result:
                    performance_monitor.log_performance(monitor_name, execution_time)
        
        return wrapper
    return decorator


# 便捷函数
def start_monitoring(name: str) -> None:
    """开始监控"""
    performance_monitor.start_timer(name)


def stop_monitoring(name: str) -> float:
    """停止监控并返回执行时间"""
    return performance_monitor.end_timer(name)


def get_performance_summary() -> Dict[str, Any]:
    """获取性能摘要"""
    return performance_monitor.get_metrics_summary()


def clear_performance_data() -> None:
    """清空性能数据"""
    performance_monitor.clear_metrics()


# 示例使用
if __name__ == "__main__":
    # 测试性能监控
    @monitor_execution_time("test_function")
    def test_function():
        time.sleep(0.1)
        return "test"
    
    # 执行测试
    result = test_function()
    
    # 获取性能摘要
    summary = get_performance_summary()
    print("Performance Summary:")
    for name, metrics in summary.items():
        if name != 'system':
            print(f"  {name}: {metrics}")
    
    print(f"System Info: {summary.get('system', {})}")