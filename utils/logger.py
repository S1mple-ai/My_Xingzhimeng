"""
统一日志管理模块
提供完整的日志记录、异常捕获和调试功能
"""

import logging
import os
import sys
import traceback
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
import json
import streamlit as st


class SystemLogger:
    """系统日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.lock = threading.Lock()
        self._ensure_log_directory()
        self._setup_loggers()
        self._exception_count = 0
        
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _setup_loggers(self):
        """设置不同类型的日志记录器"""
        # 应用日志
        self.app_logger = self._create_logger(
            'app', 
            os.path.join(self.log_dir, 'app.log'),
            logging.INFO
        )
        
        # 错误日志
        self.error_logger = self._create_logger(
            'error', 
            os.path.join(self.log_dir, 'error.log'),
            logging.ERROR
        )
        
        # 调试日志
        self.debug_logger = self._create_logger(
            'debug', 
            os.path.join(self.log_dir, 'debug.log'),
            logging.DEBUG
        )
        
        # 性能日志
        self.perf_logger = self._create_logger(
            'performance', 
            os.path.join(self.log_dir, 'performance.log'),
            logging.INFO
        )
        
        # 数据库操作日志
        self.db_logger = self._create_logger(
            'database', 
            os.path.join(self.log_dir, 'database.log'),
            logging.INFO
        )
    
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """创建日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器（轮转）
        file_handler = RotatingFileHandler(
            filename, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, category: str = 'app'):
        """记录信息日志"""
        logger = getattr(self, f'{category}_logger', self.app_logger)
        logger.info(message)
    
    def warning(self, message: str, category: str = 'app'):
        """记录警告日志"""
        logger = getattr(self, f'{category}_logger', self.app_logger)
        logger.warning(message)
    
    def error(self, message: str, exception: Exception = None, category: str = 'error'):
        """记录错误日志"""
        with self.lock:
            self._exception_count += 1
        
        logger = getattr(self, f'{category}_logger', self.error_logger)
        
        if exception:
            error_info = {
                'message': message,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc(),
                'timestamp': datetime.now().isoformat()
            }
            logger.error(f"{message} - {json.dumps(error_info, ensure_ascii=False, indent=2)}")
        else:
            logger.error(message)
    
    def debug(self, message: str, category: str = 'debug'):
        """记录调试日志"""
        logger = getattr(self, f'{category}_logger', self.debug_logger)
        logger.debug(message)
    
    def performance(self, operation: str, duration: float, details: Dict = None):
        """记录性能日志"""
        perf_info = {
            'operation': operation,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            perf_info.update(details)
        
        self.perf_logger.info(f"PERFORMANCE - {json.dumps(perf_info, ensure_ascii=False)}")
    
    def database_operation(self, operation: str, table: str = None, success: bool = True, details: Dict = None):
        """记录数据库操作日志"""
        db_info = {
            'operation': operation,
            'table': table,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            db_info.update(details)
        
        level = 'info' if success else 'error'
        getattr(self.db_logger, level)(f"DB_OPERATION - {json.dumps(db_info, ensure_ascii=False)}")
    
    def get_exception_count(self) -> int:
        """获取异常计数"""
        return self._exception_count
    
    def get_log_files(self) -> List[Dict[str, Any]]:
        """获取所有日志文件信息"""
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
    
    def read_log_file(self, filename: str, lines: int = 100) -> List[str]:
        """读取日志文件内容"""
        file_path = os.path.join(self.log_dir, filename)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.error(f"读取日志文件失败: {filename}", e)
            return []
    
    def search_logs(self, keyword: str, category: str = None, days: int = 7) -> List[Dict[str, Any]]:
        """搜索日志内容"""
        results = []
        log_files = self.get_log_files()
        
        # 过滤文件
        if category:
            log_files = [f for f in log_files if f['category'] == category]
        
        # 过滤时间
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        log_files = [f for f in log_files if f['modified'].timestamp() > cutoff_date]
        
        for log_file in log_files:
            try:
                with open(log_file['path'], 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            results.append({
                                'file': log_file['name'],
                                'line_number': line_num,
                                'content': line.strip(),
                                'timestamp': log_file['modified']
                            })
            except Exception as e:
                self.error(f"搜索日志文件失败: {log_file['name']}", e)
        
        return results[:100]  # 限制结果数量
    
    def clear_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        for log_file in self.get_log_files():
            if log_file['modified'].timestamp() < cutoff_date:
                try:
                    os.remove(log_file['path'])
                    self.info(f"已清理旧日志文件: {log_file['name']}")
                except Exception as e:
                    self.error(f"清理日志文件失败: {log_file['name']}", e)


# 全局日志管理器实例
system_logger = SystemLogger()


def log_exceptions(category: str = 'error', reraise: bool = True):
    """异常捕获装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录异常信息
                func_name = f"{func.__module__}.{func.__name__}"
                system_logger.error(
                    f"函数 {func_name} 发生异常",
                    exception=e,
                    category=category
                )
                
                # 在Streamlit中显示用户友好的错误信息
                if 'streamlit' in sys.modules:
                    st.error(f"操作失败: {str(e)}")
                
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def log_performance(category: str = 'performance'):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                func_name = f"{func.__module__}.{func.__name__}"
                system_logger.performance(
                    operation=func_name,
                    duration=duration,
                    details={'success': True}
                )
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                func_name = f"{func.__module__}.{func.__name__}"
                system_logger.performance(
                    operation=func_name,
                    duration=duration,
                    details={'success': False, 'error': str(e)}
                )
                raise
        return wrapper
    return decorator


def log_database_operation(operation: str, table: str = None):
    """数据库操作日志装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                system_logger.database_operation(
                    operation=operation,
                    table=table,
                    success=True,
                    details={'function': func.__name__}
                )
                return result
            except Exception as e:
                system_logger.database_operation(
                    operation=operation,
                    table=table,
                    success=False,
                    details={'function': func.__name__, 'error': str(e)}
                )
                raise
        return wrapper
    return decorator


# 便捷函数
def log_info(message: str, category: str = 'app'):
    """记录信息日志"""
    system_logger.info(message, category)


def log_warning(message: str, category: str = 'app'):
    """记录警告日志"""
    system_logger.warning(message, category)


def log_error(message: str, exception: Exception = None, category: str = 'error'):
    """记录错误日志"""
    system_logger.error(message, exception, category)


def log_debug(message: str, category: str = 'debug'):
    """记录调试日志"""
    system_logger.debug(message, category)