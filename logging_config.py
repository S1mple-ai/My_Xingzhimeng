"""
统一日志配置模块
解决项目中分散的日志配置问题，提供统一的日志管理
"""

import logging
import os
from typing import Optional
from utils.logger import SystemLogger

# 全局日志配置
_logger_initialized = False
_system_logger: Optional[SystemLogger] = None


def init_logging(log_dir: str = "logs", log_level: str = "INFO") -> SystemLogger:
    """
    初始化统一的日志系统
    
    Args:
        log_dir: 日志文件目录
        log_level: 日志级别
        
    Returns:
        SystemLogger: 系统日志管理器实例
    """
    global _logger_initialized, _system_logger
    
    if _logger_initialized and _system_logger:
        return _system_logger
    
    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 初始化系统日志管理器
    _system_logger = SystemLogger(log_dir)
    
    # 设置根日志级别
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 禁用其他库的详细日志
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    _logger_initialized = True
    _system_logger.info("统一日志系统初始化完成", "app")
    
    return _system_logger


def get_logger() -> SystemLogger:
    """
    获取系统日志管理器实例
    
    Returns:
        SystemLogger: 系统日志管理器实例
    """
    global _system_logger
    
    if not _system_logger:
        _system_logger = init_logging()
    
    return _system_logger


def cleanup_old_logging_configs():
    """
    清理旧的日志配置
    移除根日志处理器，避免重复日志输出
    """
    root_logger = logging.getLogger()
    
    # 移除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置不传播到父级
    root_logger.propagate = False


def configure_module_logger(module_name: str) -> logging.Logger:
    """
    为模块配置标准日志记录器
    
    Args:
        module_name: 模块名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(module_name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 不传播到根日志
    logger.propagate = False
    
    return logger


# 日志级别映射
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def set_log_level(level: str):
    """
    设置全局日志级别
    
    Args:
        level: 日志级别字符串
    """
    if level.upper() in LOG_LEVELS:
        logging.getLogger().setLevel(LOG_LEVELS[level.upper()])
        get_logger().info(f"日志级别已设置为: {level.upper()}", "app")
    else:
        get_logger().warning(f"无效的日志级别: {level}", "app")


def get_log_statistics() -> dict:
    """
    获取日志统计信息
    
    Returns:
        dict: 日志统计数据
    """
    system_logger = get_logger()
    log_files = system_logger.get_log_files()
    
    stats = {
        'total_files': len(log_files),
        'total_size_mb': sum(f.get('size', 0) for f in log_files) / (1024 * 1024),
        'files_by_category': {},
        'latest_modified': None
    }
    
    for log_file in log_files:
        category = log_file.get('category', 'unknown')
        if category not in stats['files_by_category']:
            stats['files_by_category'][category] = 0
        stats['files_by_category'][category] += 1
        
        if not stats['latest_modified'] or log_file.get('modified', '') > stats['latest_modified']:
            stats['latest_modified'] = log_file.get('modified')
    
    return stats


# 导出主要接口
__all__ = [
    'init_logging',
    'get_logger',
    'cleanup_old_logging_configs',
    'configure_module_logger',
    'set_log_level',
    'get_log_statistics',
    'LOG_LEVELS'
]