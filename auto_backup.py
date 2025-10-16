"""
自动备份模块
实现每日自动备份功能，包括客户管理、面料管理、包型管理、订单管理数据
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Any
import streamlit as st


class AutoBackup:
    def __init__(self, db_manager):
        self.db = db_manager
        self.backup_dir = "backups"
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_today_date(self) -> str:
        """获取今天的日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_backup_filename(self, data_type: str) -> str:
        """生成备份文件名"""
        today = self.get_today_date()
        return f"{data_type}_backup_{today}.json"
    
    def get_backup_filepath(self, data_type: str) -> str:
        """获取备份文件完整路径"""
        filename = self.get_backup_filename(data_type)
        return os.path.join(self.backup_dir, filename)
    
    def is_backup_exists_today(self, data_type: str) -> bool:
        """检查今天是否已经备份了指定类型的数据"""
        filepath = self.get_backup_filepath(data_type)
        return os.path.exists(filepath)
    
    def backup_customers(self) -> bool:
        """备份客户数据"""
        try:
            customers = self.db.get_customers()
            filepath = self.get_backup_filepath("customers")
            
            # 转换数据格式，确保可以JSON序列化
            backup_data = {
                "backup_date": self.get_today_date(),
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_type": "customers",
                "count": len(customers),
                "data": customers
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"❌ 客户数据备份失败: {str(e)}")
            return False
    
    def backup_fabrics(self) -> bool:
        """备份面料数据"""
        try:
            fabrics = self.db.get_fabrics()
            filepath = self.get_backup_filepath("fabrics")
            
            backup_data = {
                "backup_date": self.get_today_date(),
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_type": "fabrics",
                "count": len(fabrics),
                "data": fabrics
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"❌ 面料数据备份失败: {str(e)}")
            return False
    
    def backup_bag_types(self) -> bool:
        """备份包型数据"""
        try:
            bag_types = self.db.get_bag_types()
            filepath = self.get_backup_filepath("bag_types")
            
            backup_data = {
                "backup_date": self.get_today_date(),
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_type": "bag_types",
                "count": len(bag_types),
                "data": bag_types
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"❌ 包型数据备份失败: {str(e)}")
            return False
    
    def backup_orders(self) -> bool:
        """备份订单数据（包含订单项）"""
        try:
            # 获取所有订单
            orders = self.db.get_orders()
            
            # 为每个订单获取详细信息和订单项
            detailed_orders = []
            for order in orders:
                order_items = self.db.get_order_items(order['id'])
                order_with_items = order.copy()
                order_with_items['items'] = order_items
                detailed_orders.append(order_with_items)
            
            filepath = self.get_backup_filepath("orders")
            
            backup_data = {
                "backup_date": self.get_today_date(),
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_type": "orders",
                "count": len(detailed_orders),
                "data": detailed_orders
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"❌ 订单数据备份失败: {str(e)}")
            return False
    
    def backup_inventory(self) -> bool:
        """备份库存数据"""
        try:
            inventory = self.db.get_inventory_items()
            filepath = self.get_backup_filepath("inventory")
            
            backup_data = {
                "backup_date": self.get_today_date(),
                "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_type": "inventory",
                "count": len(inventory),
                "data": inventory
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"❌ 库存数据备份失败: {str(e)}")
            return False
    
    def perform_daily_backup(self) -> Dict[str, bool]:
        """执行每日备份"""
        backup_results = {}
        data_types = ["customers", "fabrics", "bag_types", "orders", "inventory"]
        
        for data_type in data_types:
            # 检查今天是否已经备份
            if self.is_backup_exists_today(data_type):
                backup_results[data_type] = "already_exists"
                continue
            
            # 执行备份
            if data_type == "customers":
                backup_results[data_type] = self.backup_customers()
            elif data_type == "fabrics":
                backup_results[data_type] = self.backup_fabrics()
            elif data_type == "bag_types":
                backup_results[data_type] = self.backup_bag_types()
            elif data_type == "orders":
                backup_results[data_type] = self.backup_orders()
            elif data_type == "inventory":
                backup_results[data_type] = self.backup_inventory()
        
        return backup_results
    
    def perform_force_backup(self) -> Dict[str, bool]:
        """强制执行完整备份（忽略今日是否已备份）"""
        backup_results = {}
        data_types = ["customers", "fabrics", "bag_types", "orders", "inventory"]
        
        for data_type in data_types:
            # 强制执行备份，不检查今日是否已备份
            if data_type == "customers":
                backup_results[data_type] = self.backup_customers()
            elif data_type == "fabrics":
                backup_results[data_type] = self.backup_fabrics()
            elif data_type == "bag_types":
                backup_results[data_type] = self.backup_bag_types()
            elif data_type == "orders":
                backup_results[data_type] = self.backup_orders()
            elif data_type == "inventory":
                backup_results[data_type] = self.backup_inventory()
        
        return backup_results
    
    def get_backup_summary(self) -> Dict[str, Any]:
        """获取备份摘要信息"""
        today = self.get_today_date()
        data_types = ["customers", "fabrics", "bag_types", "orders", "inventory"]
        
        summary = {
            "backup_date": today,
            "backups": {}
        }
        
        for data_type in data_types:
            filepath = self.get_backup_filepath(data_type)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    summary["backups"][data_type] = {
                        "exists": True,
                        "count": backup_data.get("count", 0),
                        "backup_time": backup_data.get("backup_time", "未知"),
                        "file_size": os.path.getsize(filepath)
                    }
                except Exception:
                    summary["backups"][data_type] = {
                        "exists": True,
                        "count": 0,
                        "backup_time": "读取失败",
                        "file_size": os.path.getsize(filepath)
                    }
            else:
                summary["backups"][data_type] = {
                    "exists": False,
                    "count": 0,
                    "backup_time": "未备份",
                    "file_size": 0
                }
        
        return summary
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """清理旧的备份文件，保留指定天数的备份"""
        try:
            current_time = datetime.now()
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    # 如果文件超过保留天数，则删除
                    if (current_time - file_time).days > keep_days:
                        os.remove(filepath)
                        
        except Exception as e:
            st.error(f"❌ 清理旧备份失败: {str(e)}")


def check_and_perform_backup(db_manager, force_backup: bool = False) -> bool:
    """检查并执行自动备份"""
    backup_manager = AutoBackup(db_manager)
    
    # 执行每日备份
    if force_backup:
        # 强制备份所有数据
        results = backup_manager.perform_force_backup()
    else:
        results = backup_manager.perform_daily_backup()
    
    # 统计结果
    new_backups = sum(1 for result in results.values() if result is True)
    existing_backups = sum(1 for result in results.values() if result == "already_exists")
    failed_backups = sum(1 for result in results.values() if result is False)
    
    # 显示备份结果
    if new_backups > 0:
        st.success(f"✅ 成功备份 {new_backups} 个数据模块")
    
    if existing_backups > 0:
        st.info(f"ℹ️ {existing_backups} 个数据模块今日已备份")
    
    if failed_backups > 0:
        st.error(f"❌ {failed_backups} 个数据模块备份失败")
    
    # 清理30天前的旧备份
    backup_manager.cleanup_old_backups(30)
    
    return failed_backups == 0