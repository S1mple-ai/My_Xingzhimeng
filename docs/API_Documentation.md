# 📚 API 文档

## 概述

星之梦手作管理系统提供了完整的 API 接口，支持所有核心业务功能的编程访问。本文档详细介绍了各个模块的 API 使用方法。

## 🗄️ 数据库管理 API

### DatabaseManager 类

主要的数据库管理类，提供所有数据操作接口。

#### 初始化
```python
from database import DatabaseManager

db = DatabaseManager()
```

#### 客户管理 API

##### 获取所有客户
```python
customers = db.get_customers()
# 返回: List[Dict] - 客户信息列表
```

##### 添加客户
```python
customer_id = db.add_customer(
    name="客户姓名",
    phone="手机号码",
    address="客户地址",
    points=0  # 初始积分
)
# 返回: int - 新客户ID
```

##### 更新客户信息
```python
success = db.update_customer(
    customer_id=1,
    name="新姓名",
    phone="新手机号",
    address="新地址"
)
# 返回: bool - 操作是否成功
```

##### 删除客户
```python
success = db.delete_customer(customer_id=1)
# 返回: bool - 操作是否成功
```

##### 更新客户积分
```python
success = db.update_customer_points(
    customer_id=1,
    points=100
)
# 返回: bool - 操作是否成功
```

#### 面料管理 API

##### 获取所有面料
```python
fabrics = db.get_fabrics()
# 返回: List[Dict] - 面料信息列表
```

##### 添加面料
```python
fabric_id = db.add_fabric(
    name="面料名称",
    material_type="细帆",  # 细帆/细帆绗棉/缎面绗棉
    usage_type="表布",     # 表布/里布
    image_path="图片路径"
)
# 返回: int - 新面料ID
```

##### 更新面料信息
```python
success = db.update_fabric(
    fabric_id=1,
    name="新名称",
    material_type="细帆绗棉",
    usage_type="里布",
    image_path="新图片路径"
)
# 返回: bool - 操作是否成功
```

##### 删除面料
```python
success = db.delete_fabric(fabric_id=1)
# 返回: bool - 操作是否成功
```

#### 包型管理 API

##### 获取包型分类
```python
categories = db.get_bag_categories()
# 返回: List[Dict] - 分类信息列表
```

##### 添加包型分类
```python
category_id = db.add_bag_category(
    name="分类名称",
    parent_id=None  # 父分类ID，None表示顶级分类
)
# 返回: int - 新分类ID
```

##### 获取包型列表
```python
bag_styles = db.get_bag_styles()
# 返回: List[Dict] - 包型信息列表
```

##### 添加包型
```python
style_id = db.add_bag_style(
    name="包型名称",
    category_id=1,
    price=299.00,
    image_path="图片路径",
    video_path="视频路径"
)
# 返回: int - 新包型ID
```

#### 库存管理 API

##### 获取库存列表
```python
inventory = db.get_inventory()
# 返回: List[Dict] - 库存信息列表
```

##### 添加库存商品
```python
item_id = db.add_inventory_item(
    product_name="商品名称",
    quantity=10,
    price=199.00,
    description="商品描述",
    image_path="图片路径"
)
# 返回: int - 新商品ID
```

##### 更新库存数量
```python
success = db.update_inventory_quantity(
    item_id=1,
    quantity=20
)
# 返回: bool - 操作是否成功
```

#### 订单管理 API

##### 获取订单列表
```python
orders = db.get_orders()
# 返回: List[Dict] - 订单信息列表
```

##### 创建订单
```python
order_id = db.create_order(
    customer_id=1,
    total_amount=299.00,
    status="待处理",
    notes="订单备注"
)
# 返回: int - 新订单ID
```

##### 添加订单商品
```python
success = db.add_order_item(
    order_id=1,
    item_type="现货",  # 现货/定制
    item_id=1,
    quantity=2,
    price=199.00
)
# 返回: bool - 操作是否成功
```

##### 更新订单状态
```python
success = db.update_order_status(
    order_id=1,
    status="已完成"
)
# 返回: bool - 操作是否成功
```

## 🚀 缓存管理 API

### CacheManager 类

提供智能缓存管理功能。

#### 基本使用
```python
from cache_manager import cache_manager

# 设置缓存
cache_manager.set("key", "value", ttl=3600)

# 获取缓存
value = cache_manager.get("key")

# 删除缓存
cache_manager.delete("key")

# 清空所有缓存
cache_manager.clear()
```

#### 装饰器使用
```python
from cache_manager import smart_cache

@smart_cache(ttl=1800, key_prefix="customers")
def get_customer_data(customer_id):
    # 数据获取逻辑
    return data
```

## 📊 性能监控 API

### PerformanceMonitor 类

提供系统性能监控功能。

#### 基本使用
```python
from performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()

# 开始监控
monitor.start_monitoring("operation_name")

# 结束监控
monitor.end_monitoring("operation_name")

# 获取性能报告
report = monitor.get_performance_report()
```

#### 装饰器使用
```python
from performance_monitor import monitor_execution_time

@monitor_execution_time
def expensive_operation():
    # 耗时操作
    pass
```

## 📝 日志系统 API

### SystemLogger 类

提供统一的日志管理功能。

#### 基本使用
```python
from utils.logger import SystemLogger

logger = SystemLogger()

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

#### 装饰器使用
```python
from utils.logger import log_exceptions, log_performance

@log_exceptions()
@log_performance()
def business_function():
    # 业务逻辑
    pass
```

## 🔧 服务层 API

### DashboardService 类

提供仪表板数据服务。

```python
from services import DashboardService

service = DashboardService(db)

# 获取仪表板统计数据
stats = service.get_dashboard_stats()

# 获取订单趋势数据
trends = service.get_order_trends()

# 获取库存预警
alerts = service.get_inventory_alerts()
```

### ExportService 类

提供数据导出服务。

```python
from services import ExportService

service = ExportService(db)

# 导出客户数据
customer_data = service.export_customers()

# 导出订单数据
order_data = service.export_orders(start_date, end_date)

# 导出库存数据
inventory_data = service.export_inventory()
```

## 🛠️ 工具类 API

### 状态管理
```python
from utils.state_manager import state_manager

# 获取状态
value = state_manager.get("key")

# 设置状态
state_manager.set("key", "value")

# 清除状态
state_manager.clear("key")
```

### 异常处理
```python
from utils.exception_handler import GlobalExceptionHandler

# 设置全局异常处理
handler = GlobalExceptionHandler()
handler.setup()
```

## 📋 数据模型

### 客户模型
```python
{
    "id": int,
    "name": str,
    "phone": str,
    "address": str,
    "points": int,
    "created_at": str
}
```

### 面料模型
```python
{
    "id": int,
    "name": str,
    "material_type": str,  # 细帆/细帆绗棉/缎面绗棉
    "usage_type": str,     # 表布/里布
    "image_path": str,
    "created_at": str
}
```

### 包型模型
```python
{
    "id": int,
    "name": str,
    "category_id": int,
    "price": float,
    "image_path": str,
    "video_path": str,
    "created_at": str
}
```

### 库存模型
```python
{
    "id": int,
    "product_name": str,
    "quantity": int,
    "price": float,
    "description": str,
    "image_path": str,
    "created_at": str
}
```

### 订单模型
```python
{
    "id": int,
    "customer_id": int,
    "total_amount": float,
    "status": str,
    "notes": str,
    "created_at": str
}
```

## 🔒 错误处理

所有 API 方法都包含适当的错误处理机制：

- **数据库错误**：自动回滚事务，记录错误日志
- **参数验证**：检查必需参数和数据类型
- **业务逻辑错误**：返回明确的错误信息
- **系统异常**：全局异常捕获和处理

## 📈 性能优化

- **查询优化**：使用索引和优化的 SQL 查询
- **缓存机制**：智能缓存频繁访问的数据
- **批量操作**：支持批量数据处理
- **连接池**：数据库连接池管理

## 🔍 调试和测试

### 启用调试模式
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 性能测试
```python
from performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
# 执行性能测试
report = monitor.run_performance_test()
```

---

**注意**：本 API 文档会随着系统更新而持续更新，请关注最新版本。