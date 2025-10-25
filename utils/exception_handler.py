"""
全局异常处理模块
提供自动异常捕获、错误恢复和批量装饰器应用功能
"""

import sys
import traceback
import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Type
from functools import wraps
import streamlit as st

from .logger import system_logger, log_exceptions


class GlobalExceptionHandler:
    """全局异常处理器"""
    
    def __init__(self):
        self.original_excepthook = sys.excepthook
        self.exception_handlers: Dict[Type[Exception], Callable] = {}
        self.ignored_exceptions: List[Type[Exception]] = []
        
    def install(self):
        """安装全局异常处理器"""
        sys.excepthook = self._handle_exception
        
    def uninstall(self):
        """卸载全局异常处理器"""
        sys.excepthook = self.original_excepthook
        
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if exc_type in self.ignored_exceptions:
            return
            
        # 记录异常
        system_logger.error(
            f"未捕获的异常: {exc_type.__name__}",
            exception=exc_value,
            category='critical'
        )
        
        # 检查是否有自定义处理器
        if exc_type in self.exception_handlers:
            try:
                self.exception_handlers[exc_type](exc_value)
                return
            except Exception as handler_error:
                system_logger.error(
                    f"异常处理器失败: {exc_type.__name__}",
                    exception=handler_error
                )
        
        # 在Streamlit中显示友好的错误信息
        if 'streamlit' in sys.modules:
            st.error("系统发生未预期的错误，请联系管理员")
            with st.expander("错误详情"):
                st.code(f"{exc_type.__name__}: {exc_value}")
        
        # 调用原始异常处理器
        self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def register_handler(self, exc_type: Type[Exception], handler: Callable):
        """注册异常处理器"""
        self.exception_handlers[exc_type] = handler
        
    def ignore_exception(self, exc_type: Type[Exception]):
        """忽略特定类型的异常"""
        self.ignored_exceptions.append(exc_type)


class AutoDecorator:
    """自动装饰器应用器"""
    
    def __init__(self):
        self.decorated_functions = set()
        
    def apply_to_module(self, module, decorator_func: Callable, 
                       include_private: bool = False,
                       exclude_functions: List[str] = None):
        """为模块中的所有函数应用装饰器"""
        exclude_functions = exclude_functions or []
        
        for name, obj in inspect.getmembers(module):
            if self._should_decorate(name, obj, include_private, exclude_functions):
                try:
                    decorated = decorator_func(obj)
                    setattr(module, name, decorated)
                    self.decorated_functions.add(f"{module.__name__}.{name}")
                    system_logger.debug(f"已为函数 {module.__name__}.{name} 应用装饰器")
                except Exception as e:
                    system_logger.warning(f"无法为函数 {module.__name__}.{name} 应用装饰器: {e}")
    
    def apply_to_class(self, cls, decorator_func: Callable,
                      include_private: bool = False,
                      exclude_methods: List[str] = None):
        """为类中的所有方法应用装饰器"""
        exclude_methods = exclude_methods or ['__init__', '__new__', '__del__']
        
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if self._should_decorate(name, method, include_private, exclude_methods):
                try:
                    decorated = decorator_func(method)
                    setattr(cls, name, decorated)
                    self.decorated_functions.add(f"{cls.__name__}.{name}")
                    system_logger.debug(f"已为方法 {cls.__name__}.{name} 应用装饰器")
                except Exception as e:
                    system_logger.warning(f"无法为方法 {cls.__name__}.{name} 应用装饰器: {e}")
    
    def _should_decorate(self, name: str, obj: Any, include_private: bool, exclude_list: List[str]) -> bool:
        """判断是否应该装饰该对象"""
        if not callable(obj):
            return False
            
        if name in exclude_list:
            return False
            
        if not include_private and name.startswith('_'):
            return False
            
        if not inspect.isfunction(obj) and not inspect.ismethod(obj):
            return False
            
        # 避免重复装饰
        if hasattr(obj, '__wrapped__'):
            return False
            
        return True
    
    def get_decorated_functions(self) -> List[str]:
        """获取已装饰的函数列表"""
        return list(self.decorated_functions)


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """安全执行函数，捕获并记录异常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        func_name = f"{func.__module__}.{func.__name__}"
        system_logger.error(f"函数 {func_name} 执行失败", exception=e)
        
        if 'streamlit' in sys.modules:
            st.error(f"操作失败: {str(e)}")
        
        return None


def create_safe_wrapper(error_message: str = "操作失败", 
                       return_value: Any = None,
                       show_error: bool = True):
    """创建安全包装器装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = f"{func.__module__}.{func.__name__}"
                system_logger.error(f"函数 {func_name} 执行失败", exception=e)
                
                if show_error and 'streamlit' in sys.modules:
                    st.error(f"{error_message}: {str(e)}")
                
                return return_value
        return wrapper
    return decorator


def database_safe(table_name: str = None):
    """数据库操作安全装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                system_logger.database_operation(
                    operation=func.__name__,
                    table=table_name,
                    success=True
                )
                return result
            except Exception as e:
                system_logger.database_operation(
                    operation=func.__name__,
                    table=table_name,
                    success=False,
                    details={'error': str(e)}
                )
                
                if 'streamlit' in sys.modules:
                    st.error(f"数据库操作失败: {str(e)}")
                
                raise
        return wrapper
    return decorator


def ui_safe(error_message: str = "页面加载失败"):
    """UI操作安全装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = f"{func.__module__}.{func.__name__}"
                system_logger.error(f"UI函数 {func_name} 执行失败", exception=e)
                
                if 'streamlit' in sys.modules:
                    st.error(f"{error_message}，请刷新页面重试")
                    with st.expander("错误详情"):
                        st.code(str(e))
                
                return None
        return wrapper
    return decorator


# 全局实例
global_exception_handler = GlobalExceptionHandler()
auto_decorator = AutoDecorator()


def setup_global_exception_handling():
    """设置全局异常处理"""
    global_exception_handler.install()
    
    # 注册常见异常的处理器
    global_exception_handler.register_handler(
        ConnectionError,
        lambda e: system_logger.error("网络连接异常", exception=e)
    )
    
    global_exception_handler.register_handler(
        FileNotFoundError,
        lambda e: system_logger.error("文件未找到", exception=e)
    )
    
    global_exception_handler.register_handler(
        PermissionError,
        lambda e: system_logger.error("权限不足", exception=e)
    )
    
    # 忽略一些不重要的异常
    global_exception_handler.ignore_exception(KeyboardInterrupt)
    
    system_logger.info("全局异常处理已启用")


def apply_exception_handling_to_module(module_name: str):
    """为指定模块应用异常处理"""
    try:
        module = sys.modules.get(module_name)
        if module:
            auto_decorator.apply_to_module(
                module,
                log_exceptions(),
                exclude_functions=['__init__', '__new__', '__del__']
            )
            system_logger.info(f"已为模块 {module_name} 应用异常处理")
        else:
            system_logger.warning(f"模块 {module_name} 未找到")
    except Exception as e:
        system_logger.error(f"为模块 {module_name} 应用异常处理失败", exception=e)


def get_exception_statistics() -> Dict[str, Any]:
    """获取异常统计信息"""
    return {
        'total_exceptions': system_logger.get_exception_count(),
        'decorated_functions': len(auto_decorator.get_decorated_functions()),
        'decorated_function_list': auto_decorator.get_decorated_functions()
    }