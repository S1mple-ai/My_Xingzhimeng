"""
项目配置管理

集中管理项目的所有配置项，包括数据库配置、UI配置、业务配置等。
支持从环境变量加载配置，便于不同环境的配置管理。
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "business_management.db"
    connection_timeout: int = 30
    query_timeout: int = 60
    max_connections: int = 10
    
    # 缓存配置
    cache_ttl_default: int = 300  # 5分钟
    cache_ttl_customers: int = 300
    cache_ttl_fabrics: int = 600  # 10分钟
    cache_ttl_inventory: int = 180  # 3分钟
    cache_ttl_orders: int = 60  # 1分钟
    cache_ttl_dashboard: int = 300


@dataclass
class UIConfig:
    """UI界面配置"""
    page_title: str = "星之梦手工定制管理系统"
    page_icon: str = "👗"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    
    # 分页配置
    page_size_options: List[int] = field(default_factory=lambda: [10, 20, 50])
    default_page_size: int = 10
    
    # 颜色主题
    primary_color: str = "#FF6B6B"
    secondary_color: str = "#4ECDC4"
    success_color: str = "#45B7D1"
    warning_color: str = "#FFA07A"
    error_color: str = "#FF6B6B"
    
    # 图表配置
    chart_height: int = 400
    chart_background_color: str = "rgba(0,0,0,0)"
    chart_paper_color: str = "rgba(0,0,0,0)"
    chart_font_color: str = "#2D3748"
    chart_font_size: int = 16


@dataclass
class BusinessConfig:
    """业务配置"""
    # 积分系统
    points_per_yuan: int = 1
    min_points_for_discount: int = 100
    max_discount_percentage: float = 20.0
    
    # 订单状态
    order_statuses: List[str] = field(default_factory=lambda: [
        "pending", "confirmed", "in_production", "completed", "cancelled"
    ])
    
    order_status_display: Dict[str, str] = field(default_factory=lambda: {
        "pending": "待确认",
        "confirmed": "已确认",
        "in_production": "生产中",
        "completed": "已完成",
        "cancelled": "已取消"
    })
    
    # 商品类型
    product_types: List[str] = field(default_factory=lambda: ["inventory", "custom"])
    product_type_display: Dict[str, str] = field(default_factory=lambda: {
        "inventory": "现货",
        "custom": "定制"
    })
    
    # 面料类型
    fabric_types: List[str] = field(default_factory=lambda: ["表布", "里布"])
    
    # 导出配置
    export_formats: List[str] = field(default_factory=lambda: ["csv", "pdf"])
    max_export_records: int = 1000
    
    # PDF导出配置
    pdf_page_width_mm: float = 76.0
    pdf_page_height_mm: float = 130.0


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 数据库查询优化
    enable_query_cache: bool = True
    enable_connection_pool: bool = True
    
    # 批量操作配置
    batch_size: int = 100
    max_batch_operations: int = 1000
    
    # 内存管理
    max_memory_usage_mb: int = 512
    cleanup_interval_minutes: int = 30


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/app.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # 日志级别映射
    level_mapping: Dict[str, int] = field(default_factory=lambda: {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    })


class Config:
    """主配置类"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.ui = UIConfig()
        self.business = BusinessConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量加载配置"""
        config = cls()
        
        # 数据库配置
        config.database.db_path = os.getenv("DB_PATH", config.database.db_path)
        config.database.connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", config.database.connection_timeout))
        config.database.query_timeout = int(os.getenv("DB_QUERY_TIMEOUT", config.database.query_timeout))
        
        # 缓存配置
        config.database.cache_ttl_default = int(os.getenv("CACHE_TTL_DEFAULT", config.database.cache_ttl_default))
        config.database.cache_ttl_customers = int(os.getenv("CACHE_TTL_CUSTOMERS", config.database.cache_ttl_customers))
        config.database.cache_ttl_fabrics = int(os.getenv("CACHE_TTL_FABRICS", config.database.cache_ttl_fabrics))
        config.database.cache_ttl_inventory = int(os.getenv("CACHE_TTL_INVENTORY", config.database.cache_ttl_inventory))
        config.database.cache_ttl_orders = int(os.getenv("CACHE_TTL_ORDERS", config.database.cache_ttl_orders))
        config.database.cache_ttl_dashboard = int(os.getenv("CACHE_TTL_DASHBOARD", config.database.cache_ttl_dashboard))
        
        # UI配置
        config.ui.page_title = os.getenv("PAGE_TITLE", config.ui.page_title)
        config.ui.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", config.ui.default_page_size))
        
        # 业务配置
        config.business.points_per_yuan = int(os.getenv("POINTS_PER_YUAN", config.business.points_per_yuan))
        config.business.max_export_records = int(os.getenv("MAX_EXPORT_RECORDS", config.business.max_export_records))
        
        # 性能配置
        config.performance.enable_query_cache = os.getenv("ENABLE_QUERY_CACHE", "true").lower() == "true"
        config.performance.batch_size = int(os.getenv("BATCH_SIZE", config.performance.batch_size))
        config.performance.max_memory_usage_mb = int(os.getenv("MAX_MEMORY_USAGE_MB", config.performance.max_memory_usage_mb))
        
        # 日志配置
        config.logging.level = os.getenv("LOG_LEVEL", config.logging.level)
        config.logging.file_path = os.getenv("LOG_FILE_PATH", config.logging.file_path)
        
        return config
    
    def get_page_config(self) -> Dict[str, Any]:
        """获取Streamlit页面配置"""
        return {
            "page_title": self.ui.page_title,
            "page_icon": self.ui.page_icon,
            "layout": self.ui.layout,
            "initial_sidebar_state": self.ui.initial_sidebar_state
        }
    
    def get_chart_config(self) -> Dict[str, Any]:
        """获取图表配置"""
        return {
            "height": self.ui.chart_height,
            "plot_bgcolor": self.ui.chart_background_color,
            "paper_bgcolor": self.ui.chart_paper_color,
            "title_font_size": self.ui.chart_font_size,
            "title_font_color": self.ui.chart_font_color,
            "font": {"color": self.ui.chart_font_color}
        }
    
    def get_cache_config(self, cache_type: str = "default") -> int:
        """
        获取缓存配置
        
        Args:
            cache_type: 缓存类型
            
        Returns:
            缓存TTL时间（秒）
        """
        cache_mapping = {
            "default": self.database.cache_ttl_default,
            "customers": self.database.cache_ttl_customers,
            "fabrics": self.database.cache_ttl_fabrics,
            "inventory": self.database.cache_ttl_inventory,
            "orders": self.database.cache_ttl_orders,
            "dashboard": self.database.cache_ttl_dashboard
        }
        
        return cache_mapping.get(cache_type, self.database.cache_ttl_default)
    
    def validate(self) -> List[str]:
        """
        验证配置的有效性
        
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证数据库配置
        if not self.database.db_path:
            errors.append("数据库路径不能为空")
        
        if self.database.connection_timeout <= 0:
            errors.append("数据库连接超时时间必须大于0")
        
        # 验证UI配置
        if self.ui.default_page_size not in self.ui.page_size_options:
            errors.append("默认页面大小必须在可选项中")
        
        # 验证业务配置
        if self.business.points_per_yuan <= 0:
            errors.append("每元积分数必须大于0")
        
        if not (0 <= self.business.max_discount_percentage <= 100):
            errors.append("最大折扣百分比必须在0-100之间")
        
        # 验证性能配置
        if self.performance.batch_size <= 0:
            errors.append("批量操作大小必须大于0")
        
        if self.performance.max_memory_usage_mb <= 0:
            errors.append("最大内存使用量必须大于0")
        
        return errors


# 全局配置实例
config = Config.from_env()

# 验证配置
validation_errors = config.validate()
if validation_errors:
    import logging
    logger = logging.getLogger(__name__)
    for error in validation_errors:
        logger.error(f"配置验证失败: {error}")