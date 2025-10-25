# 编码规范 - NULL值处理

## 概述

本文档定义了项目中处理NULL值和已删除关联数据的编码标准，确保用户界面始终显示友好的信息而不是"None"或空值。

## 核心原则

1. **防御性显示**: 始终假设数据可能为NULL或已删除
2. **用户友好**: 显示有意义的默认值而不是技术术语
3. **一致性**: 在整个应用中使用统一的处理方式
4. **可维护性**: 使用集中化的工具函数

## 必须遵循的规则

### ✅ 安全的字段访问模式

#### 1. 使用 `utils.display_utils` 中的格式化函数（推荐）

```python
from utils.display_utils import format_item_display, format_fabric_display, format_customer_display

# 商品名称显示
item_name = format_item_display(item)  # 自动处理已删除商品

# 面料名称显示
outer_fabric = format_fabric_display(item, 'outer')  # 自动处理已删除面料
inner_fabric = format_fabric_display(item, 'inner')

# 客户名称显示
customer_name = format_customer_display(order)  # 自动处理已删除客户
```

#### 2. 使用 `safe_get` 函数

```python
from utils.display_utils import safe_get

# 安全获取字段值
inventory_name = safe_get(item, 'inventory_name', '未知商品')
customer_phone = safe_get(customer, 'phone_suffix', '无')
```

#### 3. 使用 `.get()` 方法并提供默认值

```python
# 基本字段访问
item_name = item.get('inventory_name', '未知商品')
fabric_name = item.get('fabric_name', '未指定面料')
customer_name = order.get('customer_name', '未知客户')
```

#### 4. 使用 `or` 操作符

```python
# 简单的空值处理
display_name = item['inventory_name'] or '已删除的商品'
notes = order['notes'] or '无备注'
```

### ❌ 禁止的不安全模式

#### 1. 直接字典访问（可能导致KeyError或显示None）

```python
# ❌ 错误 - 可能抛出KeyError
item_name = item['inventory_name']

# ❌ 错误 - 可能显示None
st.write(f"商品: {item['inventory_name']}")
```

#### 2. 不带默认值的 `.get()` 调用

```python
# ❌ 错误 - 可能返回None
item_name = item.get('inventory_name')
```

#### 3. 在显示逻辑中直接使用可能为None的变量

```python
# ❌ 错误 - 可能显示"None"
st.write(f"客户: {customer_name}")  # 如果customer_name为None
```

## 默认值规范

### 标准默认值

| 字段类型 | 默认值 | 说明 |
|---------|--------|------|
| 商品名称 | `'已删除的商品'` | 库存商品被删除时 |
| 定制商品 | `'定制商品'` | 定制类型商品 |
| 面料名称 | `'已删除的面料'` | 面料被删除但ID存在时 |
| 客户名称 | `'已删除的客户'` | 客户被删除时 |
| 加工商名称 | `'已删除的加工商'` | 加工商被删除时 |
| 备注信息 | `'无'` 或 `'无备注'` | 没有备注时 |
| 电话号码 | `'无'` | 没有电话信息时 |

### 特殊情况处理

```python
# 面料显示 - 区分无面料和已删除面料
def format_fabric_display(item, fabric_type):
    fabric_name = item.get(f'{fabric_type}_fabric_name')
    fabric_id = item.get(f'{fabric_type}_fabric_id')
    
    if fabric_name:
        return fabric_name
    elif fabric_id:
        return '已删除的面料'  # 有ID但无名称，说明被删除
    else:
        return None  # 完全没有面料信息
```

## 工具函数使用指南

### `utils.display_utils` 模块

#### 核心函数

1. **`safe_get(dict_obj, key, default)`**
   - 安全获取字典值
   - 自动处理None和空字符串

2. **`format_item_display(item, item_type='现货')`**
   - 格式化商品显示名称
   - 自动处理已删除商品

3. **`format_fabric_display(item, fabric_type)`**
   - 格式化面料显示名称
   - fabric_type: 'outer'(表布) 或 'inner'(里布)

4. **`format_customer_display(order)`**
   - 格式化客户显示名称
   - 自动处理已删除客户

5. **`format_processor_display(order)`**
   - 格式化加工商显示名称
   - 自动处理已删除加工商

6. **`format_order_item_line(item)`**
   - 格式化完整的订单项显示行
   - 包含商品名称、面料信息等

## 代码审查检查清单

### 提交代码前必须检查

- [ ] 没有直接使用 `item['field_name']` 访问可能为空的字段
- [ ] 所有 `.get()` 调用都提供了合适的默认值
- [ ] 显示逻辑中使用了安全的字段访问模式
- [ ] 使用了 `utils.display_utils` 中的格式化函数
- [ ] 运行 `python code_checker.py` 没有发现问题

### 自动化检查

项目包含 `code_checker.py` 脚本，可以自动检测不安全的字段访问模式：

```bash
# 运行代码检查
python code_checker.py

# 检查特定文件
python code_checker.py --file main.py
```

## 示例代码

### 订单详情显示

```python
from utils.display_utils import format_order_item_line, format_customer_display

# 安全的订单显示
def display_order_details(order):
    customer_name = format_customer_display(order)
    st.write(f"客户: {customer_name}")
    
    for item in order['items']:
        item_line = format_order_item_line(item)
        st.write(item_line)
```

### 导出功能

```python
from utils.display_utils import format_item_display, format_fabric_display

# CSV导出中的安全字段访问
def export_order_item(item):
    item_name = format_item_display(item)
    outer_fabric = format_fabric_display(item, 'outer') or '无'
    inner_fabric = format_fabric_display(item, 'inner') or '无'
    
    return {
        '商品名称': item_name,
        '表布': outer_fabric,
        '里布': inner_fabric
    }
```

## 常见错误和解决方案

### 错误1: 显示"None"

```python
# ❌ 问题代码
st.write(f"客户: {order['customer_name']}")  # 可能显示 "客户: None"

# ✅ 正确做法
customer_name = format_customer_display(order)
st.write(f"客户: {customer_name}")  # 显示 "客户: 已删除的客户"
```

### 错误2: KeyError异常

```python
# ❌ 问题代码
fabric_name = item['outer_fabric_name']  # 可能抛出KeyError

# ✅ 正确做法
fabric_name = format_fabric_display(item, 'outer')
```

### 错误3: 不一致的默认值

```python
# ❌ 问题代码 - 不同地方使用不同默认值
name1 = item.get('inventory_name', '未知')
name2 = item.get('inventory_name', '无商品')

# ✅ 正确做法 - 使用统一的格式化函数
name1 = format_item_display(item)
name2 = format_item_display(item)
```

## 维护和更新

1. **新增字段**: 如果添加新的可能为NULL的字段，需要在 `display_utils.py` 中添加相应的格式化函数
2. **默认值更新**: 如果需要修改默认值，只需在 `display_utils.py` 中的 `DEFAULT_VALUES` 常量中修改
3. **代码检查**: 定期运行 `code_checker.py` 确保代码质量

---

**记住**: 用户永远不应该看到"None"、"null"或空白值。始终提供有意义的默认显示内容！