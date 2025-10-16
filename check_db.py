import sqlite3
from database import DatabaseManager

def comprehensive_database_check():
    """全面检查数据库结构和完整性"""
    print("=== 全面数据库检查 ===\n")
    
    conn = sqlite3.connect('business_management.db')
    cursor = conn.cursor()
    
    # 1. 检查所有表结构
    print("1️⃣ 表结构检查:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    expected_tables = ['customers', 'fabrics', 'bag_categories', 'bag_types', 'inventory', 'orders', 'order_items']
    existing_tables = [table[0] for table in tables if table[0] != 'sqlite_sequence']
    
    print(f"   发现表: {existing_tables}")
    print(f"   期望表: {expected_tables}")
    
    missing_tables = set(expected_tables) - set(existing_tables)
    extra_tables = set(existing_tables) - set(expected_tables)
    
    if missing_tables:
        print(f"   ❌ 缺少表: {missing_tables}")
    if extra_tables:
        print(f"   ⚠️ 额外表: {extra_tables}")
    if not missing_tables and not extra_tables:
        print("   ✅ 所有期望的表都存在")
    
    # 2. 检查外键关系
    print("\n2️⃣ 外键关系检查:")
    
    # 检查order_items表的外键
    cursor.execute("PRAGMA table_info(order_items);")
    order_items_columns = [col[1] for col in cursor.fetchall()]
    
    expected_fk_columns = ['order_id', 'inventory_id', 'bag_type_id', 'outer_fabric_id', 'inner_fabric_id']
    missing_fk = [col for col in expected_fk_columns if col not in order_items_columns]
    
    if missing_fk:
        print(f"   ❌ order_items表缺少外键列: {missing_fk}")
    else:
        print("   ✅ order_items表外键列完整")
    
    # 3. 检查数据完整性
    print("\n3️⃣ 数据完整性检查:")
    
    # 检查是否有孤立的外键引用
    checks = [
        ("orders", "customer_id", "customers", "id"),
        ("order_items", "order_id", "orders", "id"),
        ("order_items", "inventory_id", "inventory", "id"),
        ("order_items", "bag_type_id", "bag_types", "id"),
        ("order_items", "outer_fabric_id", "fabrics", "id"),
        ("order_items", "inner_fabric_id", "fabrics", "id"),
    ]
    
    for child_table, child_col, parent_table, parent_col in checks:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {child_table} 
                WHERE {child_col} IS NOT NULL 
                AND {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
            """)
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                print(f"   ❌ {child_table}.{child_col} 有 {orphaned} 个孤立引用")
            else:
                print(f"   ✅ {child_table}.{child_col} 引用完整")
        except sqlite3.Error as e:
            print(f"   ⚠️ 检查 {child_table}.{child_col} 时出错: {e}")
    
    # 4. 检查数据统计
    print("\n4️⃣ 数据统计:")
    for table in existing_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count} 条记录")
        except sqlite3.Error as e:
            print(f"   ❌ 无法统计 {table}: {e}")
    
    # 5. 检查索引
    print("\n5️⃣ 索引检查:")
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';")
    indexes = cursor.fetchall()
    
    if indexes:
        print("   发现的索引:")
        for idx_name, table_name in indexes:
            print(f"     - {idx_name} (在表 {table_name})")
    else:
        print("   ⚠️ 没有发现自定义索引，可能影响查询性能")
    
    conn.close()
    print("\n=== 检查完成 ===")

def test_database_operations():
    """测试数据库操作"""
    print("\n=== 数据库操作测试 ===\n")
    
    try:
        db = DatabaseManager()
        
        # 测试获取面料
        print("1️⃣ 测试获取面料:")
        fabrics = db.get_fabrics()
        print(f"   ✅ 成功获取 {len(fabrics)} 个面料")
        
        # 测试获取客户
        print("\n2️⃣ 测试获取客户:")
        customers = db.get_customers()
        print(f"   ✅ 成功获取 {len(customers)} 个客户")
        
        # 测试获取订单
        print("\n3️⃣ 测试获取订单:")
        orders = db.get_orders()
        print(f"   ✅ 成功获取 {len(orders)} 个订单")
        
        print("\n✅ 所有基本操作测试通过")
        
    except Exception as e:
        print(f"❌ 数据库操作测试失败: {e}")

if __name__ == "__main__":
    comprehensive_database_check()
    test_database_operations()